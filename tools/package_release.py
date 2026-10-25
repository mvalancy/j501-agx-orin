"""Build the print-ready release zip: STL files, assembly instructions and a few renders.

    python tools/package_release.py      # writes exports/j501-agx-<rev>-print.zip

The instructions are the README's bill of materials and assembly sections, with file links pointing into the zip.
"""
from pathlib import Path
import json, re, zipfile

R = Path(__file__).resolve().parents[1]
rev = json.loads((R / 'cad/parameters.json').read_text())['revision'].split('-')[0]
name = f'j501-agx-rev{rev}-print'
parts = list(json.loads((R / 'exports/geometry-checks.json').read_text()))
RENDERS = {'assembled': 'Assembled', 'exploded': 'Exploded view', 'open': 'Lid off', 'rear': 'Rear plate',
           'bottom': 'Underside: tie-down screws and floor opening', 'heatsink-tiedown': 'Cooler tie-down screws',
           'antennas': 'RP-SMA antenna bulkheads', 'service-buttons': 'Reset and recovery pin holes',
           'storage-configs': 'Drive tray stacks', 'storage-exploded': 'Drive tray stack, exploded',
           'drive-bays': 'Drive bays', 'cable-routing': 'SATA cable routing'}

readme = (R / 'README.md').read_text()
body = readme[readme.index('## Bill of materials'):readme.index('## Design notes')]
body = re.sub(r'\[([\w.]+)\.3mf\]\(exports/\1\.3mf\)', lambda m: f'[{m[1]}.stl](stl/{m[1]}.stl)', body)
body = body.replace('Every printed part has a [3MF](exports/) (opens in Bambu Studio), STL and STEP file in [`exports/`](exports/). '
                    'The full BOM with dimensions is [docs/BOM.csv](docs/BOM.csv).',
                    'Every printed part is in `stl/`, in millimetres. The full BOM with dimensions is `BOM.csv`. '
                    '3MF and STEP files are in the GitHub repository.')
assert '](exports/' not in body and '](docs/' not in body, 'unconverted repo link in the instructions'
gallery = '\n\n'.join(f'**{t}**\n\n![{t}](renders/{k}.png)' for k, t in RENDERS.items())
doc = f'''# J501 AGX Orin Enclosure, Rev {rev}: print package

A 3D-printable housing for the Seeed reServer Industrial J501 carrier board with an NVIDIA Jetson AGX Orin module.
Source, 3MF and STEP files: https://github.com/mvalancy/j501-agx-orin

**Status:** fit-check prototype. Every part and clearance is checked in CAD only; nothing has been printed or
test-fitted yet, so print the test parts first.

**You need:** a Seeed reServer Industrial J501 carrier (https://www.seeedstudio.com/reServer-Industrial-J501-Carrier-board-for-Jetson-AGX-Orin-p-5950.html),
a Jetson AGX Orin module and a cooler. More at https://www.seeedstudio.com/

![Assembled](renders/assembled.png)

{body.rstrip()}

## Renders

{gallery}

MIT licensed (see `LICENSE`). Not affiliated with or endorsed by Seeed Studio or NVIDIA.
'''

out = R / 'exports' / f'{name}.zip'
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr(f'{name}/INSTRUCTIONS.md', doc)
    z.write(R / 'LICENSE', f'{name}/LICENSE')
    z.write(R / 'docs/BOM.csv', f'{name}/BOM.csv')
    for p in parts:
        z.write(R / 'exports' / f'{p}.stl', f'{name}/stl/{p}.stl')
    for k in RENDERS:
        z.write(R / 'preview' / f'{k}.png', f'{name}/renders/{k}.png')
print(f'Wrote {out.relative_to(R)}: {len(parts)} STL, {len(RENDERS)} renders, {out.stat().st_size / 1e6:.1f} MB')

# Release notes for the GitHub release. It stays a pre-release until a printed unit has been fit-checked.
tested = json.loads((R / 'exports/review-validation.json').read_text()).get('physical_fit_verified') is True
status = ('**Status: fit-checked.** A printed unit has been assembled on the real board.' if tested else
          '**Status: fit-check prototype.** Every part and clearance is checked in CAD only. Nothing has been printed or '
          'test-fitted yet, so print the test parts (P9, P11–P14) first.')
(R / 'exports/release-notes.md').write_text(f'''Print package for the J501 AGX Orin enclosure, Rev {rev}.

**Download `{name}.zip`.** It contains:
- `stl/`: all {len(parts)} printable parts, in millimetres
- `INSTRUCTIONS.md`: which parts to print, hardware to buy, and assembly steps
- `BOM.csv`: full bill of materials with dimensions
- `renders/`: {len(RENDERS)} views of the assembly, drive trays, tie-down and service access

{status}

You need a [Seeed reServer Industrial J501 carrier](https://www.seeedstudio.com/reServer-Industrial-J501-Carrier-board-for-Jetson-AGX-Orin-p-5950.html), a Jetson AGX Orin module and a cooler. 3MF (Bambu Studio) and STEP files are in the repository's `exports/` folder.
''')
(R / 'exports/release-prerelease').write_text('false' if tested else 'true')
