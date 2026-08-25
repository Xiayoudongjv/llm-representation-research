from __future__ import annotations

import json
from pathlib import Path

from experiments.paper_a import validate_paper_a_release as release


def test_release_validator_passes_on_frozen_assets() -> None:
    summary = release.validate()
    assert summary["profile_models"] == 3
    assert summary["figures"] == 5
    assert summary["tables"] == 4


def test_profile_assets_keep_classification_and_continuous_ci() -> None:
    data = json.loads((release.ASSET_ROOT / "data/figure_02_profile_data.json").read_text(encoding="utf-8"))
    for profile in data["profiles"].values():
        for metric in ("distance_related_degradation", "sdi"):
            assert "classification" in profile[metric] or "support" in profile[metric]
            assert "statistic" in profile[metric]
            assert set(profile[metric]["confidence_interval"]) == {"lower", "upper"}
        recovery = profile["restricted_low_d_recovery"]
        assert "support" in recovery
        assert "mean_recovery" in recovery
        assert set(recovery["confidence_interval"]) == {"lower", "upper"}


def test_handoff_and_attack_matrix_are_scoped() -> None:
    root = Path(__file__).resolve().parents[1] / "docs/paper_a"
    handoff = (root / "PAPER-A-MANUSCRIPT-HANDOFF-V0.1.md").read_text(encoding="utf-8")
    matrix = (root / "PAPER-A-REVIEWER-ATTACK-MATRIX.md").read_text(encoding="utf-8")
    assert "CROSS_TASK_ROBUSTNESS" in handoff
    assert "three tested models" in handoff
    assert "statistically or causally independent" in handoff
    for attack in ("NOVELTY_TOO_CLOSE_TO_PROBING", "LAST_TOKEN_CARRIER_LIMITATION", "NO_CKA_BASELINE"):
        assert attack in matrix
