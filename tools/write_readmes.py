"""Write a README.md with pictures into every folder, so the project can be browsed on GitHub.

Each README links that folder's files and shows the renders from preview/ and docs/assembly/ as a grid of cards.
exports/README.md is the print index: every part with its picture, size and 3MF / STL / STEP download links.

    python tools/write_readmes.py
"""
from pathlib import Path
import json, re

R = Path(__file__).resolve().parents[1]
REV = json.loads((R / 'cad/parameters.json').read_text())['revision'].split('-')[0]
RELEASE = f'https://github.com/mvalancy/j501-agx-orin/releases/tag/rev{REV}'


def w(rel, text):
    (R / rel).write_text(text.lstrip('\n'))
    print('wrote', rel)


def grid(items, cols=3):
    """GitHub-safe HTML table of image cards. item = (img, caption[, link]); the link defaults to the image."""
    wd = f'{100 // cols}%'
    rows = []
    for i in range(0, len(items), cols):
        cells = [f'<td width="{wd}" valign="top"><a href="{it[2] if len(it) > 2 else it[0]}"><img src="{it[0]}" '
                 f'alt="{re.sub(r"<[^>]+>", "", it[1])}" width="100%"></a><br>{it[1]}</td>' for it in items[i:i + cols]]
        cells += [f'<td width="{wd}"></td>'] * (cols - len(cells))
        rows.append('<tr>\n' + '\n'.join(cells) + '\n</tr>')
    return '<table>\n' + '\n'.join(rows) + '\n</table>\n'


PARTS = [('P1','base','Base'),('P1M','base_mount','Base with mounting tabs'),('P2','cover','Cover'),('P3','front_gmsl','Front plate, GMSL'),
 ('P4','front_no_gmsl','Front plate'),('P5','rear_io','Rear plate'),('P10','side_hatch','Side hatch'),('P18','chimney_cap','Floor cap'),
 ('P15','storage_35','3.5 in tray'),('P16','storage_25','2.5 in tray'),('P17','storage_mount_plate','Mounting plate'),('P19','ssd_clip','SSD clip'),
 ('P9','mount_fit_template','Board fit template'),('P11','m3_insert_coupon','Insert coupon'),('P12','rail_coupon','Rail coupon'),
 ('P13','rail_key','Rail key'),('P14','countersink_coupon','Countersink coupon')]
CONNECTORS = [('front_power','DC power input'),('ethernet_10g','10G Ethernet'),('ethernet_1g','1G Ethernet'),('rear_terminal','I/O terminal block'),
 ('rear_tall_connector','Rear tall connector'),('rear_usb_lower','USB, lower'),('rear_usb_upper','USB, upper'),('rear_connector_flat','Rear flat connector'),
 ('rear_bottom_port_a','Rear bottom port A'),('rear_bottom_port_b','Rear bottom port B'),('front_bottom_port','J18 nano-SIM'),('side_header','J17 side header'),
 ('module_socket','Module socket')]

# ---------------------------------------------------------------- exports: the print index
# (title, intro, [(id, file, name, qty, note)])
GROUPS = [
 ('Core enclosure', 'Every build needs these, except that P1M (under [Mounting and closures](#mounting-and-closures)) replaces P1 on a wall or robot mount without drive trays. Pick **one** front plate.', [
  ('P1', 'base', 'Base', '1', 'Desktop, or any setup with drive trays. Board supports, cooler columns, SATA floor opening.'),
  ('P2', 'cover', 'Cover', '1', 'Hex-grille lid. Captures the plates and hatch; 4 × M3 × 16 from the top.'),
  ('P3', 'front_gmsl', 'Front plate, GMSL', '1 of P3/P4', 'With the GMSL extension board: audio, GMSL, 1G, 10G, LED, DC IN.'),
  ('P4', 'front_no_gmsl', 'Front plate', '1 of P3/P4', 'Without the GMSL board: audio, 1G, 10G, LED, DC IN.'),
  ('P5', 'rear_io', 'Rear plate', '1', 'I/O terminal, HDMI, 3 × USB-A, 2 × USB-C.'),
  ('P10', 'side_hatch', 'Side hatch', '1', 'Flush door over the J17 header; the lid holds it in.')]),
 ('Mounting and closures', 'Depends on how the enclosure is mounted and whether drive trays are fitted.', [
  ('P1M', 'base_mount', 'Base with mounting tabs', '0–1', 'Replaces P1 for a wall or robot mount <b>without</b> drive trays. Four M6 slots.'),
  ('P17', 'storage_mount_plate', 'Mounting plate', '0–1', 'Wall or robot mount <b>under</b> a drive-tray stack, with the same tab pattern as P1M.'),
  ('P18', 'chimney_cap', 'Floor cap', '0–1', 'Plugs the SATA cable opening in the floor when no trays are fitted.')]),
 ('Drive storage', 'Optional. Stack 1 tray, 1 of each or 2 of each, in any order, under P1.', [
  ('P15', 'storage_35', '3.5 in tray', '0–2', 'One 3.5 in drive. Needs its own 12 V supply (12V IN hole).'),
  ('P16', 'storage_25', '2.5 in tray', '0–2', 'Two 2.5 in drives up to 15 mm thick, powered from the board.'),
  ('P19', 'ssd_clip', 'SSD clip', '4 per drive', 'Holds a 7 mm SSD that has side holes only.')]),
 ('Jigs, fixtures and test coupons', '<b>Print these first</b>, in the filament you will use for the enclosure. They are small and check the fits that depend on your printer.', [
  ('P9', 'mount_fit_template', 'Board fit template', '1', 'Jig: set the bare board on it. Every pad should touch, and the cooler holes should line up.'),
  ('P11', 'm3_insert_coupon', 'Insert coupon', '1', 'Five pilot holes, 3.7–4.1 mm. Use the one that holds an M3 insert best.'),
  ('P12', 'rail_coupon', 'Rail coupon', '1', 'A short length of the plate channel. Test with P13.'),
  ('P13', 'rail_key', 'Rail key', '1', 'Should slide in P12 without rattling.'),
  ('P14', 'countersink_coupon', 'Countersink coupon', '1', 'An M3 × 35 flat head should sit flush on its cone.')])]
