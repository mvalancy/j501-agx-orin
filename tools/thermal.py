"""Airflow and heat in the J501 enclosure (cadagent.cfd: OpenFOAM chtMultiRegionSimpleFoam).

Cases (pick with arguments, default all):
  bare40   AGX module with no heatsink at 40 W (MAXN on the 32 GB module): the starting point
  bare15   the same at 15 W (the lowest power mode)
  cooled   the J501 cooler (heat-pipe base, fins, 80 mm fan (8015) blowing down) at 40 W

Geometry comes from the build (base, lid, plates, hatch) and the carrier references (board outline and connector
meshes). The cooler and the fan are the provisional envelope from cad/parameters.json; their real fin count, heat
pipes and fan curve are not measured yet, so the cooled case is a model of a typical cooler of that size.
Writes sim/<case>/ (the OpenFOAM case, not tracked) and exports/thermal/<case>.json.
"""
from pathlib import Path
import sys, json, argparse, time
R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / 'cad'))
import build as b
import trimesh
import numpy as np
from cadagent.cfd import ThermalCase, Fan, SOLIDS

P = b.P
TH = P.get('thermal', {})


def box(lo, hi):
    lo, hi = np.asarray(lo, float), np.asarray(hi, float)
    return trimesh.creation.box(extents=hi - lo, transform=trimesh.transformations.translation_matrix((lo + hi) / 2))


def board_parts():
    """PCB slab and the connectors (as obstacles), in enclosure coordinates."""
    off = (b.M, b.M, b.Z)
    pcb = trimesh.load(R / 'references/pcb-outline.stl')
    pcb.apply_translation(off)
    skip = {'carrier-full', 'carrier-open-shells', 'module_socket'}
    conns = []
    for f in sorted((R / 'references/hardware').glob('*.stl')):
        if f.stem in skip:
            continue
        m = trimesh.load(f)
        m.apply_translation(off)
        conns.append(m)
    return pcb, conns


def module_parts():
    """AGX module: body (obstacle), SoC package (heat source) and thermal transfer plate (aluminium)."""
    m = TH['module']
    x0, y0, z0, x1, y1, z1 = 55.0, 62.0, 24.47, 155.0, 149.0, b.AGX_TOP   # module envelope from the NVIDIA STEP
    ttp_z = z1 - m['ttp_thickness']
    soc_z = ttp_z - m['soc_thickness']
    cx, cy = (x0 + x1) / 2 + m['soc_offset'][0], (y0 + y1) / 2 + m['soc_offset'][1]
    s = m['soc_size'] / 2
    body = box((x0, y0, z0), (x1, y1, soc_z))
    soc = box((cx - s, cy - s, soc_z), (cx + s, cy + s, ttp_z))
    ttp = box((x0, y0, ttp_z), (x1, y1, z1))
    return body, soc, ttp


def cooler_geometry():
    """The datasheet cooler as a compact model: a closed shell (base, side plates, fan housing, top cover) with a
    porous fin block open at the two exhaust faces, the fan bore and its hub."""
    c, f = TH['cooler'], TH['fan']
    sx, sy, sz = c['size']
    cx, cy = b.c['center_in_pcb'][0] + b.M, b.c['center_in_pcb'][1] + b.M
    z0 = b.AGX_TOP                                    # the pad is a contact resistance in the network, not a gap
    zb = b.COOLER_SEAT + c['base_thickness']          # top of the base
    zt = b.COOLER_SEAT + sz                           # top of the cooler
    zf = zt - c['cover_thickness'] - 15.5             # bottom of the fan = top of the fins
    side = 0.8
    x0, x1, y0, y1 = cx - sx / 2, cx + sx / 2, cy - sy / 2, cy + sy / 2
    if c['exhaust_axis'] == 'x':
        fins_lo, fins_hi = (x0 - 1, y0 + side, zb), (x1 + 1, y1 - side, zf)
    else:
        fins_lo, fins_hi = (x0 + side, y0 - 1, zb), (x1 - side, y1 + 1, zf)
    shell = box((x0, y0, z0), (x1, y1, zt))
    bore = trimesh.creation.cylinder(radius=f['bore'] / 2, height=zt - zf + 2, transform=trimesh.transformations.translation_matrix((cx, cy, (zf + zt) / 2 + 1)))
    shell = shell.difference(box(fins_lo, fins_hi)).difference(bore)
    hub = trimesh.creation.cylinder(radius=f['d_hub'] / 2, height=zt - zf, transform=trimesh.transformations.translation_matrix((cx, cy, (zf + zt) / 2)))
    fins = (np.maximum(fins_lo, (x0, y0, zb)), np.minimum(fins_hi, (x1, y1, zf)))
    return {'shell': shell, 'hub': hub, 'fins': fins, 'fan_centre': (cx, cy, (zf + zt) / 2), 'top': zt, 'centre': (cx, cy)}


