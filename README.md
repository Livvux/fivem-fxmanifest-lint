# fivem-fxmanifest-lint

A dependency-free tokenizer and validator for FiveM `fxmanifest.lua` files. It reads manifest syntax as text and never executes Lua.

Use the hosted [fxmanifest.lua Generator & Validator](https://hifivem.com/setting-up-fxmanifest-lua-fivem/) for quick browser checks. Use this CLI when you also need local files, globs, and neighboring dependencies checked in a resource directory or CI job.

## Requirements

- Python 3.10 or newer
- No third-party packages

## Usage

```bash
python fxmanifest_lint.py path/to/my-resource
python fxmanifest_lint.py path/to/resources
python fxmanifest_lint.py path/to/resources --format json
python fxmanifest_lint.py path/to/resources --fail-on-warnings
python fxmanifest_lint.py --version
```

The path can be a resource directory, an `fxmanifest.lua` file, or a tree containing multiple resources.

## What version 2 checks

- required and valid `fx_version` and `game`/`games` values;
- Lua call syntax, scalar directives, and plural table directives;
- duplicate singleton, script, file, and dependency declarations;
- local `ui_page` coverage through `file`/`files`;
- `data_file` type/path pairs and their `files` coverage;
- allowed `node_version` values (`16` and `22`);
- the deprecated `lua54` opt-in, which is no longer needed since all Lua scripts use Lua 5.4;
- referenced client, server, shared, and pack files, including local `@resource/path` references;
- file globs that match nothing;
- named dependencies found next to the current resource;
- deprecated `__resource.lua` manifests.

Named dependencies can live in another resources root on a real server. A dependency missing from the current resource's parent directory is therefore a warning, not an error.

Rules are based on the official [Cfx.re resource manifest documentation](https://docs.fivem.net/docs/scripting-reference/resource-manifest/). `ruleset-v2.0.0.json` and `fixtures-v2.0.0.json` are the versioned contract shared with the hosted browser validator.

## Output and exit codes

Text output is the default:

```text
[example-resource]
  ERROR   FXM009 line 5: client_script reference 'client/missing.lua' matched no local file.

1 finding(s) across 1 resource(s). Ruleset 2.0.0.
```

`--format json` returns machine-readable findings with `rule_id`, `severity`, `line`, `message`, `docs_url`, and `resource`.

| Exit | Meaning |
| --- | --- |
| `0` | No errors. Warnings may be present. |
| `1` | Errors found, or warnings found with `--fail-on-warnings`. |
| `2` | Invalid invocation, missing input, or runtime/read failure. |

## CI example

```yaml
- name: Validate FiveM resource manifests
  run: python fxmanifest_lint.py resources --format text --fail-on-warnings
```

## Tests

```bash
python -m unittest discover -v
```

The suite covers comments, Lua call and table syntax, NUI files, globs, dependencies, duplicate declarations, `lua54`, `node_version`, the size limit, CLI output/exit codes, and malicious-looking input that must never execute.

## License

MIT — see [LICENSE](LICENSE).