BOUNDS = {k: v['print_bounds_mm'] for k, v in json.loads((R / 'exports/print-review.json').read_text()).items()}
missing = {f for _, _, ps in GROUPS for _, f, *_ in ps} ^ set(BOUNDS)
assert not missing, f'parts missing from the print index, or not printable: {missing}'


def card(pid, f, name, qty, note):
    size = ' × '.join(f'{x:.0f}' for x in sorted(BOUNDS[f], reverse=True))
    return (f'<td width="33%" valign="top">\n<a href="{f}.stl"><img src="../preview/part-{f}.png" alt="{pid} {name}" width="100%"></a><br>\n'
            f'<b>{pid} · {name}</b><br>\n<sub>Qty {qty} · {size} mm</sub><br>\n{note}<br>\n'
            f'<b><a href="{f}.stl">3D view</a></b> · <a href="{f}.3mf?raw=true">3MF</a> · <a href="{f}.stl?raw=true">STL</a> · <a href="{f}.step?raw=true">STEP</a>\n</td>')


def cards(ps):
    rows = [[card(*p) for p in ps[i:i + 3]] for i in range(0, len(ps), 3)]
    return '<table>\n' + '\n'.join('<tr>\n' + '\n'.join(r + ['<td width="33%"></td>'] * (3 - len(r))) + '\n</tr>' for r in rows) + '\n</table>\n'


package = re.search(r'^\s*package:\s*\n\s*name:\s*(\S+)', (R / 'cad-agent.yaml').read_text(), re.M)[1]
w('exports/README.md', f"""
# Print files

The parts you need to print for the Rev {REV} enclosure. Click a picture or **3D view** to spin the part in GitHub's
built-in STL viewer, or use the links under it to download the part:

- **3MF** opens in Bambu Studio and other slicers, on a 256 mm plate.
- **STL** works in any slicer.
- **STEP** is for editing in CAD.

STL and 3MF files are already in print orientation. Every part fits a 256 mm bed. Sizes are outside dimensions, largest first.

**One download:** the [Rev {REV} print package]({RELEASE}) has every STL, the instructions and the renders.
**Hardware to buy:** [main README](../README.md#hardware-to-buy). **Build steps:** [ASSEMBLY.md](../ASSEMBLY.md).

<p align="center">
  <img src="../preview/exploded.png" alt="Exploded view of the enclosure" width="820">
</p>

> **Fit-check prototype.** Every part is checked in CAD only and nothing has been printed yet. Print the
> [jigs, fixtures and test coupons](#jigs-fixtures-and-test-coupons) first, in the filament you plan to use.

**Sections:** [Core enclosure](#core-enclosure) · [Mounting and closures](#mounting-and-closures) · [Drive storage](#drive-storage) · [Jigs, fixtures and test coupons](#jigs-fixtures-and-test-coupons) · [Other files](#other-files-in-this-folder)

## What to print for your setup

Every setup needs the cover (P2), the rear plate (P5), the side hatch (P10) and one front plate (P3 or P4). Then add:

| Setup | Base | Mounting and closures | Drive storage |
|---|---|---|---|
| Desktop | P1 | P18 floor cap | none |
| Desktop with drives | P1 | none | P15 and/or P16 trays; P19 clips for side-hole SSDs |
| Wall or robot mount | P1M | P18 floor cap | none |
| Wall or robot mount with drives | P1 | P17 under the stack | P15 and/or P16 trays; P19 clips for side-hole SSDs |

Use the **P3** front plate if you have the GMSL extension board, and **P4** if you don't.

""" + ''.join(f'## {t}\n\n{intro}\n\n{cards(ps)}\n' for t, intro, ps in GROUPS) + f"""## Other files in this folder

The design pipeline (`cad-agent all`) writes these. You don't need them for printing.

| File | What it is |
|---|---|
| `{package}-manifest.json` | sha256 of every file from the last pipeline run; CI checks the print files against it |
| `review-validation.json` | Pass or fail for every design check |
| `geometry-checks.json`, `print-review.json` | Per-part geometry and printability checks |
| `assembly-checks.json`, `assembly-paths.json`, `mount-checks.json` | Assembly order, plate insertion paths, mounting tabs |
| `carrier-clearances.json`, `shell-clearances.json`, `storage-checks.json` | Clearances to the board, its connectors and the drive trays |
| `design-metrics.json` | Measured dimensions and design calculations |
| `cad-agent-results.json` | Summary of the pipeline run |

Assemblies that include the carrier board and the NVIDIA module are built locally but not committed, because we can't redistribute the vendor models.
""")

