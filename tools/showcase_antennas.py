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
          'tools/showcase-antenna-reference.json', 'tools/showcase-cellular-reference.json')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError('expected finite mm number')
    return float(value)


def mounts(parameters):
    """Mirror hardware.antenna_bulkheads' washer .5 + nut 2 stack about W/2.

    Nut faces are X=-2.5 / W+2.5, not the wall or exposed thread tips.
    Threads/receptacle engagement are deliberately omitted: this is no fit check.
    """
    if parameters.get('units') != 'mm':
        raise ValueError('expected mm')
    enclosure = parameters['enclosure']
    width = number(enclosure['width'])
    if width <= 0:
        raise ValueError('expected positive enclosure width')
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
        left = expected_side == 'left'
        result.append({'label': q['label'], 'origin_mm': [-2.5 if left else width + 2.5, y, z],
                       'outward_axis': [-1 if left else 1, 0, 0], 'up_axis': [0, 0, 1]})
    if len({tuple(q['origin_mm']) for q in result}) != 4:
        raise ValueError('duplicate connector centres')
    return sorted(result, key=lambda q: q['label'])


def mesh(origin, kind='wifi'):
    """One closed swept tube, authored here, not tessellated from vendor CAD.

    Wi-Fi local u points outward (-X), v points -Y, w points +Z.
    Cellular is rotated 180 degrees about Z: u=+X, v=+Y, w=+Z;
    this is a proper rotation (determinant +1), not a winding-reversing mirror.
    A 5.3 mm bend, shoulder taper and flat cap are illustrative choices. Housing
    bottom w=-3.5, top=22.1; connector radius3.9 adds .4 below the housing.
    """
    if kind not in ('wifi', 'cellular'):
        raise ValueError('unknown visual reference')
    cellular = kind == 'cellular'
    coupling, bend = (8.4, 4.7) if cellular else (8.1, 5.3)
    base_radius, coupling_radius = (3.9, 4.) if cellular else (3.5, 3.9)
    rings = [(0., 0., 0., coupling_radius), (coupling - .3, 0., 0., coupling_radius),
             (coupling, 0., 0., base_radius)] if cellular else [
                 (0., 0., 0., 3.9), (7.8, 0., 0., 3.9), (8.1, 0., 0., 3.5)]
    for i in range(1, 13):
        angle = math.pi / 2 * i / 12
        rings.append((coupling + bend * math.sin(angle), bend * (1 - math.cos(angle)), angle, base_radius))
    rings += ([(13.1, 7., math.pi / 2, 3.9), (13.1, 40.3, math.pi / 2, 3.9),
               (13.1, 40.8, math.pi / 2, 3.4)] if cellular else [
                  (13.4, 7., math.pi / 2, 3.7), (13.4, 21.6, math.pi / 2, 3.7),
                  (13.4, 22.1, math.pi / 2, 3.2)])
    vertices = []
    segments = 32
    for u, w, angle, radius in rings:
        for i in range(segments):
            p = 2 * math.pi * i / segments
            du = -radius * math.sin(p) * math.sin(angle)
            v = radius * math.cos(p)
            dw = radius * math.sin(p) * math.cos(angle)
            if cellular:
                vertices.append((origin[0] + u + du, origin[1] + v, origin[2] + w + dw))
            else:
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
    cellular_reference = json.loads((root / INPUTS[4]).read_text())
    manifest = {
        'schema': 'j501-original-showcase-context-v2', 'units': 'mm',
        'coordinate_frame': 'existing enclosure assembly; no lid/part transforms changed',
        'source_sha256': sources, 'recipe_revision_sha256': sources[INPUTS[2]],
        'mechanical_reference': reference, 'cellular_reference': cellular_reference,
        'optional': True, 'display_only': True,
        'printable': False, 'purchase_bom': False, 'physical_fit_verified': False,
        'rf_qualified': False,
        'seating_assumption': 'coupling planes on visual nut outer faces, X=-2.5 / W+2.5; washer .5 + nut 2 from cad/hardware.py; no mating thread detail',
        'representation': 'original closed 32-sided swept tubes; per-part illustrative elbow/shoulder/flat tip; black color including coupling; no markings, threads, pins, internals or vendor mesh',
        'limits': ['not manufacturing geometry', 'not a connector fit or collision qualification',
                   'not radio, band, ground-plane, pigtail or MIMO selection',
                   'bulkhead sites unchanged; fitted lid stays in existing position',
                   'cellular reference is older penta-band 800-2200 MHz, not LTE/5G or installed-modem qualification',
                   '25.6 mm housing datum is not the complete generated envelope'],
        'parts': [],
    }
    result = {}
    for mount in mounts(parameters):
        name = mount['label'].lower().replace(' ', '_') + '_antenna'
        cellular = mount['label'].startswith('CELL ')
        vertices, faces = mesh(mount['origin_mm'], 'cellular' if cellular else 'wifi')
        filename = name + '.stl'
        data = stl(vertices, faces)
        result[filename] = data
        bounds = [[min(p[i] for p in vertices) for i in range(3)],
                  [max(p[i] for p in vertices) for i in range(3)]]
        manifest['parts'].append({'name': name, 'file': filename, 'sha256': sha(data),
                                  'bounds_mm': bounds, 'triangles': len(faces),
                                  'color': [0.06, 0.065, 0.075], 'category': 'context',
                                  'visible': True, 'optional': True, 'display_only': True,
                                  'reference_key': 'cellular_reference' if cellular else 'mechanical_reference',
                                  'representation': ('original circularized 8 mm coupling, illustrative 4.7 mm bend and flat tip; no hex corners/threads/contact/markings; approximately 17x8x44.8 mm generated envelope, separate from vendor tolerances' if cellular else 'unchanged original Wi-Fi approximation; approximately 17.1x7.8x26 mm envelope'),
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
