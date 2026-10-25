from pathlib import Path
import cadquery as cq,numpy as np,json
root=Path(__file__).resolve().parents[1]
s=cq.importers.importStep(str(root/'references/pcb-outline.step')).val()
f=max(s.Faces(),key=lambda f:f.Area())
rows=[]
for w in f.Wires():
 b=w.BoundingBox();pts=[]
 for e in w.Edges():
  pts.extend([[p.x,p.y] for p in e.positions(np.linspace(0,1,17))])
 a=np.array(pts);A=np.c_[2*a[:,0],2*a[:,1],np.ones(len(a))];cx,cy,k=np.linalg.lstsq(A,(a*a).sum(axis=1),rcond=None)[0]
 radius=np.sqrt(k+cx*cx+cy*cy);err=np.sqrt(((np.sqrt(((a-[cx,cy])**2).sum(axis=1))-radius)**2).mean())
 row={'center':[round(cx,4),round(cy,4)],'diameter_fit':round(2*radius,4),'radial_rms_mm':round(err,6),'bbox':[round(v,4) for v in (b.xmin,b.ymin,b.xmax,b.ymax)]}
 rows.append(row)
(root/'references/pcb-hole-fits.json').write_text(json.dumps(rows,indent=2))
for r in rows:
 if r['radial_rms_mm']<0.01:print(r)
