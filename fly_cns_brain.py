"""
Fly CNS Brain - FULL MaleCNS connectome reservoir computing flight controller

Uses the complete adult male fly connectome (~211k neurons, ~151.8M synapses)
as a sparse recurrent reservoir. The reservoir state is a 211k-dimensional
vector; a learned linear readout (W_out) is trained online from the steering
teacher by behavioral cloning.

Reservoir matrix is cached as a scipy sparse .npz (~1.3GB) after a one-time
build that streams the Feather connectome in batches (memory-safe).

Interface matches FlyBrain so it can drop into desktop_gui_3d.py.
"""

import numpy as np
import os

ANNOT_PATH = 'data/body-annotations-male-cns-v1.0-minconf-0.5.feather'
CONN_PATH = 'data/connectome-weights-male-cns-v1.0-minconf-0.5.feather'
CACHE_PATH = 'fly_cns_reservoir.npz'
NODES_PATH = 'fly_cns_nodes.npy'
CELLTYPES_PATH = 'fly_cns_celltypes.npz'

N_FEATURES = 36
N_ACTIONS = 2
ACTION_GAIN = 3.0
UPDATE_EVERY = 10      # reservoir matvec every N physics steps (~5 Hz brain)
LEAK = 0.98            # recurrent leak factor


class FlyCNSBrain:
    """Full-connectome reservoir brain with learned readout."""

    def __init__(self, cache_path=CACHE_PATH, seed=7):
        import scipy.sparse as sp

        self.rng = np.random.default_rng(seed)
        self.W_res = self._load_or_build_reservoir(cache_path)
        self.n_neurons = self.W_res.shape[0]

        self.state = np.zeros(self.n_neurons, dtype=np.float32)
        self._steps = 0
        self._pred = np.zeros(N_ACTIONS)

        # Learned readout
        self.W_out = np.zeros((N_ACTIONS, self.n_neurons), dtype=np.float32)
        self.b_out = np.zeros(N_ACTIONS, dtype=np.float32)
        # auto-scale: keep per-update output change ~0.05 regardless of N
        self.learn_rate = 0.05 / (0.3 * self.n_neurons)

        # Online learning buffer: teacher targets awaiting a readout update
        self._pending = []
        self.max_pending = 60

        self.exploration = 1.0
        self.episode_count = 0
        self._loaded = False

        # --- real fly cell types from MaleCNS annotations ---
        self.node_ids = getattr(self, 'node_ids', None)
        self.superclass = None
        self.cell_class = None
        self.cell_type = None
        self.superclass_names = []
        self.class_names = []
        self.type_names = []
        self.sensory_mask = None
        self.motor_mask = None
        self._load_cell_types()
        self._build_io_matrices()

    # ---------------- cell types ----------------

    _SENSORY_SUPERCLASSES = {
        'cb_sensory', 'vnc_sensory', 'ol_sensory',
        'visual_projection', 'sensory_ascending',
    }
    _MOTOR_SUPERCLASSES = {
        'descending_neuron', 'vnc_motor', 'cb_motor',
        'ascending_neuron', 'vnc_efferent',
    }

    def _load_cell_types(self):
        """Annotate every reservoir neuron with its real MaleCNS cell type."""
        if self.node_ids is None:
            return
        n = self.n_neurons
        try:
            if os.path.exists(CELLTYPES_PATH):
                d = np.load(CELLTYPES_PATH, allow_pickle=True)
                if len(d['superclass']) == n:
                    self.superclass = d['superclass']
                    self.cell_class = d['cell_class']
                    self.cell_type = d['cell_type']
                    self.superclass_names = list(d['superclass_names'])
                    self.class_names = list(d['class_names'])
                    self.type_names = list(d['type_names'])
                    self._make_masks()
                    return
        except Exception:
            pass

        import pyarrow as pa
        import pandas as pd
        dfs = []
        with pa.memory_map(ANNOT_PATH, 'r') as src:
            r = pa.ipc.open_file(src)
            for i in range(r.num_record_batches):
                dfs.append(r.get_batch(i).select(
                    ['bodyId', 'superclass', 'class', 'type']).to_pandas())
        df = pd.concat(dfs, ignore_index=True)

        # node_ids is sorted unique bodyId; map each annotation row to node idx
        pos = np.searchsorted(self.node_ids, df['bodyId'].to_numpy())
        pos = np.clip(pos, 0, n - 1)
        valid = self.node_ids[pos] == df['bodyId'].to_numpy()

        def encode(col):
            vals = df[col].fillna('unknown').astype(str).to_numpy()
            names = np.array(sorted(set(vals)))
            codes = np.searchsorted(names, vals).astype(np.int32)
            out = np.full(n, -1, dtype=np.int32)
            out[pos[valid]] = codes[valid]
            return out, names.tolist()

        self.superclass, self.superclass_names = encode('superclass')
        self.cell_class, self.class_names = encode('class')
        self.cell_type, self.type_names = encode('type')
        self._make_masks()

        try:
            np.savez(CELLTYPES_PATH,
                     superclass=self.superclass, cell_class=self.cell_class,
                     cell_type=self.cell_type,
                     superclass_names=np.array(self.superclass_names),
                     class_names=np.array(self.class_names),
                     type_names=np.array(self.type_names))
        except Exception:
            pass

        # report composition
        counts = {}
        for i, name in enumerate(self.superclass_names):
            counts[name] = int((self.superclass == i).sum())
        top = sorted(counts.items(), key=lambda x: -x[1])[:8]
        print("FlyCNSBrain cell types:",
              ", ".join(f"{k}={v:,}" for k, v in top))

    def _make_masks(self):
        sens = set(self._SENSORY_SUPERCLASSES)
        mot = set(self._MOTOR_SUPERCLASSES)
        self.sensory_mask = np.array(
            [self.superclass_names[s] in sens
             for s in self.superclass if s >= 0], dtype=bool)
        self.motor_mask = np.array(
            [self.superclass_names[s] in mot
             for s in self.superclass if s >= 0], dtype=bool)
        # pad/truncate safety
        if len(self.sensory_mask) != self.n_neurons:
            self.sensory_mask = np.zeros(self.n_neurons, bool)
            self.motor_mask = np.zeros(self.n_neurons, bool)

    # ---------------- I/O matrices ----------------

    def _build_io_matrices(self):
        """Cell-type-targeted input projection + premotor readout."""
        n = self.n_neurons
        # Sensory-targeted W_in: real sensory neurons get ~2x drive
        self.W_in = (self.rng.normal(0, 0.4, (n, N_FEATURES))
                     ).astype(np.float32)
        if self.sensory_mask is not None and self.sensory_mask.any():
            self.W_in[self.sensory_mask] *= 2.0
            print(f"FlyCNSBrain: W_in boosted on "
                  f"{int(self.sensory_mask.sum()):,} sensory neurons")

        # Premotor readout: fixed sparse projection from motor-related
        # populations to the 59 official flybody actuators
        self.W_motor = np.zeros((59, n), dtype=np.float32)
        if self.motor_mask is not None and self.motor_mask.any():
            mrows = np.where(self.motor_mask)[0]
            # each actuator samples ~300 motor neurons
            for a in range(59):
                sel = self.rng.choice(mrows, size=min(300, len(mrows)),
                                      replace=False)
                self.W_motor[a, sel] = self.rng.normal(0, 0.2, len(sel))
            print(f"FlyCNSBrain: W_motor wired to "
                  f"{len(mrows):,} motor/descending neurons")
        else:
            mask = self.rng.random((59, n)) < 0.001
            self.W_motor[mask] = self.rng.normal(0, 0.2, mask.sum())

    # ---------------- reservoir build ----------------

    def _load_or_build_reservoir(self, cache_path):
        import scipy.sparse as sp

        if os.path.exists(cache_path):
            try:
                W = sp.load_npz(cache_path).tocsr()
                print(f"FlyCNSBrain: loaded MaleCNS connectome "
                      f"({W.shape[0]} neurons, {W.nnz} synapses)")
                self.node_ids = self._load_node_ids(W.shape[0])
                return self._scale_reservoir(W)
            except Exception as e:
                print(f"FlyCNSBrain: cache load failed ({e}), rebuilding")

        W = self._build_reservoir()
        self.node_ids = self._load_node_ids(W.shape[0])
        try:
            sp.save_npz(cache_path, W.tocsr())
            print(f"FlyCNSBrain: cached reservoir to {cache_path}")
        except Exception as e:
            print(f"FlyCNSBrain: could not cache reservoir ({e})")
        return self._scale_reservoir(W)

    def _load_node_ids(self, n):
        """Load the bodyId for each reservoir neuron (for cell typing)."""
        if os.path.exists(NODES_PATH):
            try:
                ids = np.load(NODES_PATH)
                if len(ids) == n:
                    return ids
            except Exception:
                pass
        # Fallback: re-derive from annotations (sorted unique bodyId)
        try:
            import pyarrow as pa
            ids = []
            with pa.memory_map(ANNOT_PATH, 'r') as src:
                r = pa.ipc.open_file(src)
                for i in range(r.num_record_batches):
                    ids.append(r.get_batch(i).column('bodyId').to_numpy())
            ids = np.unique(np.concatenate(ids)).astype(np.int64)
            if len(ids) == n:
                return ids
        except Exception:
            pass
        return None

    @staticmethod
    def _scale_reservoir(W, target_radius=0.9, iters=30):
        """Power-iterate to estimate spectral radius, scale to target."""
        import scipy.sparse as sp
        n = W.shape[0]
        rng = np.random.default_rng(0)
        v = rng.normal(0, 1, n).astype(np.float32)
        v /= np.linalg.norm(v)
        lam = 1.0
        for _ in range(iters):
            v = W @ v
            nv = np.linalg.norm(v)
            if nv == 0:
                break
            lam = nv
            v /= nv
        scale = target_radius / max(lam, 1e-9)
        print(f"FlyCNSBrain: spectral radius ~{lam:.3f}, scaling by {scale:.4f}")
        W = W.copy()
        W.data = (W.data.astype(np.float32) * np.float32(scale))
        return W.tocsr()

    def _build_reservoir(self):
        """Stream MaleCNS neuron->neuron edges into a CSR sparse matrix.

        Node set = the 211,577 annotated CNS bodies, so every reservoir
        neuron has a real cell type (superclass/class/type) from the
        MaleCNS annotations. Edges to non-neuronal bodies (muscles,
        other namespaces) are dropped - they cannot affect recurrence.
        """
        import pyarrow as pa
        import scipy.sparse as sp

        # --- node IDs from annotations (sorted unique bodyId) ---
        ids = []
        with pa.memory_map(ANNOT_PATH, 'r') as src:
            r = pa.ipc.open_file(src)
            for i in range(r.num_record_batches):
                ids.append(r.get_batch(i).column('bodyId').to_numpy())
        ids = np.unique(np.concatenate(ids)).astype(np.int64)
        n = len(ids)
        print(f"FlyCNSBrain: {n} annotated CNS neurons")
        try:
            np.save(NODES_PATH, ids)
        except Exception:
            pass

        def map_ids(idarr):
            pos = np.searchsorted(ids, idarr)
            pos = np.clip(pos, 0, n - 1)
            ok = ids[pos] == idarr
            return np.where(ok, pos, -1).astype(np.int64)

        # --- pass 1: count valid edges per pre-neuron ---
        counts = np.zeros(n, dtype=np.int64)
        total_valid = 0
        with pa.memory_map(CONN_PATH, 'r') as src:
            r = pa.ipc.open_file(src)
            for bi in range(r.num_record_batches):
                b = r.get_batch(bi)
                pre = map_ids(b.column('body_pre').to_numpy())
                post = map_ids(b.column('body_post').to_numpy())
                ok = (pre >= 0) & (post >= 0)
                if ok.any():
                    counts += np.bincount(pre[ok], minlength=n)
                    total_valid += int(ok.sum())
                if bi % 400 == 0:
                    print(f"  pass1 batch {bi}/{r.num_record_batches}")
        print(f"FlyCNSBrain: {total_valid} valid edges")

        indptr = np.zeros(n + 1, dtype=np.int64)
        np.cumsum(counts, out=indptr[1:])
        indices = np.empty(total_valid, dtype=np.int32)
        data = np.empty(total_valid, dtype=np.float32)
        prior = np.zeros(n, dtype=np.int64)   # edges written per row so far

        # --- pass 2: fill CSR slots ---
        with pa.memory_map(CONN_PATH, 'r') as src:
            r = pa.ipc.open_file(src)
            for bi in range(r.num_record_batches):
                b = r.get_batch(bi)
                pre = map_ids(b.column('body_pre').to_numpy())
                post = map_ids(b.column('body_post').to_numpy())
                w = b.column('weight').to_numpy().astype(np.float32)
                ok = (pre >= 0) & (post >= 0)
                if not ok.any():
                    continue
                rows, cols, ww = pre[ok], post[ok], w[ok]

                # sort by row so same-row edges are contiguous in this batch
                order = np.argsort(rows, kind='stable')
                rows, cols, ww = rows[order], cols[order], ww[order]

                # rank of each edge within its row-group in this batch
                newgrp = np.ones(len(rows), dtype=bool)
                newgrp[1:] = rows[1:] != rows[:-1]
                grp_start = np.maximum.accumulate(
                    np.where(newgrp, np.arange(len(rows)), 0))
                rank = np.arange(len(rows)) - grp_start

                dest = indptr[rows] + prior[rows] + rank
                indices[dest] = cols.astype(np.int32)
                data[dest] = np.log1p(ww)

                uniq, cnts = np.unique(rows, return_counts=True)
                np.add.at(prior, uniq, cnts)

                if bi % 400 == 0:
                    print(f"  pass2 batch {bi}/{r.num_record_batches}")

        W = sp.csr_matrix((data, indices, indptr), shape=(n, n))
        print(f"FlyCNSBrain: neuron->neuron connectome built "
              f"({W.nnz} synapses among {W.shape[0]} CNS neurons)")
        return W

    # ---------------- sensing (same as FlyBrain) ----------------

    def features(self, position, velocity, obstacles):
        f = [
            position[1] / 10.0,
            position[2] / 10.0,
            velocity[1] / 5.0,
            velocity[2] / 5.0,
            position[0] / 100.0,
        ]
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
        while len(f) < N_FEATURES:
            f.append(0.0)
        return np.array(f[:N_FEATURES], dtype=np.float64)

    # ---------------- acting ----------------

    def act(self, feat):
        """Run reservoir step (every UPDATE_EVERY calls), return steering."""
        self._steps += 1
        feat = np.asarray(feat, dtype=np.float32)

        if self._steps % UPDATE_EVERY == 1:
            drive = self.W_in @ feat
            # full-connectome recurrent update
            self.state = np.tanh(
                LEAK * self.state + self.W_res @ self.state + drive)
            self._pred = self.W_out @ self.state + self.b_out

        action = np.tanh(self._pred) * ACTION_GAIN
        if self.exploration > 0:
            action = action + self.rng.normal(
                0, 0.8 * self.exploration, N_ACTIONS)
        # state is huge; return None - learning uses internal state
        return action.astype(np.float64), None

    def actuator_commands(self):
        """59-dim motor command for the official flybody actuators.

        Premotor populations (descending/motor neurons) project through
        W_motor onto the actuators, gated by a wingbeat rhythm so the
        flybody's muscles actually contract in flight patterns.
        """
        if not hasattr(self, 'W_motor'):
            return np.zeros(59)
        drive = self.W_motor @ self.state          # (59,)
        # ~8 Hz visible wingbeat at dt=0.02 (50 Hz sim rate)
        t = self._steps * UPDATE_EVERY * 0.02
        phase = np.arange(59) * 0.7
        rhythm = np.sin(2 * np.pi * 8.0 * t + phase)
        # steering modulates left/right asymmetry (yaw)
        asym = np.tanh(self._pred[1]) * 0.3
        rhythm = rhythm * (1.0 + asym * np.where(np.arange(59) % 2 == 0, 1, -1))
        return (np.tanh(drive) * 0.6 * rhythm).astype(np.float64)

    def reset_episode(self):
        self.state *= 0.3   # partial decay, keep some history

    # ---------------- learning (online delta rule) ----------------

    def record(self, state, target):
        """Queue a teacher action; applied on next learn() against live state."""
        self._pending.append(np.asarray(target, dtype=np.float32))
        if len(self._pending) > self.max_pending:
            self._pending.pop(0)

    def learn(self, steps=5):
        """Apply queued teacher targets as delta-rule updates on W_out."""
        n = 0
        while self._pending and n < steps * 10:
            tgt = self._pending.pop(0) / ACTION_GAIN
            tgt = np.clip(tgt, -0.99, 0.99)
            pred_t = np.tanh(self._pred)
            err = tgt - pred_t
            # backprop through tanh to pre-activation
            g = err * (1.0 - pred_t ** 2)
            self.W_out += self.learn_rate * np.outer(g, self.state)
            self.b_out += self.learn_rate * g
            n += 1

    def end_episode(self, score, is_best):
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
        if 'W_out' in w and w['W_out'].shape == self.W_out.shape:
            self.W_out = w['W_out'].astype(np.float32).copy()
            self.b_out = w['b_out'].astype(np.float32).copy()
        self.episode_count = w.get('episode_count', 0)
        self.exploration = w.get('exploration', 1.0)
        self._loaded = True
