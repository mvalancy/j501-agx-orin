"""Aggregate check results and verify every local link in the review pages."""
from pathlib import Path
import json,re,hashlib
R=Path(__file__).resolve().parents[1];E=R/'exports'
def load(n):return json.loads((E/n).read_text())
parts=list(load('geometry-checks.json'))
missing=[]
pages={'preview/index.html':(re.compile(r'(?:href|src)="([^"$#?]+)["?]'),[]),'README.md':(re.compile(r'\]\(([^)#]+)\)'),[]),'docs/engineering-review.html':(re.compile(r'href="([^"#?]+)"'),[])}
for page,(rx,_) in pages.items():
 base=(R/page).parent
 for link in rx.findall((R/page).read_text()):
  if link.startswith(('http','mailto')):continue
  if not (base/link).resolve().exists():missing.append(f'{page}: {link}')
for n in parts:
 for ext in ('stl','3mf','step'):
  if not (E/f'{n}.{ext}').exists():missing.append(f'exports/{n}.{ext}')
  png=R/'preview'/f'part-{n}.png'
 if not png.exists():missing.append(str(png.relative_to(R)))
geo=load('geometry-checks.json');pr=load('print-review.json')
def sliced():
 # true only while the slice report has grams for every part and each 3MF is the one that was sliced
 if not (E/'slice-report.json').exists():return False
 rows=load('slice-report.json').get('parts',{})
 return all(n in rows and (rows[n].get('grams') or 0)>0 and (E/f'{n}.3mf').exists() and rows[n].get('sha256')==hashlib.sha256((E/f'{n}.3mf').read_bytes()).hexdigest() for n in parts)
report={'local_links_missing':missing,
 'all_parts_single_valid_watertight':all(v['cad_valid'] and v['solid_count']==1 and v['watertight'] for v in geo.values()),
 'plastic_intersections_zero':all(x['intersection_mm3']<.01 for x in load('assembly-checks.json')['plastic_intersections']),
 'carrier_and_hardware_pass':load('carrier-clearances.json')['pass'],'open_shell_pass':load('shell-clearances.json')['pass'],
 'mount_checks_pass':load('mount-checks.json')['pass'],'port_plug_fit_pass':load('port-checks.json')['pass'],'storage_checks_pass':load('storage-checks.json')['pass'],'assembly_paths_pass':load('assembly-paths.json')['pass'],
 'nominal_P1S_bounds_pass':all(v['within_nominal_P1S_256_cube'] for v in pr.values()),
 'print_parts_checked':len(parts),'physical_fit_verified':False,'slicer_run':sliced()}
(E/'review-validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
