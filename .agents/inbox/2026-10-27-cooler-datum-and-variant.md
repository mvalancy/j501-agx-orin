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

Keep separate cooler profiles with source dimensions, seating datums and uncertainty. Check the actual lid solid, including ring and ribs, against an expanded occupied envelope. Preserve the known collision as a negative control. Distinguish generic vendor mounting hardware from the product-specific adapter; require physical confirmation before choosing tie-down axes or bolt lengths. Isolate the study from active worktrees and simulation outputs.

## Limits

The G48R contact stack, adapter pattern, photo placement and pipe bends remain provisional. The 19 mm lift and 101 mm replacement-roof height are geometric candidates, not released parts, strength results or cooling predictions. See the [full fit review](../../docs/cooler-fit-review.md).
