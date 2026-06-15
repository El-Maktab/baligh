"""Confidence shared by GED subsystems.

NOTE: maybe we will make this more complex if we found that
fusion is not working well.

Authors:
    Amir Anwar
"""

from src.services.ged.schemas import ProvenanceTier

TIER_CONFIDENCE: dict[ProvenanceTier, float] = {
    ProvenanceTier.TIER_1_RULE_DERIVED: 1.0,
    ProvenanceTier.TIER_2_RULE_SUPPORTED: 0.8,
    ProvenanceTier.TIER_3_STATISTICAL: 0.5,
}
