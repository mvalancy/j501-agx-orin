#!/usr/bin/env python3
"""Original optional display context; standard library only, never a print export.

python3 tools/showcase_antennas.py         # regenerate exports/showcase-antennas
python3 tools/showcase_antennas.py --check # byte-compare committed evidence
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path('exports/showcase-antennas')
INPUTS = ('cad/parameters.json', 'cad/hardware.py', 'tools/showcase_antennas.py',
          'tools/showcase-antenna-reference.json')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError('expected finite mm number')
    return float(value)


def mounts(parameters):
    """Mirror hardware.antenna_bulkheads' washer .5 + nut 2 stack about W/2.

    X=-2.5 is the visual nut face, not the wall or the exposed thread tip (-7).
    Threads/receptacle engagement are deliberately omitted: this is no fit check.
    """
    if parameters.get('units') != 'mm':
        raise ValueError('expected mm')
    enclosure = parameters['enclosure']
    number(enclosure['width'])
    a = enclosure['antenna_bulkheads']
    z = number(a['z'])
    positions = a['positions']
    labels = [q['label'] for q in positions]
    if len(labels) != 4 or set(labels) != {'WIFI 1', 'WIFI 2', 'CELL 1', 'CELL 2'}:
        raise ValueError('expected four unique existing Wi-Fi/cellular sites')
    result = []
    for q in positions:
        y = number(q['y'])
        expected_side = 'left' if q['label'].startswith('WIFI ') else 'right'
        if q['side'] != expected_side:
            raise ValueError('unexpected connector side')
        if expected_side == 'left':
            result.append({'label': q['label'], 'origin_mm': [-2.5, y, z],
                           'outward_axis': [-1, 0, 0], 'up_axis': [0, 0, 1]})
    if result[0]['origin_mm'] == result[1]['origin_mm']:
        raise ValueError('duplicate Wi-Fi centres')
    return sorted(result, key=lambda q: q['label'])


def mesh(origin):
    """One closed swept tube, authored here, not tessellated from vendor CAD.

    Local u points outward (-X), v points -Y (right-handed), w points +Z.
    A 5.3 mm bend, shoulder taper and flat cap are illustrative choices. Housing
    bottom w=-3.5, top=22.1; connector radius3.9 adds .4 below the housing.
    """
    rings = [(0., 0., 0., 3.9), (7.8, 0., 0., 3.9), (8.1, 0., 0., 3.5)]
    for i in range(1, 13):
        angle = math.pi / 2 * i / 12
        rings.append((8.1 + 5.3 * math.sin(angle), 5.3 * (1 - math.cos(angle)), angle, 3.5))
    rings += [(13.4, 7., math.pi / 2, 3.7), (13.4, 21.6, math.pi / 2, 3.7),
              (13.4, 22.1, math.pi / 2, 3.2)]
    vertices = []
    segments = 32
    for u, w, angle, radius in rings:
        for i in range(segments):
            p = 2 * math.pi * i / segments
            du = -radius * math.sin(p) * math.sin(angle)
            v = radius * math.cos(p)
            dw = radius * math.sin(p) * math.cos(angle)
            vertices.append((origin[0] - u - du, origin[1] - v, origin[2] + w + dw))
    faces = []
    for j in range(len(rings) - 1):
        for i in range(segments):
            a, b = j * segments + i, j * segments + (i + 1) % segments
            c, d = a + segments, b + segments
            faces += [(a, b, c), (b, d, c)]
    for i in range(1, segments - 1):
        faces += [(0, i + 1, i)]
        k = (len(rings) - 1) * segments
        faces += [(k, k + i, k + i + 1)]
    # Round to binary STL precision before reporting bounds/checking geometry.
    vertices = [struct.unpack('<3f', struct.pack('<3f', *p)) for p in vertices]
    return vertices, faces


def stl(vertices, faces):
    data = bytearray(b'Original render-only antenna approximation; millimetres'.ljust(80, b' '))
    data.extend(struct.pack('<I', len(faces)))
    for face in faces:
        a, b, c = [vertices[i] for i in face]
        u, v = [b[i] - a[i] for i in range(3)], [c[i] - a[i] for i in range(3)]
        n = (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
        length = math.sqrt(sum(x*x for x in n))
        if length <= 1e-9:
            raise ValueError('degenerate triangle')
        data.extend(struct.pack('<12fH', *(x/length for x in n), *a, *b, *c, 0))
    return bytes(data)


def artifacts(root=ROOT):
    parameters = json.loads((root / INPUTS[0]).read_text())
    sources = {p: sha((root / p).read_bytes()) for p in INPUTS}
    reference = json.loads((root / INPUTS[3]).read_text())
    manifest = {
        'schema': 'j501-original-showcase-context-v1', 'units': 'mm',
        'coordinate_frame': 'existing enclosure assembly; no lid/part transforms changed',
        'source_sha256': sources, 'recipe_revision_sha256': sources[INPUTS[2]],
        'mechanical_reference': reference, 'optional': True, 'display_only': True,
        'printable': False, 'purchase_bom': False, 'physical_fit_verified': False,
        'rf_qualified': False,
        'seating_assumption': 'coupling plane on visual nut outer face, X=-2.5; washer .5 + nut 2 mirrored from cad/hardware.py; no mating thread detail',
        'representation': 'original closed 32-sided swept tube; illustrative elbow/shoulder/flat tip; black color including coupling; no markings, threads, pins, internals or vendor mesh',
        'limits': ['not manufacturing geometry', 'not a connector fit or collision qualification',
                   'not radio, band, ground-plane, pigtail or MIMO selection',
                   'CELL sites unchanged; fitted lid stays in existing position',
                   '25.6 mm housing datum is not the complete generated envelope'],
        'parts': [],
    }
    result = {}
    for mount in mounts(parameters):
        name = mount['label'].lower().replace(' ', '_') + '_antenna'
        vertices, faces = mesh(mount['origin_mm'])
        filename = name + '.stl'
        data = stl(vertices, faces)
        result[filename] = data
        bounds = [[min(p[i] for p in vertices) for i in range(3)],
                  [max(p[i] for p in vertices) for i in range(3)]]
        manifest['parts'].append({'name': name, 'file': filename, 'sha256': sha(data),
                                  'bounds_mm': bounds, 'triangles': len(faces),
                                  'color': [0.06, 0.065, 0.075], 'category': 'context',
                                  'visible': True, 'optional': True, 'display_only': True,
                                  'mount': mount})
    result['manifest.json'] = (json.dumps(manifest, indent=2, allow_nan=False) + '\n').encode()
    return result


def check(root=ROOT):
    expected = artifacts(root)
    output = root / OUTPUT
    if not output.is_dir() or {p.name for p in output.iterdir() if p.suffix in ('.stl', '.json')} != set(expected):
        raise ValueError('missing or unexpected showcase artifact')
    for name, data in expected.items():
        if (output / name).read_bytes() != data:
            raise ValueError(f'stale showcase artifact: {name}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if args.check:
        check()
        print('Showcase antenna bytes, provenance and transforms: PASS')
    else:
        output = ROOT / OUTPUT
        output.mkdir(parents=True, exist_ok=True)
        for name, data in artifacts().items():
            (output / name).write_bytes(data)
        print(f'Wrote optional display context to {OUTPUT}')
