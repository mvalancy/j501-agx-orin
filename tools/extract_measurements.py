from pathlib import Path
import cadquery as cq, json
root=Path(__file__).resolve().parents[1]
s=cq.Shape.importBrep(str(root/'references/carrier.brep'))
solids=s.Solids(); board=solids[5169]
# These are the exact published STEP's board extents, verified in inspection.
origin=(32.199,-510.506,-1.578)
shift=tuple(-v for v in origin)
board=board.translate(shift)
cq.exporters.export(board,str(root/'references/pcb-outline.step'))
cq.exporters.export(board,str(root/'references/pcb-outline.stl'),tolerance=0.08,angularTolerance=0.2)
holes=[]
for e in board.Edges():
 if e.geomType()=='CIRCLE':
  r=e.radius();c=e.arcCenter()
  if r>1.3:holes.append({'center':[round(c.x,4),round(c.y,4),round(c.z,4)],'diameter':round(r*2,4),'arc_length':round(e.Length(),4)})
(root/'references/pcb-circles.json').write_text(json.dumps(holes,indent=2))
print('CIRCULAR EDGES',json.dumps(holes,indent=2),flush=True)
rows=json.loads((root/'references/solids.json').read_text()); items=[]
for row in rows:
 b=[round(x+shift[i%3],4) for i,x in enumerate(row['bbox'])]
 dx,dy,dz=[b[i+3]-b[i] for i in range(3)]
 if row['index']!=5169 and ((dy>6 and dx>5 and (b[1]<1 or b[4]>162)) or (b[3]>175 and dy>7)):
  items.append({'solid_index':row['index'],'bbox_pcb_datum':b})
(root/'references/edge-components.json').write_text(json.dumps(items,indent=2))
print('EDGE COMPONENTS',json.dumps(items,indent=2),flush=True)
