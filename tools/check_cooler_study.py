#!/usr/bin/env python3
"""Check the committed cooler fit study without vendor files or a CAD installation (runs in CI).

Catches stale evidence (source and artifact hashes), a lost negative control (the printed Rev 0.8 lid must still hit
the cooler with no riser) and a release lid that no longer clears the cooler with the fan-position uncertainty.
tools/cooler_fit_review.py does the STEP readback and the exact intersections; this only checks what it recorded.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check():
    report = json.loads((ROOT / 'exports/cooler-study/fit-review.json').read_text())
    cooler = json.loads((ROOT / 'cad/parameters.json').read_text())['cooler']
    errors = []

    def require(condition, message):
        if not condition:
            errors.append(message)

    for field in ('source_sha256', 'artifact_sha256'):
        hashes = report.get(field, {})
        require(bool(hashes), f'missing {field}')
        for relative, digest in hashes.items():
            path = (ROOT / relative).resolve()
            require(ROOT in path.parents and path.is_file(), f'missing/unsafe {relative}')
            if ROOT in path.parents and path.is_file():
                require(hashlib.sha256(path.read_bytes()).hexdigest() == digest, f'stale {relative} (rerun tools/cooler_fit_review.py)')

    require(report['study_valid'] is True, 'component STEP readback failed')
    for key in ('production_ready', 'physical_fit_verified'):
        require(report[key] is False, f'unsupported approval: {key}')
    parts = report['parts']
    require(parts['heat_pipes']['solid_count'] == cooler['heatsink']['heat_pipes'], 'heat-pipe count')
    for name, height in (('spreader', None), ('fan_frame', cooler['fan']['thickness']), ('spacers', cooler['standoffs']['height'])):
        if height is not None:
            bb = parts[name]['bounds_mm']
            require(abs(bb[5] - bb[2] - height) < 0.01, f'{name} height')
    for name, part in parts.items():
        require(part['valid'] and part['volume_mm3'] > 0, f'invalid STEP {name}')

    require(report['fan_xy_uncertainty_mm'] >= 3.0, 'fan-position uncertainty dropped below 3 mm')
    rel = report['release_cover']
    for variant, res in rel.items():
        for name, r in res.items():
            for case in ('nominal', 'worst_shift'):
                require(r[case]['intersection_mm3'] < 1e-6, f'release lid hits the {name} ({variant}, {case})')
    require(rel['modelled_frame']['fan']['worst_shift']['minimum_gap_mm'] >= cooler['minimum_fan_clearance'],
            'release lid closer than minimum_fan_clearance to the moved fan')
    require(rel['frame_95mm']['fan']['worst_shift']['minimum_gap_mm'] >= 0.5, 'release lid within 0.5 mm of a moved 95 mm fan')
    require(report['release_cover_fit_pass'] is True, 'release_cover_fit_pass is false')

    trials = {row['lid_lift_mm']: row for row in report['rev08_cover_trials']}
    require(trials[0.0]['fan']['nominal']['intersection_mm3'] > 100, 'lost negative control: the Rev 0.8 lid no longer hits the cooler')
    riser = trials[report['riser']['rise_mm']]
    for name in ('fan', 'heat_sink'):
        require(riser[name]['worst_shift']['intersection_mm3'] < 1e-6, f"Rev 0.8 lid on the {report['riser']['rise_mm']:g} mm riser hits the {name}")
    require(len(report['unresolved']) >= 3, 'lost the unresolved-dimension register')

    for error in errors:
        print('FAIL:', error)
    print(f"Cooler study: {len(parts)} components, hashes, release-lid clearance with ±{report['fan_xy_uncertainty_mm']:g} mm fan position, "
          f"Rev 0.8 collision control and riser: {'FAIL' if errors else 'PASS'}")
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(check())