def heatsink_model():
    """The analytic plate-fin model of the same cooler (cadagent.heatsink)."""
    from cadagent.heatsink import PlateFin
    c = TH['cooler']
    sx, sy, sz = c['size']
    along, across = (sx, sy) if c['exhaust_axis'] == 'x' else (sy, sx)
    fin_h = sz - c['base_thickness'] - c['cover_thickness'] - 15.5
    m = TH['module']
    return PlateFin(length=along, width=across - 1.6, fin_height=fin_h, fin_thickness=c['fin_thickness'], pitch=c['fin_pitch'],
                    base_thickness=c['base_thickness'], k_fin=c['k_fin'], k_base=c['k_base_eff'], flow_length=along / 2,
                    branches=2, source=(m['soc_size'] + 2 * m['ttp_thickness'],) * 2)


def enclosure():
    parts = [b.base(), b.cover(), b.panel(), b.panel(False), b.side_hatch()]
    from cadagent.cfd import _mesh_of
    return _mesh_of(parts, tol=0.1)


def make(name, power_w, cooled, fine, cell=None, iterations=None):
    th = dict(TH['case'], **{k: v for k, v in (('cell_mm', cell), ('iterations', iterations)) if v})
    ms, mt = th['margin_side'], th['margin_top']        # room air around the enclosure, open on five sides
    domain = ((-ms, b.Y0 - ms, -3.0), (b.W + ms, b.Y1 + ms, b.H + mt))
    case = ThermalCase(name, domain=domain, cell_mm=th['cell_mm'], ambient_c=th['ambient_c'], iterations=th['iterations'])
    case.wall('enclosure', enclosure(), level=(2, 3))
    pcb, conns = board_parts()
    case.wall('pcb', pcb, level=(2, 3))
    case.wall('connectors', conns, level=(2, 3))
    body, soc, ttp = module_parts()
    lv = 4 if fine else 3
    if cooled:   # the heat leaves through the cooler's fin block; the module is an obstacle, its temperature comes from the network
        case.wall('module', [body, soc, ttp], level=(3, lv))
    else:
        case.wall('modulebody', body, level=(3, lv))
        case.solid('soc', soc, SOLIDS['silicon'], power_w=power_w, level=(3, lv))
        case.solid('ttp', ttp, SOLIDS['al6061'], level=(3, lv))
        case.contact('soc', 'ttp', thickness_mm=0.1, k=4.0)
    case.refine((b.PX0 - 5, b.Y0, 0), (b.PX1 + 5, b.Y1, b.H), 2)          # the inside of the enclosure
    case.refine((40, 50, 20), (170, 165, 60), 3)                          # around the module
    if cooled:
        g = cooler_geometry()
        f = TH['fan']
        hs = heatsink_model()
        pc = hs.porous_coefficients()          # channel friction only: the CFD resolves the fan jet and the block's faces
        # local axes: e1 along the channels, e2 across the fins (nearly closed), e3 vertical (open between the plates)
        e1, e2 = ((1, 0, 0), (0, 1, 0)) if TH['cooler']['exhaust_axis'] == 'x' else ((0, 1, 0), (1, 0, 0))
        case.wall('cooler', g['shell'], level=(3, lv))
        case.wall('fanhub', g['hub'], level=(3, 3))
        # isothermal fins (heat pipes, 96 % fin efficiency): conductance hA from the plate-fin model at its own fan
        # operating point, first fin temperature from effectiveness-NTU; calibrate_fins() then makes it deliver power_w
        from cadagent.heatsink import FanCurve, operating_point
        op = operating_point(hs, FanCurve(f['dp0_pa'], f['q_free_m3h']))
        r = hs.resistance(op['q_m3s'], detail=True)
        ha = 1 / r['fins']
        # first fin temperature: the block's effective conductance seen in a coarse calibration run (the CFD block is
        # flushed unevenly), so calibration starts close to its answer
        t_fin = TH['case']['ambient_c'] + 8.0 + power_w / (ha * TH['cooler']['block_effectiveness_guess'])
        case.porous_box('fins', *g['fins'], d=pc['d_vector'], f=pc['f_vector'], e1=e1, e2=e2,
                        ha_w_k=round(ha, 4), fin_temperature_c=round(t_fin, 2), target_w=power_w,
                        note='compact fin block: Darcy-Forchheimer and fin conductance from cadagent.heatsink.PlateFin; '
                             'isothermal fins, temperature calibrated so the block delivers the module power')
        case.fan(Fan('fan', centre=g['fan_centre'], axis=f['axis'], d_outer=f['d_outer'], d_hub=f['d_hub'], thickness=f['thickness'],
                     dp0_pa=f['dp0_pa'], q_free_m3h=f['q_free_m3h'], note=f['note']))
        cx, cy = g['centre']
        case.refine((cx - 60, cy - 55, 38), (cx + 60, cy + 55, g['top'] + 8), 3)
    return case


