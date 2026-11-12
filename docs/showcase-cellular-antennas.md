# Optional cellular showcase pair

The completed Wi-Fi slice in [issue 19](https://github.com/mvalancy/j501-agx-orin/issues/19) / PRs 20–21 intentionally supplied only the left Wi-Fi pair. The owner requested the complete two-sided antenna set on 2026-11-12 UTC. This separate [issue 22](https://github.com/mvalancy/j501-agx-orin/issues/22) adds original optional right-side display context while keeping the real modem, antenna and cable choices unresolved, as recorded in `docs/connector-inventory.csv` at J11.

## Proposed visual reference

Taoglas **TG.22.0152** has an explicitly **RP-SMA(M) fixed right-angle** connector in the [manufacturer datasheet](https://www.taoglas.com/datasheets/TG.22.0152.pdf), document **SPE-11-8-112/E/SS**, checked 2026-11-12 UTC. The page 5 mechanical drawing gives 44.8±2 mm overall height, 38±2 mm housing length, 17±0.5 mm lateral extent, Ø7.8±0.3 mm housing, 8.4±0.3 mm coupling axial length and 8 mm hex across flats. Private reference SHA-256: `02043b24baef5c8ee43238535d3c45f19dcf77f72ee8a47923fc2453e7a5414c`. No vendor file or geometry is redistributed; [machine-readable reference](../tools/showcase-cellular-reference.json) records the facts and limits.

This is an older penta-band cellular reference described as GSM/DCS/PCS/UMTS/CDMA/GPRS/EDGE/HSPA, 800–2200 MHz. It does **not** establish LTE/5G, low-band, installed-modem, pigtail, ground-plane or MIMO suitability. It is a proposed visual reference only, not selected build hardware, a purchasing recommendation or RF/fit approval. The 2.4 GHz Wi-Fi reference is not relabeled as cellular.

## Implementation / validation plan

Extend the existing standard-library original display recipe and hash-bound manifest to the existing CELL 1/2 nut outer faces at X=W+2.5=208.5 mm, Y=46.5/145.5 mm, Z=62 mm. Use a proper 180° rotation around Z relative to the left orientation so outward is +X and up remains +Z, preserving closed mesh winding. Keep the existing Wi-Fi STL bytes and every manufacturing input/BOM/print output unchanged. Record actual generated bounds separately from the cited nominal/tolerance dimensions; original bend, tip and circularized coupling remain approximations.

Add pair-count, side/direction, rotation/winding, reference and stale-provenance controls to the existing mesh tests, then run normal bounded product checks. Parent coordination owns independent GPT-6 review and branch→dev→main incorporation without a tag. The homepage receives the exact reviewed four-fragment manifest after main incorporation. No CAD/solver job, dependency install, vendor-file redistribution, hardware purchase or radio operation is needed.
