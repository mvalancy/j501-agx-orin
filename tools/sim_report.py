"""The Rev 0.8 -> Rev 0.9 simulation and optimisation report (cadagent.simreport): preview/simulation.html.

Reads what the studies wrote and shows whatever exists:
  exports/slice-report*.json          filament grams and print time (Bambu Studio CLI)
  exports/structure/<case>-<rev>.json lid and base load cases (cadagent.fea)
  exports/thermal/<case>.json         airflow and heat (cadagent.cfd), pictures in preview/thermal/
  exports/topology/<study>.json       topology optimisation (cadagent.topopt), pictures in preview/topology-*
"""
from pathlib import Path
import sys, json
R = Path(__file__).resolve().parents[1]
from cadagent.simreport import write_report, metric

P = json.loads((R / 'cad/parameters.json').read_text())
TH = P['thermal']
LIM = TH['limits']
PREV, CUR = '0.8', P['revision'].split('-')[0]


def load(rel):
    p = R / rel
    return json.loads(p.read_text()) if p.exists() else None


def exists(rel):
    return (R / rel).exists()


def figs(items):
    # the page lives in preview/, next to the pictures
    return [{'src': s, 'caption': c} for s, c in items if exists('preview/' + s)]


def section_material():
    a, b = load(f'exports/slice-report-{PREV}.json'), load(f'exports/slice-report-{CUR}.json')
    if not (a and b):
        return None
    names = {'base': 'Base (P1)', 'cover': 'Lid (P2)', 'front_no_gmsl': 'Front plate (P4)', 'rear_io': 'Rear plate (P5)', 'side_hatch': 'Side hatch (P10)'}
    rows = [metric(names.get(k, k), a['parts'][k]['grams'], b['parts'][k]['grams'], 'g') for k in names if k in a['parts'] and k in b['parts']]
    rows.append(metric('Enclosure total', a['total_grams'], b['total_grams'], 'g'))
    rows.append(metric('Print time, all five parts', a['total_hours'], b['total_hours'], 'h', digits=2))
    o = load(f'exports/slice-options-{CUR}.json')
    extra = []
    if o:
        base = o['15% grid (default)']['base+lid']
        extra = [f"Option: {k} infill on the Rev {CUR} base and lid gives {v['base+lid']} g (default profile {base} g). "
                 'Not the default: the FEA models solid walls.' for k, v in o.items() if k != '15% grid (default)']
    return {'id': 'material', 'title': 'Filament and print time',
            'summary': f"Measured with the Bambu Studio command line on a P1S ({b['process']}, {b['filament']}), the same profile for "
                       "both revisions. These are the slicer's grams, not CAD volumes.",
            'metrics': rows, 'limits': [b['note'], f'One copy of each part; only the lid changed between Rev {PREV} and Rev {CUR}.'] + extra}


