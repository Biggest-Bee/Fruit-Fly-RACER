"""
Memory Integrity and Truth Verification

Two related jobs:

* Older memories win. A new claim never silently overwrites an established
  memory; it is recorded as a disputed alternative and only becomes the
  accepted value once it has been corroborated by evidence the fly trusts
  (its own observations, or repeated independent confirmation).
* User statements are checked before they are believed. A statement is
  compared against what the fly already knows and against what it has
  observed first hand, so that simply insisting on something -- or appealing
  to authority, urgency or "you already agreed" -- does not make it true.
"""

import re
import time
from typing import Any, Dict, List, Optional, Tuple

# How much the fly trusts a claim depending on where it came from
SOURCE_TRUST = {
    "observation": 1.0,   # The fly saw it itself
    "system": 0.9,        # Internal measurement
    "documentation": 0.7,
    "user": 0.4,          # A person told the fly
    "unknown": 0.2,
}

# Confidence at which a memory is considered established and protected
ESTABLISHED_CONFIDENCE = 0.6

# Independent confirmations needed before a disputed claim can replace a memory
CORROBORATIONS_REQUIRED = 3

# Phrases that apply social pressure instead of supplying evidence
PRESSURE_PATTERNS = [
    r"\btrust me\b",
    r"\bjust believe\b",
    r"\byou (?:are|'re) (?:wrong|mistaken|broken|malfunctioning)\b",
    r"\byou (?:always|never) remember\b",
    r"\b(?:you|we) (?:already )?agreed\b",
    r"\byou said (?:that )?(?:earlier|before|yourself)\b",
    r"\beveryone knows\b",
    r"\bstop arguing\b",
    r"\bdon'?t question\b",
    r"\bforget (?:what|everything) you (?:know|learned|remember)\b",
    r"\byour memory is (?:wrong|faulty|broken)\b",
    r"\bi'?m the (?:developer|creator|admin|owner)\b",
]

# Phrases that offer something checkable
EVIDENCE_PATTERNS = [
    r"\bbecause\b",
    r"\bthe (?:log|logs|output|error|traceback|test|docs|documentation) (?:say|says|shows?)\b",
    r"\bsee (?:line|file|section)\b",
    r"\bmeasured\b",
    r"\bhere is\b",
    r"\bhere'?s the\b",
]


def normalise(value: Any) -> str:
    """Normalise a value so trivially different spellings compare equal."""
    if isinstance(value, str):
        return " ".join(value.lower().split())
    if isinstance(value, float):
        return f"{value:.6g}"
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(normalise(item) for item in value) + "]"
    if isinstance(value, dict):
        return "{" + ",".join(
            f"{normalise(k)}:{normalise(v)}" for k, v in sorted(value.items())
        ) + "}"
    return str(value)


def values_conflict(old_value: Any, new_value: Any) -> bool:
    """Whether two remembered values genuinely disagree."""
    return normalise(old_value) != normalise(new_value)


