# EXP-017 Generation-Time Intervention Pilot

The historical preregistration remains in
[`intervention_conditions.json`](intervention_conditions.json). The first
official behavioral run is governed by the post-audit amendment in
[`intervention_conditions_v2.json`](intervention_conditions_v2.json) and
[`EXP-017-AMENDMENT-V1.md`](../../docs/experiments/EXP-017-AMENDMENT-V1.md).

Validate the frozen runner without loading a model or writing results:

```bash
python experiments/exp017/behavioral_pilot.py --dry-run
```

`--run` is reserved for the separately authorized 320-generation official
pilot. It uses EXP-003 prompts only for steering-vector fitting, EXP-011D only
for behavioral evaluation, and atomically publishes five compact result files
only after the run succeeds. It never saves hidden states or steering vectors.
