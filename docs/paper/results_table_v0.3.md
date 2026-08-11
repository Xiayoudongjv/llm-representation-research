# Results Table v0.3

| Experiment | Question | Key Result | Interpretation | Claim Strength |
|---|---|---|---|---|
| EXP-001 final-layer geometry | Is there final-layer group structure? | PCA and cosine group patterns appeared in 12 prompts | Initial task-associated signal | Partial |
| EXP-002 layer-wise geometry | Does geometry vary with depth? | Geometry was non-monotonic; layer 16 was useful | Layer dependence is exploratory | Partial |
| EXP-003 paraphrase control | Does a controlled signal persist? | Weak controlled signal persisted near layer 16 | Some confounds were reduced, not removed | Partial |
| EXP-004 normalized steering | Can a normalized direction move representations? | Movement was too weak for reliable reassignment | Direction alone is insufficient | Supported for baseline result |
| EXP-004B calibrated steering | Does calibration improve transitions? | Beta 0.75 reached assignment rate 1.0 in the tested pair | Stronger representation movement | Supported at representation level |
| EXP-005 multi-pair steering | Does this extend across pairs? | All 12 ordered pairs reached assignment rate 1.0 by beta 0.75 | Consistent in this controlled setting | Supported for tested setting |
| EXP-006 invariant score | How does movement affect relations? | Higher beta increased IVS and reduced RSM Pearson | Assignment and preservation trade off | Proxy only |
| EXP-007 validity frontier | Is there an operating point? | All pairs selected beta 0.75 | Stable exploratory frontier | Partial |
| EXP-008 invariant-aware selection | Does penalty-aware selection change it? | 23/24 settings retained mean beta 0.75 | Frontier is robust under most tested penalties | Partial |
| EXP-009 answer baseline | Can answer behavior be measured? | Overall strict accuracy was 0.625 | Preliminary behavioral baseline | Descriptive |
| EXP-009B scoring audit | Are strict errors scoring artifacts? | Upper bound remained 0.625; 4 ambiguous and 2 partial | No clear scoring misses, but annotation is limited | Descriptive |
| EXP-010 representation-behavior link | Do metrics track difficulty? | Strongest r was -0.9122, but n=4 | No reliable association can be claimed | Inconclusive |