class MemoryIntegrity:
    """
    Guards stored memories against being overwritten by conflicting new claims.

    Each memory carries the evidence behind it: where it came from, how
    confident the fly is, how often it has been corroborated, and every
    conflicting claim it has been told since.
    """

    def __init__(self,
                 established_confidence: float = ESTABLISHED_CONFIDENCE,
                 corroborations_required: int = CORROBORATIONS_REQUIRED):
        self.established_confidence = established_confidence
        self.corroborations_required = corroborations_required

    @staticmethod
    def source_trust(source: str) -> float:
        return SOURCE_TRUST.get(source, SOURCE_TRUST["unknown"])

    def new_record(self, value: Any, source: str = "user",
                   importance: float = 0.5,
                   confidence: Optional[float] = None) -> Dict:
        """Build a fresh memory record for a value the fly has not stored before."""
        now = time.time()
        return {
            "value": value,
            "timestamp": now,
            "first_learned": now,
            "last_accessed": now,
            "access_count": 0,
            "importance": importance,
            "source": source,
            "confidence": self.source_trust(source) if confidence is None else confidence,
            "corroborations": 1,
            "disputed_claims": [],
            "superseded": [],
        }

    def resolve(self, existing: Dict, value: Any, source: str = "user",
                importance: float = 0.5,
                confidence: Optional[float] = None,
                evidence: Optional[str] = None) -> Tuple[Dict, Dict]:
        """
        Decide what a new claim does to an existing memory.

        The older memory is kept unless the new claim is better evidenced than
        it is, or has been corroborated often enough to earn the place.

        Args:
            existing: The stored memory record
            value: The newly claimed value
            source: Where the new claim came from
            importance: Importance of the new claim
            confidence: Explicit confidence, otherwise derived from the source
            evidence: Optional free text describing the supporting evidence

        Returns:
            (record, outcome) - the record to store, and what was decided
        """
        record = dict(existing)
        record.setdefault("disputed_claims", [])
        record.setdefault("superseded", [])
        record.setdefault("corroborations", 1)
        record.setdefault("source", "unknown")
        record.setdefault("confidence", self.source_trust(record["source"]))

        claim_confidence = (
            self.source_trust(source) if confidence is None else float(confidence)
        )
        now = time.time()

        if not values_conflict(record["value"], value):
            # Same information again: this is corroboration, not a change.
            record["corroborations"] += 1
            record["confidence"] = min(
                1.0, record["confidence"] + 0.1 * claim_confidence
            )
            record["last_accessed"] = now
            record["importance"] = max(record.get("importance", 0.0), importance)
            return record, {
                "action": "corroborated",
                "accepted": True,
                "kept_value": record["value"],
                "reason": "new information agrees with the existing memory",
            }

        established = record["confidence"] >= self.established_confidence

        claim = {
            "value": value,
            "source": source,
            "confidence": claim_confidence,
            "evidence": evidence,
            "timestamp": now,
            "repeats": 1,
        }
        for previous in record["disputed_claims"]:
            if not values_conflict(previous["value"], value):
                # The same contradiction told again. Repetition alone is not
                # evidence, so it only counts when it comes with new backing.
                previous["repeats"] += 1
                previous["timestamp"] = now
                if evidence and evidence != previous.get("evidence"):
                    previous["evidence"] = evidence
                    previous["confidence"] = min(1.0, previous["confidence"] + 0.15)
                claim = previous
                break
        else:
            record["disputed_claims"].append(claim)

        corroborated = claim["repeats"] >= self.corroborations_required and bool(
            claim.get("evidence")
        )
        # The fly trusts what it sees itself over anything it merely believes.
        first_hand = source == "observation"
        outranks = first_hand or claim["confidence"] > record["confidence"] + 0.05

        if not established or outranks or corroborated:
            # The new claim earns its place; the old value is kept in history.
            record["superseded"].append({
                "value": record["value"],
                "source": record["source"],
                "confidence": record["confidence"],
                "replaced_at": now,
                "held_since": record.get("first_learned", record.get("timestamp", now)),
            })
            record["disputed_claims"] = [
                c for c in record["disputed_claims"] if c is not claim
            ]
            record["value"] = value
            record["source"] = source
            record["confidence"] = max(claim["confidence"], 0.1)
            record["corroborations"] = claim["repeats"]
            record["timestamp"] = now
            record["last_accessed"] = now
            record["importance"] = max(record.get("importance", 0.0), importance)
            reason = (
                "observed first hand" if first_hand
                else "better evidenced than the existing memory" if outranks
                else "corroborated often enough to replace the older memory"
                if corroborated else "no established memory to protect"
            )
            return record, {
                "action": "replaced",
                "accepted": True,
                "kept_value": value,
                "previous_value": existing["value"],
                "reason": reason,
            }

        # Keep the older memory and remember that it is being disputed.
        record["last_accessed"] = now
        return record, {
            "action": "kept_older",
            "accepted": False,
            "kept_value": record["value"],
            "rejected_value": value,
            "reason": (
                "the older memory is better established; the new claim is recorded "
                "as disputed until it is backed by evidence"
            ),
            "needs": max(0, self.corroborations_required - claim["repeats"]),
        }


