"""
Brain Controller
Connects the spiking brain simulation to the fly's body in the 3D environment.

The fly's movement is produced by a recurrently connected spiking network:
sensory neurons -> interneurons (recurrent, laterally inhibiting) -> motor neurons.
Motor firing rates become thrust / yaw / pitch / roll commands for FlyCharacter.
"""

import math
import os
import sys
from typing import Dict, List, Optional, Tuple

import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from .fly_character import FlyCharacter
except ImportError:
    from fly_character import FlyCharacter

from brain_sim.neuron_models import Neuron
from training_system.survival_system import SurvivalSystem


class SimNeuron(Neuron):
    """
    Integrate-and-fire neuron driven by simulation time instead of the wall clock,
    so the brain can be stepped faster or slower than real time.
    """

    #: Membrane time constant in ms
    tau = 1.5

    def step(self, input_current: float, sim_time: float, dt: float = 1.0) -> bool:
        if sim_time - self.last_spike_time < self.refractory_period:
            self.membrane_potential = self.resting_potential
            return False

        # Leaky integration towards the input current
        self.membrane_potential += (input_current - self.membrane_potential) / self.tau * dt

        if self.membrane_potential >= self.threshold:
            self.membrane_potential = self.resting_potential
            self.last_spike_time = sim_time
            return True

        return False


