# Optional cellular showcase pair

The completed Wi-Fi slice in [issue 19](https://github.com/mvalancy/j501-agx-orin/issues/19) / PRs 20–21 intentionally supplied only the left Wi-Fi pair. The owner requested the complete two-sided antenna set on 2026-11-12 UTC. This separate [issue 22](https://github.com/mvalancy/j501-agx-orin/issues/22) adds original optional right-side display context while keeping the real modem, antenna and cable choices unresolved, as recorded in `docs/connector-inventory.csv` at J11.

## Proposed visual reference

Taoglas **TG.22.0152** has an explicitly **RP-SMA(M) fixed right-angle** connector in the [manufacturer datasheet](https://www.taoglas.com/datasheets/TG.22.0152.pdf), document **SPE-11-8-112/E/SS**, checked 2026-11-12 UTC. The page 5 mechanical drawing gives 44.8±2 mm overall height, 38±2 mm housing length, 17±0.5 mm lateral extent, Ø7.8±0.3 mm housing, 8.4±0.3 mm coupling axial length and 8 mm hex across flats. Private reference SHA-256: `02043b24baef5c8ee43238535d3c45f19dcf77f72ee8a47923fc2453e7a5414c`. No vendor file or geometry is redistributed; [machine-readable reference](../tools/showcase-cellular-reference.json) records the facts and limits.

This is an older penta-band cellular reference described as GSM/DCS/PCS/UMTS/CDMA/GPRS/EDGE/HSPA, 800–2200 MHz. It does **not** establish LTE/5G, low-band, installed-modem, pigtail, ground-plane or MIMO suitability. It is a proposed visual reference only, not selected build hardware, a purchasing recommendation or RF/fit approval. The 2.4 GHz Wi-Fi reference is not relabeled as cellular.

## Representation and exact placement

The existing standard-library original display recipe and v2 hash-bound manifest now include CELL 1/2 at nut outer faces X=W+2.5=208.5 mm, Y=46.5/145.5 mm, Z=62 mm. The local-to-assembly map uses a proper 180° rotation around Z relative to the left orientation: outward is +X, tangential +Y and up +Z (determinant +1), preserving closed mesh winding. All four parts name their own reference via `reference_key`; the two source families cannot be presented as one antenna model.

| Fragment | Actual assembly bounds, mm (rounded; exact float32 bounds in manifest) | Faces |
|---|---|---|
| `cell_1_antenna.stl` | `[208.5,42.5,58.0]` to `[225.5,50.5,102.8]` | 1148 |
| `cell_2_antenna.stl` | `[208.5,141.5,58.0]` to `[225.5,149.5,102.8]` | 1148 |

The original approximation is approximately **17 × 8 × 44.8 mm**, visibly taller than the Wi-Fi pair. The 8 mm connector is circularized from the drawing's **8 mm hex across flats**, so hex corner extents are deliberately omitted; generated bounds are not an exact vendor envelope or tolerance model. Coupling Z=-4..4 mm and housing tip Z=40.8 mm relative to the mount are assumed display datums. The 4.7 mm curved bend, shoulder and flat tip are original choices, not manufacturer dimensions. Near-black color covers even the coupling; real finish, grooves, markings, threads, pins and mating engagement are omitted. Existing protruding bulkhead threads and collision/fit are not qualified.

Both existing Wi-Fi STL hashes remain unchanged: `4aa970157d32ba071915cc1ab6986a5dff23013f5356c9609446d36aff078679` and `6d66d8cf6f2231c32bdf513e3e98a43cd3ce3dd55cb097fcf40b8936f07173c6`. All manufacturing inputs, purchasing BOM and print outputs remain unchanged from incorporated main `2f3853ca`.

## Validation and delivery

`python3 tools/test_showcase_antennas.py -v` passes seven tests: four exact mounts, independent Wi-Fi/cellular movement and enclosure-width controls, fourteen invalid-input cases, positive-volume/closed/oriented single-component STL readback for every part, actual bounds, exact four-part count and separate reference assignment, preserved Wi-Fi byte hashes, determinism, each changed source/output/manifest plus missing or extra fragment rejection, and manufacturing-inventory exclusion. `python3 tools/showcase_antennas.py --check` compares all committed bytes and provenance.

Parent coordination owns independent GPT-6 review and branch→dev→main incorporation without a tag. The homepage receives the exact reviewed four-fragment manifest after main incorporation. No CAD/solver job, dependency install, vendor-file redistribution, hardware purchase or radio operation is needed.