# ---------------------------------------------------------------- preview
P = lambda n: f'{n}.png'
w('preview/README.md', f'''
# Renders

Every picture of the Rev {REV} design, rendered from the CAD by [`tools/render.py`](../tools/render.py). Click a picture for full size.

The same renders are on the local review site, which adds STL, 3MF and Bambu Studio download buttons:
`python tools/serve_preview.py` serves [`index.html`](index.html). The print files themselves are in [`exports/`](../exports/).

**Sections:** [Assembled](#assembled) · [Structure](#structure) · [Storage and cables](#storage-and-cables) · [Printed parts](#printed-parts) · [Hardware and electronics](#hardware-and-electronics) · [Carrier connectors](#carrier-connectors)

## Assembled

{grid([(P('assembled'),'<b>Assembled</b>: flush shell, framed I/O plates, finger-safe hex roof'),
       (P('exploded'),'<b>Exploded</b>: sliding plates captured by the lid, cooler tied to the floor'),
       (P('open'),'<b>Open</b>: every carrier solid and open shell kept'),
       (P('top'),'<b>Top</b>: board corner supports and cooler tie-down pattern'),
       (P('rear'),'<b>Rear I/O</b>: per-port windows sized for plug overmolds'),
       (P('no-gmsl'),'<b>Desktop, no GMSL</b>: no dummy openings'),
       (P('front-fit'),'<b>Front plate</b>: one window per connector group'),
       (P('rear-fit'),'<b>Rear plate</b>: windows sized to plug overmolds'),
       (P('side-access'),'<b>J17 access</b>: lid off, the flush hatch lifts out'),
       (P('antennas'),'<b>Antennas</b>: RP-SMA bulkheads in the fixed base walls'),
       (P('service-buttons'),'<b>Reset and recovery</b>: pin access through the rear plate')])}
## Structure

{grid([(P('board-mount'),'<b>Board mounting</b>: printed supports and M3 inserts'),
       (P('heatsink-tiedown'),'<b>Cooler tie-down</b>: section; the weight of the cooler goes into the floor'),
       (P('bottom'),'<b>Underside</b>: recessed tie-down screws, foot pockets, mounting tabs'),
       (P('support-detail'),'<b>Supports</b>: radius fillets at the floor and under each pad (half cut)'),
       (P('lid-detail'),'<b>Lid</b>: honeycomb grille over the cooler fan'),
       (P('hex-inlet'),'<b>Lid inlet</b>: fan-side chamfer on the grille cells'),
       (P('lid-column-detail'),'<b>Lid-screw column</b>: fused to the side wall'),
       (P('mount-clearance'),'<b>Mounting tabs</b>: M6 screw, washer and driver access')])}
## Storage and cables

{grid([(P('storage-configs'),'<b>Storage options</b>: 1 tray, 1 of each, 2 of each'),
       (P('storage-exploded'),'<b>Storage, exploded</b>: trays stack under the base'),
       (P('storage-stack'),'<b>Stack</b>: base, 3.5 in tray, 2.5 in tray, mounting plate'),
       (P('base-stacking'),'<b>P1 underside</b>: where the trays attach'),
       (P('drive-bays'),'<b>Drive mounting</b>: 3.5 in, 2.5 in, and 7 mm SSDs on P19 clips'),
       (P('ssd-clip-detail'),'<b>P19 clip</b>: holds a 7 mm SSD by its side holes'),
       (P('underside-slots'),'<b>Under the board</b>: Mini PCIe, M.2 B and M.2 E cards, SATA plugs'),
       (P('cable-routing'),'<b>Cable routing</b>: underside connectors, floor opening, chimney, drives'),
       (P('cable-routing-side'),'<b>Cable routing, side cut</b>'),
       (P('cable-path'),'<b>Cable path</b>: SATA leads drop through the floor into the trays'),
       (P('cable-route-diagram'),'<b>Cable-route diagram</b>: side elevation and tray plan'),
       (P('sata-power-schematic'),'<b>SATA power</b>: the board supplies 5 V only (schematic sheet 27)')])}
## Printed parts

Click a part to open it in GitHub's 3D viewer. Download links for each part are in [`exports/`](../exports/).

{grid([(f'part-{f}.png', f'<b>{pid}</b> {name}', f'../exports/{f}.stl') for pid, f, name in PARTS], cols=4)}
## Hardware and electronics

Bought parts and vendor models, shown for fit. Fastener threads, cooler internals and the GMSL component positions are approximate.

{grid([(P('part-carrier'),'<b>E1</b> J501 carrier board'),(P('part-module'),'<b>E2</b> Jetson AGX Orin module'),
       (P('part-cooler'),'<b>E2 / E3 / H7</b> module, cooler and tie-down screws'),(P('part-gmsl'),'<b>E4–E8</b> GMSL extension board'),
       (P('part-fakra'),'<b>E5</b> mini-FAKRA connector (candidate model)'),(P('part-M3_insert'),'<b>H1</b> M3 × 10 heat-set insert'),
       (P('part-M3_lid_screw'),'<b>H3</b> M3 × 16 lid screw'),(P('part-M3_board_screw'),'<b>H5</b> M3 × 10 board screw'),
       (P('part-jumper_cap'),'<b>H6</b> 2.54 mm jumper cap'),(P('part-cooler_tiedown_screw'),'<b>H7</b> cooler tie-down screw')], cols=4)}
## Carrier connectors

Connector bodies extracted from the carrier board's STEP model, used for the plate cutouts and clearance checks.

{grid([(f'connector-{n}.png', cap) for n, cap in CONNECTORS], cols=4)}''')