def section_structure():
    rows, figures, videos = [], [], []
    labels = {'lid_press': '300 N on the lid', 'base_mount': 'Robot mounting, 10 g down + 5 g sideways'}
    for case, label in labels.items():
        a, b = load(f'exports/structure/{case}-{PREV}.json'), load(f'exports/structure/{case}-{CUR}.json')
        if not (a and b):
            continue
        rows += [metric(f'{label}: deflection', a['max_displacement_mm'], b['max_displacement_mm'], 'mm', digits=2),
                 metric(f'{label}: stress, 99.9th percentile', a.get('von_mises_p999_mpa'), b.get('von_mises_p999_mpa'), 'MPa', digits=1),
                 metric(f'{label}: safety factor (99.9th percentile)', a.get('safety_factor_p999'), b.get('safety_factor_p999'), '', better='higher', digits=2),
                 metric(f'{label}: stiffness', a.get('stiffness_n_per_mm'), b.get('stiffness_n_per_mm'), 'N/mm', better='higher', digits=0)]
        if 'grille_max_displacement_mm' in b:
            rows += [metric(f'{label}: roof deflection (fan grille aside)', a['max_displacement_mm'], b['roof_max_displacement_mm'], 'mm', digits=2,
                            note=f"limit {P['structure'][case]['max_deflection_mm']} mm (Rev 0.7 lid)"),
                     metric(f'{label}: fan grille deflection', None, b['grille_max_displacement_mm'], 'mm', better=None, digits=2,
                            note=f"limit {P['structure'][case]['max_grille_deflection_mm']} mm: stays at least 1 mm off the fan, which sits {b.get('fan_clearance_mm')} mm below")]
        for rev in (PREV, CUR):
            figures.append((f'structure-{case}-{rev}.png', f'Rev {rev}: {label}. Colour: von Mises stress; deformation exaggerated.'))
            videos.append((f'structure-{case}-{rev}.mp4', f'Rev {rev}: {label}, load ramped past first failure (black: past the strength).'))
    if not rows:
        return None
    return {'id': 'structure', 'title': 'Strength and stiffness',
            'summary': 'Linear-elastic FEA (gmsh + scikit-fem, quadratic tetrahedra) on the printed shells, PLA with its layer-direction '
                       f"strength ({25} MPa). The safety factor uses the 99.9th-percentile stress so one sharp corner (a mesh-dependent spike) "
                       'does not decide it; the peak and where it is are in the JSON.',
            'metrics': rows, 'figures': figs(figures), 'videos': figs(videos),
            'limits': ['linear elastic, small deflection, isotropic (printed parts are weaker across layers: the layer strength is used)',
                       'no contact, bolt preload, buckling or impact; sub-millimetre details (text, insert seats) are left out of the mesh',
                       'radius fillets are meshed as 45-degree chamfers (slightly conservative)']}


def thermal_rows():
    out = {}
    for name in ('bare15', 'bare40', f'cooled-{PREV}', f'cooled-{CUR}'):
        r = load(f'exports/thermal/{name}.json')
        if r:
            out[name] = r
    return out


def section_thermal_bare(t):
    if not any(k in t for k in ('bare15', 'bare40')):
        return None
    rows, figures, videos = [], [], []
    for name, w in (('bare15', 15), ('bare40', 40)):
        r = t.get(name)
        if not r:
            continue
        s = r['solids']
        bal = r.get('energy_balance_pct')
        rising = '' if r.get('converged') else (f"still rising when the run stopped ({bal:+.0f} % energy balance, "
                                                f"{len(r.get('continuation', [])) and r['continuation'][-1]['iterations'] or 1200} "
                                                "iterations): the steady value is higher. ")
        rows.append(metric(f'{w} W: SoC package (hottest)', None, s['soc']['max_c'], '°C', better=None, note=rising.strip()))
        rows.append(metric(f'{w} W: thermal plate (hottest)', None, s['ttp']['max_c'], '°C', better=None,
                           note=rising + f"Limit {LIM['ttp_max_c']} °C."))
        figures += [(f'thermal/{name}-section-y.png', f'{w} W, no heatsink: temperature through the module'),
                    (f'thermal/{name}-flow.png', f'{w} W, no heatsink: air rising off the plate'),
                    (f'thermal/{name}-convergence.png', f'{w} W: convergence')]
        videos += [(f'thermal/{name}-flow.mp4', f'{w} W, no heatsink: airflow'), (f'thermal/{name}-sweep.mp4', f'{w} W: section sweep')]
    return {'id': 'bare', 'title': 'Starting point: the AGX module with no heatsink',
            'summary': 'The bare module in the Rev 0.7 enclosure, natural convection only (no fan), heat spread through the aluminium thermal '
                       'plate. It shows why the cooler is not optional.',
            'heads': ('', 'Result'), 'metrics': rows, 'figures': figs(figures), 'videos': figs(videos),
            'limits': (t.get('bare40') or t.get('bare15'))['limits']}


