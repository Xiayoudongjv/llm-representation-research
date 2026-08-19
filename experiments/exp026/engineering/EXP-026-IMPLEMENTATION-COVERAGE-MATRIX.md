# EXP-026 Implementation Coverage Matrix

Status key: `IMPLEMENTED_AND_TESTED`

| Frozen endpoint | Implementation | Test / qualification | Status |
| --- | --- | --- | --- |
| Frozen authority hashes | `verify_frozen_design` | `test_frozen_authorities_match` | `IMPLEMENTED_AND_TESTED` |
| Mode separation / fail-closed parser | `build_parser`, `main` | `test_mode_requires_one_mode` | `IMPLEMENTED_AND_TESTED` |
| Formal authorization required | `run_formal_run`, `validate_formal_authorization` | `test_formal_run_fails_closed_without_authorization`, `test_formal_authorization_validation` | `IMPLEMENTED_AND_TESTED` |
| All-layer carrier extraction | `extract_all_layers`, `ForwardHookCapture` | `test_fake_all_layer_extraction`; real Qwen/OLMo qualification | `IMPLEMENTED_AND_TESTED` |
| Last-valid-token semantics | `last_valid_token_indices`, `select_last_valid_token` | `test_last_valid_token_indices_numpy`, `test_select_last_valid_token_torch` | `IMPLEMENTED_AND_TESTED` |
| Tensor-to-NumPy `float32` boundary | `to_float32_analysis_array` | `test_to_float32_analysis_array_from_numpy`, `test_to_float32_analysis_array_from_torch_and_ndim_reduction` | `IMPLEMENTED_AND_TESTED` |
| Balanced accuracy | `balanced_accuracy` | `test_balanced_accuracy_known_answer_and_errors` | `IMPLEMENTED_AND_TESTED` |
| Classifier / probability mapping | `fit_classifier`, `classifier_class_mapping` | `test_fit_classifier_probability_class_mapping` | `IMPLEMENTED_AND_TESTED` |
| Scaler contract | `fit_scaler`, `transform_with_stats` | `test_fit_scaler_and_transform_with_stats_known_answer` | `IMPLEMENTED_AND_TESTED` |
| Matrix indexing | `_matrix_from_observations` | `test_matrix_from_observations_and_condition_pool` | `IMPLEMENTED_AND_TESTED` |
| `C0` matrix | `_compute_c0_for_partition` | `test_compute_matrix_profile_synthetic_shapes_and_diagonal` | `IMPLEMENTED_AND_TESTED` |
| `Ccal` / `A_mu_sigma` matrix | `_compute_c_cal_for_partition` | `test_compute_matrix_profile_synthetic_shapes_and_diagonal` | `IMPLEMENTED_AND_TESTED` |
| `D`, diagonal identity | `compute_matrix_profile` | `test_compute_matrix_profile_synthetic_shapes_and_diagonal` | `IMPLEMENTED_AND_TESTED` |
| `R` recovery matrix | `compute_matrix_profile` | `test_compute_matrix_profile_synthetic_shapes_and_diagonal` | `IMPLEMENTED_AND_TESTED` |
| Source usability gate | `_source_qualification` | `test_compute_matrix_profile_synthetic_shapes_and_diagonal` | `IMPLEMENTED_AND_TESTED` |
| Source coverage gate | `_source_qualification` | `test_compute_matrix_profile_synthetic_shapes_and_diagonal` | `IMPLEMENTED_AND_TESTED` |
| `DISTANCE_ASSOCIATION` | `_distance_association_point` | `test_distance_association_sdi_and_localization_primitives` | `IMPLEMENTED_AND_TESTED` |
| `SDI` | `_sdi_point` | `test_distance_association_sdi_and_localization_primitives` | `IMPLEMENTED_AND_TESTED` |
| `LOCALIZATION` | `_localization_point` | `test_distance_association_sdi_and_localization_primitives` | `IMPLEMENTED_AND_TESTED` |
| `LOW_D_RECOVERY` | `_low_d_pair_mask`, `_summarize_point_profile` | `test_distance_association_sdi_and_localization_primitives` | `IMPLEMENTED_AND_TESTED` |
| Statistical unit / cluster bootstrap | `_bootstrap_model_summaries` | `test_compute_matrix_profile_synthetic_shapes_and_diagonal` | `IMPLEMENTED_AND_TESTED` |
| Routing `P3 > P1 > P2 > P4 > P5` | `classify_route` | `test_routing_priority_order` | `IMPLEMENTED_AND_TESTED` |
| Matrix serialization round-trip | `_matrix_serialization` | `test_matrix_serialization_roundtrip` | `IMPLEMENTED_AND_TESTED` |
| Result schema | `validate_result_schema`, `validate_synthetic_result_schema` | `test_result_schema_validation`, `test_synthetic_result_schema_validation` | `IMPLEMENTED_AND_TESTED` |
| Provenance / authority binding | `build_result_payload` | `test_synthetic_formal_qualification_uses_real_executor` | `IMPLEMENTED_AND_TESTED` |
| Authorization consumption | `consume_authorization` | `test_authorization_consumption_exclusive` | `IMPLEMENTED_AND_TESTED` |
| Atomic publication | `_publish_result_exclusive` | `test_result_publication_race` | `IMPLEMENTED_AND_TESTED` |
| Publication race rejection | `_atomic_write_json_exclusive` | `test_atomic_write_and_exclusive_race`, `test_result_publication_race` | `IMPLEMENTED_AND_TESTED` |
| Static preflight | `run_static_preflight` | `test_static_preflight`, CLI run | `IMPLEMENTED_AND_TESTED` |
| Real engineering qualification | `run_engineering_qualification` | CLI real-model run | `IMPLEMENTED_AND_TESTED` |
| Synthetic formal pipeline E2E | `run_synthetic_formal_qualification` | `test_synthetic_formal_qualification_uses_real_executor`, CLI run | `IMPLEMENTED_AND_TESTED` |

No endpoint remains `PARTIAL`, `IMPLEMENTED_UNTESTED`, `NOT_IMPLEMENTED`, or
`SPECIFICATION_GAP`.
