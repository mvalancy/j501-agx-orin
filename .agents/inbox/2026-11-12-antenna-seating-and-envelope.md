# Keep antenna housing datums separate from the generated envelope and visual seating plane

2026-11-12 UTC, original optional showcase context for issue 19 / PR 20. Existing lessons were searched in `.agents/README.md`, `.agents/inbox/`, `docs/showcase-antennas.md` and `cad/hardware.py`; this checkout has no `.agents/WRITING-IT-DOWN.md`.

**Evidence:** `rg -n -A15 '^def antenna_bulkheads' cad/hardware.py` shows the right-side washer starts at W, thickness 0.5, and the nut spans W+0.5..W+2.5; left parts rotate 180° about X=W/2. Therefore the left outer nut face is X=-2.5, independently of the wall X=0 or thread end X=-7. At the initial Wi-Fi commit, `python3 tools/test_showcase_antennas.py -v` passed six tests, including exact origin [-2.5,46.5,62] / [-2.5,145.5,62], closed STL readback and envelope checks. The actual generated Wi-Fi Z bounds are 58.099998474121094..84.0999984741211 mm, approximately 26.0 mm tall. Issue 22 later adds separately referenced cellular context and a seventh test; it preserves those Wi-Fi bytes.

**Cause / potential failure:** conflating the manufacturer's 18.6 mm upper housing segment, 7 mm base and 25.6 mm housing datum with a complete connector-inclusive bound could hide a 0.4 mm lower connector extension. Seating at the chassis wall rather than the existing visible nut would also place the display accessory 2.5 mm too far inward.

**Corrective rule:** cite mechanical facts with their datum; derive the visual seating face from the actual bulkhead stack and mirror; report float32 mesh readback bounds separately. Keep an explicit assumption for mating/engagement and hash the source hardware and parameters with the original display recipe. Preserve the manufacturing inputs and make the accessory optional context outside release/print and purchasing inventories.

**Limits:** only this original render approximation is checked. Proprietary TE reference files stay untracked; no exact vendor geometry, physical fit, collision/RF qualification or purchasing recommendation follows. Hardware stack changes require a renewed seating audit. Downstream graphics use the reviewed source commit and manifest, not a local note as published evidence.
