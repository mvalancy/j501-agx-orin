"""Build the print release with `cad-agent release`, plus the GitHub release notes.

    python tools/package_release.py      # writes release/j501-agx-rev<release>/ and release/j501-agx-rev<release>.zip

The release is what someone printing the enclosure needs, not the review package:
- `index.html`: a page with every printed part, its thumbnail, quantity, orientation, supports, and the slicer's
  grams and time;
- the recommended print settings;
- the assembly guide and the hardware to buy;
- the STEP, STL and 3MF files, and the source that builds them.

The parts, notes and hardware are in `cad-agent.yaml` under `release:`. Simulation results and render galleries
stay in the repository.
"""
from pathlib import Path
import json, subprocess, sys

R = Path(__file__).resolve().parents[1]
P = json.loads((R / 'cad/parameters.json').read_text())
rel = P.get('release', P['revision'].split('-')[0])
name = f'j501-agx-rev{rel}'
out = R / 'release' / name
subprocess.run([sys.executable, '-m', 'cadagent.cli', 'release', '--project', str(R), '--out', str(out), '--revision', rel],
               check=True)
zip_ = out.parent / f'{name}.zip'
assert (out / 'index.html').is_file() and zip_.is_file(), 'cad-agent release wrote no page or zip'
m = json.loads((out / 'manifest.json').read_text())
parts = m.get('parts') or []
print(f'Wrote {zip_.relative_to(R)}: {len(parts)} parts, {zip_.stat().st_size / 1e6:.1f} MB')

# Release notes for the GitHub release. It stays a pre-release until a printed unit has been fit-checked.
tested = json.loads((R / 'exports/review-validation.json').read_text()).get('physical_fit_verified') is True
status = ('**Status: fit-checked.** A printed unit has been assembled on the real board.' if tested else
          '**Status: fit-check prototype.** Every part and clearance is checked in CAD only; a printed unit has not '
          'been fit-checked yet. Print the test parts in the page\'s "Test prints" group first, in your filament.')
fix = P.get('release_note', '')
(R / 'exports/release-notes.md').write_text(f'''Print release for the J501 AGX Orin enclosure, release {rel} (design revision {P['revision']}).

**Download `{name}.zip` and open `index.html`.** The page lists every printed part with a picture, how many to print,
the orientation and supports, and the slicer's grams and time with the recommended Bambu Studio settings. It links each
part's STEP, STL and 3MF, the assembly guide and the hardware to buy. The zip also has the source that builds the parts
(`source/`).

{status}

{fix}

You need a [Seeed reServer Industrial J501 carrier](https://www.seeedstudio.com/reServer-Industrial-J501-Carrier-board-for-Jetson-AGX-Orin-p-5950.html), a Jetson AGX Orin module and a cooler.
Simulation results, renders and the full review are in the repository: https://github.com/mvalancy/j501-agx-orin
''')
(R / 'exports/release-prerelease').write_text('false' if tested else 'true')
