#!/usr/bin/env python3
"""Cooler fit study: the reComputer mini J501 (G48R) cooler against the lids, with the fan-position uncertainty.

Exports the cooler's components (one model: cad/hardware.py, grouped by cad/cooler_reference.py) as STEP and reads
them back, then intersects exact lid solids with the cooler keep-outs:

- the release lid (exports/cover.step) with the fan moved by the photo-registration uncertainty in eight directions,
  for the modelled frame and for the S06 table's 95 mm size; it must clear both;
- the Rev 0.8 lid (git tag rev0.8) at lifts of 0 mm (the collision the printed lid showed: a negative control),
  15 mm and the riser height (tools/lid_riser.py), the recovery path for an already printed Rev 0.8 lid.

Writes exports/cooler-study/fit-review.json (bound to source and artifact hashes; checked in CI by
tools/check_cooler_study.py), component STEPs and preview/cooler-study-*.png (the components also show in the project's 3D viewer:
tools/view_model.py).
"""
from pathlib import Path
import sys, json, hashlib, subprocess, tempfile
import cadquery as cq
R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / 'cad'))
sys.path.insert(0, str(R / 'tools'))
import cooler_reference as c  # noqa: E402
import build as b  # noqa: E402
from lid_riser import screw as riser_screw  # noqa: E402
from cadagent.render import Renderer  # noqa: E402

OUT = R / 'exports/cooler-study'
REV08 = 'rev0.8'          # the printed lid that hit the cooler
RISER = 18.0              # tools/lid_riser.py default
SOURCES = ['cad/parameters.json', 'cad/cooler_reference.py', 'cad/hardware.py', 'cad/build.py',
           'tools/cooler_fit_review.py', 'exports/cover.step']


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def bounds(s):
    bb = s.BoundingBox()
    return [round(x, 4) for x in (bb.xmin, bb.ymin, bb.zmin, bb.xmax, bb.ymax, bb.zmax)]


def gap(lid, shell, s):
    # Overlap from the solids; clearance from the lid's faces: a lid read back from STEP can misclassify a nearby
    # point as inside itself and report a distance of 0 (seen on the 95 mm keep-out).
    v = lid.intersect(s).Volume()
    return {'intersection_mm3': round(v, 3), 'minimum_gap_mm': 0.0 if v > 1e-6 else round(shell.distance(s), 3)}


def worst(rows):
    # the tightest case over the shifts: largest intersection, else smallest gap
    return min(rows, key=lambda r: (-r['intersection_mm3'], r['minimum_gap_mm']))


def lid_vs_cooler(lid, dz=0.0, conservative=False):
    lid = lid.translate((0, 0, dz)) if dz else lid
    shell = cq.Compound.makeCompound(lid.Faces())
    out = {}
    for name in ('fan', 'heat_sink'):
        rows = []
        for sh in c.shifts():
            r = gap(lid, shell, c.keepouts(sh, conservative)[name])
            rows.append(dict(r, shift_mm=list(sh)))
        out[name] = {'nominal': rows[0], 'worst_shift': worst(rows[1:])}
    return out


