"""Visual hardware models, not manufacturing drawings of purchased fasteners.
Threads are represented by annular grooves, not helical mating geometry.
Cooler fasteners and GMSL connector shapes/locations are explicitly provisional.
"""
import build as b
import cadquery as cq
from pathlib import Path

def insert(length=10):
    # User dimensions: M6, 7.25 mm starter and 8 mm maximum body diameter.
    s=b.cyl(0,0,0,4,length-1).fuse(cq.Solid.makeCone(4,3.625,1,cq.Vector(0,0,length-1)))
    cuts=[b.cyl(0,0,-1,2.5,length+2)]
    for z in (2,4,6,8):
        if z<length-1:
            cuts.append(b.cyl(0,0,z,4.05,.4).cut(b.cyl(0,0,z-.1,3.65,.6)))
    return b.subtract(s,cuts)

def washer(inner=6.6,outer=12,thickness=1.6):
    return b.cyl(0,0,0,outer/2,thickness).cut(b.cyl(0,0,-1,inner/2,thickness+2))

def screw(d=6,length=20,head_d=10,head_h=6,socket=5):
    # Shaft extends down -Z from its under-head plane, head extends +Z.
    s=b.cyl(0,0,-length,d/2,length).fuse(b.cyl(0,0,0,head_d/2,head_h))
    hole=cq.Workplane('XY').polygon(6,socket/0.8660254).extrude(head_h/2+1).val().translate((0,0,head_h/2))
    return s.cut(hole)

def board_insert():
    s=b.cyl(0,0,0,2.1,9).fuse(cq.Solid.makeCone(2.1,1.875,1,cq.Vector(0,0,9)))
    return s.cut(b.cyl(0,0,-1,1.25,12))

def jumper():
    body=b.box(-2.5,-1.3,0,5,2.6,6)
    return b.subtract(body,[b.box(x-.4,-.4,-.1,.8,.8,5.2) for x in (-1.27,1.27)])

def orient(s,axis):
    if axis=='xp':return s.rotate((0,0,0),(0,1,0),90)
    if axis=='xm':return s.rotate((0,0,0),(0,1,0),-90)
    if axis=='yp':return s.rotate((0,0,0),(1,0,0),-90)
    if axis=='ym':return s.rotate((0,0,0),(1,0,0),90)
    if axis=='zm':return s.rotate((0,0,0),(1,0,0),180)
    return s

COL={'steel':(.70,.73,.75),'brass':(.76,.56,.19),'dark':(.1,.12,.15),'copper':(.72,.38,.20),'pcb':(.08,.32,.17),'teal':(.04,.57,.61)}

def flat_screw(d=3,length=40,head_d=6.72,head_h=1.86,socket=2):
    # ISO 10642 style countersunk screw; z=0 is the head face, shank extends +Z.
    s=cq.Solid.makeCone(head_d/2,d/2,head_h,cq.Vector(0,0,0)).fuse(b.cyl(0,0,0,d/2,length))
    hole=cq.Workplane('XY').polygon(6,socket/0.8660254).extrude(1.2).val()
    return s.cut(hole)

def heatsink_screw_head_z():
    # Head face of the flat-head screw on the raised countersink seat inside the column.
    return b.HS_HEAD_Z

def heatsink_screw_length():
    # Standard length chosen so the thread engagement in the heatsink standoff is exactly the specified 8 threads.
    return b.e['heatsink_screw_length']

def enclosure_hardware():
    items=[]
    for x,y in b.e['lid_screw_centers']:
        items += [('H1 lid M3 insert',orient(board_insert(),'zm').translate((x,y,b.BH)),COL['brass']),
                  ('H3 lid M3 x 16 socket screw',screw(3,16,5.5,3,2.5).translate((x,y,b.e['lid_screw_head_z'])),COL['steel'])]
    for x,y in b.board_holes():
        items += [('H4 M3 board insert',orient(board_insert(),'zm').translate((x,y,b.Z)),COL['brass']),
                  ('H5 M3 board screw',screw(3,10,5.7,1.65,2).translate((x,y,b.Z+b.p['thickness'])),COL['steel'])]
    return items+antenna_bulkheads()

