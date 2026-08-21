"""Prospective EXP-027 bootstrap prototype.

This module is an engineering-only prototype. It does not modify the frozen
EXP-026 reference implementation and it must not be used for scientific
interpretation until a future EXP-027 engineering qualification demonstrates
equivalence against the reference implementation.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any, Sequence

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
EXP026_DIR = ROOT / "experiments" / "exp026"
if str(EXP026_DIR) not in sys.path:
    sys.path.insert(0, str(EXP026_DIR))

import run_exp026 as ref  # noqa: E402


CLASS_ORDER = ref.CLASS_ORDER
CONDITION_ORDER = ref.CONDITION_ORDER


def _eval_clusters(observations: Sequence[Any], condition_order: Sequence[str]) -> dict[str, dict[str, list[Any]]]:
    eval_rows = ref.filter_condition_realization(observations, "EVAL")
    clusters: dict[str, dict[str, list[Any]]] = {}
    for condition in condition_order:
        by_family: dict[str, list[Any]] = {}
        for obs in eval_rows:
            if obs.condition_id == condition:
                by_family.setdefault(obs.source_family_id, []).append(obs)
        if not by_family:
            raise ref.ProtocolIntegrityError("BOOTSTRAP_CONDITION_CLUSTER_EMPTY")
        clusters[condition] = by_family
    return clusters


def _precompute_cell_counts(
    clusters: dict[str, dict[str, list[Any]]],
    condition_order: Sequence[str],
    num_layers: int,
    models: Sequence[Any],
    calibration: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Precompute classwise additive counts for C0 and Ccal per family cluster."""
    condition_index = {condition: index for index, condition in enumerate(condition_order)}
    target_by_layer_condition = calibration["target_by_layer_condition"]
    precomputed: dict[str, dict[str, Any]] = {}

    for condition in condition_order:
        c_index = condition_index[condition]
        precomputed[condition] = {}
        for family_id, family_obs in clusters[condition].items():
            # cell[source][target][class] = [n, c0_correct, ccal_correct]
            cell = [[[ [0, 0, 0] for _ in CLASS_ORDER ] for _ in range(num_layers)] for _ in range(num_layers)]
            y = [obs.semantic_class for obs in family_obs]
            for target in range(num_layers):
                X = np.stack([obs.vectors[target] for obs in family_obs], axis=0).astype(np.float32)
                mean, scale = target_by_layer_condition[target][c_index]
                Z = ref.transform_with_stats(X, mean, scale)
                for source in range(num_layers):
                    pred = [str(value) for value in models[source].predict(X)]
                    pred_cal = [str(value) for value in models[source].predict(Z)]
                    for row_index, cls in enumerate(y):
                        cell[source][target][CLASS_ORDER.index(cls)][0] += 1
                        if pred[row_index] == cls:
                            cell[source][target][CLASS_ORDER.index(cls)][1] += 1
                        if pred_cal[row_index] == cls:
                            cell[source][target][CLASS_ORDER.index(cls)][2] += 1
            class_totals = [sum(1 for obs in family_obs if obs.semantic_class == CLASS_ORDER[cls_index]) for cls_index in range(len(CLASS_ORDER))]
            precomputed[condition][family_id] = {
                "cell": cell,
                "class_totals": class_totals,
            }
    return precomputed


