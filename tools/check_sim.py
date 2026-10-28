"""Simulation acceptance for the current revision: reads the committed results, never re-runs them.

Fails when a result is missing, was produced for another revision (the revision string recorded with it), or misses its
criteria (cad/parameters.json: structure, thermal.criteria). The cooled CFD case must have converged with a settled
fin calibration. The single-element peak stress is reported as advisory: at a sharp inside corner it grows with mesh
refinement, so the gate is the 99.9th-percentile stress.
Writes exports/simulation-checks.json.
"""
from pathlib import Path
import sys, json, hashlib
R = Path(__file__).resolve().parents[1]
P = json.loads((R / 'cad/parameters.json').read_text())
REV = P['revision'].split('-')[0]


def load(rel):
    p = R / rel
    return json.loads(p.read_text()) if p.exists() else None


rows, ok = [], True


def row(name, passed, detail, advisory=False):
    """An advisory row is reported (pass or warn) but does not fail the gate: a diagnostic whose effect a gated
    row already includes."""
    global ok
    if not advisory:
        ok = ok and passed
    rows.append({'check': name, 'pass': bool(passed), 'detail': detail, **({'advisory': True} if advisory else {})})


crit = P['structure']
for case, c in (('lid_press', crit['lid_press']), ('base_mount', crit['base_mount'])):
    r = load(f'exports/structure/{case}-{REV}.json')
    if not r:
        row(f'structure {case}', False, f'exports/structure/{case}-{REV}.json missing: run tools/structure.py')
        continue
    sf = r.get('safety_factor_p999')
    if 'grille_max_displacement_mm' in r and 'max_grille_deflection_mm' in c:   # roof and fan grille judged separately
        d, dg = r['roof_max_displacement_mm'], r['grille_max_displacement_mm']
        passed = sf is not None and sf >= c['min_sf_p999'] and d <= c['max_deflection_mm'] and dg <= c['max_grille_deflection_mm'] and r.get('revision') == P['revision']
        row(f'structure {case}', passed, f"SF {sf} (min {c['min_sf_p999']}), roof deflection {d} mm (max {c['max_deflection_mm']}), "
            f"fan grille {dg} mm (max {c['max_grille_deflection_mm']}, fan {r.get('fan_clearance_mm')} mm below), revision {r.get('revision')}")
    else:
        passed = sf is not None and sf >= c['min_sf_p999'] and r['max_displacement_mm'] <= c.get('max_deflection_mm', 1e9) and r.get('revision') == P['revision']
        row(f'structure {case}', passed, f"SF {sf} (min {c['min_sf_p999']}), deflection {r['max_displacement_mm']} mm"
            + (f" (max {c['max_deflection_mm']})" if 'max_deflection_mm' in c else '') + f", revision {r.get('revision')}")
    row(f'structure {case}: peak', (r.get('safety_factor') or 0) >= 1.0,
        f"single-element peak {r.get('max_von_mises_mpa')} MPa, SF {r.get('safety_factor')} at {r.get('peak_at_mm')} mm; "
        "advisory: a sharp inside corner, mesh-dependent", advisory=True)

t = load(f'exports/thermal/cooled-{REV}.json') if REV != '0.7' else load('exports/thermal/cooled.json')
tc = P['thermal']['criteria']
if not t:
    row('thermal cooled', False, 'no CFD result for this revision: run tools/thermal.py cooled')
else:
    n, f = t.get('network', {}), t['fans'].get('fan', {})
    margin = n.get('margin_c', -1)
    # air into the fins (thermal.py works it out for either fan direction; older results: the air through the fan)
    intake = n.get('air_into_fins_c', f.get('air_through_fan_c', 99)) - P['thermal']['case']['ambient_c']
    row('CFD on this revision', t.get('revision', P['revision']) == P['revision'], f"result revision {t.get('revision', 'not recorded')}")
    row('thermal plate margin', margin >= tc['ttp_margin_c'], f"{n.get('ttp_hotspot_c')} °C, {margin} K under the limit (min {tc['ttp_margin_c']})")
    row('fan operating point', f.get('fraction_of_free_air', 0) >= tc['min_fan_fraction_of_free_air'], f"{f.get('flow_cfm')} CFM, {f.get('fraction_of_free_air')} of free air")
    row('no re-breathing', intake <= tc['max_intake_rise_c'],
        f"air into the fins {intake:+.1f} K above the room (target {tc['max_intake_rise_c']} K); advisory: its effect is in "
        "the plate temperature, which is gated above", advisory=True)
    row('CFD converged', bool(t.get('converged')) and bool(t.get('calibrated')),
        f"fins calibrated: {bool(t.get('calibrated'))} (carry {t.get('block_heat_w')} W of 40); energy balance "
        f"{t.get('energy_balance_pct')} %")

# filament is reported by `cad-agent slice` (the report checks its 3MF hashes), not gated here
out = {'revision': P['revision'], 'pass': ok, 'checks': rows,
       'note': 'Reads committed simulation results; CFD and topology optimisation are run by hand (hours), FEA by tools/structure.py.'}
(R / 'exports/simulation-checks.json').write_text(json.dumps(out, indent=2) + '\n')
for r in rows:
    print(('PASS ' if r['pass'] else 'WARN ' if r.get('advisory') else 'FAIL ') + r['check'] + ': ' + r['detail'])
print('simulation checks', 'PASS' if ok else 'FAIL')
