# Final prior-art positioning audit

Internal submission-preparation record. This file is not part of the anonymous
paper and introduces no scientific result.

## Novelty accounting

LINEAR_PROBING_NOVELTY = false
LAYERWISE_PROBING_NOVELTY = false
FROZEN_CROSS_LAYER_PROBE_TRANSFER_NOVELTY = false
SOURCE_TARGET_TRANSFER_MATRIX_NOVELTY = false
AFFINE_OR_FEATUREWISE_CALIBRATION_NOVELTY = false
GENERIC_READOUT_REPRESENTATION_DISTINCTION_NOVELTY = false
CKA_NOVELTY = false
GENERIC_CROSS_MODEL_HETEROGENEITY_NOVELTY = false
NEGATIVE_RESULT_REPORTING_NOVELTY = false
C0DR_HEADLINE_METRIC_NOVELTY = false
SDI_HEADLINE_METRIC_NOVELTY = false
LOWD_HEADLINE_METRIC_NOVELTY = false

Primary novelty center: a controlled direct-reuse / restricted-recalibration
contrast under one common held-out source-target protocol, applied across the
complete registered depth grid and yielding a bounded three-model joint
characterization with registered boundary evidence.

## Prior-art closure

### Kniazev & Fijalkow (2026)

PRIMARY_SOURCE_VERIFIED = true
ATOMIC_OVERLAP = source-layer probe training, evaluation at other layers without retraining, and a cross-layer transfer matrix
SCIENTIFIC_QUESTION_OVERLAP = direct cross-layer probe transfer
WHAT_IS_PRIOR_ART = frozen cross-layer transfer and matrix representation
WHAT_PAPER_A_STILL_ADDS = controlled contrast with one restricted FIT-only recalibration branch under a common held-out protocol, plus the joint three-model characterization
MANUSCRIPT_ACKNOWLEDGEMENT_ADEQUATE = true
DISPOSITION = DIRECT_PRIOR_ART

### Gilg et al. (2026)

PRIMARY_SOURCE_VERIFIED = true
GILG_CROSS_LAYER_TRANSFER_CONFIRMED = true
ATOMIC_OVERLAP = probe trained at one layer and transferred across layers
SCIENTIFIC_QUESTION_OVERLAP = cross-layer probe transfer in persona-dependent preference measurement
WHAT_IS_PRIOR_ART = cross-layer transfer is an established supporting operation beyond one prior example
WHAT_PAPER_A_STILL_ADDS = a within-model task-panel contrast between unchanged direct reuse and restricted recalibration, not a persona-preference transfer study
MANUSCRIPT_ACKNOWLEDGEMENT_ADEQUATE = true
DISPOSITION = DIRECT_PRIOR_ART

### Anthes et al. (2023)

PRIMARY_SOURCE_VERIFIED = true
ATOMIC_OVERLAP = readout misalignment distinguished from information loss
SCIENTIFIC_QUESTION_OVERLAP = native-readout failure need not mean loss of task-relevant information
WHAT_IS_PRIOR_ART = diagnostic readout/alignment decomposition in continual learning
WHAT_PAPER_A_STILL_ADDS = a different within-model cross-depth fixed task interface and restricted FIT-only recalibration comparison
MANUSCRIPT_ACKNOWLEDGEMENT_ADEQUATE = true
DISPOSITION = GENERAL_PREDECESSOR

### SemRF (2026)

PRIMARY_SOURCE_VERIFIED = true
ATOMIC_OVERLAP = cross-depth comparability and measurement/interface alignment
SCIENTIFIC_QUESTION_OVERLAP = whether intermediate representations can be compared across depth
WHAT_IS_PRIOR_ART = anchor-based semantic reference frames with synchronization, admissibility, distortion controls, and trajectories
WHAT_PAPER_A_STILL_ADDS = no semantic frame or trajectory geometry; only operational portability and one restricted recalibration diagnostic
MANUSCRIPT_ACKNOWLEDGEMENT_ADEQUATE = true
DISPOSITION = CLOSE_CONCEPTUAL_NEIGHBOR

### Fresh-Head (2026)

PRIMARY_SOURCE_VERIFIED = true
ATOMIC_OVERLAP = representation/readout failure localization
SCIENTIFIC_QUESTION_OVERLAP = separating representation and readout contributions in model merging
WHAT_IS_PRIOR_ART = general representation/readout decomposition prior art
WHAT_PAPER_A_STILL_ADDS = within-model cross-depth direct reuse versus restricted recalibratability
MANUSCRIPT_ACKNOWLEDGEMENT_ADEQUATE = true
DISPOSITION = GENERAL_PREDECESSOR

