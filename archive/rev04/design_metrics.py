from pathlib import Path
import json,sys,math
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'cad'));import build as b
cover=b.cover();base=b.base(True);e=b.e
outer=(b.W+2*(b.T+b.C))*(b.D+2*(b.T+b.C))-(4-math.pi)*e['cover_corner_radius']**2
closed=sum(f.Area() for f in cover.Faces() if abs(f.BoundingBox().zmin-b.H)<1e-5 and abs(f.BoundingBox().zmax-b.H)<1e-5)
opened=outer-closed;old_outer=(b.W+2*(b.T+b.C))*(b.D+2*(b.T+b.C));old_open=12*6*8*20
checks=[]
for x in e['mount_ear_x']:
 for y in (-e['mount_hole_offset'],b.D+e['mount_hole_offset']):
  tool=b.cyl(x,y,24,e['mount_tool_envelope_diameter']/2,b.H+20-24)
  v=tool.intersect(cover).Volume()+tool.intersect(base).Volume()
  checks.append({'center':[x,y],'tool_diameter':e['mount_tool_envelope_diameter'],'tool_bottom_z':24,'plastic_intersection_mm3':round(v,6)})
  assert v<.01
r={'revision':b.P['revision'],'roof':{'outer_projected_area_mm2':round(outer,3),'open_area_mm2':round(opened,3),'open_percent':round(100*opened/outer,2),'closed_percent':round(100*closed/outer,2),'rev03_open_percent':round(100*old_open/old_outer,2),'open_area_ratio_to_rev03':round(opened/old_open,3),'cell_count':len(b.roof_windows()),'rib_width_mm':e['roof_rib_width'],'rib_depth_mm':e['roof_rib_depth'],'rib_min_z':b.H-e['roof_rib_depth'],'nominal_cooler_clearance_mm':round(b.H-e['roof_rib_depth']-(b.Z+b.p['thickness']+b.c['seat_above_pcb_top']+b.c['size'][2]),3),'new_rectangular_rib_I_mm4':e['roof_rib_width']*e['roof_rib_depth']**3/12,'rev03_rectangular_rib_I_mm4':[6*6**3/12,8*6**3/12],'limits':'I is a section property, not a whole-lid stiffness/load/FEA result. Span, grid joints, material and layer adhesion matter. Open-area ratio is not an airflow prediction.'},'mounts':{'layout':'front and rear, integral','tab_width':e['mount_ear_width'],'tab_projection':e['mount_ear_projection'],'tab_thickness':e['mount_ear_thickness'],'mount_centers':[[x,y] for x in e['mount_ear_x'] for y in (-e['mount_hole_offset'],b.D+e['mount_hole_offset'])],'slot_size':[12,6.6],'slot_long_axis':'X','washer_envelope_diameter':e['mount_washer_envelope_diameter'],'driver_envelope_diameter':e['mount_tool_envelope_diameter'],'driver_to_cover_plane_clearance_mm':e['mount_hole_offset']-(b.T+b.C)-e['mount_tool_envelope_diameter']/2,'nominal_print_bounds':[217,253,72],'P1S_centered_nominal_Y_margin_each':1.5,'tool_checks':checks,'limits':'External screw length/anchor depend on mounting surface. Center on P1S and check machine exclusions; no more than 1.5 mm nominal Y margin before brim.'},'fillets':{'base_vertical_corner_R':e['outer_corner_radius'],'lid_vertical_corner_R':e['cover_corner_radius'],'mount_vertical_corner_R':4,'outer_rim_R':e['external_rim_radius'],'panel_exposed_face_edge_R':e['panel_edge_radius'],'grille_internal_corner_R':e['roof_opening_corner_radius'],'exceptions':'Keep bed-contact faces, rib crests, rail reference faces, insert seats and 45-degree vent closures dimensionally controlled.'}}
(R/'exports/design-metrics.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
