"""Exact carrier-to-plastic and hardware-to-plastic intersections, using AABB only as a broad-phase filter."""
from pathlib import Path
import sys,json,cadquery as cq
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'cad'));import build as b;import hardware as h
source=cq.Shape.importBrep(str(R/'references/carrier.brep')).Solids()
rows=json.loads((R/'references/solids.json').read_text());origin=b.p['origin_in_source_step'];shift=[b.M-origin[0],b.M-origin[1],b.Z-origin[2]]
parts={'base_mount':b.base(True),'front_gmsl':b.panel(gmsl=True),'front_no_gmsl':b.panel(),'rear_io':b.panel(False),'cover':b.cover(),'side_hatch':b.side_hatch(),'mount_fit_template_in_place':b.fit_template().translate((0,0,b.Z-b.e['fit_template_height']))}
result=[];tested=0;degenerate=[]
# Plastic near the carrier: everything below the PCB underside, plus the side/front/rear margins.
X1,Y1=b.M+b.p['width'],b.M+b.p['depth']
regions=[[0,b.Y0,0,b.W,b.Y1,b.Z+.01],[0,b.Y0,0,b.M,b.Y1,b.H],[X1,b.Y0,0,b.W,b.Y1,b.H],[0,b.Y0,0,b.W,b.M,b.H],[0,Y1,0,b.W,b.Y1,b.H]]
def overlap(a,bb):return all(a[k+3]>bb[k]+.0001 and a[k]<bb[k+3]-.0001 for k in range(3))
for name,s in parts.items():
 bb=s.BoundingBox();bounds=[bb.xmin,bb.ymin,bb.zmin,bb.xmax,bb.ymax,bb.zmax]
 for row in rows:
  i=row['index']
  if any(row['bbox'][k+3]-row['bbox'][k]<.00001 for k in range(3)):
   if i not in degenerate:degenerate.append(i)
   continue
  if i in range(5155,5163):continue # mount-hole display proxies, not physical material
  r=[q+shift[k%3] for k,q in enumerate(row['bbox'])]
  if any(r[k+3]<=bounds[k]+.0001 or r[k]>=bounds[k+3]-.0001 for k in range(3)):continue
  if name=='base_mount' and not any(overlap(r,q) for q in regions):continue
  tested+=1;v=s.intersect(source[i].translate(shift)).Volume()
  if v>.01:
   result.append({'part':name,'source_solid':i,'intersection_mm3':round(v,5),'source_bbox':row['bbox']});print(result[-1],flush=True)
 print(name,'done',flush=True)
# Modeled hardware, cooler/module and GMSL envelopes. Heat-set inserts interfere with their pilots by design.
hw=[];intended=[]
for item,s,_ in h.enclosure_hardware()+h.cooler_and_module()+h.gmsl()+h.carrier_supplements():
 for name,p in parts.items():
  if name.startswith('mount_fit_template') and ('insert' in item or item.startswith('H7')):continue  # jig: plain 3.4 holes, used without inserts or tie-down screws
  a,q=s.BoundingBox(),p.BoundingBox()
  if a.xmax<q.xmin or a.xmin>q.xmax or a.ymax<q.ymin or a.ymin>q.ymax or a.zmax<q.zmin or a.zmin>q.zmax:continue
  v=p.intersect(s).Volume()
  if v>.01:(intended if 'insert' in item else hw).append({'item':item,'part':name,'intersection_mm3':round(v,4)})
(R/'exports/carrier-clearances.json').write_text(json.dumps({'method':'Exact BREP common volume after bounding-box broad phase; excludes mount proxies 5155..5162. Touching land-to-PCB faces allowed. Source connector internals preserved.','excluded_zero_thickness_source_solids':degenerate,'scope':'Carrier solids plus modeled hardware, module, reference cooler and provisional GMSL envelopes. Open shells checked separately. Cables not modeled.','pairs_tested':tested,'collisions':result,'hardware_collisions':hw,'intended_insert_interference':intended,'pass':not result and not hw},indent=2))
print('Done:',len(result),'carrier collisions;',len(hw),'hardware collisions;',len(intended),'intended insert interferences',flush=True)
