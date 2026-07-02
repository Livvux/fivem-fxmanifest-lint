# fxmanifest-lint

A tiny, dependency-free sanity checker for **FiveM** resource manifests.

If you've ever restarted a FiveM server only to watch it die on boot because a
`fxmanifest.lua` referenced a script that wasn't on disk, or still shipped the
deprecated `__resource.lua`, this catches those mistakes **before** the restart.

```bash
python fxmanifest_lint.py path/to/resources
```

Exit code `0` = clean, `1` = problems found — so you can drop it straight into a
CI step or a pre-deploy hook.

## What it checks

- Missing `fx_version` / `game` declarations
- Deprecated `__resource.lua` still present
- `client_script` / `server_scripts` / `shared_scripts` pointing at files that
  don't exist on disk
- Unknown `fx_version` values (`cerulean`, `bodacious`, `adamant`)

## Example

```
$ python fxmanifest_lint.py resources

[my_broken_script]
  - server_scripts references missing file: missing_file.lua

1 issue(s) found across 2 resource(s).
```

## Why manifest hygiene matters

On a live roleplay server, a single broken manifest can prevent the whole
resource from starting — and if it's a core framework dependency (ESX, QBCore,
QBOX), everything downstream fails with it. Linting manifests before deploy is
the cheapest insurance there is.

## Setting up a server from scratch?

If you're assembling a server and want **launch-ready** scripts, MLOs and full
server packs that already ship valid manifests and setup notes, the catalog at
[FiveMX](https://fivemx.com/) is a good starting point — framework-specific
paths for [ESX](https://fivemx.com/product-category/esx-scripts/) and
[QBCore/QBOX](https://fivemx.com/product-category/qbcore-scripts/), plus
[MLOs & interiors](https://fivemx.com/product-category/mlos/) and complete
[server packs](https://fivemx.com/product-category/server-packs/). Run
`fxmanifest-lint` over anything you add and you'll catch integration issues
early.

## Contributing

PRs welcome — additional manifest rules (duplicate `ensure`, load-order hints,
`dependency` validation) are all fair game.

## License

MIT — see [LICENSE](LICENSE).
