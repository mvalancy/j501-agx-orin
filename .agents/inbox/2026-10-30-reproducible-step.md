# Make exports byte-reproducible, or every rebuild looks like a change

## Incident and evidence: 2026-10-30

Every `cad-agent all` changed all 31 tracked STEP files (18 parts, 13 cooler-study pieces), even with no geometry
change (issue #12, found in the review of PR #11). A text-only edit to `cad/parameters.json` produced a 65-file diff.

## Cause

The OCCT STEP writer puts three things in each file that change with no geometry change:
- the write time, in the header `FILE_NAME`;
- a product name, `Open CASCADE STEP translator 7.9 N`, where N counts the exports made in the process. So the name
  depends on export order.
- in files with several solids, the `NEXT_ASSEMBLY_USAGE_OCCURRENCE` ids, which also count up across the process
  (found in the review of PR #13).

## Corrective rule

Write tracked STEP files with `build.export_step()`. It sets the header date to 2000-01-01T00:00:00, names the
product after the file and numbers the assembly ids from 1 within each file. Check after a rebuild with no change: `git diff --stat -- '*.step'` must be empty. The 3MF
writer is already reproducible (cad-agent#49). This matters because the hole check and the cooler study bind STEP hashes,
and the slice report binds 3MF hashes.

## Limits

Checked on the compute host: after `cad-agent all`, a second run of `cad/build.py` and `tools/cooler_fit_review.py`
gave the same sha256 for all 31 tracked STEP files. `exports/assembly_gmsl.step` (git-ignored, written by
`cq.Assembly.save`) still differs between runs. Only the three fields above are normalised. A different OCCT version can write different bytes for the same geometry.
