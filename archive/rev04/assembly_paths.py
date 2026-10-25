from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];p=json.loads((R/'cad/parameters.json').read_text());rows=json.loads((R/'references/solids.json').read_text());sh=json.loads((R/'references/open-shells.json').read_text());o=p['pcb']['origin_in_source_step'];e=p['enclosure'];m=e['pcb_margin']
bb=[[q-o[k%3] for k,q in enumerate(v['bbox'])] for v in rows]+[v['normalized_bbox'] for v in sh]
front=min(v[1] for v in bb)+m;rear=max(v[4] for v in bb)+m
result={'scope':'Rigid front/rear panel vertical translation, using complete carrier Y extent as sufficient nonintersection proof. No installed cables. Actual hardware and tolerances not measured.','front_panel_back_y':e['front_panel_y']+6,'carrier_min_y':front,'front_clearance':front-e['front_panel_y']-6,'rear_panel_front_y':e['rear_panel_y'],'carrier_max_y':rear,'rear_clearance':e['rear_panel_y']-rear,'candidate_gmsl_front_y':m-3,'candidate_gmsl_front_clearance':m-3-e['front_panel_y']-6,'no_thin_snap_arm':True,'panel_retention':'Channels constrain horizontal motion; cover stops block upward withdrawal. Remove cover before lifting panels.','pass':front>e['front_panel_y']+6 and rear<e['rear_panel_y']}
(R/'exports/assembly-paths.json').write_text(json.dumps(result,indent=2));print(result)
