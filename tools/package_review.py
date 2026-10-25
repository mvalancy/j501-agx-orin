from pathlib import Path
import zipfile,json,hashlib
R=Path(__file__).resolve().parents[1];report=json.loads((R/'exports/geometry-checks.json').read_text())
files=[R/'README.md',R/'requirements.txt',R/'cad/parameters.json']+list((R/'docs').glob('*'))
for name in report:
 files.extend([R/'exports'/(name+'.stl'),R/'exports'/(name+'.3mf'),R/'exports'/(name+'.step')])
files+=[p for p in (R/'exports').glob('*.json') if p.name!='review-package-manifest.json']+[R/'references/sources.json']
with zipfile.ZipFile(R/'exports/j501-agx-rev06-fit-check.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in files:
  if p.is_file():z.write(p,str(p.relative_to(R)))
manifest={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.is_file()}
(R/'exports/review-package-manifest.json').write_text(json.dumps(manifest,indent=2))
print('Packaged',len(files),'files')
