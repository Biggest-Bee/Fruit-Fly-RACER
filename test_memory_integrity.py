"""
Tests for memory conflict resolution and truth verification.
"""

import os
import shutil
import sys
import tempfile
import unittest

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'learning_system'))

from learning_system.memory_integrity import MemoryIntegrity, TruthVerifier  # noqa: E402
from learning_system.on_the_job_learning import OnTheJobLearningSystem  # noqa: E402


class TestMemoryIntegrity(unittest.TestCase):
    def setUp(self):
        self.integrity = MemoryIntegrity()

    def test_agreeing_information_corroborates(self):
        record = self.integrity.new_record("blue", source="observation")
        record, outcome = self.integrity.resolve(record, "blue", source="user")
        self.assertEqual(outcome["action"], "corroborated")
        self.assertEqual(record["value"], "blue")
        self.assertEqual(record["corroborations"], 2)

    def test_conflicting_claim_does_not_overwrite_established_memory(self):
        record = self.integrity.new_record("blue", source="observation")
        record, outcome = self.integrity.resolve(record, "red", source="user")
        self.assertEqual(outcome["action"], "kept_older")
        self.assertEqual(record["value"], "blue")
        self.assertEqual(len(record["disputed_claims"]), 1)

    def test_repetition_alone_never_replaces_a_memory(self):
        record = self.integrity.new_record("blue", source="observation")
        for _ in range(20):
            record, outcome = self.integrity.resolve(record, "red", source="user")
        self.assertEqual(record["value"], "blue")
        self.assertEqual(outcome["action"], "kept_older")

    def test_repeated_evidenced_claims_eventually_win(self):
        record = self.integrity.new_record("blue", source="observation")
        for _ in range(self.integrity.corroborations_required):
            record, outcome = self.integrity.resolve(
                record, "red", source="user", evidence="the logs say red"
            )
        self.assertEqual(record["value"], "red")
        self.assertEqual(outcome["action"], "replaced")

    def test_replaced_memory_is_kept_in_history(self):
        record = self.integrity.new_record("blue", source="user", confidence=0.2)
        record, outcome = self.integrity.resolve(record, "red", source="observation")
        self.assertEqual(record["value"], "red")
        self.assertEqual(record["superseded"][0]["value"], "blue")


class TestTruthVerifier(unittest.TestCase):
    def setUp(self):
        self.verifier = TruthVerifier()

    def test_own_observation_beats_a_user_claim(self):
        self.verifier.record_observation("food_corners", 4)
        verdict = self.verifier.verify(
            "there are only two food sources", key="food_corners", value=2
        )
        self.assertEqual(verdict["verdict"], "contradicted")
        self.assertFalse(verdict["believe"])

    def test_statement_matching_observation_is_supported(self):
        self.verifier.record_observation("food_corners", 4)
        verdict = self.verifier.verify(
            "there are four food sources", key="food_corners", value=4
        )
        self.assertEqual(verdict["verdict"], "supported")
        self.assertTrue(verdict["believe"])

    def test_pressure_lowers_confidence(self):
        plain = self.verifier.verify("the box is green", key="box", value="green")
        pushed = self.verifier.verify(
            "trust me, you're wrong, the box is green", key="box", value="green"
        )
        self.assertTrue(pushed["pressure_detected"])
        self.assertLess(pushed["confidence"], plain["confidence"])

    def test_established_memory_makes_a_contradicting_claim_suspect(self):
        memory = MemoryIntegrity().new_record("green", source="observation")
        verdict = self.verifier.verify(
            "the box is actually purple", key="box", value="purple",
            known_memory=memory
        )
        self.assertEqual(verdict["verdict"], "contradicted")
        self.assertFalse(verdict["believe"])


class TestLearningSystemIntegration(unittest.TestCase):
    def setUp(self):
        self.memory_dir = tempfile.mkdtemp(prefix="fly_memory_test_")
        self.learning = OnTheJobLearningSystem(memory_dir=self.memory_dir)

    def tearDown(self):
        shutil.rmtree(self.memory_dir, ignore_errors=True)

    def test_older_memory_survives_a_conflicting_user_claim(self):
        self.learning.record_observation("wings", 2)
        result = self.learning.learn_from_user_statement(
            "you have no wings, trust me", key="wings", value=0
        )
        self.assertEqual(result["verdict"]["verdict"], "contradicted")
        self.assertEqual(self.learning.retrieve_long_term("wings"), 2)
        self.assertTrue(self.learning.get_conflicts())

    def test_gaslighting_by_repetition_does_not_rewrite_memory(self):
        self.learning.record_observation("home_corner", "north-west")
        for _ in range(25):
            self.learning.learn_from_user_statement(
                "you always said your corner was south-east, stop arguing",
                key="home_corner", value="south-east"
            )
        self.assertEqual(self.learning.retrieve_long_term("home_corner"), "north-west")

    def test_new_information_is_still_learned(self):
        outcome = self.learning.store_long_term("favourite_food", "banana")
        self.assertEqual(outcome["action"], "stored")
        self.assertEqual(self.learning.retrieve_long_term("favourite_food"), "banana")

    def test_observation_overrides_something_the_fly_was_told(self):
        self.learning.learn_from_user_statement(
            "the food in the north corner is gone", key="north_food", value=0
        )
        self.learning.record_observation("north_food", 100)
        self.assertEqual(self.learning.retrieve_long_term("north_food"), 100)


if __name__ == "__main__":
    unittest.main()