# ---------------------------------------------------------------- docs
STEPS = [('01-test-prints','1. Print the test parts','1-print-the-test-parts'),('02-fit-template','2. Test-fit the board on P9','2-test-fit-the-board-on-p9'),
 ('03-inserts','3. Heat-set the inserts','3-heat-set-the-inserts'),('04-board','4. Fit the board','4-fit-the-board'),
 ('04b-floor-cap','4. Floor cap (no drive trays)','4-fit-the-board'),('05-cooler','5. Fit the module and cooler','5-fit-the-module-and-cooler'),
 ('06-tiedown','6. Tie the cooler down','6-tie-the-cooler-down'),('07-antennas','7. Fit the antennas','7-fit-the-antennas'),
 ('08-plates','8. Slide in the plates','8-slide-in-the-plates'),('09-lid','9. Fit the lid','9-fit-the-lid'),
 ('10-tray-inserts','Trays 1. Inserts in the base feet','trays-1-inserts-in-the-base-feet'),('11-drives','Trays 2. Drives into the tray','trays-2-drives-into-the-tray'),
 ('12-stack','Trays 4. Hang the tray','trays-4-hang-the-tray'),('13-mount-plate','Trays 5. Wall or robot mount','trays-5-wall-or-robot-mount')]
w('docs/assembly/README.md', f'''
# Assembly step pictures

The pictures for [ASSEMBLY.md](../../ASSEMBLY.md), drawn by [`tools/render_steps.py`](../../tools/render_steps.py). In each one the parts
added in that step are **orange** and everything already built is grey. Click a picture to read that step.

{grid([(f'{f}.png', f'<b>{cap}</b>', f'../../ASSEMBLY.md#{a}') for f, cap, a in STEPS])}''')

