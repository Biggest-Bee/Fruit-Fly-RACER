"""
Tests for the recurrent spiking network that drives the fly's body.
"""

import os
import sys
import unittest

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '3d_environment'))

from brain_controller import BrainFlyController, NeuralMotorNetwork  # noqa: E402


def drive(network: NeuralMotorNetwork, signals: dict, frames: int = 30) -> dict:
    rates = {}
    for _ in range(frames):
        rates = network.step(signals)
    return rates


class TestNeuralMotorNetwork(unittest.TestCase):
    def test_neurons_are_connected_to_each_other(self):
        network = NeuralMotorNetwork()
        state = network.get_state()
        self.assertGreater(state["recurrent_connections"], 0)
        self.assertTrue(any(network.sensory_to_inter.values()))
        self.assertTrue(any(network.inter_to_motor))

    def test_food_on_the_left_turns_the_fly_left(self):
        network = NeuralMotorNetwork()
        rates = drive(network, {"food_left": 1.0, "hunger": 1.0})
        self.assertGreater(rates["yaw_left"], rates["yaw_right"])

    def test_food_on_the_right_turns_the_fly_right(self):
        network = NeuralMotorNetwork()
        rates = drive(network, {"food_right": 1.0, "hunger": 1.0})
        self.assertGreater(rates["yaw_right"], rates["yaw_left"])

    def test_food_above_pitches_up(self):
        network = NeuralMotorNetwork()
        rates = drive(network, {"food_up": 1.0, "hunger": 1.0})
        self.assertGreater(rates["pitch_up"], rates["pitch_down"])

    def test_silent_input_keeps_motors_quiet(self):
        network = NeuralMotorNetwork()
        rates = drive(network, {})
        self.assertLess(sum(rates.values()), 1.0)


class TestBrainDrivenFly(unittest.TestCase):
    def test_fly_moves_in_three_dimensions(self):
        controller = BrainFlyController(bounds=(20.0, 20.0, 12.0))
        food = [
            {"position": (-8.0, -8.0, 1.0), "amount": 100.0},
            {"position": (8.0, -8.0, 9.0), "amount": 100.0},
            {"position": (-8.0, 8.0, 1.0), "amount": 100.0},
            {"position": (8.0, 8.0, 9.0), "amount": 100.0},
        ]
        start = controller.fly.position.copy()
        moved = [False, False, False]
        for _ in range(900):
            state = controller.update(1 / 60.0, food)
            for axis in range(3):
                if abs(state["position"][axis] - start[axis]) > 0.5:
                    moved[axis] = True
        self.assertTrue(all(moved), f"fly did not move on every axis: {moved}")

    def test_fly_stays_inside_the_enclosure(self):
        controller = BrainFlyController(bounds=(20.0, 20.0, 12.0))
        food = [{"position": (9.0, 9.0, 1.0), "amount": 100.0}]
        for _ in range(900):
            state = controller.update(1 / 60.0, food)
            self.assertLessEqual(abs(state["position"][0]), 10.0)
            self.assertLessEqual(abs(state["position"][1]), 10.0)
            self.assertGreaterEqual(state["position"][2], 0.0)
            self.assertLessEqual(state["position"][2], 12.0)

    def test_hunger_can_be_turned_off_and_on(self):
        controller = BrainFlyController(bounds=(20.0, 20.0, 12.0))
        food = [{"position": (8.0, 8.0, 1.0), "amount": 100.0}]

        controller.set_hunger_enabled(False)
        for _ in range(600):
            controller.update(1 / 60.0, food)
        self.assertFalse(controller.hunger_enabled)
        self.assertAlmostEqual(controller.hunger.energy, controller.hunger.max_energy, places=5)
        self.assertEqual(controller.hunger.hunger_drive, 0.0)

        self.assertTrue(controller.toggle_hunger())
        for _ in range(600):
            controller.update(1 / 60.0, food)
        self.assertLess(controller.hunger.energy, controller.hunger.max_energy)

    def test_hungry_fly_reaches_food_and_eats(self):
        controller = BrainFlyController(bounds=(20.0, 20.0, 12.0))
        controller.hunger.energy = 30.0
        food = [
            {"position": (-8.0, -8.0, 1.0), "amount": 100.0},
            {"position": (8.0, -8.0, 1.0), "amount": 100.0},
            {"position": (-8.0, 8.0, 1.0), "amount": 100.0},
            {"position": (8.0, 8.0, 1.0), "amount": 100.0},
        ]
        for _ in range(3600):
            controller.update(1 / 60.0, food)
            if controller.meals_eaten > 0:
                break
        self.assertGreater(controller.meals_eaten, 0, "fly never reached any food")


if __name__ == "__main__":
    unittest.main()
