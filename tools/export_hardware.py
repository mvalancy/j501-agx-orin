from pathlib import Path
import cadquery as cq,json
ROOT=Path(__file__).resolve().parents[1]; out=ROOT/'references/hardware';out.mkdir(exist_ok=True)
s=cq.Shape.importBrep(str(ROOT/'references/carrier.brep'));ss=s.Solids();shift=(-32.199,510.506,1.578)
# Full carrier retains terminals, connectors and other original components.
print('Exporting full carrier mesh',flush=True)
display_shape=cq.Compound.makeCompound([v for i,v in enumerate(ss) if i not in range(5155,5163)])
cq.exporters.export(display_shape.translate(shift),str(out/'carrier-full.stl'),tolerance=.25,angularTolerance=.35)
# Named mechanical overlays give important physical components distinct colors.
parts={'front_power':2897,'ethernet_10g':4439,'ethernet_1g':4650,'rear_terminal':4922,
       'rear_tall_connector':4863,'rear_usb_lower':5170,'rear_usb_upper':5171,
       'rear_connector_flat':5154,'rear_bottom_port_a':4819,'rear_bottom_port_b':5137,
       'front_bottom_port':4848,'side_header':4867,'module_socket':2149}
for name,i in parts.items():
 print(name,flush=True);cq.exporters.export(ss[i].translate(shift),str(out/(name+'.stl')),tolerance=.15,angularTolerance=.3)
(out/'indices.json').write_text(json.dumps(parts,indent=2)+'\n')
print('Hardware mesh export complete',flush=True)
