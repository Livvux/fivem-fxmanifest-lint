# Recorded corpus validation — 2026-10-22

Synthetic inputs only. This is a reproducibility record, not FXServer acceptance or a security certification.

- Existing validator source: commit `3b1762cf5d240313b50d930ec0fb18462c9406fb`; no runtime changes in this corpus expansion.
- Ruleset: `2.0.0`.
- Corpus: 25 cases in `fixtures-v2.0.0.json`.
- Corpus SHA-256: `a7d7db1b40d1681b35ffa67ec850e27d8ee7648ac4398f35501e537336bf92ac`.

## Python

Executed on an isolated Linux validation guest, Python `3.12.3`:

```sh
python3 -m unittest discover -v
sha256sum fixtures-v2.0.0.json
```

Result: exit 0, all 12 test methods passed, including the 25 catalog subtests. A separate pass through `validate_text` also matched all 25 expected ordered rule-ID lists. Tests include temporary directory and CLI checks. Python 3.10/3.14 are configured in CI but were not run in this manual environment.

## Hosted browser

The same 25 manifests were entered into the Validate tab at <https://rpscripts.net/tools/fxmanifest-generator/> using a real Chromium 152 browser on 2026-10-22. Each run used the page's Validate manifest button and read the rendered findings. All 25 ordered rule-ID lists matched the corpus. [Per-case results and browser version](browser-corpus-2026-10-22.json).

This checks the deployed browser validator against this finite shared corpus. It does not prove full parser parity, file existence, dependency compatibility or in-game behavior. See [CORPUS.md](CORPUS.md) for differences and exclusions. No customer resource was submitted.
