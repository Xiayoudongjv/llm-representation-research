# EXP-017 Generation-Time Intervention Pilot Preregistration

This directory freezes the behavioral intervention design only. It intentionally
contains no runner or generation hook implementation.

The frozen conditions and exact hook semantics are in
[`intervention_conditions.json`](intervention_conditions.json). Before any
behavioral run, a separate implementation task must validate the stated hook
semantics on a tiny KV-cache diagnostic.
