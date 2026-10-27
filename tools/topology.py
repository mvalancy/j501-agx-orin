"""Topology optimisation of the base floor and the lid roof (cadagent.topopt, pyMOTO): where does the material carry
load, and where can it go (to save filament, or to become vents)?

  floor  robot mounting: the base held at its four mounting ears, 1.5 kg of carrier, module and cooler at 10 g
         (150 N) pressing down through the board posts and cooler columns, plus 5 g (75 N) sideways
  roof   300 N spread over the top of the lid (someone leaning on it, or a load stacked on it), the lid held where
         it sits on the base walls

Everything that has a job (posts, columns, ribs, feet, stacking columns, wall band, chimney, plug drops) is kept
solid; the optimiser only decides the rest. Writes exports/topology/<study>.json, .stl, preview/topology-<study>.png
and .mp4.
"""
from pathlib import Path
import sys, json, argparse
R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / 'cad'))
import build as b
import numpy as np
import trimesh
from cadagent.topopt import TopOpt, hex_vents

e, S = b.e, b.S


def disc(x, y, r, z0, z1):
    return trimesh.creation.cylinder(radius=r, height=z1 - z0, sections=32,
                                     transform=trimesh.transformations.translation_matrix((x, y, (z0 + z1) / 2)))


def slab(x0, y0, z0, x1, y1, z1):
    lo, hi = np.array((x0, y0, z0)), np.array((x1, y1, z1))
    return trimesh.creation.box(extents=hi - lo, transform=trimesh.transformations.translation_matrix((lo + hi) / 2))


def floor_study(voxel):
    W, Y0, Y1, T, F = b.W, b.Y0, b.Y1, b.T, b.F
    t = TopOpt((0, Y0, 0), (W, Y1, F), voxel_mm=voxel, E_mpa=2700)
    t.design()
    band = 8.0                                      # walls stand on this band
    for s in (slab(0, Y0, 0, band, Y1, F), slab(W - band, Y0, 0, W, Y1, F), slab(0, Y0, 0, W, Y0 + band, F), slab(0, Y1 - band, 0, W, Y1, F)):
        t.keep(s)
    for x, y in b.board_holes():
        t.keep(disc(x, y, e['board_post_diameter'] / 2 + e['support_floor_flare'] + 1, 0, F))
    for x, y in b.heatsink_holes():
        t.keep(disc(x, y, e['heatsink_column_diameter'] / 2 + e['support_floor_flare'] + 1, 0, F))
    for x, y in e['foot_pockets']:
        t.keep(disc(x, y, e['foot_pocket'][0] / 2 + 3, 0, F))
    for x, y in S['standoff_centers'] + e['lid_screw_centers']:
        t.keep(disc(x, y, 9, 0, F))
    x0, y0, x1, y1 = S['chimney']
    t.keep(slab(x0 - 4, y0 - 4, 0, x1 + 4, y1 + 4, F))
    for _, s in b.envelope_boxes('plug_drop'):
        bb = s.BoundingBox()
        t.keep(slab(bb.xmin - 4, bb.ymin - 4, 0, bb.xmax + 4, bb.ymax + 4, F))
    # supports: the four mounting ears sit on the front and rear edges
    for x in e['mount_ear_x']:
        w = e['mount_ear_width'] / 2
        t.fix((x - w, Y0, 0), (x + w, Y0 + voxel, F))
        t.fix((x - w, Y1 - voxel, 0), (x + w, Y1, F))
    pts = b.board_holes() + b.heatsink_holes()
    for x, y in pts:
        r = 4.0
        t.load((x - r, y - r, F - 0.01), (x + r, y + r, F + 0.01), (0, 75.0 / len(pts), -150.0 / len(pts)))
    return t


