# Optional showcase antennas

This source slice adds two **original, render-only approximations** beside the existing Wi-Fi RP-SMA sites. It does not select radio hardware for the build, change any enclosure/mount dimension, qualify a connector fit or add an antenna to the purchasing/printing BOM. The fitted real lid stays in its existing assembly position.

## Source boundary

Visual reference: TE/Linx **ANT-2.4-CW-RAH-RPS**, TE **L9000025-01**, checked 2026-11-12 at the [official product page](https://www.te.com/en/product-L9000025-01.html).

- [Customer drawing B, C-ANT-2.4-CW-RAH-CCC](https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocFormat=pdf&DocLang=English&DocNm=C-ANT-2.4-CW-RAH-CCC&DocType=Customer+Drawing&PartCntxt=L9000025-01): housing datum 25.60 mm; lateral extent 17.10 mm; upper diameter 7.4 mm; connector diameter 7.80 mm and axial length 8.10 mm; base datum 7.00 mm. Its table distinguishes the RP-SMA SKU from the SMA variant. Private reference SHA-256: `6c76c93d3db2d94cdafaa403773f4469f890160fc3396510f08322bdd3ad065b`.
- [Linked datasheet, L9000025-01](https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocFormat=pdf&DocLang=English&DocNm=L9000025-01&DocType=Data+Sheet&PartCntxt=L9000025-01): the 18.6 mm upper segment plus 7.0 mm base explains the 25.6 mm housing datum; these are different datums, not conflicting overall dimensions. Private reference SHA-256: `aa3572733a970854894ef385b32f392de035ccfc1de300134cfac08cdee5410e`.

The drawing is proprietary and is not redistributed. No vendor drawing, image, STEP or derived vendor mesh belongs in this repository or the website. Only cited numerical facts and our own deliberately simplified representation are tracked. The product-page height field of zero is not used as physical evidence. The connector can extend below the housing datum; generated mesh bounds must be reported separately rather than asserted to equal 25.6 mm.

Electrical plots are tied to the manufacturer's reference ground plane. Neither the old frequency description, a published antenna gain nor the existing Wi-Fi labels establishes suitability for this radio, enclosure, band, pigtail, MIMO arrangement or installation. Cellular sites remain unchanged and have no new antenna.

## Recipe and assembly contract

Run `python3 tools/showcase_antennas.py` to regenerate the two optional fragments and [manifest](../exports/showcase-antennas/manifest.json). Run `python3 tools/showcase_antennas.py --check` or `python3 tools/test_showcase_antennas.py -v` to check the committed evidence, using the Python standard library alone. No vendor reference, native CAD library or full CAD run is needed. These are separate viewer-context files; the print/release configuration and purchase BOM do not reference them.

The [original recipe](../tools/showcase_antennas.py) creates a single connected closed 32-sided swept tube per antenna, with a simplified shoulder, curved elbow and flat tip. The coupling and housing share an assumed near-black display color; actual material finishes, grooves, markings, pins, threads and electrical internals are omitted. The 5.3 mm elbow radius and simplified tip are original illustrative choices, not vendor dimensions or fit evidence.

`cad/hardware.py:antenna_bulkheads` builds the right nut from X=W+0.5 through W+2.5, then mirrors left hardware around W/2. The resulting left nut outer face is **X=-2.5 mm**. The original coupling cap sits on that plane; its outward axis is **-X** and the upright housing follows **+Z**. Wi-Fi origins are `[-2.5,46.5,62]` and `[-2.5,145.5,62]` mm. This is a visual seating assumption only: the existing thread protrudes farther outward, and engagement is not modeled or qualified.

| Fragment | Assembly bounds, mm (rounded here; exact float32 readback in manifest) | Faces |
|---|---|---|
| `wifi_1_antenna.stl` | `[-19.6,42.6,58.1]` to `[-2.5,50.4,84.1]` | 1148 |
| `wifi_2_antenna.stl` | `[-19.6,141.6,58.1]` to `[-2.5,149.4,84.1]` | 1148 |

Each full generated envelope is approximately **17.1 × 7.8 × 26.0 mm**, separate from the **25.6 mm housing datum**. The housing spans local Z=-3.5..22.1 mm relative to the connector axis; the radius-3.9 coupling reaches Z=-3.9 mm. Float32 STL precision causes micrometre-scale rounding in the reported bounds.

The manifest carries SHA-256 for every input and fragment, exact assembly origins/axes, mm units, category `context`, optional/display-only flags, visibility and color. Its `recipe_revision_sha256` identifies source content without a self-referential Git hash. Downstream consumers must additionally name the reviewed product Git commit containing this manifest. They may append these two assembly-coordinate entries to a scratch viewer manifest; they must retain the source receipt/limits and leave the real fitted lid at its existing assembly transform. Public homepage packing waits for product source incorporation through main.

## Validation

`tools/test_showcase_antennas.py` reads the binary STLs back, checks actual bounds, nondegenerate triangles and stored normals, two oppositely directed uses per edge, positive signed volume, Euler characteristic 2 and a single connected component. It verifies exact Wi-Fi placement and a source-centre movement control; rejects wrong units, missing/duplicate/non-Wi-Fi/wrong-side sites, duplicate centres, NaN/Inf, booleans and numeric strings; checks byte determinism; and detects each changed source, fragment or manifest plus an unexpected cellular fragment. It also checks exclusion from manufacturing/release inventories. This establishes the declared display representation, not a collision, threaded-connection or RF qualification.

On 2026-11-12 UTC the bounded standard-library command `python3 tools/test_showcase_antennas.py -v` passed all six tests. The recipe/tests are wired into normal product CI. Existing parameter, CAD source, release configuration, print exports and BOM compare unchanged to source baseline `c06579b03ce32abe782b2f9c42ff3dd46437e670`; no new design/release tag or full CAD-run evidence is claimed.

Normal checks on implementation commit `8c0d80f47317141728d9a9af250e86a2d9b7de37` also passed: `tools/ci_check.py` checked 55 existing source/export hashes, all 18 print STLs and 22 linked pages; `tools/check_cooler_study.py` passed existing evidence freshness/clearance controls; `tools/write_readmes.py` left generated README content current; and `tools/package_release.py` built the unchanged 18-part print inventory. Inspection of the resulting release manifest found neither an accessory print part nor a generated `showcase-antennas` mesh. The existing environment supplied the pinned cad-agent `11841824e0c02568679e650e7ab33f7af6c591f1`; no dependency installation, full build, solver, purchase or release publication occurred. The file checks and package copy/zip each finished within four seconds under 1 CPU / 2 GiB / 64-task / 90-second caps.

## Delivery

1. Read only the existing `cad/parameters.json` Wi-Fi centres and the documented visual bulkhead stack in `cad/hardware.py`. Keep every manufacturing input and original export unchanged.
2. Generate a compact black right-angle housing and simplified coupling from original primitives in a separate optional showcase recipe. The connector axis points out of the left wall; the housing points +Z. Record the assumed visual seating datum, material/color assumptions and omitted thread/electrical details.
3. Export two assembly-coordinate, mm STL fragments and a product-owned manifest with source input hashes, deterministic source-recipe revision, part hashes/bounds/color/visibility, exact mount origins/axes and display-only limits. They are viewer context, not printable/release parts.
4. Test valid placement, missing/duplicate/non-Wi-Fi/wrong-side/unit/numeric controls, deterministic output, mesh bounds/faces and provenance. Use the existing product CI for the unchanged print exports and a small standard-library recipe test. No heavy CAD/native pipeline is required for original visual fragments; any full CAD/FEA/CFD run remains on a compute host under the project workflow.
5. Independently review and deliver source through dev and main without a revision tag. Hand off the exact reviewed source/fragment manifest to the homepage packing author, retaining the existing fitted lid and separately licensed carrier input. Do not label ignored pre-existing viewer exports a fresh CAD run.

Tracked in [issue 19](https://github.com/mvalancy/j501-agx-orin/issues/19) and [PR 20](https://github.com/mvalancy/j501-agx-orin/pull/20). Independent GPT-6 review and normal dev→main incorporation remain delivery gates.