def rev08_cover():
    data = subprocess.run(['git', 'show', f'{REV08}:exports/cover.step'], cwd=R, capture_output=True, check=True).stdout
    with tempfile.NamedTemporaryFile(suffix='.step') as t:
        t.write(data)
        t.flush()
        return cq.importers.importStep(t.name).val(), hashlib.sha256(data).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    pieces = c.parts()
    metrics = {}
    for name, s in pieces.items():
        path = OUT / f'{name}.step'
        b.export_step(s, path)
        read = cq.importers.importStep(str(path)).val()
        metrics[name] = {'valid': read.isValid(), 'solid_count': len(read.Solids()), 'volume_mm3': round(read.Volume(), 2),
                         'bounds_mm': bounds(read)}
        assert read.isValid() and read.Volume() > 0, name
    print('components exported and read back', flush=True)
    b.export_step(c.compound([s for k, s in pieces.items() if k not in c.CONTEXT]), OUT / 'g48r-reference.step')
    alt = c.C['alternatives']['ws_rdn_601']
    ax, ay = [v + c.M for v in alt.get('center_in_pcb', c.C['center_in_pcb'])]
    sx, sy, sz = alt['size']
    b.export_step(b.box(ax - sx / 2, ay - sy / 2, c.SPREADER_Z, sx, sy, sz), OUT / 'ws-rdn-601-envelope.step')

    release = cq.importers.importStep(str(R / 'exports/cover.step')).val()
    rel = {'modelled_frame': lid_vs_cooler(release), 'frame_95mm': lid_vs_cooler(release, conservative=True)}
    print('release lid', json.dumps({k: {n: v['worst_shift'] for n, v in r.items()} for k, r in rel.items()}), flush=True)
    old, old_sha = rev08_cover()
    trials = []
    for lift in (0.0, 15.0, RISER):
        trials.append({'lid_lift_mm': lift, **lid_vs_cooler(old, lift)})
        print('rev0.8 lid lift', lift, json.dumps({n: trials[-1][n]['worst_shift'] for n in ('fan', 'heat_sink')}), flush=True)

    f = rel['modelled_frame']
    min_fan = c.C['minimum_fan_clearance']
    release_pass = (all(v['nominal']['intersection_mm3'] < 1e-6 and v['worst_shift']['intersection_mm3'] < 1e-6 for r in rel.values() for v in r.values())
                    and f['fan']['worst_shift']['minimum_gap_mm'] >= min_fan and rel['frame_95mm']['fan']['worst_shift']['minimum_gap_mm'] >= 0.5)
    meas = c.C.get('measured', {})
    report = {
        'study_valid': all(x['valid'] for x in metrics.values()),
        'release_cover_fit_pass': release_pass,
        'scope': 'One cooler model (cad/hardware.py) against exact lid solids. Fit only: strength is tools/structure.py, '
                 'airflow tools/thermal.py.',
        'revision': b.P['revision'],
        'fan_xy_uncertainty_mm': c.C.get('fan_xy_uncertainty', 0.0),
        'source_sha256': {p: sha(R / p) for p in SOURCES},
        'rev08_cover_sha256': old_sha,
        'parts': metrics,
        'stack_z_mm': {'pcb_underside': b.Z, 'agx_thermal_plate_top': round(b.AGX_TOP, 3), 'copper_spreader_bottom': round(c.SPREADER_Z, 3),
                       'cooler_contact': round(c.CONTACT_Z, 3), 'fin_top_fan_bottom': round(c.FAN_Z, 3), 'fan_top_design': round(c.TOP, 3),
                       'fan_top_measured': round(b.Z + b.p['thickness'] + meas['pcb_top_to_fan_top_mm'], 3) if meas else None,
                       'grille_underside': round(b.H - b.e['fan_grille']['thickness'], 3),
                       'skirt_bottom': round(c.TOP - b.e['fan_grille']['skirt_below_fan_top'], 3),
                       'rib_bottom': round(b.H - b.RT - b.e['roof_ribs']['depth'], 3)},
        'measured': meas,
        'release_cover': rel,
        'rev08_cover_trials': trials,
        'riser': {'rise_mm': RISER, **riser_screw(RISER)},
        'unresolved': [
            'Fan centre: from one photo (two-plane fit, hub within 0.1 mm of the module centre); not measured on the board (covered by the 3 mm uncertainty)',
            'Spacer pattern versus the long tie-down axes, and the heatsink ear outline',
            'Effective female thread depth and short-screw length',
            'Heat-pipe bend path, plate count and the base block outline',
        ],
        'production_ready': False,
        'physical_fit_verified': False,
    }
    renderer = Renderer(R / 'preview', size=(1500, 1050), branding='J501 COOLER STUDY',
                        subtitle='reComputer mini J501 (G48R) | the project cooler model | NOT a printable part', tessellation=(0.15, 0.3))
    loaded = {k: cq.importers.importStep(str(OUT / f'{k}.step')).val() for k in pieces}

    def rgb(k):
        return tuple(int(c.COLORS[k][i:i + 2], 16) / 255 for i in (1, 3, 5))
    shapes = [(s, rgb(k)) for k, s in loaded.items() if k not in c.CONTEXT]
    for mode, view in (('assembly', 'iso'), ('top', 'top'), ('side', 'front')):
        renderer.render(f'cooler-study-{mode}.png', shapes, caption='reComputer mini J501 / G48R cooler: ' + mode, view=view,
                        note='2 mm copper spreader; 6.8 mm M3 standoffs; 5 x D6 heat pipes; 84 x 93 mm plates; 92 x 15 mm fan | bends and ears approximate')
    renderer.render('cooler-study-installed.png', [(s, rgb(k)) for k, s in loaded.items()], caption='Cooler on the carrier',
                    note='Magenta: module screw axes. The cooler is centred on the module; its ears sit on the module screw axes.')
    exploded = [(s, rgb(k), (0, 0, 50 if k.startswith('fan') else 16 if k not in ('spreader', 'spacers') else 0))
                for k, s in loaded.items() if k not in c.CONTEXT]
    renderer.render('cooler-study-exploded.png', exploded, caption='Cooler stack / separated components',
                    note='Standoffs carry the heatsink ears; the cooler contact sits directly on the copper spreader (no 6.8 mm gap)')
    draw(report)
    artifacts = sorted(OUT.glob('*.step')) + sorted((R / 'preview').glob('cooler-study-*.png'))
    report['artifact_sha256'] = {str(p.relative_to(R)): sha(p) for p in artifacts}
    (OUT / 'fit-review.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'release_cover_fit_pass': release_pass, 'fan_worst_gap_mm': f['fan']['worst_shift']['minimum_gap_mm'],
                      'fan95_worst_gap_mm': rel['frame_95mm']['fan']['worst_shift']['minimum_gap_mm']}), flush=True)
    return 0 if release_pass and report['study_valid'] else 1


