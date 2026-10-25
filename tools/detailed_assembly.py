from pathlib import Path
import sys,cadquery as cq
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'cad'));import build as b;import hardware as h
src=cq.Shape.importBrep(str(R/'references/carrier.brep'));ss=src.Solids();skip=[ss[i] for i in list(range(5155,5163))+[4981,4982,4983,4984]];bodies=[]
def walk(s):
 if s.ShapeType() in ('Solid','Shell','Face'):
  if not any(s.isSame(v) for v in skip):bodies.append(s)
  return
 for v in s:walk(v)
walk(src);carrier=cq.Compound.makeCompound(bodies).translate((b.M-32.199,b.M+510.506,b.Z+1.578))
a=cq.Assembly(name='J501_rev04_provisional_detailed')
for name,s in [('P1M_base',b.base(True)),('P2_cover',b.cover()),('P3_front_gmsl',b.panel(gmsl=True)),('P5_rear',b.panel(False)),('P10_side_hatch',b.side_hatch())]:a.add(s,name=name,color=cq.Color(.2,.4,.5))
a.add(carrier,name='E1_Seeed_carrier_solids_and_shells',color=cq.Color(.2,.3,.2))
for i,(name,s,col) in enumerate(h.enclosure_hardware()+h.cooler_and_module()+h.gmsl()+h.carrier_supplements()):a.add(s,name=f'component_{i:03d}_'+''.join(c if c.isalnum() else '_' for c in name),color=cq.Color(*col))
for i,(_,s,col) in enumerate(h.carrier_supplements()):cq.exporters.export(s.translate((-b.M,-b.M,-b.Z)),str(R/'references/hardware'/f'J26-envelope-{i}.stl'),tolerance=.1)
# Separate downloaded-module / candidate connector assemblies for review.
cq.exporters.export(cq.Compound.makeCompound([s for name,s,_ in h.gmsl()]),str(R/'exports/gmsl_reference_assembly.step'))
cq.exporters.export(cq.Compound.makeCompound([s for name,s,_ in h.cooler_and_module() if name.startswith('E2')]),str(R/'exports/module_registered.step'))
print('Writing detailed assembly with source open shells',flush=True);a.save(str(R/'exports/assembly_detailed.step'));print('Done',flush=True)
