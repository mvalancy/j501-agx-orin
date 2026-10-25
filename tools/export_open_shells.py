from pathlib import Path
import cadquery as cq,json
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
R=Path(__file__).resolve().parents[1];s=cq.Shape.importBrep(str(R/'references/carrier.brep'));shells=[]
def walk(v):
 t=v.ShapeType()
 if t=='Solid':return
 if t in ('Shell','Face'):shells.append(v);return
 for c in v:walk(c)
walk(s);rows=[];shift=(-32.199,510.506,1.578)
for i,v in enumerate(shells):
 bb=Bnd_Box();BRepBndLib.AddOptimal_s(v.wrapped,bb,False,False);bb=list(bb.Get());a=[round(x+shift[k%3],4) for k,x in enumerate(bb)]
 rows.append({'shell_index':i,'normalized_bbox':a})
 if a[1]<3 or a[4]>160:print(rows[-1],flush=True)
(R/'references/open-shells.json').write_text(json.dumps(rows,indent=2))
cq.exporters.export(cq.Compound.makeCompound(shells).translate(shift),str(R/'references/hardware/carrier-open-shells.stl'),tolerance=.15,angularTolerance=.25)
print('Exported',len(shells),'open shells',flush=True)