def section_thermal_cooled(t):
    a, b = t.get(f'cooled-{PREV}'), t.get(f'cooled-{CUR}')
    if not (a or b):
        return None
    a = a or {}
    na, nb = a.get('network', {}), (b or {}).get('network', {})
    fa, fb = a.get('fans', {}).get('fan', {}), (b or {}).get('fans', {}).get('fan', {})
    rows = [metric('Thermal plate hot spot', na.get('ttp_hotspot_c'), nb.get('ttp_hotspot_c'), '°C', note=f"limit {LIM['ttp_max_c']} °C"),
            metric('Air entering the fan', fa.get('air_through_fan_c'), fb.get('air_through_fan_c'), '°C',
                   note=f"room {TH['case']['ambient_c']} °C; above it means hot air is being re-breathed"),
            metric('Fan flow', fa.get('flow_cfm'), fb.get('flow_cfm'), 'CFM', better='higher', digits=2,
                   note='free air: 22.9 CFM (Rev 0.8 cooler, 80 mm 5 V fan) / 55.3 CFM (Rev 0.9 cooler, 92 mm 12 V fan)'),
            metric('Hottest air in the enclosure', a.get('air_max_c'), (b or {}).get('air_max_c'), '°C'),
            metric('Heat the fins carry at this fin temperature', a.get('block_heat_w'), (b or {}).get('block_heat_w'), 'W', better='higher',
                   note=f"fins at {na.get('fin_temperature_c')} / {nb.get('fin_temperature_c')} °C; the module makes 40 W."),
            metric('Converged, heat out = heat in', 'yes' if a.get('converged') else 'no', 'yes' if (b or {}).get('converged') else 'no', better=None,
                   note=f"energy balance {a.get('energy_balance_pct')} % / {(b or {}).get('energy_balance_pct')} %"),
            metric('Fin calibration settled', 'yes' if a.get('calibrated') else 'no', 'yes' if (b or {}).get('calibrated') else 'no',
                   better=None, note='no: the fins still carry more (or less) than 40 W, so the plate value is an upper (or lower) bound')]
    figures, videos = [], []
    for name, rv in ((f'cooled-{PREV}', f'Rev {PREV}, 34 mm cooler'), (f'cooled-{CUR}', f'Rev {CUR}, reComputer mini J501 cooler')):
        if name in t:
            figures += [(f'thermal/{name}-section-y.png', f'{rv}: temperature through the cooler'),
                        (f'thermal/{name}-section-x.png', f'{rv}: side section'),
                        (f'thermal/{name}-flow.png', f'{rv}: airflow'),
                        (f'thermal/{name}-walls.png', f'{rv}: air temperature on the walls (red: above the PLA design limit)')]
            videos += [(f'thermal/{name}-flow.mp4', f'{rv}: airflow'), (f'thermal/{name}-sweep.mp4', f'{rv}: section sweep')]
    hs = nb.get('heatsink_model') or na.get('heatsink_model', {})
    return {'id': 'cooled', 'title': 'With the cooler at 40 W',
            'summary': f'Rev {PREV} was simulated with the 34 mm Seeed WS-RDN-601 (80 mm, 5 V fan under a lid with an intake ring). '
                       f'Rev {CUR} uses the cooler actually fitted, the reComputer mini J501 heatsink: a 2 mm copper spreader, a five-heat-pipe '
                       'G48R tower and a 92 mm, 12 V fan whose top sits 2.4 mm under a flush grille in the roof. The two columns compare '
                       'enclosure and cooler together. The CFD resolves the enclosure, vents, grille, skirt and cooler body; the fan is an '
                       'actuator disc on its datasheet curve; the thin fins are a porous block whose resistance comes from the plate-fin model.',
            'metrics': rows, 'figures': figs(figures), 'videos': figs(videos),
            'callouts': [{'html': f"Plate temperature = the fin temperature at which the fins carry 40 W in the CFD + 40 W × "
                                  f"(spreading + base, cadagent.heatsink) + 40 W × pad. A plate-fin model alone gives "
                                  f"{na.get('ttp_hotspot_model_only_c')} °C (Rev {PREV}) / {nb.get('ttp_hotspot_model_only_c')} °C (Rev {CUR}). "
                                  f"Rev {CUR} fins: {hs.get('fin_thickness')} mm plates at {hs.get('pitch')} mm pitch (pitch counted from a photo, "
                                  "thickness assumed). The fan runs its full-speed curve; the board's fan control will run it slower when cool."}],
            'limits': (b or a).get('limits', []) + ['heat leaves the fin block evenly through its volume, so air in stagnant corners of the block runs '
                                                    'hot (the mean temperatures and the fan flow are not affected)',
                                                    'the fan centre is placed from a photo (about ±3 mm)']}


