# Cut every hole last, and check every hole of every part

## Incident and evidence: 2026-10-29

The owner found the Rev 0.9 lid's star roof ribs reaching into the four D6.4 lid-screw counterbores in
`exports/cover.stl` (issue #9). Every existing check passed: the cover was one valid, watertight solid, the fit and
clearance checks were clean, the lid FEA had a safety factor above 2, and it sliced. None of them looks inside a hole.

A probe cylinder in each counterbore of the old `cover.step` found 91.9 mm³ of rib, at Z 85 to 96. After the fix, the
same probe finds 0.000 mm³ in all four counterbores and all four clearance holes (review of PR #11).

## Cause

`cover()` cut the counterbores and clearance holes, then unioned the fan skirt and the roof ribs. The ribs run from the
fan centre to each lid-screw centre, so they refilled the holes they ended in. The base was already right: it cuts its
holes after adding its ribs.

## Corrective rule

- Cut every hole, counterbore and insert bore last, after every rib, boss, skirt and gusset (`cad/build.py`).
- `cad-agent all` runs `cad-agent holes` (Valpatel/cad-agent#88). It probes every cylindrical hole in every part's
  STEP and writes `exports/hole-checks.json`. Deliberate non-round holes (the RP-SMA D-holes) are listed exceptions in
  `cad-agent.yaml`.
- Every review walks cad-agent's
  [common-issues index](https://github.com/Valpatel/cad-agent/blob/dev/docs/common-issues.md) (AGENTS.md).

## Limits

The hole check misses a hole capped at one end, which reads as blind. It also misses a counterbore blocked right
across with a smaller hole cut through the block: that reads as a ledge, which is listed but not failed. An exception
skips its whole hole. Look at these in a section view.
