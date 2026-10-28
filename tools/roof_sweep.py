"""Parametric roof study: roof thickness x rib layout, each lid checked under the 300 N press (cadagent.fea).

Picks the lightest lid (CAD volume) whose deflection is no worse than Rev 0.7's lid and whose 99.9th-percentile
stress safety factor is at least 2. Writes exports/structure/roof-sweep.json and preview/roof-sweep.png.
"""
from pathlib import Path
import sys, json, time, itertools
R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / 'cad'))
sys.path.insert(0, str(R / 'tools'))
import numpy as np
import build as b
import structure

TARGET_DEFLECTION = json.loads((R / 'exports/structure/lid_press-0.7.json').read_text())['max_displacement_mm']
LAYOUTS = ['none', 'cross', 'star']   # ribs from the fan skirt to the wall middles, plus the four lid-screw corners


def lid(rt, layout, depth=6.0, width=2.0):
    b.RT = rt
    b.e['roof_thickness'] = rt
    b.e['roof_ribs'] = {'width': width, 'depth': depth, 'layout': layout} if layout != 'none' else None
    b.cover.cache_clear()
    return b.cover()


if __name__ == '__main__':
    structure.defeature()
    from cadagent.fea import Study, MATERIALS, plane_at
    rows = []
    for rt, layout in itertools.product((3.5, 4.0, 4.5), ('none', 'cross', 'star')):
        t = time.time()
        shape = lid(rt, layout)
        vol = shape.Volume() / 1000
        st = Study(shape, MATERIALS['pla'], mesh_mm=3.0, name=f'lid-{rt}-{layout}')
        st.fix(plane_at(2, b.BH))
        st.force(lambda f: f.kind == 'Plane' and abs(f.bbox[2] - b.H) < 0.05 and abs(f.bbox[5] - b.H) < 0.05, (0, 0, -300))
        res = st.solve()
        inner = ~st._touches_bc
        p999 = float(np.percentile(st.vm_elem[inner], 99.9))
        row = {'roof_mm': rt, 'ribs': layout, 'volume_cm3': round(vol, 1), 'deflection_mm': res['max_displacement_mm'],
               'p999_mpa': round(p999, 1), 'sf_p999': round(st.material.strength_mpa / p999, 2), 'minutes': round((time.time() - t) / 60, 1)}
        row['ok'] = row['deflection_mm'] <= TARGET_DEFLECTION and row['sf_p999'] >= 2.0
        rows.append(row)
        print(json.dumps(row), flush=True)
    ok = [r for r in rows if r['ok']]
    best = min(ok, key=lambda r: r['volume_cm3']) if ok else None
    out = {'target_deflection_mm': TARGET_DEFLECTION, 'rows': rows, 'best': best,
           'method': '300 N spread over the lid top, lid held at its rim; PLA layer strength; lightest passing variant'}
    (R / 'exports/structure/roof-sweep.json').write_text(json.dumps(out, indent=1) + '\n')

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    colours = {'none': '#2a78d6', 'cross': '#eb6834', 'star': '#1baf7a'}
    fig, ax = plt.subplots(figsize=(9, 5), dpi=130)
    for lay, col in colours.items():
        rr = [r for r in rows if r['ribs'] == lay]
        ax.plot([r['volume_cm3'] for r in rr], [r['deflection_mm'] for r in rr], '-o', color=col, lw=2, ms=8, label=f'ribs: {lay}')
        for r in rr:
            ax.annotate(f"{r['roof_mm']:g} mm", (r['volume_cm3'], r['deflection_mm']), xytext=(6, 4), textcoords='offset points', fontsize=8, color='#26323a')
    ax.axhline(TARGET_DEFLECTION, color='#52514e', lw=1, ls='--')
    ax.annotate(f'Rev 0.7 lid: {TARGET_DEFLECTION:.2f} mm', (ax.get_xlim()[0], TARGET_DEFLECTION), xytext=(4, 4), textcoords='offset points', fontsize=8, color='#52514e')
    if best:
        ax.plot(best['volume_cm3'], best['deflection_mm'], 's', ms=14, mfc='none', mec='#26323a', mew=2)
        ax.annotate('chosen', (best['volume_cm3'], best['deflection_mm']), xytext=(8, -14), textcoords='offset points', fontsize=9, color='#26323a')
    ax.set_xlabel('lid volume (cm³)')
    ax.set_ylabel('deflection under 300 N (mm)')
    ax.set_title(f"Rev {b.P['revision'].split('-')[0]} roof study: lighter is left, stiffer is down", loc='left', fontsize=11)
    ax.legend(frameon=False)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    ax.grid(alpha=0.25, lw=0.6)
    fig.tight_layout()
    fig.savefig(R / 'preview/roof-sweep.png')
    print('best', best)
