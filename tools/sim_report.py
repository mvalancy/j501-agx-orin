"""The Rev 0.7 -> Rev 0.8 simulation and optimisation report (cadagent.simreport): preview/simulation.html.

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


def load(rel):
    p = R / rel
    return json.loads(p.read_text()) if p.exists() else None


def exists(rel):
    return (R / rel).exists()


def figs(items):
    # the page lives in preview/, next to the pictures
    return [{'src': s, 'caption': c} for s, c in items if exists('preview/' + s)]


def section_material():
    a, b = load('exports/slice-report-0.7.json'), load('exports/slice-report-0.8.json')
    if not (a and b):
        return None
    names = {'base': 'Base (P1)', 'cover': 'Lid (P2)', 'front_no_gmsl': 'Front plate (P4)', 'rear_io': 'Rear plate (P5)', 'side_hatch': 'Side hatch (P10)'}
    rows = [metric(names.get(k, k), a['parts'][k]['grams'], b['parts'][k]['grams'], 'g') for k in names if k in a['parts'] and k in b['parts']]
    rows.append(metric('Enclosure total', a['total_grams'], b['total_grams'], 'g'))
    rows.append(metric('Print time, all five parts', a['total_hours'], b['total_hours'], 'h', digits=2))
    o = load('exports/slice-options-0.8.json')
    extra = []
    if o:
        base = o['15% grid (default)']['base+lid']
        extra = [f"Option: {k} infill on the Rev 0.8 base and lid gives {v['base+lid']} g (default profile {base} g). "
                 'Not the default: the FEA models solid walls.' for k, v in o.items() if k != '15% grid (default)']
    return {'id': 'material', 'title': 'Filament and print time',
            'summary': f"Measured with the Bambu Studio command line on a P1S ({b['process']}, {b['filament']}), the same profile for "
                       "both revisions. These are the slicer's grams, not CAD volumes.",
            'metrics': rows, 'limits': [b['note'], 'One copy of each part; the plates are unchanged between revisions.'] + extra}


def section_structure():
    rows, figures, videos = [], [], []
    labels = {'lid_press': '300 N on the lid', 'base_mount': 'Robot mounting, 10 g down + 5 g sideways'}
    for case, label in labels.items():
        a, b = load(f'exports/structure/{case}-0.7.json'), load(f'exports/structure/{case}-0.8.json')
        if not (a and b):
            continue
        rows += [metric(f'{label}: deflection', a['max_displacement_mm'], b['max_displacement_mm'], 'mm', digits=2),
                 metric(f'{label}: stress, 99.9th percentile', a.get('von_mises_p999_mpa'), b.get('von_mises_p999_mpa'), 'MPa', digits=1),
                 metric(f'{label}: safety factor (99.9th percentile)', a.get('safety_factor_p999'), b.get('safety_factor_p999'), '', better='higher', digits=2),
                 metric(f'{label}: stiffness', a.get('stiffness_n_per_mm'), b.get('stiffness_n_per_mm'), 'N/mm', better='higher', digits=0)]
        for rev in ('0.7', '0.8'):
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
    for name in ('bare15', 'bare40', 'cooled', 'cooled-0.8'):
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
        rows.append(metric(f'{w} W: SoC package (hottest)', None, s['soc']['max_c'], '°C', better=None))
        rows.append(metric(f'{w} W: thermal plate (hottest)', None, s['ttp']['max_c'], '°C', better=None,
                           note=f"limit {LIM['ttp_max_c']} °C"))
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
    a, b = t.get('cooled'), t.get('cooled-0.8')
    if not a:
        return None
    na, nb = a.get('network', {}), (b or {}).get('network', {})
    fa, fb = a['fans'].get('fan', {}), (b or {}).get('fans', {}).get('fan', {})
    rows = [metric('Thermal plate hot spot', na.get('ttp_hotspot_c'), nb.get('ttp_hotspot_c'), '°C', note=f"limit {LIM['ttp_max_c']} °C"),
            metric('Air entering the fan', fa.get('air_through_fan_c'), fb.get('air_through_fan_c'), '°C',
                   note=f"room {TH['case']['ambient_c']} °C; above it means hot air is being re-breathed"),
            metric('Fan flow', fa.get('flow_cfm'), fb.get('flow_cfm'), 'CFM', better='higher', digits=2, note='22.9 CFM free air'),
            metric('Hottest air in the enclosure', a.get('air_max_c'), (b or {}).get('air_max_c'), '°C')]
    figures, videos = [], []
    for name, rv in (('cooled', 'Rev 0.7'), ('cooled-0.8', 'Rev 0.8')):
        if name in t:
            figures += [(f'thermal/{name}-section-y.png', f'{rv}: temperature through the cooler'),
                        (f'thermal/{name}-section-x.png', f'{rv}: side section'),
                        (f'thermal/{name}-flow.png', f'{rv}: airflow'),
                        (f'thermal/{name}-walls.png', f'{rv}: air temperature on the walls (red: above the PLA design limit)')]
            videos += [(f'thermal/{name}-flow.mp4', f'{rv}: airflow'), (f'thermal/{name}-sweep.mp4', f'{rv}: section sweep')]
    hs = na.get('heatsink_model', {})
    return {'id': 'cooled', 'title': 'With the J501 cooler (heat pipes, fins, 80 mm fan)',
            'summary': 'Seeed WS-RDN-601 cooler at 40 W in the enclosure on a table in 25 °C room air. The CFD resolves the enclosure, '
                       'vents, intake ring and cooler shroud; the fan is an actuator disc on its datasheet curve; the thin stacked fins are a '
                       'porous block whose resistance comes from the plate-fin model, which also gives the plate temperature at the CFD flow '
                       'and intake air temperature.',
            'metrics': rows, 'figures': figs(figures), 'videos': figs(videos),
            'callouts': [{'html': f"Plate temperature = air entering the fins (CFD) + 40 W × heatsink resistance "
                                  f"({na.get('heatsink', {}).get('total_k_per_w', 0):.3f} K/W at the CFD flow, cadagent.heatsink) + pad. "
                                  f"Fin geometry assumed: {hs.get('fin_thickness')} mm fins at {hs.get('pitch')} mm pitch "
                                  "(measure your cooler)."}] if na else [],
            'limits': a['limits'] + ['heat leaves the fin block evenly through its volume, so air in stagnant corners of the block runs hot '
                                     '(the mean temperatures and the fan flow are not affected)',
                                     'cooler internals (fin pitch, heat pipes, which faces exhaust) are assumed from the datasheet photo']}


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
    sw = load('exports/structure/roof-sweep.json')
    if not sw:
        return None
    b = sw['best']
    rows = [metric(f"{r['roof_mm']:g} mm roof, ribs: {r['ribs']}", None, r['deflection_mm'], 'mm', better=None, digits=2,
                   note=f"{r['volume_cm3']} cm³, safety factor {r['sf_p999']}" + (' · passes' if r['ok'] else ''))
            for r in sw['rows']]
    return {'id': 'roof', 'title': 'Choosing the roof: a parametric sweep',
            'summary': f"Nine lids (roof 3.5 / 4 / 4.5 mm × no ribs, a cross, or the star the roof topology study suggested), each under "
                       f"the 300 N press. Acceptance, fixed before the sweep: deflection no worse than Rev 0.7 ({sw['target_deflection_mm']:.2f} mm) "
                       f"and a safety factor of at least 2. The lightest passing lid is the {b['roof_mm']:g} mm roof with star ribs "
                       f"({b['volume_cm3']} cm³). In the final lid, the ribs run 1.5 mm into the walls and the ring (for a clean print "
                       "mesh), which made it stiffer still (see Strength).",
            'heads': ('', 'Deflection'), 'metrics': rows,
            'figures': figs([('roof-sweep.png', 'Lid volume against deflection for each variant; the chosen one is boxed.')]),
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
    d = P['enclosure'].get('fan_duct', {})
    return {'id': 'changes', 'title': 'What changed in Rev 0.8',
            'summary': '<ul>'
                       f"<li><b>Cooler size corrected</b> to the Seeed WS-RDN-601 datasheet, 100 × 87 × 34 mm (the README's reference cooler). "
                       "The old 110 × 100 × 50 mm envelope came from Seeed's <i>reComputer mini J501</i> heatsink, a different product.</li>"
                       f"<li><b>Lid {P['enclosure']['height'] - 72:g} mm tall instead of 40</b> (enclosure {P['enclosure']['height']:g} mm high), "
                       f"roof {P['enclosure']['roof_thickness']:g} mm, with stiffening ribs where the roof study put them.</li>"
                       f"<li><b>Fan intake ring</b> (D{d.get('inner_diameter', 0):g} mm) from the roof to {d.get('gap_above_cooler', 0):g} mm above the "
                       "cooler: the fan breathes room air through the hex cells inside the ring, and the hot exhaust leaves through the cells "
                       "around it and the side vents.</li>"
                       "<li><b>Floor vents</b> where the floor topology study found no load path: less filament, and cool air in under the board.</li>"
                       '</ul>',
            'callouts': [{'warn': True, 'html': '<b>Before printing Rev 0.8:</b> measure your cooler (height, and which two faces show fin '
                                                'edges). Rev 0.8 assumes the 34 mm datasheet height; a 50 mm cooler will not fit under the lower lid.'}]}


if __name__ == '__main__':
    t = thermal_rows()
    sections = [s for s in (section_changes(), section_material(), section_structure(), section_roof(), section_thermal_bare(t),
                            section_thermal_cooled(t), section_topology(), section_heatsink()) if s]
    p = write_report(R / 'preview/simulation.html', 'J501 enclosure: Rev 0.7 → Rev 0.8 simulation review', sections,
                     subtitle='Less filament, still strong, better airflow. Every number below comes from a simulation or the slicer; '
                              'none of it is a physical test.',
                     meta={'Revision': P['revision'], 'Toolkit': 'cad-agent feat/fea (cadagent.cfd, heatsink, fea, topopt, slicer, simviz)'})
    print(p)