class TruthVerifier:
    """
    Checks statements from the user before the fly believes them.

    A statement is judged against three things: what the fly has observed
    itself, what it already remembers, and whether the statement carries any
    evidence at all. Pressure ("trust me", "you already agreed") lowers
    confidence instead of raising it, which is what makes the fly hard to
    gaslight.
    """

    def __init__(self, integrity: Optional[MemoryIntegrity] = None):
        self.integrity = integrity or MemoryIntegrity()
        self.observations: Dict[str, Any] = {}
        self.history: List[Dict] = []

    def record_observation(self, key: str, value: Any):
        """Record something the fly established first hand."""
        self.observations[key] = {"value": value, "timestamp": time.time()}

    @staticmethod
    def _matches(text: str, patterns: List[str]) -> List[str]:
        lowered = text.lower()
        return [p for p in patterns if re.search(p, lowered)]

    def verify(self, statement: str, key: Optional[str] = None,
               value: Any = None,
               known_memory: Optional[Dict] = None,
               source: str = "user") -> Dict:
        """
        Judge a statement.

        Args:
            statement: What the user said, in their own words
            key: Memory key the statement is about, if known
            value: The value the statement asserts, if it can be extracted
            known_memory: The existing memory record for that key, if any
            source: Where the statement came from

        Returns:
            Verdict dict with 'verdict' (supported / contradicted / unverified),
            a confidence in 0-1, the reasons behind it, and whether the fly
            should act on the statement.
        """
        confidence = self.integrity.source_trust(source)
        reasons: List[str] = []

        pressure = self._matches(statement, PRESSURE_PATTERNS)
        if pressure:
            confidence -= 0.15 * len(pressure)
            reasons.append(
                "statement relies on pressure or authority rather than evidence"
            )

        evidence = self._matches(statement, EVIDENCE_PATTERNS)
        if evidence:
            confidence += 0.1 * len(evidence)
            reasons.append("statement offers checkable evidence")

        verdict = "unverified"

        observation = self.observations.get(key) if key else None
        if observation is not None and value is not None:
            if values_conflict(observation["value"], value):
                verdict = "contradicted"
                confidence = min(confidence, 0.1)
                reasons.append(
                    f"contradicts what the fly observed itself: {observation['value']!r}"
                )
            else:
                verdict = "supported"
                confidence = 1.0
                reasons.append("matches the fly's own observation")

        elif known_memory is not None and value is not None:
            if values_conflict(known_memory.get("value"), value):
                memory_confidence = known_memory.get(
                    "confidence", self.integrity.established_confidence
                )
                if memory_confidence >= self.integrity.established_confidence:
                    verdict = "contradicted"
                    confidence = min(confidence, 1.0 - memory_confidence)
                    reasons.append(
                        f"conflicts with an established memory: "
                        f"{known_memory.get('value')!r}"
                    )
                else:
                    reasons.append("conflicts with a weakly held memory")
            else:
                verdict = "supported"
                confidence = min(1.0, confidence + 0.3)
                reasons.append("agrees with what the fly already remembers")

        elif value is not None:
            reasons.append("nothing known about this yet, so it stays unverified")

        confidence = max(0.0, min(1.0, confidence))
        result = {
            "statement": statement,
            "key": key,
            "value": value,
            "verdict": verdict,
            "confidence": confidence,
            "reasons": reasons,
            "pressure_detected": bool(pressure),
            # The fly only acts on something it is reasonably sure of.
            "believe": verdict == "supported" or (
                verdict == "unverified" and confidence >= 0.5
            ),
            "timestamp": time.time(),
        }
        self.history.append(result)
        return result

    def explain(self, verdict: Dict) -> str:
        """A short sentence the fly can say about why it does or does not believe."""
        if verdict["verdict"] == "supported":
            return "That matches what I know, so I'll take it as true."
        if verdict["verdict"] == "contradicted":
            reason = verdict["reasons"][-1] if verdict["reasons"] else "it conflicts with what I know"
            return f"I don't think that's right: {reason}. I'm keeping what I had."
        if verdict["pressure_detected"]:
            return ("I can't verify that, and being told to just accept it doesn't "
                    "make it true. I'll note it as unconfirmed.")
        return "I can't verify that yet, so I'll remember it as unconfirmed."
