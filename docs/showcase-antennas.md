# Optional showcase antennas

This source slice adds two **original, render-only approximations** beside the existing Wi-Fi RP-SMA sites. It does not select radio hardware for the build, change any enclosure/mount dimension, qualify a connector fit or add an antenna to the purchasing/printing BOM. The fitted real lid stays in its existing assembly position.

## Source boundary

Visual reference: TE/Linx **ANT-2.4-CW-RAH-RPS**, TE **L9000025-01**, checked 2026-11-12 at the [official product page](https://www.te.com/en/product-L9000025-01.html).

- [Customer drawing B, C-ANT-2.4-CW-RAH-CCC](https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocFormat=pdf&DocLang=English&DocNm=C-ANT-2.4-CW-RAH-CCC&DocType=Customer+Drawing&PartCntxt=L9000025-01): housing datum 25.60 mm; lateral extent 17.10 mm; upper diameter 7.4 mm; connector diameter 7.80 mm and axial length 8.10 mm; base datum 7.00 mm. Its table distinguishes the RP-SMA SKU from the SMA variant. Private reference SHA-256: `6c76c93d3db2d94cdafaa403773f4469f890160fc3396510f08322bdd3ad065b`.
- [Linked datasheet, L9000025-01](https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocFormat=pdf&DocLang=English&DocNm=L9000025-01&DocType=Data+Sheet&PartCntxt=L9000025-01): the 18.6 mm upper segment plus 7.0 mm base explains the 25.6 mm housing datum; these are different datums, not conflicting overall dimensions. Private reference SHA-256: `aa3572733a970854894ef385b32f392de035ccfc1de300134cfac08cdee5410e`.

The drawing is proprietary and is not redistributed. No vendor drawing, image, STEP or derived vendor mesh belongs in this repository or the website. Only cited numerical facts and our own deliberately simplified representation are tracked. The product-page height field of zero is not used as physical evidence. The connector can extend below the housing datum; generated mesh bounds must be reported separately rather than asserted to equal 25.6 mm.

Electrical plots are tied to the manufacturer's reference ground plane. Neither the old frequency description, a published antenna gain nor the existing Wi-Fi labels establishes suitability for this radio, enclosure, band, pigtail, MIMO arrangement or installation. Cellular sites remain unchanged and have no new antenna.

## Implementation and validation plan

1. Read only the existing `cad/parameters.json` Wi-Fi centres and the documented visual bulkhead stack in `cad/hardware.py`. Keep every manufacturing input and original export unchanged.
2. Generate a compact black right-angle housing and simplified coupling from original primitives in a separate optional showcase recipe. The connector axis points out of the left wall; the housing points +Z. Record the assumed visual seating datum, material/color assumptions and omitted thread/electrical details.
3. Export two assembly-coordinate, mm STL fragments and a product-owned manifest with source input hashes, deterministic source-recipe revision, part hashes/bounds/color/visibility, exact mount origins/axes and display-only limits. They are viewer context, not printable/release parts.
4. Test valid placement, missing/duplicate/non-Wi-Fi/wrong-side/unit/numeric controls, deterministic output, mesh bounds/faces and provenance. Use the existing product CI for the unchanged print exports and a small standard-library recipe test. No heavy CAD/native pipeline is required for original visual fragments; any full CAD/FEA/CFD run remains on a compute host under the project workflow.
5. Independently review and deliver source through dev and main without a revision tag. Hand off the exact reviewed source/fragment manifest to the homepage packing author, retaining the existing fitted lid and separately licensed carrier input. Do not label ignored pre-existing viewer exports a fresh CAD run.

Tracked in [issue 19](https://github.com/mvalancy/j501-agx-orin/issues/19). Implementation and generated evidence are pending at this planning commit.