w('docs/README.md', f'''
# Docs

Reference material for reviewing and building the enclosure. Most of these files are generated by
[`tools/write_docs.py`](../tools/write_docs.py) from the CAD model, so edit the model, not the tables.

<p align="center">
  <a href="assembly/"><img src="assembly/03-inserts.png" alt="Assembly step 3: heat-set inserts" width="640"></a>
</p>

| File | What it is |
|---|---|
| [`assembly/`](assembly/) | Step pictures for [ASSEMBLY.md](../ASSEMBLY.md) |
| [`BOM.csv`](BOM.csv) | Bill of materials: printed parts, hardware and electronics, with dimensions |
| [`fastener-sources.csv`](fastener-sources.csv) | Where each fastener comes from, and how closely its model matches |
| [`check-sheet.pdf`](check-sheet.pdf) | Dimensioned drawings to check printed parts against |
| [`engineering-review.html`](engineering-review.html) | Every table below on one filterable page (download it, or run `tools/serve_preview.py`) |
| [`cad-agent-report.html`](cad-agent-report.html) | Pass or fail for every part, print file and design check |
| [`measurement-register.csv`](measurement-register.csv) | Every dimension the design relies on, and whether it was measured or assumed |
| [`cutout-register.csv`](cutout-register.csv) | Every cutout in the plates and walls, and what it is for |
| [`feature-review.csv`](feature-review.csv) | Feature-by-feature printability review |
| [`connector-inventory.csv`](connector-inventory.csv) | Connectors and components on the carrier, from the schematic |
| [`model-search.csv`](model-search.csv) | Where each vendor model was found, and which are still missing |

GitHub shows the `.csv` files as searchable tables. The `.html` pages show as source on GitHub; open them locally to read them.
''')

# ---------------------------------------------------------------- cad
w('cad/README.md', '''
# CAD source

The enclosure is modelled in Python with [CadQuery](https://cadquery.readthedocs.io/). These three files produce every printed part.

<p align="center">
  <img src="../preview/open.png" alt="Open enclosure with the carrier board and cooler" width="720">
</p>

| File | What it is |
|---|---|
| [`parameters.json`](parameters.json) | Every dimension the design uses: board, enclosure, cooler, GMSL board, inserts, printer, ports, storage. **Edit this first.** |
| [`build.py`](build.py) | Builds each printed part and writes its STL (in print orientation) and STEP (in assembly position) to [`exports/`](../exports/) |
| [`hardware.py`](hardware.py) | Simplified models of the bought parts (inserts, screws, jumper cap, cooler) for renders and clearance checks. Not for manufacturing |

**Coordinates.** All dimensions are in mm. The origin is set so the board's lower-left corner sits at the PCB margin, with Z measured from the underside of the PCB.

**Before changing a dimension,** check [`docs/measurement-register.csv`](../docs/measurement-register.csv): it says which values were measured and which are assumptions.

**Rebuilding.** `build.py` reads the vendor board model, which is not in the repository. Fetch it first, then run the whole pipeline so the checks, renders and manifest stay in step:

```bash
.venv/bin/python tools/fetch_references.py
.venv/bin/cad-agent all
```

The scripts that check and render the build are in [`tools/`](../tools/).
''')

