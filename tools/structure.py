"""Structural load cases on the printed shells (cadagent.fea: gmsh + scikit-fem, quadratic tetrahedra).

  lid_press   300 N spread over the lid top (someone leaning on it, a load on top), the lid resting on the base rim;
              the roof and the flush fan grille are reported separately (the grille must stay clear of the fan)
  base_mount  robot mounting: base_mount held at its four ear slots; 1.5 kg of carrier, module and cooler at 10 g
              (150 N) down through the board-post and cooler-column landings, plus 5 g (75 N) sideways

Material: PLA with the layer-direction (weakest) strength. Writes exports/structure/<case>.json and
preview/structure-<case>.png / .mp4 (overload animation: load ramped past the first failure).
"""
from pathlib import Path
import sys, json, argparse, time
R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / 'cad'))
import build as b
import cadquery as cq
from cadagent.fea import Study, MATERIALS, plane_at, cylinder_at, any_of


def defeature():
    # Sub-millimetre details (debossed text, the 0.075 mm insert seat step, lead-in cones) do not change the strength
    # but their sliver faces break the tetrahedral mesher: build the shells without them for FEA.
    nothing = lambda *a, **k: b.box(-500, -500, -500, .01, .01, .01)
    b.label = b.label_x = b.insert_seat = b.cone = nothing

    # Tangent radius fillets leave sliver faces where they meet the floor; a 45-degree chamfer of the same size has
    # none and concentrates stress a little more (conservative).
    def chamfer_ring(x, y, z, r, f, down=False):
        if down:
            return cq.Solid.makeCone(r, r + f, f, cq.Vector(x, y, z - f), cq.Vector(0, 0, 1))
        return cq.Solid.makeCone(r + f, r, f, cq.Vector(x, y, z), cq.Vector(0, 0, 1))
    b.fillet_ring = chamfer_ring


def lid_press(mesh):
    st = Study(b.cover(), MATERIALS['pla'], mesh_mm=mesh, name='lid')
    st.fix(plane_at(2, b.BH))
    st.force(lambda f: f.kind == 'Plane' and abs(f.bbox[2] - b.H) < 0.05 and abs(f.bbox[5] - b.H) < 0.05, (0, 0, -300))
    return st


def base_mount(mesh):
    st = Study(b.base(True), MATERIALS['pla'], mesh_mm=mesh, name='base_mount')
    t = b.e['mount_ear_thickness']
    slots = b.mount_slot_centers()
    # the slot walls, where the bolts bear
    st.fix(lambda f: f.kind != 'Plane' and f.bbox[5] <= t + 0.01 and f.bbox[2] >= -0.01 and
           any(abs(f.center[0] - x) < 8 and abs(f.center[1] - y) < 5 for x, y in slots))
    land = b.Z
    pads = b.board_holes() + b.heatsink_holes()
    st.force(lambda f: f.kind == 'Plane' and abs(f.bbox[2] - land) < 0.05 and abs(f.bbox[5] - land) < 0.05 and
             any(abs(f.center[0] - x) < 6 and abs(f.center[1] - y) < 6 for x, y in pads), (0, 75, -150))
    return st


CASES = {'lid_press': lid_press, 'base_mount': base_mount}

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('cases', nargs='*', default=list(CASES))
    ap.add_argument('--mesh', type=float, default=3.0)
    ap.add_argument('--tag', default=b.P['revision'].split('-')[0], help='label for the outputs, e.g. 0.8')
    ap.add_argument('--no-video', action='store_true')
    a = ap.parse_args()
    out = R / 'exports/structure'
    out.mkdir(parents=True, exist_ok=True)
    defeature()
    for name in a.cases:
        t = time.time()
        st = CASES[name](a.mesh)
        res = st.solve()
        import numpy as np
        inner = ~st._touches_bc if (~st._touches_bc).any() else np.ones(len(st.vm_elem), bool)
        vm, cent = st.vm_elem[inner], st.points[st.tets].mean(axis=1)[inner]
        k = int(np.argmax(vm))
        # a single sharp corner makes a mesh-dependent spike: the 99th / 99.9th percentiles and the spike's position
        # tell a real overstress (many elements) from a notch (one element)
        res.update(case=name, revision=b.P['revision'], solve_minutes=round((time.time() - t) / 60, 1),
                   von_mises_p99_mpa=round(float(np.percentile(vm, 99)), 2), von_mises_p999_mpa=round(float(np.percentile(vm, 99.9)), 2),
                   peak_at_mm=[round(float(v), 1) for v in cent[k]],
                   safety_factor_p999=round(st.material.strength_mpa / float(np.percentile(vm, 99.9)), 2))
        g = b.e.get('fan_grille')
        if name == 'lid_press' and g:
            # the flush fan grille may flex more than the roof (it only has to stay clear of the fan): report both
            mag, P = np.linalg.norm(st.disp, axis=0), st.points
            cx, cy = b.fan_centre()
            grille = np.array([b.inside_outline(x, y, g['clearance']) for x, y in P[:, :2]]) & (P[:, 2] > b.H - b.RT - .1)
            res.update(grille_max_displacement_mm=round(float(mag[grille].max()), 4), roof_max_displacement_mm=round(float(mag[~grille].max()), 4),
                       fan_clearance_mm=round(b.H - g['thickness'] - b.FAN_TOP, 3))
        (out / f'{name}-{a.tag}.json').write_text(json.dumps(res, indent=2, default=float) + '\n')
        from cadagent import simviz
        label = {'lid_press': '300 N on the lid', 'base_mount': 'robot mounting, 10 g down + 5 g sideways'}[name]
        simviz.fea_view(st, R / f'preview/structure-{name}-{a.tag}.png',
                        title=f"Rev {a.tag}: {label}",
                        subtitle=f"PLA (layer strength {st.material.strength_mpa:g} MPa): safety factor {res['safety_factor_p999']} at the 99.9th-percentile "
                                 f"stress, max deflection {res['max_displacement_mm']} mm")
        if not a.no_video:
            simviz.fea_animate(st, R / f'preview/structure-{name}-{a.tag}.mp4')
        print(name, a.tag, {k: res[k] for k in ('max_displacement_mm', 'von_mises_design_mpa', 'safety_factor', 'stiffness_n_per_mm')}, flush=True)