def plate_temperature(res, power_w):
    """Thermal plate hot spot: the calibrated fin temperature (CFD) + P x (spreading + base) + P x pad. The
    plate-fin model's own estimate from the CFD intake air and fan flow is kept alongside as a cross-check."""
    hs = heatsink_model()
    fan = res['fans']['fan']
    q = fan['flow_m3h'] / 3600
    r = hs.resistance(q, detail=True)
    m = TH['module']
    a = (m['soc_size'] + 2 * m['ttp_thickness']) ** 2 * 1e-6
    r_pad = P['cooler']['tim_thickness'] / 1000 / (m['tim_k'] * a)
    t_in = fan['air_through_fan_c']
    fins = res['case_setup']['porous'][0]
    t_fin = fins.get('fin_temperature_c')
    t_plate = t_fin + power_w * (r['spreading'] + r['base'] + r_pad)
    t_model = t_in + power_w * (r['total_k_per_w'] + r_pad)
    return {'air_into_fins_c': t_in, 'fan_flow_m3h': fan['flow_m3h'], 'fin_temperature_c': round(t_fin, 2),
            'heat_out_w': res.get('heat_out_w'), 'heatsink': {k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()},
            'pad_k_per_w': round(r_pad, 4), 'ttp_hotspot_c': round(t_plate, 1), 'ttp_hotspot_model_only_c': round(t_model, 1),
            'ttp_limit_c': TH['limits']['ttp_max_c'], 'margin_c': round(TH['limits']['ttp_max_c'] - t_plate, 1), 'heatsink_model': hs.describe(),
            'method': 'T_plate = T_fin (CFD, calibrated so the fins deliver the module power) + P x (spreading + base, cadagent.heatsink) + P x pad; '
                      'ttp_hotspot_model_only_c is the plate-fin model alone at the CFD fan flow and intake air'}


