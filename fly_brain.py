"""
Fly Brain - Learned flight controller with connectome-inspired reservoir

Architecture:
  sensory features -> fixed reservoir (weights sampled from MaleCNS
  connectome edges) -> learned readout (W_out) trained by behavioral
  cloning of the steering teacher, with exploration noise early on.

The reservoir weights come from real fly connectome data (subsampled),
so the "brain" has biologically-derived recurrent structure. Only the
readout is learned - cheap, stable, and checkpointable.
"""

import numpy as np
import os


class FlyBrain:
    """Reservoir-computing flight brain with learned readout."""

    N_RES = 256          # reservoir neurons
    N_FEATURES = 36      # sensory feature size
    N_ACTIONS = 2        # outputs: lateral vy, vertical vz steering
    ACTION_GAIN = 3.0    # scales readout to m/s steering range

    def __init__(self, connectome_path='data/connectome-weights-male-cns-v1.0-minconf-0.5.feather',
                 reservoir_cache='fly_reservoir.npz', seed=7):
        self.rng = np.random.default_rng(seed)
        self.state = np.zeros(self.N_RES)
        self.replay = []          # (state, target) pairs for readout learning
        self.max_replay = 4000
        self.learn_rate = 0.02
        self.exploration = 1.0    # decays over episodes
        self.episode_count = 0

        # Fixed input weights (random, sparse)
        self.W_in = self.rng.normal(0, 0.5, (self.N_RES, self.N_FEATURES))
        self.W_in[self.rng.random(self.W_in.shape) > 0.3] = 0.0  # ~30% connectivity

        # Recurrent reservoir from connectome sample (or random fallback)
        self.W_res = self._load_or_build_reservoir(connectome_path, reservoir_cache)

        # Learned readout weights
        self.W_out = np.zeros((self.N_ACTIONS, self.N_RES))
        self.b_out = np.zeros(self.N_ACTIONS)

        self._loaded = False

    # ---------------- reservoir ----------------

    def _load_or_build_reservoir(self, connectome_path, cache_path):
        if os.path.exists(cache_path):
            try:
                data = np.load(cache_path)
                W = data['W_res']
                if W.shape == (self.N_RES, self.N_RES):
                    print(f"FlyBrain: loaded reservoir from {cache_path}")
                    return W
            except Exception as e:
                print(f"FlyBrain: reservoir cache load failed ({e}), rebuilding")

        W = self._build_reservoir(connectome_path)
        try:
            np.savez(cache_path, W_res=W)
            print(f"FlyBrain: reservoir cached to {cache_path}")
        except Exception as e:
            print(f"FlyBrain: could not cache reservoir ({e})")
        return W

    def _build_reservoir(self, connectome_path, n_edges=400_000):
        """Sample edges from MaleCNS connectome, aggregate into N_RES x N_RES."""
        W = np.zeros((self.N_RES, self.N_RES))
        edges_sampled = 0

        if os.path.exists(connectome_path):
            try:
                import pyarrow as pa
                import pyarrow.feather as feather

                # Stream record batches to avoid loading 151M rows into RAM
                with pa.memory_map(connectome_path, 'r') as src:
                    reader = pa.ipc.open_file(src)
                    total_rows = 151_856_684  # known size of this dataset

                    sample_frac = min(1.0, n_edges / total_rows)
                    oversample = 3  # extra edges, we trim after

                    for bi in range(reader.num_record_batches):
                        batch = reader.get_batch(bi)
                        n = batch.num_rows
                        take = max(1, int(n * sample_frac * oversample))
                        if take >= n:
                            idx = np.arange(n)
                        else:
                            idx = self.rng.choice(n, size=take, replace=False)
                        pre = batch.column('body_pre').to_numpy()[idx]
                        post = batch.column('body_post').to_numpy()[idx]
                        w = batch.column('weight').to_numpy()[idx].astype(np.float64)

                        # Map neuron IDs into reservoir bins, aggregate log-weights
                        ii = pre % self.N_RES
                        jj = post % self.N_RES
                        contrib = np.log1p(w)
                        np.add.at(W, (ii, jj), contrib)
                        edges_sampled += len(idx)
                        if edges_sampled >= n_edges * oversample:
                            break

                print(f"FlyBrain: sampled {edges_sampled} connectome edges")
            except Exception as e:
                print(f"FlyBrain: connectome sampling failed ({e}), using random reservoir")
                W = np.zeros((self.N_RES, self.N_RES))

        if W.max() == 0:
            # Fallback: random sparse recurrent reservoir
            mask = self.rng.random(W.shape) < 0.02
            W[mask] = self.rng.normal(0, 0.3, mask.sum())
            print("FlyBrain: using random sparse reservoir")
        else:
            # Normalize + sparsify: keep strongest 2% of weights
            W = W / (W.max() + 1e-9)
            thresh = np.quantile(W[W > 0], 0.98) if (W > 0).any() else 1.0
            W[W < thresh] = 0.0
            W *= 0.9  # spectral radius-ish scaling for tanh stability
            print(f"FlyBrain: connectome reservoir built ({(W != 0).sum()} synapses)")

        return W

    # ---------------- sensing ----------------

    def features(self, position, velocity, obstacles):
        """Compact sensory feature vector for the brain."""
        f = [
            position[1] / 10.0,   # vertical offset
            position[2] / 10.0,   # lateral offset
            velocity[1] / 5.0,    # vertical velocity
            velocity[2] / 5.0,    # lateral velocity
            position[0] / 100.0,  # progress along tunnel (-1..1)
        ]
        # Nearest obstacles ahead: relative dx, dy, dz, size
        ahead = [o for o in obstacles if o['position'][0] > position[0] - 1.0]
        ahead.sort(key=lambda o: o['position'][0] - position[0])
        for o in ahead[:8]:
            op = o['position']
            f += [
                (op[0] - position[0]) / 50.0,
                (op[1] - position[1]) / 10.0,
                (op[2] - position[2]) / 10.0,
                min(o['size'] / 5.0, 1.0),
            ]
        while len(f) < self.N_FEATURES:
            f.append(0.0)
        return np.array(f[:self.N_FEATURES], dtype=np.float64)

    # ---------------- acting ----------------

    def act(self, feat):
        """Run one reservoir step, return (vy, vz) steering command."""
        feat = np.asarray(feat, dtype=np.float64)
        drive = self.W_in @ feat
        self.state = np.tanh(self.W_res @ self.state * 0.9 + drive)
        out = self.W_out @ self.state + self.b_out
        action = np.tanh(out) * self.ACTION_GAIN
        # Exploration noise decays over episodes
        if self.exploration > 0:
            action = action + self.rng.normal(0, 0.8 * self.exploration, self.N_ACTIONS)
        return action, self.state.copy()

    def reset_episode(self):
        self.state = np.zeros(self.N_RES)

    # ---------------- learning ----------------

    def record(self, state, target):
        """Store (reservoir_state, teacher_action) for readout training."""
        self.replay.append((state.copy(), np.asarray(target, dtype=np.float64)))
        if len(self.replay) > self.max_replay:
            self.replay.pop(0)

    def learn(self, steps=30, batch=64):
        """A few SGD steps on W_out to match teacher actions (behavioral cloning)."""
        if len(self.replay) < batch:
            return
        idx = self.rng.choice(len(self.replay), size=min(batch, len(self.replay)), replace=False)
        S = np.array([self.replay[i][0] for i in idx]).T          # (R, B)
        T = np.array([self.replay[i][1] for i in idx]).T          # (2, B)
        P = np.tanh(self.W_out @ S + self.b_out[:, None]) * self.ACTION_GAIN / self.ACTION_GAIN
        # dMSE/dW_out: pred = tanh(W_out@S)*GAIN -> use tanh' approx via (P_raw - T)/GAIN * (1-P_raw^2)
        raw = np.arctanh(np.clip(P, -0.999, 0.999))
        err = (raw - T) * (1.0 - P ** 2)
        grad_W = err @ S.T / S.shape[1]
        grad_b = err.mean(axis=1)
        self.W_out -= self.learn_rate * grad_W
        self.b_out -= self.learn_rate * grad_b

    def end_episode(self, score, is_best):
        """Decay exploration; checkpoint handled by caller via get_weights."""
        self.episode_count += 1
        self.exploration = max(0.05, 1.0 * (0.92 ** self.episode_count))

    # ---------------- checkpointing ----------------

    def get_weights(self):
        return {
            'W_out': self.W_out.copy(),
            'b_out': self.b_out.copy(),
            'episode_count': self.episode_count,
            'exploration': self.exploration,
        }

    def set_weights(self, w):
        if not w:
            return
        self.W_out = w['W_out'].copy()
        self.b_out = w['b_out'].copy()
        self.episode_count = w.get('episode_count', 0)
        self.exploration = w.get('exploration', 1.0)
        self._loaded = True
