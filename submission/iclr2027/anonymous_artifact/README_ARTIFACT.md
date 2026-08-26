# Anonymous artifact

This artifact is a minimal, anonymous reproducibility companion for Paper A. It contains machine-readable comparison outputs, CKA matrices, exact profile values, hashes, and a manifest. It does not contain model weights, hidden-state tensors, prompts, source material, repository history, private metadata, or author identity.

The comparison outputs are EVAL-only and preserve the registered directed source-target pair orientation. The profile file is a sanitized derivative transcription of canonical values; it is not a replacement for the canonical result authorities.

Suggested checks:

```text
python -c "import json; json.load(open('manifest.json', encoding='utf-8')); print('artifact manifest JSON OK')"
```

The artifact is intended to support inspection and reproduction of the reported analyses. Model execution is outside the artifact package.
