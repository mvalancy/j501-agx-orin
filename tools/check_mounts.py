"""Check the tab variant: plastic overlap, washer support and driver access."""
from pathlib import Path
import sys,json
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'cad'));import build as b
base=b.base(True);e=b.e;parts={'cover':b.cover(),'front_gmsl':b.panel(gmsl=True),'front_no_gmsl':b.panel(),'rear_io':b.panel(False),'side_hatch':b.side_hatch()};checks=[]
for name,s in parts.items():
 v=base.intersect(s).Volume();checks.append({'parts':['base_mount',name],'intersection_mm3':round(v,6)});assert v<.01,(name,v)
washer=[];tools=[];t=e['mount_ear_thickness'];L,w=e['mount_slot']
for x,y in b.mount_slot_centers():
 front=y<b.Y0;pad=b.mount_ear(x,front)
 for offset in (-(L-w)/2,0,(L-w)/2):
  disk=b.cyl(x+offset,y,t-.01,e['mount_washer_envelope_diameter']/2,.01)
  missing=disk.cut(pad).Volume();washer.append({'center':[round(x+offset,2),y],'unsupported_area_mm2':round(missing/.01,4)});assert missing<.0001
 tool=b.cyl(x,y,t+.5,e['mount_tool_envelope_diameter']/2,b.H+40)
 v=sum(tool.intersect(s).Volume() for s in [base]+list(parts.values()))
 tools.append({'center':[x,y],'tool_diameter':e['mount_tool_envelope_diameter'],'tool_bottom_z':t+.5,'plastic_intersection_mm3':round(v,6)});assert v<.01
report={'revision':b.P['revision'],'mounted_variant_intersections':checks,'washer_16mm_full_support_at_slot_ends':washer,'driver_access':tools,'slot_centers':b.mount_slot_centers(),
 'scope':'Flat tab support tested before cutting the slot; does not imply material under the washer hole. No load rating.','pass':True}
(R/'exports/mount-checks.json').write_text(json.dumps(report,indent=2));print('Mounted variant, washer envelopes and driver access pass')
