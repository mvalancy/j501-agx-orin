# Rules for AI agents working in this repo

This project is built with [cad-agent](https://github.com/Valpatel/cad-agent). Follow its agent workflow kit
([docs/agent-workflow.md](https://github.com/Valpatel/cad-agent/blob/dev/docs/agent-workflow.md); install it with
`cad-agent agents install`): the `cad-work-tracking`, `cad-pr-review` and `cad-remote-runs` skills and the
`cad-pr-reviewer` and `cad-resume` subagents.

Assume the session can end at any time (token budget, crash, a reformatted machine). GitHub is the record:

- **Issue first.** Every piece of work has an issue with a checklist (done / next / running / how to resume). The
  current tracking issue for a revision links the others.
- **Branch `dev`.** `main` is protected: push to `dev` in clean commits as you go, open a (draft) PR `dev` → `main`
  early with `Closes #<issue>`, get a review from a separate agent (`cad-pr-reviewer`), answer and resolve every
  thread, CI green, merge with a merge commit. Ask the user before tagging `revX.Y` (it publishes a release).
- **Long runs** (OpenFOAM CFD, FEA sweeps, `cad-agent all`) go on a compute host, not the shared workstation; record
  host role, command, log and how to collect results in the issue (`cad-remote-runs`).
- **Evidence is regenerated, not edited.** Exports, reports and renders come from `cad-agent all` on the committed
  sources; commit them together with the change that produced them.
- **Vendor files are not redistributed.** References (Seeed carrier STEP, NVIDIA module, datasheets) are fetched by
  `tools/fetch_references.py`; only our own measurements and derived checks are tracked.
- **The user's observations are data.** Record measurements and observations (photos, "the fan blows up", "68 mm")
  in `cad/parameters.json` with a note and date, and in the issue; check assumptions such as photo orientation and
  flow direction against them before building on them. Lessons go in [.agents/](.agents/README.md).