def roof_study(voxel):
    """Lid roof: ribs may grow under the roof between the cooler clearance and the roof; the intake ring is kept and
    its inside left open for air."""
    W, Y0, Y1, H = b.W, b.Y0, b.Y1, b.H
    cool_top = b.COOLER_SEAT + b.c['size'][2]
    z0 = H - voxel * int((H - cool_top - 2.0) // voxel)       # whole voxels, top layer at the roof surface
    t = TopOpt((0, Y0, z0), (W, Y1, H), voxel_mm=voxel, E_mpa=2700)
    t.design()
    t.keep(slab(0, Y0, H - voxel, W, Y1, H))                     # the roof skin carries the spread load
    band = 6.0
    for s in (slab(0, Y0, z0, band, Y1, H), slab(W - band, Y0, z0, W, Y1, H), slab(0, Y0, z0, W, Y0 + band, H), slab(0, Y1 - band, z0, W, Y1, H)):
        t.keep(s)
    for x, y in e['lid_screw_centers']:
        t.keep(disc(x, y, e['lid_column_diameter'] / 2 + 2, z0, H))
    d = e.get('fan_duct')
    if d:
        cx, cy = b.c['center_in_pcb'][0] + b.M, b.c['center_in_pcb'][1] + b.M
        ri = d['inner_diameter'] / 2
        t.keep(disc(cx, cy, ri + d['wall'], z0, H))
        t.void(disc(cx, cy, ri, z0 - 1, H - voxel))
    for lo, hi in (((0, Y0, z0), (W, Y0 + band, z0 + 0.01)), ((0, Y1 - band, z0), (W, Y1, z0 + 0.01)),
                   ((0, Y0, z0), (band, Y1, z0 + 0.01)), ((W - band, Y0, z0), (W, Y1, z0 + 0.01))):
        t.fix(lo, hi)
    t.load((band, Y0 + band, H - 0.01), (W - band, Y1 - band, H + 0.01), (0, 0, -300.0))
    return t


def _seg_dist(p, a, b):
    p, a, b = (np.asarray(v, float) for v in (p, a, b))
    t = np.clip(np.dot(p - a, b - a) / np.dot(b - a, b - a), 0, 1)
    return float(np.linalg.norm(p - (a + t * (b - a))))


def write_floor_vents(t, out):
    """Hex vents where the floor carries no load (density < 0.3 everywhere in the cell), clear of the floor ribs.
    cad/build.py cuts them when enclosure.floor_vents is set."""
    v = e['floor_vents']
    pts = hex_vents(t, threshold=v['threshold'], across_flats=v['across_flats'], web=v['web'])
    hs, bp = b.heatsink_holes(), b.board_holes()
    ribs = [(hs[i], hs[j]) for i, j in ((0, 1), (1, 3), (3, 2), (2, 0))] + [(hs[i], bp[i]) for i in range(4)]
    clear = v['across_flats'] / np.sqrt(3) + e['floor_rib'][0] / 2 + v['rib_clearance']
    pts = [q for q in pts if all(_seg_dist(q, a, c) > clear for a, c in ribs)]
    pitch = v['across_flats'] + v['web']
    for _ in range(2):   # drop stragglers: a vent needs at least two neighbours, so the openings read as panels
        pts = [q for q in pts if sum(0 < np.hypot(q[0] - r[0], q[1] - r[1]) < 1.1 * pitch for r in pts) >= 2]
    (out / 'floor-vents.json').write_text(json.dumps({'centres': pts, 'source': 'tools/topology.py floor', **v}, indent=1) + '\n')
    print('floor vents', len(pts), flush=True)


STUDIES = {'floor': (floor_study, 0.35, 6.0, '+z',
                     'Base floor, robot mounting: held at the 4 ears; 150 N down + 75 N sideways through the posts and columns'),
           'roof': (roof_study, 0.15, 5.0, '-z', 'Lid roof: 300 N spread over the top; held where the lid sits on the walls')}

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('studies', nargs='*', default=list(STUDIES))
    ap.add_argument('--voxel', type=float, default=2.0)
    ap.add_argument('--maxit', type=int, default=60)
    a = ap.parse_args()
    out = R / 'exports/topology'
    out.mkdir(parents=True, exist_ok=True)
    for name in a.studies:
        make, vf, filt, overhang, title = STUDIES[name]
        t = make(a.voxel)
        res = t.run(volfrac=vf, filter_mm=filt, overhang=overhang, maxit=a.maxit)
        res['study'] = title
        (out / f'{name}.json').write_text(json.dumps(res, indent=2) + '\n')
        t.export_stl(out / f'{name}.stl')
        np.save(out / f'{name}-density.npy', t.density.astype(np.float32))
        t.render(R / f'preview/topology-{name}.png', title=f'Topology optimisation: {name}', view=(-30, 55))
        t.animate(R / f'preview/topology-{name}.mp4', view=(-30, 55))
        if name == 'floor':
            write_floor_vents(t, out)
        print(name, json.dumps({k: res[k] for k in ('volfrac_result', 'compliance_nmm', 'iterations', 'grey_fraction')}), flush=True)
