from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];p=json.loads((R/'cad/parameters.json').read_text());rows=json.loads((R/'references/solids.json').read_text());sh=json.loads((R/'references/open-shells.json').read_text());o=p['pcb']['origin_in_source_step'];e=p['enclosure'];m=e['pcb_margin'];t=e['panel_thickness']
bb=[[q-o[k%3] for k,q in enumerate(v['bbox'])] for v in rows]+[v['normalized_bbox'] for v in sh]
front=min(v[1] for v in bb)+m;rear=max(v[4] for v in bb)+m
result={'scope':'Rigid front/rear plate vertical translation, using complete carrier Y extent as sufficient nonintersection proof. No installed cables. Actual hardware and tolerances not measured.','panel_thickness':t,'front_panel_back_y':e['front_panel_y']+t,'carrier_min_y':front,'front_clearance':round(front-e['front_panel_y']-t,3),'rear_panel_front_y':e['rear_panel_y'],'carrier_max_y':rear,'rear_clearance':round(e['rear_panel_y']-rear,3),'candidate_gmsl_front_y':m-3,'candidate_gmsl_front_clearance':round(m-3-e['front_panel_y']-t,3),'no_thin_snap_arm':True,'panel_retention':'Corner-post channels and the floor sill groove constrain horizontal motion; lid ledges block upward withdrawal. Remove the lid before lifting plates or the J17 hatch.','pass':front>e['front_panel_y']+t and rear<e['rear_panel_y']}
# The rear plate's button sleeves reach inside the carrier's Y extent, so sweep them from above (PCB datum).
sb=e['service_buttons'];r=sb['sleeve_od']/2;xs=[x for x,_ in sb['actuators_pcb_xz']];zc=sb['actuators_pcb_xz'][0][1]
sweep=[min(xs)-r,p['pcb']['depth']+sb['sleeve_gap_to_pcb_edge'],zc-r,max(xs)+r,e['rear_panel_y']-m,1e9]
hits=[i for i,v in enumerate(bb) if v[0]<sweep[3] and v[3]>sweep[0] and v[1]<sweep[4] and v[4]>sweep[1] and v[5]>sweep[2]]
result['rear_button_sleeve_sweep']={'box_pcb_datum':sweep[:5],'carrier_bboxes_hit':hits,'pcb_edge_gap':sb['sleeve_gap_to_pcb_edge'],'pass':not hits}
result['scope']+=' Rear button sleeves checked separately by a vertical sweep.'
result['pass']=result['pass'] and not hits
(R/'exports/assembly-paths.json').write_text(json.dumps(result,indent=2));print(result)
