[J501 AGX Orin](../../README.md) / **.github/workflows**

# CI

[`ci.yml`](ci.yml) runs on every push and pull request, and on `rev*` tags.

The CAD build needs vendor models (one behind a login), so CI cannot rebuild the parts. It checks the committed files instead, with
[`tools/ci_check.py`](../../tools/ci_check.py):

1. Every print file and `cad/parameters.json` matches the sha256 recorded by the last local `cad-agent all` run.
2. That run passed every design check.
3. Every STL is one watertight body that fits a 256 mm bed.
4. Every local link and image in the README files and ASSEMBLY.md resolves.

It also reruns [`tools/write_readmes.py`](../../tools/write_readmes.py) and fails if any README changed.
It then builds the print release with [`tools/package_release.py`](../../tools/package_release.py) (`cad-agent release`, pinned in the workflow) and keeps it as a download for 30 days.
On a `rev*` tag it also publishes a [GitHub release](https://github.com/mvalancy/j501-agx-orin/releases). See
[Making a release](../../README.md#making-a-release).
