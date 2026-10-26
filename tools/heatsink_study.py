"""Heatsink design study (cadagent.heatsink): fin pitch x fin thickness against the cooler's own fan curve.

For each fin geometry the fan's operating point is found (fan curve meets the fin pressure drop), and the plate's
temperature rise above the intake air at 40 W follows. It answers "would a different fin stack on the same fan run
cooler?" in microseconds per design, ready for an optimiser; the chosen design is then checked in CFD.
Writes exports/heatsink-study.json and preview/heatsink-study.png.
"""
from pathlib import Path
import sys, json
R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / 'tools'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from cadagent.heatsink import FanCurve, operating_point
from cadagent.simviz import TEMP_RAMP
import thermal

P = json.loads((R / 'cad/parameters.json').read_text())
TH = P['thermal']
POWER = 40.0


def rise(pitch, t):
    hs = thermal.heatsink_model()
    hs.pitch, hs.fin_thickness = pitch, t
    fan = FanCurve(TH['fan']['dp0_pa'], TH['fan']['q_free_m3h'])
    op = operating_point(hs, fan)
    return POWER * hs.resistance(op['q_m3s']), op['q_m3h']


if __name__ == '__main__':
    pitches = np.round(np.arange(1.2, 4.01, 0.1), 2)
    thick = np.round(np.arange(0.2, 1.01, 0.05), 2)
    grid = np.array([[rise(p, t)[0] if t < p - 0.5 else np.nan for p in pitches] for t in thick])
    flows = np.array([[rise(p, t)[1] if t < p - 0.5 else np.nan for p in pitches] for t in thick])
    i, j = np.unravel_index(np.nanargmin(grid), grid.shape)
    cur_p, cur_t = TH['cooler']['fin_pitch'], TH['cooler']['fin_thickness']
    cur, cur_q = rise(cur_p, cur_t)
    best = {'pitch_mm': float(pitches[j]), 'fin_thickness_mm': float(thick[i]), 'rise_c': round(float(grid[i, j]), 2), 'flow_m3h': round(float(flows[i, j]), 2)}
    out = {'power_w': POWER, 'fan': TH['fan'], 'current': {'pitch_mm': cur_p, 'fin_thickness_mm': cur_t, 'rise_c': round(cur, 2), 'flow_m3h': round(cur_q, 2)},
           'best': best, 'pitches_mm': pitches.tolist(), 'fin_thickness_mm': thick.tolist(),
           'rise_c': [[None if np.isnan(v) else round(float(v), 3) for v in row] for row in grid],
           'note': 'Plate temperature rise above the air entering the fins, at 40 W, with the fan at its operating point on each fin stack. '
                   'Same envelope (100 x 87 mm, fins 14 mm tall), same 3.5 mm heat-pipe base. Analytic model; confirm the pick in CFD.'}
    (R / 'exports/heatsink-study.json').write_text(json.dumps(out, indent=1) + '\n')

    fig, ax = plt.subplots(figsize=(10, 5.6), dpi=130)
    cm = LinearSegmentedColormap.from_list('t', TEMP_RAMP)
    lo = float(np.floor(np.nanmin(grid)))
    hi = lo + 12                                    # the useful range; tighter stacks choke the fan and go off the scale
    cm.set_over('#4a1802')
    im = ax.pcolormesh(pitches, thick, grid, cmap=cm, shading='nearest', vmin=lo, vmax=hi)
    cs = ax.contour(pitches, thick, grid, levels=np.arange(lo + 1, hi, 1.0), colors='#26323a', linewidths=0.6, alpha=0.6)
    ax.clabel(cs, fmt='%.0f K', fontsize=7)
    ax.plot(cur_p, cur_t, 'o', ms=9, mfc='white', mec='#26323a', mew=2)
    ax.annotate(f'assumed current\n{cur:.1f} K, {cur_q:.1f} m³/h', (cur_p, cur_t), xytext=(12, 10), textcoords='offset points', fontsize=9, color='#26323a')
    ax.plot(best['pitch_mm'], best['fin_thickness_mm'], 's', ms=9, mfc='#2a78d6', mec='white', mew=2)
    ax.annotate(f"best: {best['pitch_mm']} mm pitch, {best['fin_thickness_mm']} mm fins\n{best['rise_c']:.1f} K, {best['flow_m3h']:.1f} m³/h",
                (best['pitch_mm'], best['fin_thickness_mm']), xytext=(14, 18), textcoords='offset points', fontsize=9, color='#26323a')
    ax.set_xlabel('fin pitch (mm)')
    ax.set_ylabel('fin thickness (mm)')
    ax.set_title('Heatsink study: plate temperature rise above intake air at 40 W, on the 8015 fan curve', loc='left', fontsize=11)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    fig.colorbar(im, ax=ax, label='temperature rise (K); darkest: beyond the scale', extend='max')
    fig.tight_layout()
    fig.savefig(R / 'preview/heatsink-study.png')
    print(json.dumps({'current': out['current'], 'best': best}))
