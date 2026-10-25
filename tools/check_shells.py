from pathlib import Path
import cadquery as cq,sys,json
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'cad'));import build as b
s=cq.Shape.importBrep(str(R/'references/carrier.brep'));shells=[]
def walk(v):
 if v.ShapeType()=='Solid':return
 if v.ShapeType() in ('Shell','Face'):shells.append(v);return
 for c in v:walk(c)
walk(s);rows=json.loads((R/'references/open-shells.json').read_text());collisions=[]
for name,shape in [('base',b.base()),('front_gmsl',b.panel(gmsl=True)),('front_no_gmsl',b.panel()),('rear_io',b.panel(False)),('cover',b.cover()),('side_hatch',b.side_hatch())]:
 bb=shape.BoundingBox();bb=[bb.xmin,bb.ymin,bb.zmin,bb.xmax,bb.ymax,bb.zmax]
 for i,row in enumerate(rows):
  bounds=[v+[b.M,b.M,b.Z][k%3] for k,v in enumerate(row['normalized_bbox'])]
  if any(bounds[k+3]<bb[k] or bounds[k]>bb[k+3] for k in range(3)):continue
  shell=shells[i].translate((b.M-32.199,b.M+510.506,b.Z+1.578))
  common=shape.intersect(shell);area=common.Area()
  if area>.01:collisions.append({'part':name,'shell':i,'clipped_area_mm2':round(area,4)})
 print(name,flush=True)
(R/'exports/shell-clearances.json').write_text(json.dumps({'method':'Clip each open source shell against plastic solid; nonzero common face area signals intrusion, not penetration volume. Tangency may require inspection.','collisions':collisions,'pass':not collisions},indent=2));print(collisions)