def hexbar(af,length):
    return cq.Workplane('YZ').polygon(6,af/0.8660254).extrude(length).val()

def antenna_bulkheads():
    # RP-SMA female bulkhead pigtails (visual): body bears on the spot-faced inner wall, lock washer + nut outside.
    a=b.e['antenna_bulkheads'];lw=a['local_wall'];z=a['z'];W=b.W;items=[]
    for q in a['positions']:
        y=q['y'];parts=[('body',hexbar(8,6).translate((W-lw-6,y,z)),COL['brass']),
            ('ferrule',b.cyl(W-lw-6,y,z,2.2,10,(-1,0,0)),COL['brass']),
            ('thread',b.cyl(W-lw,y,z,6.35/2,lw+7,(1,0,0)),COL['brass']),
            ('lock washer',b.cyl(W,y,z,4.6,.5,(1,0,0)).cut(b.cyl(W-1,y,z,3.3,3,(1,0,0))),COL['steel']),
            ('nut',hexbar(8,2).translate((W+.5,y,z)).cut(b.cyl(W,y,z,3.2,4,(1,0,0))),COL['brass'])]
        for name,s,col in parts:
            if q['side']=='left':s=s.rotate((W/2,y,0),(W/2,y,1),180)
            items.append((f"H10 {q['label']} RP-SMA bulkhead {name}",s,col))
    return items

def heatsink_tiedown():
    hz=heatsink_screw_head_z();L=heatsink_screw_length()
    return [('H7 cooler tie-down M3 flat head from below',flat_screw(3,L).translate((x,y,hz)),COL['steel']) for x,y in b.heatsink_holes()]

def cooler_and_module():
    c=b.c;cx,cy=c['center_in_pcb'];cx+=b.M;cy+=b.M;sx,sy,sz=c['size']
    seat=b.COOLER_SEAT
    # Module envelope and existing cooler retention screws, not replacement specifications.
    module=cq.Shape.importBrep(str(b.ROOT/'references/nvidia-module/p3701-sku0-simplified.brep')).rotate((0,0,0),(0,0,1),-90).translate((b.M+48.25,b.M+131.5,b.Z+b.p['thickness']+8))
    base=b.box(cx-sx/2,cy-sy/2,seat,sx,sy,3)
    for x,y in b.p['module_mount_centers']:
        base=base.cut(b.cyl(b.M+x,b.M+y,seat-1,2.2,5))
    items=[('E2 NVIDIA AGX Orin source STEP',module,COL['dark']),('E3 cooler copper base envelope',base,COL['copper'])]
    for x in range(int(cx-sx/2)+8,int(cx+sx/2)-7,5):
        items.append(('E3 approximate cooling fins',b.box(x,cy-sy/2+8,seat+3,1.2,sy-16,31),(.55,.55,.56)))
    ring=b.cyl(cx,cy,seat+34,46,16).cut(b.cyl(cx,cy,seat+33,42,18))
    hub=b.cyl(cx,cy,seat+34,14,16)
    items += [('E3 fan frame',ring,COL['dark']),('E3 fan hub',hub,COL['dark'])]
    for a in range(0,360,45):
        blade=b.box(cx+10,cy-7,seat+40,32,14,3).rotate((cx,cy,0),(cx,cy,1),a)
        items.append(('E3 fan blade',blade,COL['dark']))
    return items+heatsink_tiedown()

