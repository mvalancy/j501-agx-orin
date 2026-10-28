"""Pictures and animations for each finished thermal case (cadagent.simviz).

For every exports/thermal/<case>.json with a matching sim/<case>/VTK folder, writes into preview/thermal/:
  <case>-section-y.png, -section-x.png   temperature sections through the module centre
  <case>-flow.png                        streamlines coloured by air temperature
  <case>-walls.png                       air temperature on the enclosure's inner faces, past the PLA limit in red
  <case>-convergence.png                 residuals and the hottest temperature of each solid against iteration
  <case>-flow.mp4, <case>-sweep.mp4      moving air and a sweeping section (skip with --no-video)
"""
from pathlib import Path
import sys, json, argparse
R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / 'cad'))
from cadagent import simviz as sv

P = json.loads((R / 'cad/parameters.json').read_text())
LIM = P['thermal']['limits']
TITLES = {'bare40': 'AGX module with no heatsink, 40 W', 'bare15': 'AGX module with no heatsink, 15 W',
          'cooled': 'Rev 0.7 with the 34 mm WS-RDN-601 cooler, 40 W', 'cooled-0.8': 'Rev 0.8 with the 34 mm WS-RDN-601 cooler, 40 W',
          'cooled-0.9': 'Rev 0.9 with the reComputer mini J501 cooler (fan blowing up through a flush grille), 40 W'}


def subtitle(res):
    bits = []
    for k, v in res.get('solids', {}).items():
        if v.get('max_c') is not None:
            bits.append(f"{k} {v['max_c']:.0f} °C")
    if res.get('network'):
        bits.append(f"thermal plate {res['network']['ttp_hotspot_c']:.0f} °C (limit {LIM['ttp_max_c']})")
    n = res.get('network') or {}
    for k, f in res.get('fans', {}).items():
        if n.get('fan_role') == 'exhaust':
            bits.append(f"fan {f['flow_cfm']:.1f} CFM up, air into the fins {n['air_into_fins_c']:.1f} °C, out {f['air_through_fan_c']:.1f} °C")
        else:
            bits.append(f"fan {f['flow_cfm']:.1f} CFM, air in {f['air_through_fan_c']:.1f} °C")
    return ' · '.join(bits)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('cases', nargs='*')
    ap.add_argument('--no-video', action='store_true')
    a = ap.parse_args()
    out = R / 'preview/thermal'
    out.mkdir(parents=True, exist_ok=True)
    cases = a.cases or sorted(p.stem for p in (R / 'exports/thermal').glob('*.json') if (R / 'sim' / p.stem / 'VTK').exists())
    for name in cases:
        res = json.loads((R / f'exports/thermal/{name}.json').read_text())
        r = sv.CFDResult(R / 'sim' / name)
        title = TITLES.get(name, name)
        sub = subtitle(res)
        cx, cy = 105.0, 105.5
        clim = r.t_range()
        sv.section(r, out / f'{name}-section-y.png', normal='y', at=cy, title=f'{title}: section through the module', subtitle=sub, clim=clim)
        sv.section(r, out / f'{name}-section-x.png', normal='x', at=cx, title=f'{title}: side section', subtitle=sub, clim=clim)
        lines = sv.streamlines(r, 900)
        sv.flow(r, out / f'{name}-flow.png', title=f'{title}: airflow', subtitle=sub, lines=lines)
        sv.walls(r, out / f'{name}-walls.png', limit_c=LIM['pla_wall_limit_c'], limit_label='(PLA design limit)',
                 title=f'{title}: wall temperature', subtitle=sub,
                 note=f"PLA heat-deflection {LIM['pla_hdt_c']} °C, PETG {LIM['petg_hdt_c']} °C; design limits {LIM['pla_wall_limit_c']} / {LIM['petg_wall_limit_c']} °C.")
        sv.convergence_chart(res, out / f'{name}-convergence.png', title=f'{title}: convergence')
        if not a.no_video:
            sv.animate_flow(r, out / f'{name}-flow.mp4')
            sv.animate_sweep(r, out / f'{name}-sweep.mp4', normal='x')
        print(name, 'figures written', flush=True)
