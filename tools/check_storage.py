"""Storage expansion and underside-slot checks -> exports/storage-checks.json.

1. Underside envelopes (stacked Mini PCIe + M.2 B cards, M.2 E card, SATA/PH plug drops):
   plastic intrusion before relief, and minimum gap to the as-built base after relief.
2. Storage stacks: plastic/plastic and hardware/plastic intersections for several module combinations,
   with and without the mount plate.
3. Cable chimney: the plug-drop footprint must be open from the SATA connectors down through every module.
"""
from pathlib import Path
import json,sys
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'cad'))
import build as b
import hardware as h
from OCP.BRepExtrema import BRepExtrema_DistShapeShape

def gap(a,c):
    d=BRepExtrema_DistShapeShape(a.wrapped,c.wrapped);d.Perform();return round(d.Value(),3)

base=b.base();raw=b.base(False,False);out={'revision':b.P['revision']}
env=[]
for (name,s),it in zip(b.envelope_boxes(),b.P['underside_envelopes']['items']):
    bb=s.BoundingBox()
    env.append({'name':name,'ref':it['ref'],'role':it['role'],'enclosure_box':[round(v,2) for v in (bb.xmin,bb.ymin,bb.zmin,bb.xmax,bb.ymax,bb.zmax)],
                'intrusion_before_relief_mm3':round(raw.intersect(s).Volume(),2),'gap_to_base_after_relief_mm':gap(s,base) if it['role']=='card' else None,
                'lowest_point_above_floor_mm':round(bb.zmin-b.F,2) if it['role']=='card' else None,'basis':it['basis']})
out['underside_envelopes']=env
out['underside_space']={'pcb_underside_z':b.Z,'floor_top_z':b.F,'clear_height_mm':b.Z-b.F,
    'stacked_cards_need_mm':-min(it['box'][2] for it in b.P['underside_envelopes']['items'] if it['role']=='card')}

configs={'1 total: 3.5':(['storage_35'],False,False),'1 total: 2.5':(['storage_25'],False,False),'1 total: 2.5 skinny SSDs on clips':(['storage_25'],False,True),
         '1 of each: 3.5 over 2.5':(['storage_35','storage_25'],False,False),'1 of each: 2.5 over 3.5, on plate':(['storage_25','storage_35'],True,True),
         '2 of each':(['storage_35','storage_35','storage_25','storage_25'],False,False),'2 of each, on plate':(['storage_25','storage_25','storage_35','storage_35'],True,True)}
# Two onboard SATA ports: (port, module index, bay index) wired in each configuration. Rule: the front connector feeds
# the 3.5 in drive; from the rear one the turn into a 3.5 in drive's data plug is tighter than the 12 mm bend radius.
LINKS={'1 total: 3.5':[(0,0,0)],'1 total: 2.5':[(0,0,0),(1,0,1)],'1 total: 2.5 skinny SSDs on clips':[(0,0,0),(1,0,1)],
       '1 of each: 3.5 over 2.5':[(0,0,0),(1,1,0)],'1 of each: 2.5 over 3.5, on plate':[(1,0,0),(0,1,0)],
       '2 of each':[(0,0,0),(1,2,0)],'2 of each, on plate':[(1,0,0),(0,2,0)]}