def gmsl():
    g=b.P['gmsl'];x,y,z=g['preview_origin_in_pcb'];x+=b.M;y+=b.M;z+=b.Z
    s=b.box(x,y,z,103,45,1.6)
    for hx,hy in g['candidate_support_centers']:s=s.cut(b.cyl(b.M+hx,b.M+hy,z-1,1.7,4))
    items=[('E4 GMSL PCB envelope - position provisional',s,COL['pcb'])]
    # Exact Amphenol candidate geometry; match to Seeed BOM not established.
    model=cq.Shape.importBrep(str(b.ROOT/'references/FM4-NZRP-PCB-1.brep'))
    model=model.rotate((0,0,0),(1,0,0),90)
    for px in g['candidate_port_left_edges']:
        items.append(('E5 FM4-NZRP-PCB-1 candidate',model.translate((b.M+px+6,b.M-3,z-6.65)),COL['teal']))
    # Mated 60-signal connector envelope, 16 mm board-facing surface separation.
    # XY location is provisional, not used as a manufacturing locator.
    items.append(('E6 Samtec QSH QTH mated envelope',b.box(b.M+76.226,b.M+34.636,b.Z+b.p['thickness'],21.81,8.5,16),COL['dark']))
    for hx,hy in g['candidate_support_centers']:
        support=b.cyl(b.M+hx,b.M+hy,b.Z+b.p['thickness'],2.75,16).cut(b.cyl(b.M+hx,b.M+hy,b.Z,1.25,20))
        items += [('H8 original GMSL support - provisional',support,COL['brass']),('H9 original GMSL screw - provisional',screw(3,6,5.7,1.65,2).translate((b.M+hx,b.M+hy,z+1.6)),COL['steel'])]
    # Prominent top components: schematic package sizes, photo-estimated placement.
    for px in (36,106):items.append(('E7 MAX96724 8x8x0.9 envelope - XY provisional',b.box(b.M+px-4,b.M+20-4,z+1.6,8,8,.9),COL['dark']))
    for px in (54,62,74,82):
        for py in (10,20):items.append(('E8 SPM0635 6.5x5.6 footprint - height/XY assumed',b.box(b.M+px-3.25,b.M+py-2.8,z+1.6,6.5,5.6,3.5),COL['dark']))
    return items


def carrier_supplements():
    # J26 source STEP is a 3.81 mm-high placeholder. Footprint label supplies 13.85 mm.
    # Add a visibly differentiated service envelope, not a claimed exact vendor model.
    x,y,z=b.M+100.943,b.M+138.998,b.Z+b.p['thickness']
    body=b.box(x,y,z,7.12,25.7,13.85)
    body=body.cut(b.box(x+.35,y+17,z+.35,6.42,9.7,13.15))
    tongue=b.box(x+2.2,y+17.7,z+2,1.4,7.6,9.85)
    return [('E9 J26 corrected height envelope - MPN unconfirmed',body,(.72,.47,.30)),('E9 J26 tongue illustrative',tongue,(.1,.3,.55))]

# ---------------------------------------------------------------- storage stack (visual + clearance models)
def standoff(length,male=6.0,af=5.5):
    # M3 male-female hex standoff: body z 0..length (female end at z=0), male thread above.
    body=cq.Workplane('XY').polygon(6,af/0.8660254).extrude(length).val().cut(b.cyl(0,0,-1,1.25,6))
    return body.fuse(b.cyl(0,0,length-.01,1.5,male+.01))

def drive_model(kind,height=None):
    # SFF envelope with the connector end at x=0; SATA connectors shown as a dark strip on the end face.
    d=b.S['drives'][kind];L,Wd,Hd=d['size'];Hd=height or Hd
    body=b.box(0,0,0,L,Wd,Hd)
    conn=b.box(-.01,Wd*.12,1.0,.6,Wd*.45,5.5) if kind=='d35' else b.box(-.01,Wd*.1,.8,.6,Wd*.55,5.0)
    return body,conn