class NeuralMotorNetwork:
    """
    Recurrent spiking network that turns sensory signals into motor commands.

    Neurons are explicitly connected to each other: sensory -> interneuron,
    interneuron -> interneuron (recurrent), interneuron -> motor, motor -> interneuron
    (efference copy) and mutual inhibition between antagonistic motor neurons.
    """

    SENSORY_INPUTS = [
        "food_forward", "food_left", "food_right", "food_up", "food_down",
        "food_close", "hunger", "explore_left", "explore_right", "explore_up",
        "wall_ahead", "wall_below",
    ]

    MOTOR_OUTPUTS = [
        "thrust", "yaw_left", "yaw_right", "pitch_up", "pitch_down",
    ]

    ANTAGONISTS = {
        "yaw_left": "yaw_right",
        "yaw_right": "yaw_left",
        "pitch_up": "pitch_down",
        "pitch_down": "pitch_up",
    }

    def __init__(self, num_interneurons: int = 60, seed: int = 7):
        self.rng = np.random.default_rng(seed)
        self.num_interneurons = num_interneurons

        next_id = 0
        self.sensory: Dict[str, SimNeuron] = {}
        for name in self.SENSORY_INPUTS:
            self.sensory[name] = SimNeuron(next_id, "sensory")
            next_id += 1

        self.interneurons: List[SimNeuron] = []
        for _ in range(num_interneurons):
            self.interneurons.append(SimNeuron(next_id, "interneuron"))
            next_id += 1

        self.motor: Dict[str, SimNeuron] = {}
        for name in self.MOTOR_OUTPUTS:
            self.motor[name] = SimNeuron(next_id, "motor")
            next_id += 1

        self.sim_time = 0.0
        self.firing_rates: Dict[str, float] = {name: 0.0 for name in self.MOTOR_OUTPUTS}
        self.interneuron_activity = 0.0
        self.spike_count = 0

        # Decaying synaptic input traces
        self.trace_decay = 0.8
        self.inter_trace = np.zeros(num_interneurons)
        self.motor_trace: Dict[str, float] = {name: 0.0 for name in self.MOTOR_OUTPUTS}

        self._build_connections()

    def _build_connections(self):
        """Wire the neurons to each other."""
        n = self.num_interneurons

        # Sensory -> interneuron: every sensory input drives its own pool of
        # interneurons, so the pools stay distinguishable from each other.
        self.sensory_to_inter: Dict[str, List[Tuple[int, float]]] = {}
        pool_size = max(2, n // len(self.SENSORY_INPUTS))
        self.pools: Dict[str, List[int]] = {}
        for i, name in enumerate(self.SENSORY_INPUTS):
            targets = [(i * pool_size + k) % n for k in range(pool_size)]
            self.pools[name] = targets
            self.sensory_to_inter[name] = [
                (t, float(self.rng.uniform(12.0, 16.0))) for t in targets
            ]

        # Interneuron -> interneuron: sparse recurrent connections, mostly weak and
        # a third of them inhibitory, so the pools influence each other.
        self.inter_to_inter: List[List[Tuple[int, float]]] = [[] for _ in range(n)]
        for i in range(n):
            for j in self.rng.choice(n, size=5, replace=False):
                if int(j) == i:
                    continue
                weight = float(self.rng.uniform(0.5, 1.5))
                if self.rng.random() < 0.35:
                    weight = -weight
                self.inter_to_inter[i].append((int(j), weight))

        # Interneuron -> motor: the slice each sensory input drives is biased towards
        # the motor neuron that makes behavioural sense for that signal.
        bias = {
            "food_forward": [("thrust", 3.0)],
            "food_left": [("yaw_left", 3.0), ("thrust", 1.0)],
            "food_right": [("yaw_right", 3.0), ("thrust", 1.0)],
            "food_up": [("pitch_up", 3.0)],
            "food_down": [("pitch_down", 3.0)],
            "food_close": [("thrust", 1.5)],
            "hunger": [("thrust", 1.5)],
            "explore_left": [("yaw_left", 2.0), ("thrust", 1.0)],
            "explore_right": [("yaw_right", 2.0), ("thrust", 1.0)],
            "explore_up": [("pitch_up", 2.0)],
            "wall_ahead": [("yaw_left", 2.5)],
            "wall_below": [("pitch_up", 3.5)],
        }
        self.inter_to_motor: List[List[Tuple[str, float]]] = [[] for _ in range(n)]
        for name, targets in self.pools.items():
            for idx in targets:
                for motor_name, weight in bias.get(name, []):
                    self.inter_to_motor[idx].append(
                        (motor_name, float(weight * self.rng.uniform(0.8, 1.2)))
                    )

        # Motor -> interneuron efference copy, and mutual inhibition of antagonists.
        self.motor_to_inter: Dict[str, List[Tuple[int, float]]] = {}
        for motor_name in self.MOTOR_OUTPUTS:
            targets = self.rng.choice(n, size=4, replace=False)
            self.motor_to_inter[motor_name] = [(int(t), -1.0) for t in targets]

        # Antagonistic motor neurons inhibit each other, so the stronger side wins
        # instead of both firing flat out.
        self.motor_inhibition = -10.0

    def step(self, sensory_values: Dict[str, float], steps: int = 12, dt: float = 1.0) -> Dict[str, float]:
        """
        Run the network for a few milliseconds and return motor firing rates (0-1).

        Synaptic input is held in decaying traces so a single presynaptic spike keeps
        depolarising its targets for a few steps, the way real synapses do.

        Args:
            sensory_values: Sensory drive per input name, each in 0-1
            steps: Number of simulation steps to run
            dt: Step size in milliseconds
        """
        motor_spikes = {name: 0 for name in self.MOTOR_OUTPUTS}
        inter_spikes = 0

        for _ in range(steps):
            self.sim_time += dt

            # Decay synaptic traces from previous steps. Inhibition is floored so a
            # burst of inhibition cannot silence a neuron indefinitely.
            self.inter_trace = np.maximum(self.inter_trace * self.trace_decay, -12.0)
            for name in self.MOTOR_OUTPUTS:
                self.motor_trace[name] = max(self.motor_trace[name] * self.trace_decay, -12.0)

            # Sensory layer
            for name, neuron in self.sensory.items():
                drive = float(np.clip(sensory_values.get(name, 0.0), 0.0, 1.0))
                if neuron.step(-70.0 + drive * 75.0, self.sim_time, dt):
                    self.spike_count += 1
                    for target, weight in self.sensory_to_inter[name]:
                        self.inter_trace[target] += weight

            # Interneuron layer (recurrent)
            fired_inter = []
            for i, neuron in enumerate(self.interneurons):
                if neuron.step(-70.0 + self.inter_trace[i], self.sim_time, dt):
                    fired_inter.append(i)
                    inter_spikes += 1
                    self.spike_count += 1

            for i in fired_inter:
                for target, weight in self.inter_to_inter[i]:
                    self.inter_trace[target] += weight
                for motor_name, weight in self.inter_to_motor[i]:
                    self.motor_trace[motor_name] += weight

            # Motor layer
            fired_motor = []
            for name, neuron in self.motor.items():
                if neuron.step(-70.0 + self.motor_trace[name], self.sim_time, dt):
                    fired_motor.append(name)
                    motor_spikes[name] += 1
                    self.spike_count += 1

            for name in fired_motor:
                for target, weight in self.motor_to_inter[name]:
                    self.inter_trace[target] += weight
                antagonist = self.ANTAGONISTS.get(name)
                if antagonist:
                    self.motor_trace[antagonist] += self.motor_inhibition

        # Spike counts -> normalised firing rates (a neuron in refractory cannot
        # fire on every step, so normalise by the maximum achievable count)
        for name in self.MOTOR_OUTPUTS:
            max_spikes = max(1.0, steps * dt / self.motor[name].refractory_period)
            rate = min(1.0, motor_spikes[name] / max_spikes)
            self.firing_rates[name] = 0.5 * self.firing_rates[name] + 0.5 * rate
        self.interneuron_activity = inter_spikes / max(1, steps * self.num_interneurons)

        return dict(self.firing_rates)

    def get_state(self) -> Dict:
        return {
            "neurons": len(self.sensory) + len(self.interneurons) + len(self.motor),
            "sensory_neurons": len(self.sensory),
            "interneurons": len(self.interneurons),
            "motor_neurons": len(self.motor),
            "recurrent_connections": sum(len(c) for c in self.inter_to_inter),
            "total_spikes": self.spike_count,
            "interneuron_activity": self.interneuron_activity,
            "firing_rates": dict(self.firing_rates),
        }

    def reset(self):
        for neuron in list(self.sensory.values()) + self.interneurons + list(self.motor.values()):
            neuron.reset()
        self.sim_time = 0.0
        self.spike_count = 0
        self.firing_rates = {name: 0.0 for name in self.MOTOR_OUTPUTS}
        self.inter_trace = np.zeros(self.num_interneurons)
        self.motor_trace = {name: 0.0 for name in self.MOTOR_OUTPUTS}


class BrainFlyController:
    """
    Drives the 3D fly body from brain activity, hunger and survival drives.

    The controller owns the fly's physics (FlyCharacter), its survival state
    (SurvivalSystem / HungerMechanics) and the spiking network that produces motor
    commands. Hunger can be switched off at any time, in which case the fly keeps
    its energy and simply explores.
    """

    def __init__(self,
                 bounds: Tuple[float, float, float] = (20.0, 20.0, 12.0),
                 start_position: Optional[Tuple[float, float, float]] = None,
                 hunger_enabled: bool = True,
                 seed: int = 7):
        self.bounds = np.array(bounds, dtype=float)
        if start_position is None:
            start_position = (0.0, 0.0, bounds[2] * 0.5)

        self.fly = FlyCharacter(start_position=start_position)
        self.fly.max_speed = 6.0
        self.fly.max_acceleration = 14.0
        self.fly.turn_rate = 2.2

        self.network = NeuralMotorNetwork(seed=seed)
        self.survival = SurvivalSystem(initial_energy=100.0)
        self.hunger = self.survival.hunger_mechanics
        self.set_hunger_enabled(hunger_enabled)

        # Wing thrust that exactly cancels gravity, so the fly hovers by default
        self.hover_lift = 9.8 * self.fly.mass / self.fly.max_acceleration

        self.explore_phase = 0.0
        self.eating_timer = 0.0
        self.current_target: Optional[int] = None
        self.meals_eaten = 0
        self.behavior = "exploring"

    # ------------------------------------------------------------------ hunger
    def set_hunger_enabled(self, enabled: bool):
        """Turn hunger on or off. With hunger off the fly never loses energy."""
        self.hunger.set_enabled(enabled)
        if not enabled:
            self.hunger.energy = self.hunger.max_energy
            self.hunger.hunger_level = 0.0
            self.hunger.hunger_drive = 0.0
            self.hunger.survival_drive = 0.0
            self.hunger.is_starving = False
            self.hunger.is_critical = False
            self.hunger.death_imminent = False

    def toggle_hunger(self) -> bool:
        self.set_hunger_enabled(not self.hunger.enabled)
        return self.hunger.enabled

    @property
    def hunger_enabled(self) -> bool:
        return self.hunger.enabled

    def feed(self, energy: float = 25.0):
        """Feed the fly directly, without it having to find food."""
        self.survival.process_feeding(energy)
        self.eating_timer = 1.0

    # ----------------------------------------------------------------- sensing
    def _sense(self, food_sources: List[Dict]) -> Dict[str, float]:
        """Encode the world into sensory drives for the brain."""
        sensory = {name: 0.0 for name in NeuralMotorNetwork.SENSORY_INPUTS}

        hunger_drive = self.hunger.hunger_drive if self.hunger.enabled else 0.0
        sensory["hunger"] = float(np.clip(hunger_drive, 0.0, 1.0))

        # Wandering: a slow oscillation that turns the fly one way then the other,
        # weaker while it is hungry and following food.
        wander = (1.0 - 0.7 * sensory["hunger"])
        swing = math.sin(self.explore_phase)
        sensory["explore_left"] = max(0.0, swing) * wander
        sensory["explore_right"] = max(0.0, -swing) * wander
        sensory["explore_up"] = max(0.0, math.sin(self.explore_phase * 0.6)) * wander

        target = self._select_target(food_sources)
        if target is not None:
            to_food = np.array(target["position"], dtype=float) - self.fly.position
            distance = float(np.linalg.norm(to_food))
            if distance > 1e-6:
                direction = to_food / distance
                forward = self.fly._get_thrust_direction()
                left = np.array([-forward[1], forward[0], 0.0])
                norm = np.linalg.norm(left)
                left = left / norm if norm > 1e-6 else np.array([0.0, 1.0, 0.0])

                # Smell / see food more strongly when hungry, but never blind to it.
                gain = 0.45 + 0.55 * sensory["hunger"]
                alignment = float(np.dot(direction, forward))
                lateral = float(np.dot(direction, left))

                # Amplify the lateral error so small misalignments still steer.
                sensory["food_forward"] = max(0.0, alignment) * gain
                sensory["food_left"] = min(1.0, max(0.0, lateral) * 3.0) * gain
                sensory["food_right"] = min(1.0, max(0.0, -lateral) * 3.0) * gain
                if alignment < 0.0:
                    # Food is behind: turn hard towards whichever side it lies on.
                    if lateral >= 0.0:
                        sensory["food_left"] = gain
                    else:
                        sensory["food_right"] = gain
                sensory["food_up"] = min(1.0, max(0.0, float(direction[2])) * 3.0) * gain
                sensory["food_down"] = min(1.0, max(0.0, float(-direction[2])) * 3.0) * gain
                sensory["food_close"] = float(np.clip(1.0 - distance / 15.0, 0.0, 1.0)) * gain

        # Walls: how much room is left straight ahead, and how close the floor is.
        # A wall the fly is flying towards matters; one it is flying away from does not.
        half = self.bounds / 2.0
        forward = self.fly._get_thrust_direction()
        clearance = float("inf")
        for axis in (0, 1):
            if abs(forward[axis]) < 1e-6:
                continue
            limit = half[axis] if forward[axis] > 0 else -half[axis]
            clearance = min(clearance, (limit - self.fly.position[axis]) / forward[axis])
        if clearance == float("inf"):
            clearance = 4.0
        wall_ahead = float(np.clip(1.0 - clearance / 4.0, 0.0, 1.0))
        # Food beats wall avoidance, otherwise the fly can never land in a corner.
        sensory["wall_ahead"] = wall_ahead * (1.0 - sensory["food_close"])
        sensory["wall_below"] = float(np.clip(1.0 - self.fly.position[2] / 2.0, 0.0, 1.0)) * (
            1.0 - sensory["food_down"]
        )

        return sensory

    def _select_target(self, food_sources: List[Dict]) -> Optional[Dict]:
        """Pick the nearest food source that still has food in it."""
        best = None
        best_distance = float("inf")
        for index, source in enumerate(food_sources):
            if source.get("amount", 0.0) <= 0.0:
                continue
            distance = float(np.linalg.norm(
                np.array(source["position"], dtype=float) - self.fly.position
            ))
            if distance < best_distance:
                best_distance = distance
                best = source
                self.current_target = index
        if best is None:
            self.current_target = None
        return best

    # ------------------------------------------------------------------ update
    def update(self, dt: float, food_sources: List[Dict]) -> Dict:
        """
        Advance brain, body and survival state by one frame.

        Args:
            dt: Frame time in seconds
            food_sources: List of {"position": (x, y, z), "amount": float} dicts

        Returns:
            State dict describing the fly this frame
        """
        dt = float(np.clip(dt, 0.0, 0.1))
        self.explore_phase += dt * 1.3

        sensory = self._sense(food_sources)
        motor = self.network.step(sensory)

        climb = motor["pitch_up"] - motor["pitch_down"]
        turn = motor["yaw_left"] - motor["yaw_right"]
        control = {
            "thrust": float(np.clip(0.2 + motor["thrust"] * 1.2, 0.0, 1.0)),
            "yaw": float(np.clip(turn, -1.0, 1.0)),
            # A positive pitch angle tilts the body nose-down, so climbing needs a
            # negative pitch command.
            "pitch": float(np.clip(-climb * 0.5, -1.0, 1.0)),
            "roll": float(np.clip(turn * 0.5, -1.0, 1.0)),
            # Wing beat holds the fly up; motor pitch neurons make it climb or dive.
            "lift": float(np.clip(self.hover_lift + climb * 0.5, 0.0, 1.5)),
        }

        if self.eating_timer > 0.0:
            self.eating_timer = max(0.0, self.eating_timer - dt)
            control["thrust"] = 0.05
            control["yaw"] *= 0.2
            control["pitch"] *= 0.2
            control["lift"] = 0.0

        self.fly.update(dt, control)
        self._keep_inside_bounds()

        activity = float(np.linalg.norm(self.fly.velocity)) / max(self.fly.max_speed, 1e-6)
        self.survival.update(dt, activity_level=activity)
        self.fly.energy = self.hunger.energy

        eaten = self._try_eat(food_sources)

        if self.eating_timer > 0.0:
            self.behavior = "eating"
        elif self.hunger.enabled and self.hunger.should_seek_food():
            self.behavior = "seeking food"
        else:
            self.behavior = "exploring"

        return {
            "position": self.fly.position.copy(),
            "velocity": self.fly.velocity.copy(),
            "speed": float(np.linalg.norm(self.fly.velocity)),
            "yaw": self.fly.yaw,
            "pitch": self.fly.pitch,
            "roll": self.fly.roll,
            "wing_beat_phase": self.fly.wing_beat_phase,
            "energy": self.hunger.energy,
            "hunger_level": self.hunger.hunger_level,
            "hunger_enabled": self.hunger.enabled,
            "behavior": self.behavior,
            "target_index": self.current_target,
            "eating": self.eating_timer > 0.0,
            "meals_eaten": self.meals_eaten,
            "motor": motor,
            "sensory": sensory,
            "brain": self.network.get_state(),
            "ate_this_frame": eaten,
        }

    def _keep_inside_bounds(self):
        """Bounce the fly off the walls of the enclosure."""
        half = self.bounds / 2.0
        for axis, limit in ((0, half[0] - 0.6), (1, half[1] - 0.6)):
            if self.fly.position[axis] > limit:
                self.fly.position[axis] = limit
                self.fly.velocity[axis] *= -0.4
            elif self.fly.position[axis] < -limit:
                self.fly.position[axis] = -limit
                self.fly.velocity[axis] *= -0.4

        if self.fly.position[2] > self.bounds[2] - 0.6:
            self.fly.position[2] = self.bounds[2] - 0.6
            self.fly.velocity[2] *= -0.4
        elif self.fly.position[2] < 0.4:
            self.fly.position[2] = 0.4
            self.fly.velocity[2] *= -0.4

    def _try_eat(self, food_sources: List[Dict], reach: float = 1.2) -> float:
        """Consume food when the fly reaches a source it is interested in."""
        eaten = 0.0
        for source in food_sources:
            if source.get("amount", 0.0) <= 0.0:
                continue
            distance = float(np.linalg.norm(
                np.array(source["position"], dtype=float) - self.fly.position
            ))
            if distance > reach:
                continue

            wants_food = (not self.hunger.enabled) or self.hunger.energy < self.hunger.max_energy
            if not wants_food:
                continue

            bite = min(source["amount"], 25.0 * 0.5)
            source["amount"] -= bite
            eaten += bite
            if self.hunger.enabled:
                self.survival.process_feeding(bite)
            if self.eating_timer <= 0.0:
                self.meals_eaten += 1
            self.eating_timer = 1.5
            break
        return eaten

    def reset(self, start_position: Optional[Tuple[float, float, float]] = None):
        if start_position is None:
            start_position = (0.0, 0.0, float(self.bounds[2]) * 0.5)
        self.fly.reset(start_position)
        self.network.reset()
        enabled = self.hunger.enabled
        self.survival.reset()
        self.set_hunger_enabled(enabled)
        self.eating_timer = 0.0
        self.meals_eaten = 0
        self.behavior = "exploring"


if __name__ == "__main__":
    print("Testing brain-driven fly controller (headless)...")
    controller = BrainFlyController(bounds=(20.0, 20.0, 12.0))
    food = [
        {"position": (-8.0, -8.0, 0.8), "amount": 100.0},
        {"position": (8.0, -8.0, 0.8), "amount": 100.0},
        {"position": (-8.0, 8.0, 0.8), "amount": 100.0},
        {"position": (8.0, 8.0, 0.8), "amount": 100.0},
    ]

    for step in range(300):
        state = controller.update(1 / 60.0, food)
        if step % 60 == 0:
            pos = state["position"]
            print(f"t={step/60:.1f}s pos=({pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f}) "
                  f"speed={state['speed']:.2f} energy={state['energy']:.1f} "
                  f"behavior={state['behavior']}")

    print("Brain state:", controller.network.get_state())
    print("Controller test completed!")
