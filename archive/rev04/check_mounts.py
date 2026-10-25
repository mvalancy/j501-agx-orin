"""Check the projecting base variant, washer support envelope and tool access."""
from pathlib import Path
import sys,json
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'cad'));import build as b
base=b.base(True);parts={'cover':b.cover(),'front_gmsl':b.panel(gmsl=True),'front_no_gmsl':b.panel(),'rear_io':b.panel(False),'side_hatch':b.side_hatch()};checks=[]
for name,s in parts.items():
 v=base.intersect(s).Volume();checks.append({'parts':['base_mount',name],'intersection_mm3':round(v,6)});assert v<.01,(name,v)
washer=[]
for x in b.e['mount_ear_x']:
 for front in (True,False):
  y=-b.e['mount_hole_offset'] if front else b.D+b.e['mount_hole_offset'];pad=b.mount_pad(x,front)
  for offset in (-2.7,0,2.7):
   disk=b.cyl(x+offset,y,b.e['mount_ear_thickness']-.01,8,.01)
   missing=disk.cut(pad).Volume();washer.append({'center':[x+offset,y],'unsupported_volume_before_intentional_slot_mm3':round(missing,8)});assert missing<.0001
report={'revision':b.P['revision'],'mounted_variant_intersections':checks,'washer_16mm_envelope_full_flat_pad_support_at_slot_endpoints':washer,'scope':'Flat pad support tested before cutting the intentional mounting slot; does not imply the washer has material under its hole. No load rating. Tool access checks are in design-metrics.json.','pass':True}
(R/'exports/mount-checks.json').write_text(json.dumps(report,indent=2));print('Mounted variant and 12 washer-envelope positions pass')