def storage_hardware(kinds,plate=False,ssd7=False):
    # Standoffs hang from the part above: hex top in that part's 2 mm counterbore, female end on this tray's ledge.
    S=b.S;items=[];cb,lg=S['foot_counterbore'],S['ledge']
    for x,y in S['standoff_centers']:
        items.append(('H11 base M3 stacking insert',board_insert().translate((x,y,cb)),COL['brass']))
    mods=b.stack(kinds)
    for name,_,z in mods:
        k=name.rsplit('_',1)[0];m=S['modules'][k];L=m['standoff_length']
        for x,y in S['standoff_centers']:
            items.append((f'H12 {name} M3 x {L:g} M-F hex standoff',standoff(L).translate((x,y,z+cb+lg)),COL['steel']))
        for bay in m['bays']:
            d=S['drives'][bay['type']];clips=ssd7 and bay['type']=='d25';k=S['ssd_clip'];zf=z+S['floor']+S['pad_height']
            body,conn=drive_model(bay['type'],7.0 if clips else None)
            off=(b.conn_x(bay['type']),bay['y'],zf+(k['flange_thickness'] if clips else 0))
            label='7 mm SATA SSD (side holes only)' if clips else d['name']
            items+=[(f'D {name} {label}',body.translate(off),(.30,.32,.35)),(f'D {name} SATA connectors',conn.translate(off),(.08,.08,.09))]
            dcb,cbd=d['counterbore'];big=bay['type']=='d35'
            if clips:
                for x,y,r,zc in b.ssd_clip_placements(bay['y'],zf):
                    items.append((f'P19 {name} SSD clip',b.placed_clip(x,y,r,zc),(.86,.47,.18)))
                    sgn=1 if r==0 else -1;w=k['wall']
                    side=orient(screw(3.0,5.0,5.7,1.65,2.0),'ym' if sgn>0 else 'yp').translate((x,y-sgn*w,zc+k['flange_thickness']+d['side_hole_height']))
                    items.append((f'H17 {name} M3 x 5 side screw',side,COL['steel']))
                for hx,hy in b.drive_holes('d25',bay['y']):
                    items.append((f'H16 {name} M3 x 6 clip floor screw',orient(screw(3.0,6.0,5.7,1.65,2.0),'zm').translate((hx,hy,z+cbd)),COL['steel']))
                continue
            for hx,hy in b.drive_holes(bay['type'],bay['y']):
                s=screw(3.5 if big else 3.0,4.76 if big else 4.0,7.0 if big else 5.7,2.4 if big else 1.65,2.0)
                items.append((f'H13 {name} drive screw ({d["screw"]})',orient(s,'zm').translate((hx,hy,z+cbd)),COL['steel']))
    zb=mods[-1][2]
    for x,y in S['standoff_centers']:
        if plate:
            t=b.e['mount_ear_thickness']
            items.append(('H14 plate M3 x 10 socket head',orient(screw(3,10,5.5,3,2.5),'zm').translate((x,y,zb-t+4)),COL['steel']))
        else:
            items.append(('H15 closing M3 x 6 button head',orient(screw(3,6,5.7,1.65,2.0),'zm').translate((x,y,zb+cb)),COL['steel']))
    return items

# ---------------------------------------------------------------- storage cabling (visual + route-clearance models)
def tube(points,r):
    # Round cable along a polyline: cylinders between points, spheres at the bends.
    parts=[]
    for (x0,y0,z0),(x1,y1,z1) in zip(points,points[1:]):
        v=cq.Vector(x1-x0,y1-y0,z1-z0)
        if v.Length>1e-6:parts.append(cq.Solid.makeCylinder(r,v.Length,cq.Vector(x0,y0,z0),v))
    parts+=[cq.Solid.makeSphere(r,cq.Vector(*p)) for p in points[1:-1]]
    return b.combine(parts)

def board_sata_ports():
    # Enclosure-frame centres of the underside receptacles (STEP solids 5063/5064 data, 5061/5062 PH power); z = mating face.
    s=b.envelope_boxes;zf=b.Z-3.81
    return {'data':[(b.M+4.1,b.M+23.89,zf),(b.M+4.1,b.M+40.89,zf)],'power':[(b.M+10.89,b.M+26.98,zf),(b.M+10.89,b.M+37.79,zf)]}

def drive_ports(kind,y0,z_bottom):
    # Approximate SATA data / power plug centres on a drive's connector end.
    d=b.S['drives'][kind];Wd=d['size'][1];x=b.conn_x(kind)
    return {'data':(x,y0+Wd*.22,z_bottom+4.0),'power':(x,y0+Wd*.47,z_bottom+4.0)}

