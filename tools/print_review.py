from pathlib import Path
import json,numpy as np,trimesh
R=Path(__file__).resolve().parents[1];result={}
for name in json.loads((R/'exports/geometry-checks.json').read_text()):
 m=trimesh.load_mesh(R/'exports'/f'{name}.stl');mask=(m.face_normals[:,2]<-np.sin(np.deg2rad(47))) & (m.triangles_center[:,2]>.3)
 faces=np.flatnonzero(mask);big=faces[m.area_faces[faces]>.5]
 result[name]={'print_bounds_mm':m.extents.round(3).tolist(),'within_nominal_P1S_256_cube':bool(np.all(m.extents<=256)), 'downward_surface_area_over_47deg_excluding_bed_mm2':round(float(m.area_faces[faces].sum()),3),'large_face_centers_mm':m.triangles_center[big].round(3).tolist(), 'interpretation':'Screen only; not a slicer. Small chamfers/bores may bridge. Inspect any large downward faces, layer paths, brims and excluded machine regions.'}
(R/'exports/print-review.json').write_text(json.dumps(result,indent=2))
for k,v in result.items():print(k,v['downward_surface_area_over_47deg_excluding_bed_mm2'],len(v['large_face_centers_mm']))