# ---------------------------------------------------------------- tools
w('tools/README.md', f'''
# Tools

Scripts that check, render, document and package the design. [`cad-agent.yaml`](../cad-agent.yaml) runs them in order
(`cad-agent all`); without the toolkit, run the scripts in the table below in that order with `.venv/bin/python`.

{grid([('../preview/cable-route-diagram.png','<b>cable_diagram.py</b>: cable-route diagram'),
       ('../preview/heatsink-tiedown.png','<b>render.py</b>: renders for <code>preview/</code>'),
       ('../docs/assembly/06-tiedown.png','<b>render_steps.py</b>: assembly step pictures')])}
## The pipeline, in order

| Step | Script | Writes |
|---|---|---|
| build | [`../cad/build.py`](../cad/build.py) | Print files in `exports/` |
| clearances | [`check_clearances.py`](check_clearances.py) | `exports/carrier-clearances.json`: plastic against the board and hardware |
| shells | [`check_shells.py`](check_shells.py) | `exports/shell-clearances.json`: plastic against the board's open surface shells |
| assembly-paths | [`assembly_paths.py`](assembly_paths.py) | `exports/assembly-paths.json`: each plate can slide into place |
| print-review | [`print_review.py`](print_review.py) | `exports/geometry-checks.json`, `exports/print-review.json`: watertight, fits the bed, overhangs |
| design-metrics | [`design_metrics.py`](design_metrics.py) | `exports/design-metrics.json`: measured dimensions and design calculations |
| mounts | [`check_mounts.py`](check_mounts.py) | `exports/mount-checks.json`: mounting tabs, washer support and driver access |
| storage | [`check_storage.py`](check_storage.py) | `exports/storage-checks.json`: trays, cable routes, bend radii, underside slots |
| cable-diagram | [`cable_diagram.py`](cable_diagram.py) | `preview/cable-route-diagram.png` |
| docs | [`write_docs.py`](write_docs.py) | The tables in `docs/` and `docs/engineering-review.html` |
| check-sheet | [`check_sheet.py`](check_sheet.py) | `docs/check-sheet.pdf` |
| detailed-assembly | [`detailed_assembly.py`](detailed_assembly.py) | Full assemblies with the vendor models (local only, not committed) |
| render | [`render.py`](render.py) | Every picture in `preview/` |
| assembly-steps | [`render_steps.py`](render_steps.py) | `docs/assembly/*.png` |
| readmes | [`write_readmes.py`](write_readmes.py) | A `README.md` with pictures in every folder, including the print index in `exports/` |
| validate | [`validate_review.py`](validate_review.py) | `exports/review-validation.json`: every check passed, every link resolves |

`cad-agent` also writes the 3MF files and the manifest. [`export_3mf.py`](export_3mf.py) does the 3MF step on its own.

## Other scripts

| Script | What it does |
|---|---|
| [`fetch_references.py`](fetch_references.py) | Downloads the vendor models and datasheets in `references/sources.json`, checks their sha256, and rebuilds the caches |
| [`inspect_reference.py`](inspect_reference.py) | Lists the solids in the carrier board model (`references/solids.json`) |
| [`extract_measurements.py`](extract_measurements.py) | Measures the PCB outline, holes and edge components from the board model |
| [`extract_features.py`](extract_features.py) | Pulls the mounting features out of the board model |
| [`measure_pcb_holes.py`](measure_pcb_holes.py) | Fits the PCB holes (`references/pcb-hole-fits.json`) |
| [`export_hardware.py`](export_hardware.py) | Writes connector meshes to `references/hardware/` |
| [`export_open_shells.py`](export_open_shells.py) | Writes the board's open surface shells for the shell check |
| [`renderkit.py`](renderkit.py) | Shared VTK helpers for `render.py` and `render_steps.py` |
| [`serve_preview.py`](serve_preview.py) | Serves the local review site ([`preview/index.html`](../preview/index.html)) |
| [`package_release.py`](package_release.py) | Builds the print zip and release notes |
| [`ci_check.py`](ci_check.py) | What CI runs: print files match the manifest, every check passed, STLs are sound, README links resolve |
''')

# ---------------------------------------------------------------- references
w('references/README.md', f'''
# References

Vendor models, datasheets and schematics the design is measured from, plus the measurements taken from them.

**The vendor files are not in this repository**, because they are not ours to redistribute. [`sources.json`](sources.json) lists each
one with its original URL and sha256. To download them and rebuild the caches the build reads:

```bash
.venv/bin/python tools/fetch_references.py   # the NVIDIA module model needs a developer login; the script says where
```

<p align="center">
  <img src="../preview/part-carrier.png" alt="The J501 carrier board model" width="720">
</p>

## What is in the repository

| File | What it is |
|---|---|
| [`sources.json`](sources.json) | Every vendor file: ID, original URL, date retrieved, sha256 |
| [`extra-source-urls.json`](extra-source-urls.json) | Other pages consulted |
| [`seeed-oshw-tree.json`](seeed-oshw-tree.json) | Index of Seeed's open-hardware file tree, used to find the models |
| [`measurements.log`](measurements.log) | Log of the measurements taken from the board model |
| [`solids.json`](solids.json) | Every solid in the carrier board model, with its bounding box |
| [`edge-components.json`](edge-components.json) | Connectors along the board edges, which the plate cutouts follow |
| [`mount-features.json`](mount-features.json) | Mounting holes and features |
| [`pcb-circles.json`](pcb-circles.json), [`pcb-hole-fits.json`](pcb-hole-fits.json) | PCB holes and their fitted diameters |
| [`open-shells.json`](open-shells.json) | Surface shells in the board model that are not closed solids |
| [`pcb-outline.step`](pcb-outline.step), [`pcb-outline.stl`](pcb-outline.stl) | The PCB outline on its own |
| [`hardware/`](hardware/) | Connector meshes (downloaded) and their index |

## Vendor sources

| ID | File | Source |
|---|---|---|
''' + ''.join(f"| {s['id']} | `{s['file']}` | [{s['url'].split('/')[2]}]({s['url']}) |\n" for s in __import__('json').loads((R/'references/sources.json').read_text())))