def draw(report):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle, Circle, Polygon
    fig, (ax, side) = plt.subplots(1, 2, figsize=(14, 7.5), gridspec_kw={'width_ratios': [1.25, 1]})
    ax.add_patch(Rectangle((0, b.Y0), b.W, b.D, fill=False, edgecolor='#254958', lw=2))
    ax.add_patch(Rectangle((c.M, c.M), c.B['width'], c.B['depth'], fc='#d8e9dc', ec='#62967b'))
    sp = c.C['spreader']
    px, py = [v + c.M for v in sp['center_in_pcb']]
    sx, sy = sp['size']
    ax.add_patch(Rectangle((px - sx / 2, py - sy / 2), sx, sy, fc='#c68b59', alpha=0.4, label='2 mm copper spreader'))
    g = b.e['fan_grille']
    ax.add_patch(Polygon(b.fan_outline(), closed=True, fill=False, ec='#187aa4', lw=2, label='fan frame (model)'))
    for sh in c.shifts()[1:]:
        ax.add_patch(Polygon(b.fan_outline(0, sh), closed=True, fill=False, ec='#187aa4', lw=0.5, alpha=0.5))
    ax.add_patch(Polygon(b.fan_outline(g['clearance']), closed=True, fill=False, ec='#c23c35', lw=2, label=f"lid fan pocket (+{g['clearance']:g} mm)"))
    ax.add_patch(Polygon(b.fan_outline(g['clearance'] + g['skirt_wall']), closed=True, fill=False, ec='#c23c35', lw=1, ls='--', label='skirt outer face'))
    ax.add_patch(Circle((c.CX, c.CY), c.C['fan']['blade_diameter'] / 2, fill=False, ec='#26323a', lw=1, ls=':', label='rotor'))
    for x0, y0, x1, y1 in b.rib_segments():
        ax.plot([x0, x1], [y0, y1], c='#ad4e93', lw=2)
    ax.plot([], [], c='#ad4e93', lw=2, label='roof ribs (outside the pocket)')
    ax.annotate(f"fan moved ±{report['fan_xy_uncertainty_mm']:g} mm (thin outlines)", (c.CX, c.CY), xytext=(12, 192),
                arrowprops={'arrowstyle': '->'}, fontsize=9)
    ax.set(xlim=(-5, 211), ylim=(-3, 207), xlabel='Enclosure X (mm)', ylabel='Enclosure Y (mm)', title=f"Plan: Rev {report['revision'].split('-')[0]} lid against the cooler")
    ax.set_aspect('equal')
    ax.legend(loc='lower left', fontsize=7)
    z = report['stack_z_mm']
    for name, lo, hi, color in (('Copper spreader', z['copper_spreader_bottom'], z['cooler_contact'], '#bb743e'),
                                ('G48R base, pipes, plates', z['cooler_contact'], z['fin_top_fan_bottom'], '#a4b3bc'),
                                ('15 mm fan', z['fin_top_fan_bottom'], z['fan_top_design'], '#375966')):
        side.add_patch(Rectangle((0, lo), 55, hi - lo, fc=color, ec='white'))
        side.text(3, (lo + hi) / 2, name, va='center', fontsize=9, color='white' if name.startswith('15') else '#192a34')
    for label, key, color in (('Grille underside', 'grille_underside', '#c23c35'), ('Skirt bottom (6 mm outside the frame)', 'skirt_bottom', '#ad4e93'),
                              ('Rib bottom (outside the pocket)', 'rib_bottom', '#665599')):
        side.plot([-2, 95], [z[key], z[key]], ls='--', c=color)
        side.text(58, z[key] + 0.4, f'{label}\nZ{z[key]:.2f}', fontsize=8, color=color)
    side.axhline(z['fan_top_design'], c='#187aa4')
    side.text(58, z['fan_top_design'] - 2.2, f"Fan top Z{z['fan_top_design']:.2f} (design, 70 mm over the PCB)", fontsize=8, c='#187aa4')
    if z.get('fan_top_measured'):
        side.axhline(z['fan_top_measured'], c='#187aa4', ls=':')
        side.text(58, z['fan_top_measured'] - 2.2, f"measured Z{z['fan_top_measured']:.2f} (68 mm)", fontsize=8, c='#187aa4')
    side.set(xlim=(-3, 100), ylim=(38, 100), xticks=[], ylabel='Enclosure Z (mm)', title='Height stack (levels, not a section)')
    fan = report['release_cover']['modelled_frame']['fan']['worst_shift']
    f95 = report['release_cover']['frame_95mm']['fan']['worst_shift']
    fig.suptitle(f"Cooler fit: worst gap to the moved fan {fan['minimum_gap_mm']:.2f} mm (95 mm frame: {f95['minimum_gap_mm']:.2f} mm)", fontsize=14)
    fig.text(0.04, 0.02, 'Exact lid solid vs keep-outs. The standoffs carry the heatsink ears; the cooler contact sits on the spreader.', fontsize=9)
    fig.tight_layout(rect=(0, 0.04, 1, 0.95))
    fig.savefig(R / 'preview/cooler-study-clearance.png', dpi=145)
    plt.close(fig)


if __name__ == '__main__':
    raise SystemExit(main())
