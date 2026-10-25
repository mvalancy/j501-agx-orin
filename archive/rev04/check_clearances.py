"""Exact carrier-to-plastic intersections, using AABB only as a broad-phase filter."""
from pathlib import Path
import sys,json,cadquery as cq
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'cad'));import build as b
source=cq.Shape.importBrep(str(R/'references/carrier.brep')).Solids()
rows=json.loads((R/'references/solids.json').read_text());origin=b.p['origin_in_source_step'];shift=[b.M-origin[0],b.M-origin[1],b.Z-origin[2]]
parts={'base':b.base(),'front_gmsl':b.panel(gmsl=True),'rear_io':b.panel(False),'cover':b.cover(),'side_hatch':b.side_hatch()}
result=[];tested=0;degenerate=[]
regions=[[0,0,0,b.W,b.D,b.F],[0,0,b.F,14,b.D,b.BH],[b.W-14,0,0,b.W+11,b.D,b.BH]]
regions += [[b.M+x-8,b.M+y-8,b.F,b.M+x+8,b.M+y+8,b.Z] for x,y in b.p['mount_holes']]
regions += [[10,12.8,50,30,25.8,b.BH],[b.W-30,12.8,50,b.W-10,25.8,b.BH],[10,b.D-25.8,50,30,b.D-12.8,b.BH],[b.W-30,b.D-25.8,50,b.W-10,b.D-12.8,b.BH]]
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
  if name=='base' and not any(overlap(r,bb) for bb in regions):continue
  # Skip the enormous PCB when it is only coplanar with the support lands.
  tested+=1;v=s.intersect(source[i].translate(shift)).Volume()
  if v>.01:
   result.append({'part':name,'source_solid':i,'intersection_mm3':round(v,5),'source_bbox':row['bbox']});print(result[-1],flush=True)
 print(name,'done',flush=True)
(R/'exports/carrier-clearances.json').write_text(json.dumps({'method':'Exact BREP common volume after bounding-box broad phase; excludes mount proxies 5155..5162. Touching land-to-PCB faces allowed. Source connector internals preserved.','excluded_zero_thickness_source_solids':degenerate,'scope':'Carrier solids only; open shells checked separately. Does not validate unconfirmed cooler/GMSL/cables.', 'pairs_tested':tested,'collisions':result,'pass':not result},indent=2))
print('Done:',len(result),'collisions',flush=True)
