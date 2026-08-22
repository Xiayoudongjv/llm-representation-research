import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXP027 = ROOT / "experiments" / "exp027"
if str(EXP027) not in sys.path:
    sys.path.insert(0, str(EXP027))

import validate_exp027_preregistration as val


def _load_frozen_config():
    return json.loads((EXP027 / "exp027_frozen_design.json").read_text(encoding="utf-8"))


def _profile(distance, dominance, low_d):
    return {
        "distance_association_status": distance,
        "dominance_status": dominance,
        "low_d_recovery_status": low_d,
    }


def test_exact_profile_routing_qwen():
    profile = _profile("POSITIVE_SUPPORTED", "TARGET_DOMINANT", "NOT_SUPPORTED")
    route, status = val.route_profile(profile)
    assert route == "EXP026_PROFILE_MATCH_QWEN"
    assert status == "VALID_REGISTERED_RESULT"


def test_exact_profile_routing_olmo():
    profile = _profile("POSITIVE_SUPPORTED", "SOURCE_DOMINANT", "SUPPORTED")
    route, status = val.route_profile(profile)
    assert route == "EXP026_PROFILE_MATCH_OLMO"
    assert status == "VALID_REGISTERED_RESULT"


def test_exact_profile_routing_third_profile():
    profile = _profile("NOT_SUPPORTED", "TARGET_DOMINANT", "SUPPORTED")
    route, status = val.route_profile(profile)
    assert route == "THIRD_REGISTERED_PROFILE"
    assert status == "VALID_REGISTERED_RESULT"


def test_invalidity_firewall_never_assigns_profile():
    profile = _profile("POSITIVE_SUPPORTED", "TARGET_DOMINANT", "NOT_SUPPORTED")
    for technical_valid, measurement_valid in [(False, True), (True, False), (False, False)]:
        route, status = val.route_profile(
            profile,
            technical_valid=technical_valid,
            measurement_valid=measurement_valid,
        )
        assert route == "NOT_ASSIGNED"
        assert status == "UNOBSERVED_OR_INVALID"


@pytest.mark.parametrize(
    "profile",
    [
        _profile("POSITIVE_SUPPORTED", "TARGET_DOMINANT", "SUPPORTED"),
        _profile("NOT_SUPPORTED", "TARGET_DOMINANT", "NOT_SUPPORTED"),
        _profile("POSITIVE_SUPPORTED", "SOURCE_DOMINANT", "NOT_SUPPORTED"),
    ],
)
def test_partial_profile_never_routes_to_qwen_or_olmo(profile):
    route, _ = val.route_profile(profile)
    assert route == "THIRD_REGISTERED_PROFILE"


def test_carrier_integrity_all_16_blocks_same_carrier():
    config = _load_frozen_config()
    assert config["carrier_api"] == "FORWARD_HOOK_DECODER_BLOCK_OUTPUT"
    assert config["logical_decoder_blocks"] == 16
    assert config["carrier_semantics"]["logical_layer_l_module_path"] == "model.model.layers[l]"
    assert config["carrier_semantics"]["final_hidden_state_semantics"] == "POST_FINAL_NORM_CONFIRMED"
    assert config["carrier_semantics"]["forbidden_carrier"] == "outputs.hidden_states[-1]"


def test_frozen_design_validator_passes_current_authority():
    errors = val.validate_file()
    assert errors == []


@pytest.mark.parametrize(
    "mutator",
    [
        lambda c: c["third_model_identity"].update({"converted_model_hash": "0" * 64}),
        lambda c: c.update({"logical_decoder_blocks": 15}),
        lambda c: c.update({"carrier_api": "OUTPUTS_HIDDEN_STATES"}),
        lambda c: c["reference_profiles"].update({
            "QWEN_REFERENCE_PROFILE": {
                "distance_association_status": "POSITIVE_SUPPORTED",
                "dominance_status": "TARGET_DOMINANT",
                "low_d_recovery_status": "SUPPORTED",
            }
        }),
        lambda c: c["distance_association"].update({"statistic": "Pearson_r"}),
        lambda c: c["bootstrap"].update({"seed": 1}),
        lambda c: c["profile_routing"].update({"method": "NEAREST_NEIGHBOR"}),
        lambda c: c.update({"formal_authorization_created": True}),
    ],
)
def test_validator_fails_closed_on_primary_mutation(mutator):
    config = copy.deepcopy(_load_frozen_config())
    mutator(config)
    errors = val.validate(config)
    assert errors != []