w('references/hardware/README.md', f'''
# Connector meshes

Meshes of the carrier board's connectors, cut out of the vendor board model by [`tools/export_hardware.py`](../../tools/export_hardware.py).
They are used for the plate cutouts, the clearance checks and the renders.

Only [`indices.json`](indices.json), which maps each connector to its solids in the board model, is in the repository. The meshes are
rebuilt by `tools/fetch_references.py`. These are the renders of each one:

{grid([(f'../../preview/connector-{n}.png', cap) for n, cap in CONNECTORS], cols=4)}''')

# ---------------------------------------------------------------- archive
w('archive/README.md', f'''
# Archive

Earlier revisions of the design, kept for reference. **Don't print these:** the current parts are in [`exports/`](../exports/).
Each folder holds that revision's source and parameters; the scripts expect the repository layout of their time and won't run as-is.

{grid([('rev04/preview/assembled.png','<b><a href="rev04/">Rev 0.4</a></b>: open ribbed lid, rounded shell, larger mounting tabs','rev04/'),
       ('rev02/preview/part-mount_ear.png','<b><a href="rev02/">Rev 0.2</a></b>: first fit-check build, separate mounting ears and desktop feet','rev02/')])}
| Revision | Folder | What changed |
|---|---|---|
| 0.6 | (current) | Flush shell, framed I/O plates, hex roof, cooler tie-down columns, stackable drive trays |
| 0.4 | [`rev04/`](rev04/) | Open ribbed lid, rounded shell, larger mounting tabs, M6 inserts |
| 0.3 | [`rev03/`](rev03/) | Print-review pass: rail coupon and key, vents. Source and parameters only |
| 0.2 | [`rev02/`](rev02/) | First fit-check build: separate mounting ears (P6) and desktop feet (P7) |
''')

w('archive/rev02/README.md', f'''
# Rev 0.2: first fit-check build

The first fit-check version. Mounting ears (P6) and desktop feet (P7) were separate printed parts, and the board sat on metal M3 spacers.
Superseded; the current parts are in [`exports/`](../../exports/).

{grid([('preview/part-mount_ear.png','<b>P6</b> mounting ear'),('preview/part-desktop_foot.png','<b>P7</b> desktop foot'),('preview/part-M3_spacer.png','<b>H4</b> M3 spacer')])}
| File | What it is |
|---|---|
| [`parameters.json`](parameters.json) | Rev 0.2 dimensions |
| [`build.py`](build.py), [`hardware.py`](hardware.py), [`render.py`](render.py) | Rev 0.2 source |
| [`exports/`](exports/) | The ear and foot print files |
| [`preview/`](preview/) | Renders of the parts that changed |
''')
w('archive/rev02/exports/README.md', f'''
# Rev 0.2 print files

Superseded parts, kept for reference. The current print files are in [`exports/`](../../../exports/).

{grid([('../preview/part-mount_ear.png','<b>P6</b> mounting ear: <a href="mount_ear.stl">STL</a> · <a href="mount_ear.step?raw=true">STEP</a>','mount_ear.stl'),
       ('../preview/part-desktop_foot.png','<b>P7</b> desktop foot: <a href="desktop_foot.stl">STL</a> · <a href="desktop_foot.step?raw=true">STEP</a>','desktop_foot.stl')], cols=2)}''')
w('archive/rev02/preview/README.md', f'''
# Rev 0.2 renders

{grid([('part-mount_ear.png','<b>P6</b> mounting ear'),('part-desktop_foot.png','<b>P7</b> desktop foot'),('part-M3_spacer.png','<b>H4</b> M3 × 12 spacer'),
       ('part-M3_lower_screw.png','<b>H5</b> M3 × 10 screw under the floor'),('part-M3_upper_screw.png','<b>H6</b> M3 × 6 screw at the carrier')])}''')
w('archive/rev03/README.md', '''
# Rev 0.3: print review

A print-review pass on Rev 0.2. It added the rail coupon and key (now P12 and P13) and vents. Only the source and parameters were kept; there are no renders or print files.

| File | What it is |
|---|---|
| [`parameters.json`](parameters.json) | Rev 0.3 dimensions |
| [`build.py`](build.py) | Rev 0.3 source |

See [Rev 0.4](../rev04/) for the next version with pictures, or [`exports/`](../../exports/) for the current parts.
''')
R4 = [('assembled','Assembled'),('exploded','Exploded'),('open','Open'),('top','Top'),('rear','Rear'),('no-gmsl','Desktop, no GMSL'),
      ('front-fit','Front plate fit'),('rear-fit','Rear plate fit'),('side-access','J17 access'),('board-mount','Board mounting'),
      ('lid-detail','Lid'),('mount-clearance','Mounting tabs')]
