"""Rev 0.9 lid study: roof thickness x rib depth x fan-grille layout, each lid under the 300 N press (cadagent.fea).

Acceptance, fixed before the sweep (cad/parameters.json structure.lid_press): the roof deflects no more than Rev 0.7's
lid, the flush fan grille stays at least 1 mm clear of the fan, and the 99.9th-percentile safety factor is at least 2.
Picks the lightest passing lid (CAD volume); within 1.5 cm3 of it, the stronger one. Writes exports/structure/lid-sweep-<rev>.json and preview/lid-sweep-<rev>.png.
"""
from pathlib import Path
import sys, json, time
R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / 'cad'))
sys.path.insert(0, str(R / 'tools'))
import numpy as np
import build as b
import structure

REV = b.P['revision'].split('-')[0]
CRIT = b.P['structure']['lid_press']
# (roof mm, rib depth mm, spokes, hub disc mm); every rib ends at the same height (roof underside - depth = Z85.5 at 4.5/6)
VARIANTS = [(4.5, 6.0, 8, 30.0), (4.5, 6.0, 12, 20.0), (4.0, 6.5, 12, 20.0), (4.0, 7.5, 12, 20.0), (3.5, 7.0, 12, 20.0), (3.5, 8.0, 12, 20.0)]


def lid(rt, depth, spokes, hub):
    b.RT = b.e['roof_thickness'] = rt
    b.e['roof_ribs']['depth'] = depth
    b.e['fan_grille'].update(spokes=spokes, hub_diameter=hub)
    b.cover.cache_clear()
    return b.cover()


def sweep():
    structure.defeature()
    keep = (b.RT, b.e['roof_ribs']['depth'], b.e['fan_grille']['spokes'], b.e['fan_grille']['hub_diameter'])
    g = b.e['fan_grille']
    rows = []
    for rt, dep, sp, hub in VARIANTS:
        t = time.time()
        vol = lid(rt, dep, sp, hub).Volume() / 1000
        st = structure.lid_press(3.0)
        res = st.solve()
        mag, P = np.linalg.norm(st.disp, axis=0), st.points
        grille = np.array([b.inside_outline(x, y, g['clearance']) for x, y in P[:, :2]]) & (P[:, 2] > b.H - b.RT - .1)
        inner = ~st._touches_bc
        p999 = float(np.percentile(st.vm_elem[inner], 99.9))
        row = {'roof_mm': rt, 'rib_depth_mm': dep, 'spokes': sp, 'hub_mm': hub, 'volume_cm3': round(vol, 1),
               'roof_deflection_mm': round(float(mag[~grille].max()), 3), 'grille_deflection_mm': round(float(mag[grille].max()), 3),
               'sf_p999': round(st.material.strength_mpa / p999, 2), 'sf_peak': res.get('safety_factor'), 'minutes': round((time.time() - t) / 60, 1)}
        row['ok'] = (row['roof_deflection_mm'] <= CRIT['max_deflection_mm'] and row['grille_deflection_mm'] <= CRIT['max_grille_deflection_mm']
                     and row['sf_p999'] >= CRIT['min_sf_p999'])
        rows.append(row)
        print(json.dumps(row), flush=True)
    lid(*keep)
    ok = [r for r in rows if r['ok']]
    best = None
    if ok:   # the lightest passing lid; within 1.5 cm3 (under 2 g) of it, the one with the larger safety factor
        light = min(r['volume_cm3'] for r in ok)
        best = max((r for r in ok if r['volume_cm3'] <= light + 1.5), key=lambda r: r['sf_p999'])
    out = {'revision': b.P['revision'], 'criteria': {k: CRIT[k] for k in ('max_deflection_mm', 'max_grille_deflection_mm', 'min_sf_p999')},
           'rows': rows, 'best': best,
           'method': '300 N spread over the lid top (roof and grille), lid held at its rim; PLA layer strength; the lightest passing variant, '
                     'or within 1.5 cm3 of it the one with the larger safety factor'}
    (R / f'exports/structure/lid-sweep-{REV}.json').write_text(json.dumps(out, indent=1) + '\n')
    return out



def plot(out):
    rows, best = out['rows'], out['best']
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(9, 5), dpi=130)
    for r in rows:
        ax.plot(r['volume_cm3'], r['grille_deflection_mm'], 'o', color='#1baf7a' if r['ok'] else '#eb6834', ms=9)
        ax.plot(r['volume_cm3'], r['roof_deflection_mm'], 's', color='#2a78d6', ms=7)
        ax.annotate(f"{r['roof_mm']:g}/{r['rib_depth_mm']:g} mm, {r['spokes']} spokes", (r['volume_cm3'], r['grille_deflection_mm']),
                    xytext=(6, 4), textcoords='offset points', fontsize=8, color='#26323a')
    ax.axhline(CRIT['max_grille_deflection_mm'], color='#1baf7a', lw=1, ls='--')
    ax.axhline(CRIT['max_deflection_mm'], color='#2a78d6', lw=1, ls='--')
    ax.annotate('grille limit (1 mm off the fan)', (ax.get_xlim()[0], CRIT['max_grille_deflection_mm']), xytext=(4, 4), textcoords='offset points', fontsize=8)
    ax.annotate('roof limit (Rev 0.7 lid)', (ax.get_xlim()[0], CRIT['max_deflection_mm']), xytext=(4, -12), textcoords='offset points', fontsize=8)
    if best:
        ax.plot(best['volume_cm3'], best['grille_deflection_mm'], 's', ms=16, mfc='none', mec='#26323a', mew=2)
    ax.set_xlabel('lid volume (cm³)')
    ax.set_ylabel('deflection under 300 N (mm)')
    ax.set_title(f'Rev {REV} lid study: circles = fan grille (green passes), squares = roof; lighter is left', loc='left', fontsize=10)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    ax.grid(alpha=0.25, lw=0.6)
    fig.tight_layout()
    fig.savefig(R / f'preview/lid-sweep-{REV}.png')
    return best


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--plot', action='store_true', help='only redraw the figure from the saved JSON')
    a = ap.parse_args()
    out = json.loads((R / f'exports/structure/lid-sweep-{REV}.json').read_text()) if a.plot else sweep()
    print('best', plot(out))