def fillet_path(points,R,steps=8):
    """Round every corner of a 3D polyline with radius R. Returns (points, largest uniform radius the polyline allows:
    on each segment the tangent lengths of the corners at both ends must fit within the segment)."""
    import numpy as np
    P=[np.array(p,float) for p in points];n=len(P)
    seg=[P[i+1]-P[i] for i in range(n-1)];L=[float(np.linalg.norm(s)) for s in seg];U=[s/l if l>1e-9 else s for s,l in zip(seg,L)]
    tan=[0.0]*n
    for i in range(1,n-1):
        th=float(np.arccos(np.clip(U[i-1]@U[i],-1,1)));tan[i]=np.tan(th/2) if th>1e-3 else 0.0
    feasible=min([L[i]/(tan[i]+tan[i+1]) for i in range(n-1) if tan[i]+tan[i+1]>0] or [float('inf')])
    r=min(R,feasible);out=[P[0]]
    for i in range(1,n-1):
        if tan[i]==0:out.append(P[i]);continue
        u,v=U[i-1],U[i];t1=P[i]-u*r*tan[i];th=2*np.arctan(tan[i])
        nn=np.cross(u,v);nn/=np.linalg.norm(nn);c=t1+np.cross(nn,u)*r
        for k in range(steps+1):
            a=th*k/steps;out.append(c+(t1-c)*np.cos(a)+np.cross(nn,t1-c)*np.sin(a))
    out.append(P[-1]);return [tuple(p) for p in out],feasible

def cable_routes(kinds,links,ssd7=False):
    """Centre-line routes (name, signal, raw points, cable spec) for SATA data, board 5 V PH power and tray 12 V leads.
    Data/PH leads leave the vertical underside connectors straight down, drop through the floor opening and tray chimneys,
    turn toward the drive, and finish with a straight lead into the drive-end plug."""
    S=b.S;C=S['cables'];mods=b.stack(kinds);bp=board_sata_ports();routes=[]
    for port,mi,bi in links:
        name,_,z=mods[mi];k=name.rsplit('_',1)[0];bay=S['modules'][k]['bays'][bi];kind=bay['type']
        clips=ssd7 and kind=='d25';zb=z+S['floor']+S['pad_height']+(S['ssd_clip']['flange_thickness'] if clips else 0)
        dp=drive_ports(kind,bay['y'],zb)
        for sig in ('data','power'):
            if sig=='power' and kind=='d35':continue
            c=C[sig];bx,by,bz=bp[sig][port];tx,ty,tz=dp[sig];hx=tx-c['drive_plug_length']
            pts=[(bx,by,bz-c['board_plug_length']),(bx,by,tz),(hx-c['straight_lead'],ty,tz),(hx,ty,tz)]
            routes.append((f'{sig} port {port+1} -> {name} bay {bi+1}',sig,pts,c,(tx,ty,tz),(bx,by,bz)))
        if kind=='d35':
            c=C['dc12'];j=S['modules'][k]['dc_jack'];zc=z+S['floor']+(S['modules'][k]['height']-S['floor'])/2;tx,ty,tz=dp['power'];hx=tx-c['drive_plug_length']
            yb=b.Y1-S['wall'];pts=[(j['x'],yb-1,zc),(j['x'],yb-14,zc),(hx-10,yb-14,zc),(hx-10,ty+16,zc),(hx-10,ty,tz),(hx,ty,tz)]
            routes.append((f'12 V in -> {name}','dc12',pts,c,(tx,ty,tz),None))
    return routes

def storage_cables(kinds,links,ssd7=False):
    """Tube models of the cable routes with their bend radii, plus plug bodies at both ends."""
    cols={'data':(.80,.12,.12),'power':(.93,.75,.10),'dc12':(.95,.45,.05)};items=[]
    for name,sig,pts,c,(tx,ty,tz),board in cable_routes(kinds,links,ssd7):
        fp,_=fillet_path(pts,c['min_bend_radius']);items.append((f'C {name}',tube(fp,c['model_radius']),cols[sig]))
        dw={'data':16.0,'power':22.0,'dc12':22.0}[sig];L=c['drive_plug_length']
        items.append((f'C plug at drive: {name}',b.box(tx-L,ty-dw/2,tz-3,L,dw,6),(.12,.12,.13)))
        if board:
            bx,by,bz=board;w=(15.5,7.0) if sig=='data' else (10.0,4.5);pl=c['board_plug_length']
            items.append((f'C plug at board: {name}',b.box(bx-w[1]/2,by-w[0]/2,bz-pl,w[1],w[0],pl),(.12,.12,.13)))
    return items