def section_topology():
    items = []
    for study, cap in (('floor', 'Base floor, robot mounting: material kept only on the load path. The empty regions became the Rev 0.8 floor vents.'),
                       ('roof', 'Lid roof under 300 N: where ribs under the roof carry the load.')):
        if exists(f'preview/topology-{study}.png'):
            items.append((study, cap, load(f'exports/topology/{study}.json')))
    if not items:
        return None
    rows = [metric(f'{s}: design region kept', None, round(100 * r['volfrac_result'], 1), '%', better=None) for s, _, r in items if r]
    return {'id': 'topology', 'title': 'Topology optimisation',
            'summary': 'pyMOTO: minimum compliance (stiffest layout) for a volume budget, SIMP with a density filter and an overhang filter '
                       'for support-free printing, solved with MMA. Features that have a job (posts, columns, feet, joints) are kept solid; the '
                       'optimiser decides the rest. The result is read into the parametric CAD, not printed directly.',
            'heads': ('', 'Result'), 'metrics': rows,
            'figures': figs([(f'topology-{s}.png', c) for s, c, _ in items]),
            'videos': figs([(f'topology-{s}.mp4', f'{s}: the layout forming, iteration by iteration') for s, _, _ in items]),
            'limits': ['linear elastic, 2 mm voxels, one load case per study', 'a design guide: the CAD change is checked again with FEA']}


def section_roof():
    sw = load(f'exports/structure/lid-sweep-{CUR}.json')
    if not sw:
        return None
    b, c = sw['best'], sw['criteria']
    rows = [metric(f"{r['roof_mm']:g} mm roof, {r['rib_depth_mm']:g} mm ribs, {r['spokes']} spokes, D{r['hub_mm']:g} hub", None, r['grille_deflection_mm'], 'mm',
                   better=None, digits=2, note=f"{r['volume_cm3']} cm³, roof {r['roof_deflection_mm']} mm, safety factor {r['sf_p999']}"
                   + (' · passes' if r['ok'] else ''))
            for r in sw['rows']]
    return {'id': 'roof', 'title': f'Choosing the Rev {CUR} lid: a parametric sweep',
            'summary': f"{len(sw['rows'])} lids (roof thickness × rib depth × grille spokes and hub), each under the 300 N press. Acceptance, "
                       f"fixed before the sweep: the roof deflects no more than the Rev 0.7 lid ({c['max_deflection_mm']} mm), the fan grille "
                       f"stays at least 1 mm off the fan (≤ {c['max_grille_deflection_mm']} mm), and a safety factor of at least {c['min_sf_p999']}. "
                       + (f"The lightest passing lid: {b['roof_mm']:g} mm roof, {b['rib_depth_mm']:g} mm ribs, {b['spokes']} spokes ({b['volume_cm3']} cm³)."
                          if b else 'No variant passed.')
                       + ' The rib pattern (star) comes from the Rev 0.8 roof topology study.',
            'heads': ('', 'Grille deflection'), 'metrics': rows,
            'figures': figs([(f'lid-sweep-{CUR}.png', 'Lid volume against deflection for each variant; the chosen one is boxed.')]),
            'limits': ['each variant meshed at 3 mm with quadratic tetrahedra; the same load and supports as the Strength section']}