plate=b.storage_mount_plate();stacks={}
for label,(kinds,use_plate,ssd7) in configs.items():
    mods=b.stack(kinds);zb=mods[-1][2];parts=[('base',base)]+[(n,s) for n,s,_ in mods]+([('storage_mount_plate',plate.translate((0,0,zb-b.e['mount_ear_thickness'])))] if use_plate else [])
    plastic=[]
    for i,(a,sa) in enumerate(parts):
        for c,sc in parts[i+1:]:
            v=sa.intersect(sc).Volume()
            if v>.01:plastic.append({'parts':[a,c],'mm3':round(v,3)})
    hw=[];intended=0
    hwl=h.storage_hardware(kinds,use_plate,ssd7)
    for n,s,_ in hwl:
        for pn,ps in parts:
            v=ps.intersect(s).Volume()
            if v>.01:
                if 'insert' in n:intended+=1
                else:hw.append({'item':n,'part':pn,'mm3':round(v,3)})
    # Chimney: plug-drop footprint extruded from the bottom of the stack to the connectors.
    path=[]
    for name,s in b.envelope_boxes('plug_drop'):
        bb=s.BoundingBox();col=b.box(bb.xmin,bb.ymin,zb-1,bb.xmax-bb.xmin,bb.ymax-bb.ymin,bb.zmax-zb+1)
        blocked=sum(ps.intersect(col).Volume() for pn,ps in parts if pn!='storage_mount_plate')
        path.append({'zone':name,'blocked_mm3':round(blocked,3)})
    total=sum(b.S['modules'][k]['height'] for k in kinds)
    # Drives, clips and screws must not touch each other either (clips and nuts are separate parts).
    hh=[];big=[(n,s) for n,s,_ in hwl if n.startswith(('D ','P19')) and 'SATA connectors' not in n]
    for i,(a,sa) in enumerate(big):
        for c,sc in big[i+1:]:
            v=sa.intersect(sc).Volume()
            if v>.01:hh.append({'items':[a,c],'mm3':round(v,3)})
    cab=[]
    for n,s,_ in h.storage_cables(kinds,LINKS[label],ssd7):
        for pn,ps in parts:
            v=ps.intersect(s).Volume()
            if v>.05:cab.append({'cable':n,'part':pn,'mm3':round(v,2)})
    bends=[]
    for name,sig,pts,c,_,_ in h.cable_routes(kinds,LINKS[label],ssd7):
        _,f=h.fillet_path(pts,c['min_bend_radius']);bends.append({'route':name,'min_bend_required_mm':c['min_bend_radius'],'max_uniform_bend_available_mm':round(float(f),2),'ok':bool(f>=c['min_bend_radius'])})
    stacks[label]={'modules':kinds,'bend_radius':bends,'sata_links':[{'port':p+1,'module':kinds[m],'module_index':m+1,'bay':bb+1} for p,m,bb in LINKS[label]],'cable_route_hits':cab,'mount_plate':use_plate,'skinny_ssd_clips':ssd7,'drive_clip_overlaps':hh,'added_height_mm':total,'overall_height_mm':b.H+total,'with_plate_mm':b.H+total+b.e['mount_ear_thickness'] if use_plate else None,
                   'plastic_intersections':plastic,'hardware_collisions':hw,'intended_insert_interference':intended,'chimney':path,
                   'pass':not plastic and not hw and not hh and not cab and all(x['ok'] for x in bends) and all(p['blocked_mm3']<.01 for p in path)}
    print(label,stacks[label]['pass'],flush=True)
out['stacks']=stacks
d35,d25=b.S['drives']['d35'],b.S['drives']['d25']
out['cables']=b.S['cables']
out['drive_fastening']={k:{'screw':d['screw'],'material_under_head_mm':round(b.S['floor']+b.S['pad_height']-d['counterbore'][1],2),'spec_penetration_mm':d['penetration_mm']} for k,d in (('d35',d35),('d25',d25))}
out['power']={'board_sata_power':'JST PH 2.0 4-pin per port, switched SATA_5V only, 2 A ferrite per port (schematic sheet 27). Enough for 2.5 in drives.',
              '3.5_in_drives':'Need 12 V. The storage_35 module has a D8 panel hole (12V IN) and tie anchors for a DC-DC or a 12 V-to-SATA power adapter. Board input is 12-36 V; do not feed raw DC-IN to drives unless the supply is 12 V.',
              'ports':'Two onboard SATA III ports; more drives need an M.2 Key M SATA adapter or USB.'}
out['pass']=all(s['pass'] for s in stacks.values()) and all(e_['gap_to_base_after_relief_mm'] is None or e_['gap_to_base_after_relief_mm']>0 for e_ in env)
(R/'exports/storage-checks.json').write_text(json.dumps(out,indent=2)+'\n');print('pass',out['pass'])
