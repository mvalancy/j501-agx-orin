from pathlib import Path
import cadquery as cq
from OCP.BRepBndLib import BRepBndLib
from OCP.Bnd import Bnd_Box
import json
root=Path(__file__).resolve().parents[1]
cache=root/'references/carrier.brep'
print('Importing cached BREP' if cache.exists() else 'Importing STEP',flush=True)
if cache.exists(): s=cq.Shape.importBrep(str(cache))
else:
 s=cq.importers.importStep(str(root/'references/RESERVER_AGX_ORIN_CARRIER_BOARD.stp')).val()
 s.exportBrep(str(cache))
print('Imported',flush=True)
def bb(s):
 b=Bnd_Box();BRepBndLib.AddOptimal_s(s.wrapped,b,False,False)
 return [round(x,4) for x in b.Get()]
solids=s.Solids();rows=[]
for i,v in enumerate(solids):
 rows.append({'index':i,'bbox':bb(v)})
 if i%500==0:print('solid',i,'/',len(solids),flush=True)
(root/'references/solids.json').write_text(json.dumps(rows,indent=2))
print('BOUNDING BOX',bb(s),'SOLIDS',len(solids),flush=True)
print(json.dumps(sorted(rows,key=lambda x:(x['bbox'][3]-x['bbox'][0])*(x['bbox'][4]-x['bbox'][1]),reverse=True)[:30],indent=2),flush=True)