def section_heatsink():
    h = load('exports/heatsink-study.json')
    if not h:
        return None
    c, b = h['current'], h['best']
    return {'id': 'heatsink', 'title': 'Heatsink study (for later)',
            'summary': 'The plate-fin model (cadagent.heatsink) swept over fin pitch and thickness on the cooler\'s own fan curve: '
                       'each design finds its own fan operating point. With this fan, the assumed fin stack is already close to the best '
                       'one, so a different fin stack would gain little. Feeding the fan cooler air, or a fan with more pressure, matters more.',
            'metrics': [metric('Plate rise above intake air at 40 W', c['rise_c'], b['rise_c'], 'K', note=f"best: {b['pitch_mm']} mm pitch, {b['fin_thickness_mm']} mm fins"),
                        metric('Fan flow on the fins alone', c['flow_m3h'], b['flow_m3h'], 'm³/h', better='higher')],
            'heads': ('Assumed current', 'Best in the sweep'),
            'figures': figs([('heatsink-study.png', 'Temperature rise over fin pitch and thickness; circle: assumed current, square: best.')]),
            'limits': [h['note']]}


def section_changes():
    e, c = P['enclosure'], P['cooler']
    g = e['fan_grille']
    return {'id': 'changes', 'title': f'What changed in Rev {CUR}',
            'summary': '<ul>'
                       "<li><b>The cooler is the one actually fitted:</b> Seeed's <i>reComputer mini J501</i> heatsink with fan (S05/S06), "
                       "a 2 mm copper spreader, a G48R tower with five 6 mm heat pipes and a 92 × 15 mm, 12 V fan, 50.3 mm tall above the "
                       "thermal pad. The fan sits about 20 mm toward the front I/O from the module centre (from the user's photo). "
                       "Rev 0.8 had assumed the 34 mm WS-RDN-601, and its printed lid hit this cooler by about 15 mm.</li>"
                       f"<li><b>Enclosure {e['height']:g} mm tall</b> (Rev 0.8: 92 mm, Rev 0.7: 112 mm). The lid is cut away over the fan down to a "
                       f"flush {g['thickness']:g} mm grille ({g['spokes']} spokes, {g['rings']} rings): the fan top is 2.4 mm under it, so the "
                       "enclosure is only as tall as the cooler needs.</li>"
                       f"<li><b>Skirt around the fan frame</b> ({g['skirt_wall']:g} mm wall, {g['clearance']:g} mm clear): the fan breathes only "
                       "through its grille, the exhaust leaves through the hex cells further out and the wall vents, and the cut-out is "
                       "stiffened; the star ribs start on it, with round bosses at the joints.</li>"
                       "<li><b>Recovery riser</b> for a printed Rev 0.8 lid (tools/lid_riser.py, 18 mm, 4 × M3 × 30): not a release part.</li>"
                       '</ul>'}


if __name__ == '__main__':
    t = thermal_rows()
    sections = [s for s in (section_changes(), section_material(), section_structure(), section_roof(), section_thermal_bare(t),
                            section_thermal_cooled(t), section_topology(), section_heatsink()) if s]
    p = write_report(R / 'preview/simulation.html', f'J501 enclosure: Rev {PREV} → Rev {CUR} simulation review', sections,
                     subtitle='The cooler that is actually fitted, the lowest lid over it, still strong. Every number below comes from a simulation or the slicer; '
                              'none of it is a physical test.',
                     meta={'Revision': P['revision'], 'Toolkit': 'cad-agent v0.3.1+ (cadagent.cfd, heatsink, fea, topopt, slicer, simviz)'})
    print(p)