CASES = {'bare40': (40, False), 'bare15': (15, False), 'cooled': (40, True)}

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('cases', nargs='*', default=list(CASES))
    ap.add_argument('--np', type=int, default=20)
    ap.add_argument('--fine', action='store_true', help='0.5 mm cells on the module and cooler (else 1 mm)')
    ap.add_argument('--write-only', action='store_true')
    ap.add_argument('--cell', type=float, help='base cell size (mm), e.g. 16 for a quick pipeline test')
    ap.add_argument('--iterations', type=int)
    ap.add_argument('--suffix', default='', help='case folder suffix, e.g. -debug')
    ap.add_argument('--no-calibrate', action='store_true', help='skip the fin-temperature calibration (quick tests)')
    ap.add_argument('--sim-root', type=Path, default=R / 'sim', help='where the OpenFOAM cases go')
    ap.add_argument('--exports', type=Path, default=R / 'exports/thermal', help='where the result JSON goes')
    ap.add_argument('--recalibrate', type=int, metavar='ROUNDS',
                    help='cooled cases: continue the fin-temperature calibration of the existing case folder for up to ROUNDS '
                         'more rounds, starting from the fin temperature it reached')
    ap.add_argument('--balance', type=int, metavar='MAX_ITERATIONS',
                    help='continue the existing case folders 1000 iterations at a time until the energy balance is within 5 %% '
                         '(or MAX_ITERATIONS in total), instead of writing and running them from scratch')
    a = ap.parse_args()
    out = a.exports
    out.mkdir(parents=True, exist_ok=True)
    for name in a.cases:
        w, cooled = CASES[name]
        if (a.recalibrate and not cooled) or (a.balance and cooled):
            # never fall through to writing (which wipes the case folder): --recalibrate is for cooled cases, --balance for
            # the others (a cooled case is balanced by its calibration)
            print(f'{name}: skipped ({"--recalibrate needs a cooled case" if a.recalibrate else "--balance is for cases without fins"})', flush=True)
            continue
        case = make(name, w, cooled, a.fine, a.cell, a.iterations)
        if a.recalibrate:               # more calibration rounds from where the last run stopped
            d = a.sim_root / (name + a.suffix)
            meta = json.loads((d / 'cadagent-case.json').read_text())
            for z in case.porous:                  # the fin temperature the last round reached, not the first guess
                z['fin_temperature_c'] = next(m['fin_temperature_c'] for m in meta['porous'] if m['name'] == z['name'])
            earlier = json.loads((out / f'{name}{a.suffix}.json').read_text()).get('fin_calibration', [])
            t = time.time()
            res = case.calibrate_fins(d, w, rounds=a.recalibrate)
            res['fin_calibration'] = earlier + [dict(h, resumed=True) for h in res['fin_calibration']]
            rc = 0 if res.get('solver_finished') else 1
        elif a.balance:                            # continue the finished case where it stopped
            d = a.sim_root / (name + a.suffix)
            t = time.time()
            res = case.run_until_balanced(d, chunk=1000, max_iterations=a.balance)
            rc = 0 if res.get('solver_finished') else 1
            print(name, 'continuation', res['continuation'], flush=True)
        else:
            d = case.write(a.sim_root / (name + a.suffix), np_procs=a.np)
            print(f'{name}: wrote {d}', flush=True)
            if a.write_only:
                continue
            t = time.time()
            rc = case.run(d)
            res = case.calibrate_fins(d, w) if cooled and rc == 0 and not a.no_calibrate else case.results(d)
        res.update(exit_code=rc, run_minutes=round((time.time() - t) / 60, 1), revision=P['revision'],
                   case_setup=json.loads((d / 'cadagent-case.json').read_text()))
        if cooled and rc == 0:
            res['network'] = plate_temperature(res, w)
        (out / f'{name}{a.suffix}.json').write_text(json.dumps(res, indent=2) + '\n')
        print(name, 'exit', rc, {k: v.get('max_c') for k, v in res['solids'].items()}, res.get('fans'), flush=True)
