# Manifest conformance corpus

This is a small, synthetic regression corpus, not a survey of production FiveM resources. All inputs are authored examples distributed under this repository's MIT license. No customer packages, secrets or proprietary scripts are included.

## Version and reproduction

`fixtures-v2.0.0.json` contains 25 named text cases for ruleset `2.0.0`. Each case supplies the manifest text and the complete expected ordered list of rule IDs. The corpus version is the Git commit: pin that commit when comparing runs. The ruleset version identifies validation rules, not a frozen corpus membership.

With Python 3.10 or later and no third-party dependencies:

```sh
python --version
python -m unittest discover -v
```

`ManifestValidationTests.test_versioned_fixture_catalog` executes every named case. Additional tests create temporary resource directories to exercise missing files, globs, external resource references, neighboring dependencies and CLI exit codes. A separate test checks that malicious-looking Lua does not execute. CI runs Python 3.10, 3.12 and 3.14; a local pass on one version is not evidence that the whole CI matrix passed.

To reproduce a historical run, check out its exact commit and record the interpreter version, OS, command, exit status and SHA-256 of the fixture file. Report failed cases as well as passes. Test-case counts and test-method counts differ because the catalog runs as subtests.

## Coverage

| Input family | Expected behavior |
| --- | --- |
| Required metadata | Missing/unsupported `fx_version` and game values have explicit rule IDs. |
| Runtime metadata | Node 16/22 declarations pass these rules; Node 20 produces FXM006; legacy `lua54` produces FXM005. |
| Directive shape | Singular/table and plural/scalar mistakes produce FXM012. |
| Duplicates | Repeated singleton directives produce FXM007; repeated scripts/files/dependencies produce FXM013. |
| NUI | Local pages require declared file coverage; an HTTPS page has no local file requirement. |
| Data files | A missing path produces FXM015; an undeclared path produces FXM014. |
| Tokenization | Ordinary comments, call syntax and custom metadata do not create spurious findings in the included examples. |

The official [Cfx.re manifest reference](https://docs.fivem.net/docs/scripting-reference/resource-manifest/) is the source for directives. This project's rule IDs are its own contract, not Cfx.re error codes or certification.

## CLI and browser are different checks

The [hosted browser validator](https://rpscripts.net/tools/fxmanifest-generator/) reads pasted text. It cannot inspect a resource directory, resolve files or check installed dependency versions. The shared cases therefore do not require a filesystem. The Python CLI additionally checks local files and neighboring dependencies when given a resource directory. Dependencies may live elsewhere in a real deployment, so a missing neighbor is a warning.

Both implementations read text without executing Lua. Neither is a complete Lua parser, runtime emulator or security scanner. Dynamic Lua constructs, generated declarations, advanced quoting and recursive glob edge cases require separate verification. In particular, the Python 2.0.0 tokenizer does not reliably diagnose malformed syntax; the browser has additional FXM016 syntax checks. A shared ruleset number does not imply complete implementation parity.

A clean result means no findings from the selected implementation, rules and input. It does **not** prove that the resource starts, is safe, fits ESX/QBCore/Qbox, has compatible dependency versions, performs well, or works in multiplayer. No FXServer or in-game acceptance is claimed by this corpus. Check actual files, licenses, dependencies and behavior in an isolated server before deployment.

## Recorded run

[The 2026-10-22 acceptance record](VALIDATION-2026-10-22.md) includes the fixture hash, interpreter, command, result and a per-case browser report. It is evidence for that input set and date only.

## Reporting an issue

Include a minimal redistributable manifest, expected and actual findings, tool commit, ruleset version, interpreter/browser version and relevant file layout. Remove secrets and private paths. Describe the failure without uploading a customer resource. Contributions that reproduce a false positive or false negative are more useful than unsupported claims of compatibility.