def optimized_bootstrap_model_summaries(
    observations: Sequence[Any],
    num_layers: int,
    condition_order: Sequence[str],
    models: Sequence[Any],
    calibration: dict[str, Any],
    eligible_mask: Sequence[bool],
    diag_dbar: np.ndarray,
    low_d_mask: np.ndarray,
    replicates: int,
    rng: np.random.Generator,
) -> dict[str, Any]:
    """Return the same registered bootstrap summaries as the reference path."""
    clusters = _eval_clusters(observations, condition_order)
    precomputed = _precompute_cell_counts(clusters, condition_order, num_layers, models, calibration)
    dist_values = []
    sdi_values = []
    low_values = []

    for _ in range(replicates):
        condition_cells: dict[str, Any] = {}
        condition_class_totals: dict[str, list[int]] = {}
        for condition in condition_order:
            family_ids = sorted(clusters[condition])
            sampled_indices = rng.integers(0, len(family_ids), size=len(family_ids))
            cell = [[[ [0, 0, 0] for _ in CLASS_ORDER ] for _ in range(num_layers)] for _ in range(num_layers)]
            class_totals = [0] * len(CLASS_ORDER)
            for index in sampled_indices:
                family_id = family_ids[int(index)]
                family_pre = precomputed[condition][family_id]
                for cls_index in range(len(CLASS_ORDER)):
                    class_totals[cls_index] += family_pre["class_totals"][cls_index]
                for source in range(num_layers):
                    for target in range(num_layers):
                        for cls_index in range(len(CLASS_ORDER)):
                            for field in range(3):
                                cell[source][target][cls_index][field] += family_pre["cell"][source][target][cls_index][field]
            condition_cells[condition] = cell
            condition_class_totals[condition] = class_totals

        if any(any(total == 0 for total in condition_class_totals[condition]) for condition in condition_order):
            continue

        c0 = np.zeros((num_layers, num_layers, len(condition_order)), dtype=np.float32)
        ccal = np.zeros((num_layers, num_layers, len(condition_order)), dtype=np.float32)
        for c_index, condition in enumerate(condition_order):
            cell = condition_cells[condition]
            for source in range(num_layers):
                for target in range(num_layers):
                    recalls = []
                    ccal_recalls = []
                    for cls_index in range(len(CLASS_ORDER)):
                        total, c0_correct, ccal_correct = cell[source][target][cls_index]
                        if total == 0:
                            raise ref.ProtocolIntegrityError("BOOTSTRAP_CLASS_COUNT_ZERO")
                        recalls.append(c0_correct / total)
                        ccal_recalls.append(ccal_correct / total)
                    c0[source, target, c_index] = float(sum(recalls) / len(recalls))
                    ccal[source, target, c_index] = float(sum(ccal_recalls) / len(ccal_recalls))

        d_eval = ref.delta_from_c0(c0)
        r_eval = ref.residual_from_calibration(ccal, c0)
        dbar = ref._condition_pool(d_eval)
        rbar = ref._condition_pool(r_eval)
        point = ref._summarize_point_profile(dbar, rbar, eligible_mask, num_layers, diag_dbar)
        dist_values.append(point["distance_association"])
        sdi_values.append(point["sdi"]["sdi"])
        pairs = [(i, j) for i in range(num_layers) for j in range(num_layers) if low_d_mask[i, j]]
        low_values.append(float(np.mean([float(rbar[i, j]) for i, j in pairs])) if pairs else float("nan"))

    dist_values = [value for value in dist_values if math.isfinite(value)]
    sdi_values = [value for value in sdi_values if math.isfinite(value)]
    low_values = [value for value in low_values if math.isfinite(value)]
    if not sdi_values:
        raise ref.ProtocolIntegrityError("BOOTSTRAP_NO_EVALUABLE_REPLICATES")
    return {
        "distance_association_ci": [ref._percentile(dist_values, 5), ref._percentile(dist_values, 95)],
        "sdi_ci": [ref._percentile(sdi_values, 5), ref._percentile(sdi_values, 95)],
        "low_d_recovery_ci": [ref._percentile(low_values, 5), ref._percentile(low_values, 95)],
        "replicates": replicates,
    }


def optimized_matrix_bootstrap(
    observations: Sequence[Any],
    num_layers: int,
    condition_order: Sequence[str],
    bootstrap_replicates: int,
    rng: np.random.Generator,
) -> dict[str, Any] | None:
    """Fit the same frozen point estimators and return the optimized bootstrap object."""
    models = ref._fit_source_models(observations, num_layers)
    calibration = ref._fit_pair_calibration(observations, num_layers, condition_order)
    qual = ref._source_qualification(observations, num_layers, models, condition_order)
    if not qual["source_coverage_evaluable"]:
        return None
    c0_eval = ref._compute_c0_for_partition(observations, "EVAL", num_layers, condition_order, models)
    c0_diag = ref._compute_c0_for_partition(observations, "DIAGNOSTIC", num_layers, condition_order, models)
    d_diag = ref.delta_from_c0(c0_diag)
    dbar_diag = ref._condition_pool(d_diag)
    low_mask, _ = ref._low_d_pair_mask(dbar_diag, qual["eligible_source_mask"], num_layers)
    return optimized_bootstrap_model_summaries(
        observations,
        num_layers,
        condition_order,
        models,
        calibration,
        qual["eligible_source_mask"],
        dbar_diag,
        low_mask,
        bootstrap_replicates,
        rng,
    )