w('archive/rev04/README.md', f'''
# Rev 0.4: open ribbed lid

An open ribbed lid, a rounded shell and larger mounting tabs held with M6 inserts. Superseded by Rev 0.6, which has a flush shell, a hex
roof, cooler tie-down columns and drive trays. The current parts are in [`exports/`](../../exports/).

{grid([('preview/assembled.png','<b>Assembled</b>'),('preview/exploded.png','<b>Exploded</b>'),('preview/open.png','<b>Open</b>')])}
| File | What it is |
|---|---|
| [`parameters.json`](parameters.json) | Rev 0.4 dimensions |
| [`build.py`](build.py), [`hardware.py`](hardware.py) | Rev 0.4 source |
| `assembly_paths.py`, `check_*.py`, `design_metrics.py`, `render.py`, `write_docs.py` | The Rev 0.4 versions of the [`tools/`](../../tools/) scripts |
| [`exports/`](exports/) | Rev 0.4 check results, the insert coupon and the Rev 0.3 and 0.4 review zips |
| [`preview/`](preview/) | All the Rev 0.4 renders |
''')
w('archive/rev04/exports/README.md', f'''
# Rev 0.4 exports

Rev 0.4 check results and review packages, kept for reference. The current print files are in [`exports/`](../../../exports/).

{grid([('../preview/part-insert_coupon.png','<b>Insert coupon</b> (Rev 0.4): <a href="insert_coupon.stl">STL</a> · <a href="insert_coupon.step?raw=true">STEP</a>','insert_coupon.stl')], cols=2)}
| File | What it is |
|---|---|
| `j501-agx-rev03-fit-check.zip`, `j501-agx-rev04-fit-check.zip` | The Rev 0.3 and Rev 0.4 review packages |
| `review-package-manifest.json` | sha256 of every file in the Rev 0.4 package |
| `review-validation.json` | Pass or fail for every Rev 0.4 check |
| `geometry-checks.json`, `print-review.json` | Per-part geometry and printability checks |
| `assembly-checks.json`, `assembly-paths.json`, `mount-checks.json` | Assembly order, insertion paths, mounting tabs |
| `carrier-clearances.json`, `shell-clearances.json` | Clearances to the board |
| `design-metrics.json` | Measured dimensions and design calculations |
''')
R4P = ['part-base','part-base_mount','part-cover','part-front_gmsl','part-front_no_gmsl','part-rear_io','part-side_hatch',
       'part-mount_fit_template','part-insert_coupon','part-m3_insert_coupon','part-rail_coupon','part-rail_key']
R4H = [('part-carrier','Carrier'),('part-module','Module'),('part-cooler','Cooler'),('part-gmsl','GMSL board'),('part-fakra','mini-FAKRA'),
       ('part-M3_insert','M3 insert'),('part-M3_board_screw','M3 board screw'),('part-M6_insert','M6 insert'),('part-M6_screw','M6 screw'),
       ('part-M6_washer','M6 washer'),('part-jumper_cap','Jumper cap')]
w('archive/rev04/preview/README.md', f'''
# Rev 0.4 renders

All the renders of Rev 0.4. The local review page of the time is [`index.html`](index.html).

## Assembled

{grid([(f'{n}.png', f'<b>{c}</b>') for n, c in R4])}
## Printed parts

{grid([(f'{n}.png', n[5:].replace('_', ' ')) for n in R4P], cols=4)}
## Hardware and electronics

{grid([(f'{n}.png', c) for n, c in R4H], cols=4)}
## Carrier connectors

{grid([(f'connector-{n}.png', cap) for n, cap in CONNECTORS], cols=4)}''')

# ---------------------------------------------------------------- CI
w('.github/workflows/README.md', '''
# CI

[`ci.yml`](ci.yml) runs on every push and pull request, and on `rev*` tags.

The CAD build needs vendor models (one behind a login), so CI cannot rebuild the parts. It checks the committed files instead, with
[`tools/ci_check.py`](../../tools/ci_check.py):

1. Every print file and `cad/parameters.json` matches the sha256 recorded by the last local `cad-agent all` run.
2. That run passed every design check.
3. Every STL is one watertight body that fits a 256 mm bed.
4. Every local link and image in the README files and ASSEMBLY.md resolves.

It also reruns [`tools/write_readmes.py`](../../tools/write_readmes.py) and fails if any folder README changed.
It then builds the print zip with [`tools/package_release.py`](../../tools/package_release.py) and keeps it as a download for 30 days.
On a `rev*` tag it also publishes a [GitHub release](https://github.com/mvalancy/j501-agx-orin/releases). See
[Making a release](../../README.md#making-a-release).
''')
