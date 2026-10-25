from pathlib import Path
import cadquery as cq,json
root=Path(__file__).resolve().parents[1]
s=cq.Shape.importBrep(str(root/'references/carrier.brep'));solids=s.Solids()
shift=(-32.199,510.506,1.578)
rows=[]
for i in range(5155,5163):
 t=solids[i].translate(shift);b=t.BoundingBox();ed=[]
 for e in t.Edges():
  if e.geomType()=='CIRCLE':ed.append(round(e.radius()*2,4))
 rows.append({'solid_index':i,'center_xy':[round((b.xmin+b.xmax)/2,4),round((b.ymin+b.ymax)/2,4)],'bbox':[round(v,4) for v in (b.xmin,b.ymin,b.zmin,b.xmax,b.ymax,b.zmax)],'circle_diameters':sorted(set(ed))})
(root/'references/mount-features.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2),flush=True)
# Save a manageable subset for independent inspection and visual registration.
ids=[5169,5155,5156,5157,5158,5159,5160,5161,5162,2149,4439,4650,2897,4863,4867,4922,5137,5154,5170,5171,4819,4848]
small=cq.Compound.makeCompound([solids[i].translate(shift) for i in ids])
cq.exporters.export(small,str(root/'references/carrier-mechanical-subset.step'))
cq.exporters.export(small,str(root/'references/carrier-mechanical-subset.stl'),tolerance=0.1,angularTolerance=0.25)