### Chou et al. (2026)

PRIMARY_SOURCE_VERIFIED = true
ATOMIC_OVERLAP = representation/readout decomposition
SCIENTIFIC_QUESTION_OVERLAP = readout and representation roles in training dynamics
WHAT_IS_PRIOR_ART = general representation/readout decomposition prior art
WHAT_PAPER_A_STILL_ADDS = the registered cross-depth operational contrast
MANUSCRIPT_ACKNOWLEDGEMENT_ADEQUATE = true
DISPOSITION = GENERAL_PREDECESSOR

### Janati et al. (2026)

PRIMARY_SOURCE_VERIFIED = true
ATOMIC_OVERLAP = representation/readout interface behavior
SCIENTIFIC_QUESTION_OVERLAP = readout-interface behavior in post-grokking collapse
WHAT_IS_PRIOR_ART = general representation/readout decomposition prior art
WHAT_PAPER_A_STILL_ADDS = complete directed source-target compatibility characterization
MANUSCRIPT_ACKNOWLEDGEMENT_ADEQUATE = true
DISPOSITION = GENERAL_PREDECESSOR

### Tuned Lens

PRIMARY_SOURCE_VERIFIED = true
ATOMIC_OVERLAP = intermediate-layer readout construction
SCIENTIFIC_QUESTION_OVERLAP = layerwise intermediate prediction
WHAT_IS_PRIOR_ART = layer-specific affine readouts
WHAT_PAPER_A_STILL_ADDS = holding one source readout fixed across target depths and contrasting it with restricted recalibration
MANUSCRIPT_ACKNOWLEDGEMENT_ADEQUATE = true
DISPOSITION = BACKGROUND

### Patchscopes

PRIMARY_SOURCE_VERIFIED = true
ATOMIC_OVERLAP = hidden-state inspection/intervention
SCIENTIFIC_QUESTION_OVERLAP = interpreting or manipulating intermediate representations
WHAT_IS_PRIOR_ART = broad hidden-state inspection and intervention framework
WHAT_PAPER_A_STILL_ADDS = task-readout portability measurement
MANUSCRIPT_ACKNOWLEDGEMENT_ADEQUATE = true
DISPOSITION = BACKGROUND

### Functional Alignment Can Mislead

PRIMARY_SOURCE_VERIFIED = true
ATOMIC_OVERLAP = functional success does not establish representation equivalence
SCIENTIFIC_QUESTION_OVERLAP = distinction between functional and representational comparison
WHAT_IS_PRIOR_ART = warning against equating operational success with equivalence
WHAT_PAPER_A_STILL_ADDS = explicit direct/restricted operational decomposition
MANUSCRIPT_ACKNOWLEDGEMENT_ADEQUATE = true
DISPOSITION = DIRECT_PRIOR_ART

### ICR Probe

PRIMARY_SOURCE_VERIFIED = true
ATOMIC_OVERLAP = cross-layer hidden-state probing
SCIENTIFIC_QUESTION_OVERLAP = layerwise dynamics for hallucination detection
WHAT_IS_PRIOR_ART = cross-layer probe-based analysis
WHAT_PAPER_A_STILL_ADDS = a different task interface and complete source-target compatibility matrix
MANUSCRIPT_ACKNOWLEDGEMENT_ADEQUATE = true
DISPOSITION = SECONDARY_METHOD

### CKA

PRIMARY_SOURCE_VERIFIED = true
ATOMIC_OVERLAP = representation similarity
SCIENTIFIC_QUESTION_OVERLAP = comparing hidden-state representations
WHAT_IS_PRIOR_ART = centered linear CKA as a similarity measure
WHAT_PAPER_A_STILL_ADDS = only a post-closure secondary comparison with completed operational measurements
MANUSCRIPT_ACKNOWLEDGEMENT_ADEQUATE = true
DISPOSITION = BACKGROUND

## Final boundary

FROZEN_PROBE_TRANSFER_CLAIMED_NOVEL = false
TRANSFER_MATRIX_CLAIMED_NOVEL = false
GENERIC_READOUT_MISALIGNMENT_CLAIMED_NOVEL = false
SIMPLE_RECALIBRATION_CLAIMED_NOVEL = false
CKA_CLAIMED_NOVEL = false
DIRECT_REUSE_RECALIBRATION_CONTRAST_CLEAR = true
COMMON_HELDOUT_PROTOCOL_CLEAR = true
THREE_MODEL_JOINT_RESULT_CLEAR = true
NEGATIVE_BOUNDARY_EVIDENCE_CLEAR = true
