---
layout: default
title: "Install a FiveM resource: checklist and missing-file walkthrough"
---

# Install a FiveM resource: checklist and missing-file walkthrough

**Check the extracted folder, manifest paths and dependencies before starting a resource. Then test its behavior on a development server.** A clean manifest report cannot tell you whether a job pays the right player, an inventory integration works or an interface releases keyboard focus.

This guide is maintained by Lucas / Livvux, creator of [RPScripts](https://rpscripts.net/?utm_source=github&utm_medium=organic&utm_campaign=installation-checklist). It accompanies the free, MIT-licensed [fivem-fxmanifest-lint CLI](https://github.com/Livvux/fivem-fxmanifest-lint). It is an independent guide, not Cfx.re certification. Technical sources were reviewed on 26 October 2026.

[Open the reusable checklist](https://github.com/Livvux/fivem-fxmanifest-lint/blob/main/CHECKLIST.md) to record a package version, checks and unresolved issues for your own installation.

## 1. Find the actual resource folder

Extract the archive somewhere you can inspect it. Read its installation instructions before copying files into your server. Keep the previous package and configuration so you can roll back.

An archive can contain a wrapper directory, several resources or additional documentation. Identify each actual resource by its manifest. For example:

```text
resources/
  [local]/
    my_resource/
      fxmanifest.lua
      client/
        main.lua
```

`[local]` is a grouping folder; `my_resource` is the resource name in this example. Do not rename a supplied resource casually: other resources may refer to its name. The official [resource introduction](https://docs.fivem.net/docs/scripting-manual/introduction/introduction-to-resources/) explains resource directories and manifests.

## 2. Match the manifest to the files

Open `fxmanifest.lua` as text. For a GTA V resource, a small illustrative manifest can be:

```lua
fx_version 'cerulean'
game 'gta5'

client_script 'client/main.lua'
```

The path must match a real file relative to that resource. Check case as well as spelling, especially when moving from a case-insensitive development disk to Linux. Do not add guessed filenames to make an error disappear; check what the author actually shipped.

If a local NUI page is declared with `ui_page`, its HTML and required assets also need the appropriate `files` declarations. A text-only validator cannot inspect your extracted files. The [Cfx.re manifest reference](https://docs.fivem.net/docs/scripting-reference/resource-manifest/) documents script directives, dependencies and NUI packaging.

For a pasted-manifest check, the [browser generator and validator](https://rpscripts.net/tools/fxmanifest-generator/?utm_source=github&utm_medium=organic&utm_campaign=installation-checklist) needs no Python. Use the CLI below when you need local file checks.

## 3. Reproduce a missing-file finding

Requirements: Git and Python 3.10 or newer. These commands assume a terminal where `python3` runs that interpreter. No third-party Python package is required.

```sh
git clone https://github.com/Livvux/fivem-fxmanifest-lint.git
cd fivem-fxmanifest-lint
python3 --version
git rev-parse HEAD
python3 fxmanifest_lint.py examples/installation/before
```

The `before` fixture contains `client/main.lua`, but its manifest incorrectly references `client/missing.lua`. Expect exit code **1** and this finding:

```text
[before]
  ERROR   FXM009 line 4: client_script reference 'client/missing.lua' matched no local file.

1 finding(s) across 1 resource(s). Ruleset 2.0.0.
```

Now check the corrected copy:

```sh
python3 fxmanifest_lint.py examples/installation/after
```

Expect exit code **0** and:

```text
OK — 1 resource(s) checked with ruleset 2.0.0.
```

Only the manifest path changes between the copies. The Lua file is a comment-only fixture: it implements no gameplay. **Do not install these examples as resources on your server.** They demonstrate a filesystem check, not FXServer acceptance. Because the broken copy is intentionally included, scanning this whole repository will report it.

For a real package, run the CLI against that package's resource folder instead. `--format json` provides structured findings. Exit 0 means no errors from this implementation; warnings can remain unless you use `--fail-on-warnings`. Record the command and tool commit with your result. See the [corpus and limitations](https://github.com/Livvux/fivem-fxmanifest-lint/blob/main/CORPUS.md), including incomplete Lua-syntax coverage.

## 4. Resolve dependencies before starting

Read both the resource's instructions and its manifest. Record required framework, library, inventory and database versions. ESX, QBCore and Qbox are separate integration targets; a manifest alone does not establish compatibility.

The CLI looks for named dependencies and `@resource/file` imports next to the checked resource. Your server may organize them under another grouping directory. Investigate an `FXM011` warning against the actual layout rather than moving packages solely to satisfy the tool. This check does not resolve installed versions or prove dependency health.

Only apply an author's SQL after reviewing it and backing up affected development data. This guide and the linter do not import a database or edit your configuration.

## 5. Start and test on a development server

After adding a new resource to a running development server, `refresh` rescans manifests. `ensure my_resource` starts it if stopped and restarts it if already running. Use the real resource name and start its documented dependencies first. Re-running `ensure` can interrupt a running resource; it is not a harmless status check. See the official [server commands](https://docs.fivem.net/docs/server-manual/server-commands/).

Inspect the server console, connect a client and check its F8 console while using the feature. Record what you did and what happened. Test cancellation, repeated actions and a player without the required permission. For NUI, check close controls, focus release and restart behavior. For shared state or economy changes, test with two players and verify the server controls the result.

Keep startup success, functional acceptance and security review as separate results. If testing fails, save a minimal reproduction and sanitized errors. Do not publish keys, database credentials or private customer packages in an issue.

## What is verified here?

The shipped before/after fixtures reproduce a missing-file finding and its correction with the existing CLI. The [publication record](https://github.com/Livvux/fivem-fxmanifest-lint/blob/main/PUBLICATION-2026-10-26.md) records the tested revision and commands. No FXServer, gameplay, multiplayer, performance or security acceptance is claimed for these fixtures.

For a broader installation walkthrough, use the [RPScripts getting-started guide](https://rpscripts.net/docs/getting-started/?utm_source=github&utm_medium=organic&utm_campaign=installation-checklist). For this exercise, keep the [checklist](https://github.com/Livvux/fivem-fxmanifest-lint/blob/main/CHECKLIST.md) and your actual test evidence together.
