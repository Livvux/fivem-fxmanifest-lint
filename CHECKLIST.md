# FiveM resource installation checklist

Use one copy per resource and version. Work on a development server before changing a live server. The [walkthrough](https://livvux.github.io/fivem-fxmanifest-lint/) explains the checks; this file is the reusable record.

Resource name:

Package version or commit:

Date / reviewer:

## Before starting

- [ ] Keep the previous package and configuration as a rollback copy.
- [ ] Confirm the source and permission to use the package.
- [ ] Read the author's installation instructions and version requirements.
- [ ] Confirm the actual framework and required inventory, target, database and library resources. Unknown compatibility stays unresolved.
- [ ] Review the author's SQL separately; back up affected development data before any import. Do not run SQL just because a manifest check passed.

## Files and configuration

- [ ] The actual resource folder contains `fxmanifest.lua`, without an extra ZIP wrapper directory.
- [ ] Manifest paths match the extracted files, including letter case on the target host.
- [ ] Local NUI HTML, JavaScript, CSS and other required assets are present and declared under `files` where needed.
- [ ] Dependencies and any `@resource/file` imports match the installed layout and versions.
- [ ] Local manifest check reviewed, including warnings; record command, tool commit and result below.
- [ ] Configuration is reviewed without sharing keys, passwords or private player data.

## Development-server acceptance

- [ ] Start the documented dependencies, then the resource; inspect the server console.
- [ ] Connect a client and inspect its F8 console while exercising the feature.
- [ ] Test normal use, cancellation, repeated actions and missing permissions.
- [ ] For NUI, test closing, Escape if supported, input focus and resource restart.
- [ ] For shared state, money or inventory, test two players and confirm server-side authority.
- [ ] Record remaining errors and the exact reproduction before promoting the package.
- [ ] Document the live deployment window and rollback steps before making production changes.

## Evidence

Manifest command / tool commit / result:

FXServer and framework versions:

Manual test steps / observations:

Open issues / decision:

A clean manifest report is not a security audit or runtime acceptance. These boxes are blank intentionally; this template does not certify any resource.
