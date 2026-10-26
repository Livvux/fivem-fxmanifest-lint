# Installation guide: static verification, 26 October 2026

The guide and fixtures were checked against the existing CLI from base commit `c223e89102c22a4ca037531f952690ca3f52bea2`. This is a small authored example under this repository's MIT license, not an audit of third-party packages.

## Environment and commands

- Interpreter: Python 3.15.0.
- OS: Darwin 27.2.0.
- `python3 fxmanifest_lint.py examples/installation/before`: expected and observed exit 1, one FXM009 finding at line 4.
- `python3 fxmanifest_lint.py examples/installation/after`: expected and observed exit 0, no findings.
- `python3 fxmanifest_lint.py examples/installation/after --fail-on-warnings`: expected and observed exit 0.
- `luac -p` on both manifests and both comment-only client files: exit 0 (syntax only; this does not execute FiveM directives).
- `git diff --check`: passed before committing.

## SHA-256 of checked inputs

- `fxmanifest_lint.py`: `d0052fb213ec8090a7295c7d0f4d5903b141d96166061b966743772379572bee`
- `examples/installation/before/fxmanifest.lua`: `f8ddf63ac489871ab905a5abdd3243ebfb17bd3db9e2689041597d2cbe1b6c98`
- `examples/installation/after/fxmanifest.lua`: `b5f76d23363b5a50e5eceb78d15ee6828b97f179f47473f5bd45e0812c768707`

## Reproduction and limits

Follow the [walkthrough](docs/index.md) from a checkout of this publication's commit and record `git rev-parse HEAD`. The CLI implementation and existing tests were not changed. Existing GitHub Actions runs the unit suite on pushes and pull requests; its run results are separate evidence from the focused checks above.

The before fixture intentionally names a missing file. The after fixture corrects that path; both client files contain only a comment. Neither fixture was started in FXServer. No gameplay, multiplayer, security, performance or framework-compatibility acceptance is claimed. Browser publication and Google indexing are separate from these static results.

The guide's Cfx.re links and its RPScripts getting-started and manifest-tool destinations were checked for successful HTTP responses on the publication date. RPScripts links carry `utm_source=github`, `utm_medium=organic`, `utm_campaign=installation-checklist`; this makes attribution possible but does not prove an analytics event was received.
