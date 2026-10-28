# Keep cooler variants and thermal seating datums separate before changing a lid

## Incident and evidence — 2026-10-27

The user's printed lid hit the installed cooler. Existing `cad/parameters.json` describes a 34 mm WS-RDN-601; the supplied photos match the taller Mini J501 G48R. Claude's stopped session contained photo-registration research but no completed cooler-model change. Its Rev 0.9 thermal jobs and uncommitted roof changes remained owned by that session.

In a separate worktree, `python tools/cooler_fit_review.py` read back native reference STEPs and intersected conservative cooler envelopes with the committed cover:

```text
lift 0 mm: nominal fan intersection 14860.9197 mm3
lift 15 mm: nominal fan gap 0.7 mm; uncertainty-envelope intersection 413.1027 mm3
lift 19 mm: uncertainty-envelope intersection 0 mm3; minimum fan gap 2.7 mm
```

The [report](../../exports/cooler-study/fit-review.json) binds these results to source and artifact hashes. `python tools/check_cooler_study.py` checks freshness, component dimensions, the collision negative control and the candidate's clearance in CI.

## Cause

A cooler-family name hid two distinct height/footprint configurations. Centering the inlet on the module also missed the photographed fan offset. A 6.8 mm mounting spacer is a lug support, not automatically another 6.8 mm below the cooler's thermal contact surface. Treating it as a stack layer would manufacture an unproven air gap.

## Corrective rule

Check a photo registration's orientation against a known feature before using it, and check that known hardware lands on known holes.


Keep separate cooler profiles with source dimensions, seating datums and uncertainty. Check the actual lid solid, including ring and ribs, against an expanded occupied envelope. Preserve the known collision as a negative control. Distinguish generic vendor mounting hardware from the product-specific adapter; require physical confirmation before choosing tie-down axes or bolt lengths. Isolate the study from active worktrees and simulation outputs.

## Limits

The G48R contact stack, adapter pattern, photo placement and pipe bends remain provisional. The 19 mm lift and 101 mm replacement-roof height are geometric candidates, not released parts, strength results or cooling predictions. See the [full fit review](../../docs/cooler-fit-review.md).

## Resolution — Rev 0.9 (2026-10-27)

The study was merged into Rev 0.9 as one model: `cad/hardware.py` `cooler_and_module()` is the only cooler geometry, sized from `cad/parameters.json` `cooler` (the separate `cooler-profiles.json` was folded in). The photo shows an **octagonal** fan frame, as the S06 drawing does; the study's rounded-square frame overstated the corners. Both earlier photo fits (88, 70.5 and 84.5, 70.8) shared one error: the registration had IMG_1852 rotated 180 degrees (the front I/O, with DC IN, RJ45 and audio, is the photo's right-hand wall, DC IN at the top). Corrected, the fan hub lands at PCB (90.4, 90.5) and the four heatsink ears within 2 mm of the four module mounting holes: the cooler is centred on the module, as the study's own observation (ears on the module-hole pitch) suggested. The Rev 0.9 lid uses the module centre, with its fan pocket 6 mm outside the frame; `cad/build.py` and `tools/cooler_fit_review.py` check the exact lid against the fan moved 3 mm in eight directions, for the modelled frame and the S06 table's 95 mm size. The user measured the PCB top to fan top at about 68 mm, 2 mm under the 70 mm design value, so the study's +2 mm height allowance is no longer needed. The 101 mm roof estimate assumed ribs and a 4.5 mm roof; the Rev 0.9 lid is 97 mm with a flush grille over the fan. The Rev 0.8 lid collision stays in the study as a negative control, next to the 18 mm riser check.
