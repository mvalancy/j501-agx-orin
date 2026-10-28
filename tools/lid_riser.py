"""One-off lid riser (recovery part, not in the release print set).

Lifts an already printed cover by RISE mm so a taller cooler fits under it, e.g. a Rev 0.8 cover (sized for the
34 mm WS-RDN-601) over the reComputer mini J501 heatsink (G48R + 92 x 15 mm fan, 48.3 mm). The riser is the
cover's wall ring with the cover's joint underneath (rebates over the base tongues, ledges that hold the I/O panel
tops) and the base's joint on top (tongues into the cover's rebates), screw columns under the cover's columns and
exhaust slots. The lid screws get longer by RISE.

    .venv/bin/python tools/lid_riser.py --rise 18 [--slice]

Writes build/print/lid-riser-<rise>mm.{step,stl,3mf} (+ sliced .gcode.3mf with --slice) and a JSON note.
"""
import argparse, json, sys, zipfile
from pathlib import Path
R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / 'cad'))
import build as b  # noqa: E402

INSERT_LENGTH = 10.0  # M3 x 10 heat-set inserts in the base columns (docs/BOM.csv H1)
SCREW_LENGTHS = (16, 20, 25, 30, 35, 40, 45)


def riser(rise):
    e = b.e; z0, z1 = b.BH, b.BH + rise; T, W, Y0, Y1, D = b.T, b.W, b.Y0, b.Y1, b.D
    s = b.outer_block(z0, z1, e['split_chamfer'], e['split_chamfer'])
    s = b.subtract(s, [b.rrect(T, Y0 + T, W - T, Y1 - T, e['cavity_corner_radius'], z0 - 1, rise + 2)])
    # the cover's ledges: they keep the I/O panels down
    ledges = [b.prism_x([(Y0 + T - .01, z0), (b.FY + b.PT + b.PC, z0), (b.FY + b.PT + b.PC, z0 + 2), (Y0 + T - .01, z0 + 4)], T - .01, W - 2 * T + .02),
              b.prism_x([(Y1 - T + .01, z0), (b.RY - b.PC, z0), (b.RY - b.PC, z0 + 2), (Y1 - T + .01, z0 + 4)], T - .01, W - 2 * T + .02)]
    cols = [b.buttressed_column(x, y, z0, rise) for x, y in e['lid_screw_centers']]
    t0, t1, th = e['joint_tongue']; ty0, ty1 = Y0 + 3.5, Y1 - 3.5
    tongues = [b.box(t0, ty0, z1 - .01, t1 - t0, ty1 - ty0, th + .01), b.box(W - t1, ty0, z1 - .01, t1 - t0, ty1 - ty0, th + .01)]
    s = b.combine([s] + ledges + cols + tongues)
    r0, r1, rh = e['joint_rebate']
    cuts = [b.box(r0, Y0 + 3.2, z0 - 1, r1 - r0, D - 6.4, rh + 1), b.box(W - r1, Y0 + 3.2, z0 - 1, r1 - r0, D - 6.4, rh + 1)]
    cuts += [b.cyl(x, y, z0 - 1, e['lid_screw_clearance'] / 2, rise + th + 2) for x, y in e['lid_screw_centers']]
    vz0, vz1 = z0 + rh + 2, z1 - 3
    if vz1 - vz0 >= e['vent_width'] + 2:  # exhaust slots: the cooler blows its hot air out at the front and back
        for y in b.vent_positions(*e['side_vent_y']):
            cuts += [b.slot('x', -1, T + 2, y, vz0, vz1, e['vent_width']), b.slot('x', W - T - 1, T + 2, y, vz0, vz1, e['vent_width'])]
        for x in b.vent_positions(*e['panel_vent_x']):
            cuts += [b.slot('y', Y0 - 1, T + 2, x, vz0, vz1, e['vent_width']), b.slot('y', Y1 - T - 1, T + 2, x, vz0, vz1, e['vent_width'])]
    return b.subtract(s, cuts)


def screw(rise):
    # Same head seat as the cover; the thread has to reach the insert and not bottom out in the pilot hole.
    head = b.e['lid_screw_head_z'] + rise; insert_top = b.BH; hole_bottom = b.BH - b.e['lid_insert_depth']
    ok = [(L, round(insert_top - (head - L), 2)) for L in SCREW_LENGTHS if head - L > hole_bottom + .5 and insert_top - (head - L) >= 5]
    L, eng = max(ok, key=lambda q: (min(q[1], INSERT_LENGTH), -q[0]))
    return {'screw': f'M3 x {L} ISO 4762 socket head (x4)', 'length_mm': L, 'thread_in_insert_mm': min(eng, INSERT_LENGTH)}


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--rise', type=float, default=18.0)
    ap.add_argument('--slice', action='store_true')
    a = ap.parse_args()
    import cadquery as cq, trimesh
    s = riser(a.rise)
    assert s.isValid() and len(s.Solids()) == 1, 'riser is not one valid solid'
    out = R / 'build' / 'print'; out.mkdir(parents=True, exist_ok=True); stem = out / f'lid-riser-{a.rise:g}mm'
    cq.exporters.export(s, str(stem.with_suffix('.step')))
    cq.exporters.export(b.flat(s), str(stem.with_suffix('.stl')), tolerance=.05, angularTolerance=.12)
    m = trimesh.load_mesh(stem.with_suffix('.stl')); assert m.is_watertight
    sys.path.insert(0, str(R / 'tools'))
    from export_3mf import CT, RELS, model  # noqa: E402
    with zipfile.ZipFile(stem.with_suffix('.3mf'), 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', CT); z.writestr('_rels/.rels', RELS); z.writestr('3D/3dmodel.model', model(m, stem.name))
    # Rev 0.8 cover (release rev0.8): intake ring bottom 77.26, roof ribs down to 81.5 (enclosure datum)
    fan_top = b.COOLER_SEAT + b.c['size'][2]
    note = {'part': stem.name, 'rise_mm': a.rise, 'volume_cm3': round(s.Volume() / 1000, 2), 'print_bounds_mm': [round(float(v), 1) for v in m.extents],
            'print_orientation': 'as built: wide face with the rebates down on the bed, tongues up', **screw(a.rise),
            'rev08_ring_bottom_z_after_rise': round(77.26 + a.rise, 2), 'rev08_rib_bottom_z_after_rise': round(81.5 + a.rise, 2),
            'fan_top_z': round(fan_top, 2), 'ring_to_fan_mm': round(77.26 + a.rise - fan_top, 2)}
    if a.slice:
        from cadagent.slicer import slice_part
        r = slice_part(stem.with_suffix('.3mf'), workdir=R / 'build' / 'slicer' / stem.name)
        note.update(grams=r.get('grams'), minutes=r.get('minutes'))
        sliced = R / 'build' / 'slicer' / stem.name / 'out' / 'sliced.3mf'
        if sliced.exists(): (out / f'{stem.name}-sliced-P1S-PLA.gcode.3mf').write_bytes(sliced.read_bytes())
    stem.with_suffix('.json').write_text(json.dumps(note, indent=2) + '\n')
    print(json.dumps(note, indent=2))
