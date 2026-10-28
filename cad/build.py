"""J501 printable enclosure, Rev 0.5. All dimensions in mm.
See docs/measurement-register.csv before editing or printing.
Enclosure datum: PCB lower-left corner at (M, M), PCB underside at Z.
Output STLs are placed on z=0 in intended print orientation; assembly STEP
uses the enclosure datum. Vendor geometry and envelopes are NOT printed parts.
"""
from pathlib import Path
import json, math
from functools import lru_cache
import cadquery as cq
ROOT=Path(__file__).resolve().parents[1]
from ports import resolve  # port windows come from the mated plug models
P=resolve(json.loads((ROOT/'cad/parameters.json').read_text()))
p,e,c=P['pcb'],P['enclosure'],P['cooler']
M=e['pcb_margin']; W=e['width']; Y0=e['front_y']; Y1=e['rear_y']; D=Y1-Y0
F=e['floor']; Z=F+e['board_support_height']; T=e['wall']; H=e['height']; BH=e['base_height']
RT=e['roof_thickness']; R=e['outer_corner_radius']
PT=e['panel_thickness']; PC=e['panel_clearance']; PX0,PX1=e['panel_x']; FY=e['front_panel_y']; RY=e['rear_panel_y']
PANEL_TOP=BH-e['panel_top_clearance']; HY0,HY1=e['hatch_y']; HZ=e['hatch_bottom_z']
C=e['panel_clearance']  # legacy name used by older tools
AGX_TOP=Z+p['thickness']+c['agx_top_above_pcb_top']  # top of the module thermal plate; heatsink standoff threads start here
COOLER_SEAT=AGX_TOP+c['tim_thickness']
# Countersunk head face of the cooler tie-down screw: a standard length gives exactly the specified thread engagement.
HS_THREAD_Z=COOLER_SEAT+c['spreader']['thickness'] if c.get('spreader') else AGX_TOP  # where the tie-down screw meets the standoff's female thread
HS_HEAD_Z=HS_THREAD_Z+e['heatsink_thread_engagement']-e['heatsink_screw_length']
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
OUT=ROOT/'exports'; OUT.mkdir(exist_ok=True)

def box(x,y,z,dx,dy,dz): return cq.Solid.makeBox(dx,dy,dz,cq.Vector(x,y,z))
def cyl(x,y,z,r,h,d=(0,0,1)): return cq.Solid.makeCylinder(r,h,cq.Vector(x,y,z),cq.Vector(*d))
def combine(parts): return parts[0].fuse(*parts[1:]).clean() if len(parts)>1 else parts[0]
def subtract(s,parts): return s.cut(*parts).clean() if parts else s
def cone(x,y,z,r0,r1,h,d=(0,0,1)): return cq.Solid.makeCone(r0,r1,h,cq.Vector(x,y,z),cq.Vector(*d))

def rrect(x0,y0,x1,y1,r,z0,h):
    # Rounded rectangle prism in plan.
    r=min(r,(x1-x0)/2-.01,(y1-y0)/2-.01)
    return cq.Workplane('XY').box(x1-x0,y1-y0,h,centered=False).edges('|Z').fillet(r).val().translate((x0,y0,z0))

def window(x0,z0,x1,z1,r,y0,depth):
    # Rounded rectangle in XZ, cut through a panel along +Y from y0.
    r=min(r,(x1-x0)/2-.01,(z1-z0)/2-.01)
    s=cq.Workplane('XY').box(x1-x0,z1-z0,depth,centered=False).edges('|Z').fillet(r).val()
    return s.rotate((0,0,0),(1,0,0),90).translate((x0,y0+depth,z0))

def slot(axis,a,depth,b,z0,z1,w):
    # Vertical stadium vent: axis 'x' cuts a wall normal to X at y=b; 'y' cuts normal to Y at x=b.
    r=w/2;d=(1,0,0) if axis=='x' else (0,1,0)
    if axis=='x':parts=[box(a,b-r,z0+r,depth,w,z1-z0-w),cyl(a,b,z0+r,r,depth,d),cyl(a,b,z1-r,r,depth,d)]
    else:parts=[box(b-r,a,z0+r,w,depth,z1-z0-w),cyl(b,a,z0+r,r,depth,d),cyl(b,a,z1-r,r,depth,d)]
    return combine(parts)

def prism_z(pts,z0,h): return cq.Workplane('XY').polyline(pts).close().extrude(h).val().translate((0,0,z0))
def prism_x(pts,x0,length): return cq.Workplane('YZ').polyline(pts).close().extrude(length).val().translate((x0,0,0))
def prism_y(pts,y0,length):
    # XZ workplane extrudes toward -Y; shift so the prism spans y0..y0+length.
    return cq.Workplane('XZ').polyline(pts).close().extrude(length).val().translate((0,y0+length,0))

def label(text,x,z,y_face,front=True,size=None):
    # Debossed panel legend, reading correctly from outside the enclosure.
    size=size or e['label_size'];dep=e['label_depth']
    t=cq.Workplane('XY').text(text,size,dep+.2,fontPath=FONT,halign='center',valign='center').val()
    if front:return t.rotate((0,0,0),(1,0,0),90).translate((x,y_face+dep,z))
    return t.rotate((0,0,0),(0,0,1),180).rotate((0,0,0),(1,0,0),-90).translate((x,y_face-dep,z))

def label_x(text,y,z,left,size=None):
    # Debossed side-wall legend, reading correctly from outside (left wall X=0, right wall X=W).
    size=size or e['label_size'];dep=e['label_depth']
    t=cq.Workplane('XY').text(text,size,dep+.2,fontPath=FONT,halign='center',valign='center').val().rotate((0,0,0),(1,0,0),90)
    if left:return t.rotate((0,0,0),(0,0,1),-90).translate((dep,y,z))
    return t.rotate((0,0,0),(0,0,1),90).translate((W-dep,y,z))

def teardrop_x(x0,length,y,z,r,cap=None):
    # Horizontal hole along X with a 45-degree roof so it prints without support (floor-down base).
    k=r/math.sqrt(2);s=combine([cyl(x0,y,z,r,length,(1,0,0)),prism_x([(y-k,z+k),(y+k,z+k),(y,z+r*math.sqrt(2))],x0,length)])
    if cap is not None and z+r*math.sqrt(2)>cap:s=s.intersect(box(x0-1,y-r-1,z-r-1,length+2,2*r+2,cap-(z-r-1)))
    return s

def d_hole_x(x0,length,y,z,r,across,side='top'):
    # Horizontal round hole along X with one flat (an anti-rotation D, e.g. a bulkhead connector's milled thread).
    # 'top': the flat is a short bridge that replaces the hole's steepest overhang, so no teardrop is needed.
    s=cyl(x0,y,z,r,length,(1,0,0))
    keep=box(x0-1,y-r-1,z-r,length+2,2*r+2,across) if side=='top' else box(x0-1,y-r-1,z+r-across,length+2,2*r+2,across)
    return s.intersect(keep)

def vent_positions(lo,hi,pitch=None):
    pitch=pitch or e['vent_pitch'];n=int(round((hi-lo)/pitch));return [lo+i*pitch for i in range(n+1)]

# ---------------------------------------------------------------- supports
@lru_cache(maxsize=None)
def _underside_rows():
    rows=json.loads((ROOT/'references/solids.json').read_text());origin=p['origin_in_source_step'];out=[]
    for row in rows:
        if row['index'] in range(5155,5163) or row['index']==5169:continue  # mount-hole display proxies
        bb=row['bbox'];lo=[bb[i]-origin[i]+[M,M,Z][i] for i in range(3)];hi=[bb[i+3]-origin[i]+[M,M,Z][i] for i in range(3)]
        if lo[2]<Z-.001:out.append((lo,hi))
    return out

def fillet_ring(x,y,z,r,f,down=False):
    # Concave radius-f fillet where a vertical cylinder of radius r meets a horizontal face at height z (face below,
    # or above when down=True). Material shrinks away from the face, so it prints face-down without support.
    if down:
        ring=cyl(x,y,z-f,r+f-.01,f+.01);return ring.cut(cq.Solid.makeTorus(r+f,f,cq.Vector(x,y,z-f),cq.Vector(0,0,1)))
    ring=cyl(x,y,z-.01,r+f-.01,f+.01)
    return ring.cut(cq.Solid.makeTorus(r+f,f,cq.Vector(x,y,z+f),cq.Vector(0,0,1)))

def support(x,y,broad_d,land_d,land_h,z0=None):
    # Broad printed column with a pad-sized landing; underside components get 0.5 mm relief. Radius fillets at the
    # floor and under the landing remove the two sharp corners where these columns would crack.
    z0=F if z0 is None else z0;rb,rl=broad_d/2,land_d/2;fl,g=e['support_floor_flare'],e['support_shoulder_gusset'];zs=Z-land_h
    post=combine([cyl(x,y,z0,rb,zs-z0),cyl(x,y,zs-.2,rl,land_h+.2),fillet_ring(x,y,z0,rb,fl),fillet_ring(x,y,zs,rl,g)])
    reach=rb+fl+.5;relief=[]
    for lo,hi in _underside_rows():
        if hi[0]<x-reach or lo[0]>x+reach or hi[1]<y-reach or lo[1]>y+reach:continue
        relief.append(box(lo[0]-.5,lo[1]-.5,lo[2]-.5,hi[0]-lo[0]+1,hi[1]-lo[1]+1,hi[2]-lo[2]+1))
    return subtract(post,relief)

def board_holes(): return [(M+x,M+y) for x,y in p['mount_holes']]
def heatsink_holes(): return [(M+x,M+y) for x,y in p['module_mount_centers']]

def insert_seat(x,y,z,sense):
    # Short oversize seat under the lead-in cone so the insert tip drops in and stands upright before heating.
    # z is the hole mouth; sense -1 drills downward, +1 upward (inserts fitted from below).
    return cyl(x,y,z+sense*.59,e['insert_seat_diameter']/2,e['insert_seat_depth']+.01,(0,0,sense))

@lru_cache(maxsize=None)
def board_posts():
    posts=[]
    for x,y in board_holes():
        post=support(x,y,e['board_post_diameter'],e['board_landing_diameter'],e['board_landing_height'])
        post=subtract(post,[cyl(x,y,Z,e['board_insert_pilot']/2,e['board_insert_depth'],(0,0,-1)),
                            cone(x,y,Z,2.2,e['board_insert_pilot']/2,.6,(0,0,-1)),insert_seat(x,y,Z,-1)])
        posts.append(post)
    return posts

@lru_cache(maxsize=None)
def heatsink_columns():
    # The cooler is most of the mass: tie it to the floor, not just the PCB.
    # Longer flat-head screws enter from below, pass the column, carrier and module, and thread into the female
    # standoffs between the AGX module and the heatsink.
    return [support(x,y,e['heatsink_column_diameter'],e['heatsink_landing_diameter'],e['board_landing_height']) for x,y in heatsink_holes()]

def tiedown_cut(x,y,R2,height):
    # Clearance hole, D7 driver/head pocket from the floor, and a 90-degree countersink whose 6.72 mm head face
    # lands at HS_HEAD_Z. The cone narrows upward at 45 degrees, so it prints floor-down without support.
    r=e['heatsink_clearance']/2;z0=HS_HEAD_Z-(e['heatsink_countersink_diameter']-6.72)/2
    return [cyl(x,y,-1,r,height+1),cyl(x,y,-1,R2,z0+1.01),cone(x,y,z0,R2,r,R2-r)]

def heatsink_screw_cuts():
    return [s for x,y in heatsink_holes() for s in tiedown_cut(x,y,e['heatsink_countersink_diameter']/2,Z+2)]

def floor_ribs():
    # Low ribs tie the heatsink columns to each other and to the board posts.
    w,h=e['floor_rib'];hs=heatsink_holes();bp=board_holes();ribs=[]
    def rib(a,b):
        dx,dy=b[0]-a[0],b[1]-a[1];L=math.hypot(dx,dy);ang=math.degrees(math.atan2(dy,dx))
        return box(0,-w/2,F-.01,L,w,h+.01).rotate((0,0,0),(0,0,1),ang).translate((a[0],a[1],0))
    for a,b in ((0,1),(1,3),(3,2),(2,0)):ribs.append(rib(hs[a],hs[b]))
    for i in range(4):ribs.append(rib(hs[i],bp[i]))
    return ribs

# ---------------------------------------------------------------- base
def outer_block(z0,z1,bottom_chamfer,top_chamfer):
    s=cq.Workplane('XY').box(W,D,z1-z0,centered=False).translate((0,Y0,z0)).edges('|Z').fillet(R)
    if bottom_chamfer:s=s.faces('<Z').chamfer(bottom_chamfer)
    if top_chamfer:s=s.faces('>Z').chamfer(top_chamfer)
    return s.val()

def panel_channel(y):
    return box(PX0-PC,y-PC,F,PX1-PX0+2*PC,PT+2*PC,BH-F+1)

def hatch_grooves():
    # 45-degree V grooves in the notch faces; the hatch's V tongues print support-free.
    a,b,m=W-T+1.0,W-T+3.4,W-T+2.2
    side0=prism_z([(a,HY0+.3),(a,HY0),(m,HY0-1.2),(b,HY0),(b,HY0+.3)],HZ-1.2,BH-HZ+2.2)
    side1=prism_z([(a,HY1-.3),(a,HY1),(m,HY1+1.2),(b,HY1),(b,HY1-.3)],HZ-1.2,BH-HZ+2.2)
    bottom=prism_y([(a,HZ+.3),(a,HZ),(m,HZ-1.2),(b,HZ),(b,HZ+.3)],HY0-1.2,HY1-HY0+2.4)
    return [side0,side1,bottom]

def side_vents(z0,z1,hatch=False):
    cuts=[]
    for y in vent_positions(*e['side_vent_y']):
        cuts.append(slot('x',-1,T+2,y,z0,z1,e['vent_width']))
        in_hatch=HY0-4<y<HY1+4
        if hatch and in_hatch:continue
        cuts.append(slot('x',W-T-1,T+2,y,z0,z1,e['vent_width']))
    return cuts

def hatch_vent_y(): return [y for y in vent_positions(*e['side_vent_y']) if HY0+6<y<HY1-6]

def mount_ear(x,front):
    w=e['mount_ear_width'];pr=e['mount_ear_projection'];t=e['mount_ear_thickness']
    y0=Y0-pr if front else Y1-2;y1=Y0+2 if front else Y1+pr
    ear=cq.Workplane('XY').box(w,y1-y0,t,centered=False).translate((x-w/2,y0,0))
    ear=ear.edges('|Z and <Y' if front else '|Z and >Y').fillet(6).faces('>Z').edges('<Y' if front else '>Y').chamfer(1.0).val()
    # 45-degree gusset where the tab meets the frame.
    g=[(Y0-4,t),(Y0+.01,t),(Y0+.01,t+4)] if front else [(Y1+4,t),(Y1-.01,t),(Y1-.01,t+4)]
    return combine([ear,prism_x(g,x-w/2+3,w-6)])

def mount_slot_centers():
    o=e['mount_hole_offset'];return [(x,y) for x in e['mount_ear_x'] for y in (Y0-o,Y1+o)]

def buttressed_column(x,y,z0,h,flare_at=None,r=None,wall=None,rf=None,flare=None):
    # Lid-screw column fused to the nearest side wall: column + full-height buttress to the wall face, 4 mm concave
    # fillets where the buttress meets the wall, and an optional radius fillet at one end (floor or roof).
    r=r or e['lid_column_diameter']/2;rf=rf or e['lid_column_fillet'];wall=wall or T;left=x<W/2;xw=wall if left else W-wall
    x0,x1=(xw-.01,x) if left else (x,xw+.01)
    parts=[cyl(x,y,z0,r,h),box(x0,y-r,z0,x1-x0,2*r,h)]
    xf=xw if left else xw-rf;xc=xw+rf if left else xw-rf
    for sy in (1,-1):
        yb=y+sy*r;y0=yb if sy>0 else yb-rf
        parts.append(subtract(box(xf,y0,z0,rf,rf,h),[cyl(xc,yb+sy*rf,z0-1,rf,h+2)]))
    if flare_at is not None:
        fl=flare or e['lid_column_flare'];up=flare_at<=z0+1
        parts.append(fillet_ring(x,y,flare_at,r,fl,down=not up))
    return combine(parts)

def antenna_cuts():
    # RP-SMA bulkheads in the fixed base walls: the lid, plates and J17 door still lift off with antennas fitted.
    a=e['antenna_bulkheads'];z=a['z'];cuts=[]
    for q in a['positions']:
        left=q['side']=='left';y=q['y'];lw=a['local_wall']
        cuts.append(d_hole_x(-1 if left else W-T-1,T+2,y,z,a['hole']/2,a['across_flat'],a['flat_side']))
        # Inner spot face thins the wall locally so short bulkhead threads still leave room for nut and antenna.
        cuts.append(teardrop_x(lw if left else W-T-1,T-lw+1,y,z,a['spot_face_diameter']/2,a['cap_z']))
        cuts.append(label_x(q['label'],y+(a['label_offset'] if y<(Y0+Y1)/2 else -a['label_offset']),z,left))
    return cuts

@lru_cache(maxsize=None)
def base(with_ears=False,relief=True):
    cx,cy=e['corner_post_size'];sh=e['sill_height'];si0,si1=e['sill_inner_y']
    material=[box(0,Y0,0,W,D,F),box(0,Y0,0,T,D,BH),box(W-T,Y0,0,T,D,BH),
              box(0,Y0,0,W,si0-Y0,F+sh),box(0,si1,0,W,Y1-si1,F+sh)]
    for x in (0,W-cx):
        material+=[box(x,Y0,0,cx,cy,BH),box(x,Y1-cy,0,cx,cy,BH)]
    body=outer_block(0,BH,e['base_bottom_chamfer'],e['split_chamfer']).intersect(combine(material))
    cuts=[panel_channel(FY),panel_channel(RY),box(W-T-1,HY0,HZ,T+2,HY1-HY0,BH)]+hatch_grooves()+side_vents(*e['base_vent_z'],hatch=True)
    body=subtract(body,cuts)
    # Lid locating tongues along both side walls; the hatch span is left open.
    t0,t1,th=e['joint_tongue'];ty0,ty1=Y0+3.5,Y1-3.5
    adds=[box(t0,ty0,BH-.01,t1-t0,ty1-ty0,th+.01),box(W-t1,ty0,BH-.01,t1-t0,HY0-ty0,th+.01),box(W-t1,HY1,BH-.01,t1-t0,ty1-HY1,th+.01)]
    adds+=[buttressed_column(x,y,F-.01,BH-F+.01,flare_at=F-.01) for x,y in e['lid_screw_centers']]
    adds+=board_posts()+heatsink_columns()+floor_ribs()
    body=combine([body]+adds)
    cuts=[]
    for x,y in e['lid_screw_centers']:
        cuts+=[cyl(x,y,BH+.01,e['lid_insert_pilot']/2,e['lid_insert_depth']+.01,(0,0,-1)),cone(x,y,BH+.01,2.2,e['lid_insert_pilot']/2,.6,(0,0,-1)),insert_seat(x,y,BH,-1)]
    for x,y in board_holes():
        cuts.append(cyl(x,y,Z,e['board_insert_pilot']/2,e['board_insert_depth'],(0,0,-1)))
    cuts+=heatsink_screw_cuts()+antenna_cuts()+(underside_relief() if relief else [])+[cap_recess()]
    cb=S['foot_counterbore']
    for x,y in S['standoff_centers']:  # storage stacking: hex counterbore + M3 insert from below in each column foot
        cuts+=[cyl(x,y,-1,S['column_bore']/2,cb+1),cyl(x,y,cb-.01,e['lid_insert_pilot']/2,S['base_insert_depth']+.01),cone(x,y,cb-.01,2.2,e['lid_insert_pilot']/2,.6),insert_seat(x,y,cb,1)]
    d,dep=e['foot_pocket']
    cuts+=[cyl(x,y,-1,d/2,dep+1) for x,y in e['foot_pockets']]
    cuts+=floor_vents()
    body=subtract(body,cuts)
    if with_ears:
        body=combine([body]+[mount_ear(x,front) for x in e['mount_ear_x'] for front in (True,False)])
        L,w=e['mount_slot'];r=w/2
        body=subtract(body,[combine([box(x-L/2+r,y-r,-1,L-w,w,e['mount_ear_thickness']+2),cyl(x-L/2+r,y,-1,r,e['mount_ear_thickness']+2),cyl(x+L/2-r,y,-1,r,e['mount_ear_thickness']+2)]) for x,y in mount_slot_centers()])
    return body

def floor_vents():
    # Hex openings where the floor topology study found no load path (exports/topology/floor-vents.json).
    v=e.get('floor_vents')
    if not v or not (ROOT/v['file']).exists():return []
    pts=json.loads((ROOT/v['file']).read_text())['centres']
    if not pts:return []
    s=v['across_flats'];return [cq.Workplane('XY').pushPoints(pts).polygon(6,2*s/math.sqrt(3)).extrude(F+2).val().translate((0,0,-1))]

# ---------------------------------------------------------------- lid
def fan_centre(): return c['center_in_pcb'][0]+M,c['center_in_pcb'][1]+M

def fan_outline(d=0.0,shift=(0.0,0.0)):
    # The fan frame's octagon (square with 45-degree corner chamfers) grown outward by d, around the fan centre (+ shift).
    f=c['fan'];a=f['frame']/2+d;k=f['corner_chamfer']+2*d-d*math.sqrt(2);cx,cy=fan_centre();cx,cy=cx+shift[0],cy+shift[1]
    pts=[(a,-(a-k)),(a,a-k),(a-k,a),(-(a-k),a),(-a,a-k),(-a,-(a-k)),(-(a-k),-a),(a-k,-a)]
    return [(cx+x,cy+y) for x,y in pts]

def fan_keepout_gaps():
    # The lid against the fan frame moved by the photo-registration uncertainty in eight directions: the modelled
    # frame, and the S06 table's 95 mm size. Negative = overlap volume (mm3).
    u=c.get('fan_xy_uncertainty',0.0);cov=cover();out={}
    for name,grow in (('frame',0.0),('conservative',(c['fan'].get('frame_conservative',c['fan']['frame'])-c['fan']['frame'])/2)):
        worst=None
        for i in range(8):
            a=math.radians(45*i);env=prism_z(fan_outline(grow,(u*math.cos(a),u*math.sin(a))),FAN_TOP-c['fan']['thickness'],c['fan']['thickness'])
            v=cov.intersect(env).Volume();g=-v if v>1e-6 else cov.distance(env)
            worst=g if worst is None else min(worst,g)
        out[name]=round(worst,2)
    return out

def inside_outline(x,y,d):
    # True if (x,y) lies inside fan_outline(d) (convex polygon, counter-clockwise).
    pts=fan_outline(d)
    return all((x2-x1)*(y-y1)-(y2-y1)*(x-x1)>=0 for (x1,y1),(x2,y2) in zip(pts,pts[1:]+pts[:1]))

def roof_cells():
    # The open roof cells: every cell of the field that clears the fan skirt (the fan breathes through its own grille).
    g=e['fan_grille'];Rh=e['hex_across_flats']/math.sqrt(3);d=g['clearance']+g['skirt_wall']+Rh+1.0
    return [(x,y) for x,y in hex_centers() if not inside_outline(x,y,d)]

def hex_centers():
    s=e['hex_across_flats'];pitch=s+e['hex_web'];Rh=s/math.sqrt(3);x0,y0,x1,y1=e['hex_field']
    dx=pitch*math.sqrt(3)/2;nx=int((x1-x0-2*Rh)//dx);ny=int((y1-y0-s)//pitch)
    ox=(x0+x1)/2-nx*dx/2;oy=(y0+y1)/2-ny*pitch/2;pts=[]
    for i in range(nx+1):
        for j in range(ny+1):
            x=ox+i*dx;y=oy+j*pitch+(pitch/2 if i%2 else 0)
            if x-Rh>=x0-1e-6 and x+Rh<=x1+1e-6 and y-s/2>=y0-1e-6 and y+s/2<=y1+1e-6:pts.append((x,y))
    return pts

FAN_TOP=COOLER_SEAT+c['size'][2]  # top of the cooler's fan frame

@lru_cache(maxsize=None)
def cover():
    # Flush lid. Four M3 screws from the top into inserts in the base columns.
    roof_z=H-RT;cr=e['cavity_corner_radius'];g=e['fan_grille']
    s=outer_block(BH,H,e['split_chamfer'],e['roof_edge_chamfer'])
    s=subtract(s,[rrect(T,Y0+T,W-T,Y1-T,cr,BH-1,roof_z-BH+1)])
    # Chamfered ledges sit on the I/O panel tops; 45 degrees in roof-down print orientation.
    ledges=[prism_x([(Y0+T-.01,BH),(FY+PT+PC,BH),(FY+PT+PC,BH+2),(Y0+T-.01,BH+4)],T-.01,W-2*T+.02),
            prism_x([(Y1-T+.01,BH),(RY-PC,BH),(RY-PC,BH+2),(Y1-T+.01,BH+4)],T-.01,W-2*T+.02)]
    cols=[buttressed_column(x,y,BH,roof_z-BH+.01,flare_at=roof_z+.01) for x,y in e['lid_screw_centers']]
    s=combine([s]+ledges+cols)
    r0,r1,rh=e['joint_rebate']
    cuts=[box(r0,Y0+3.2,BH-1,r1-r0,D-6.4,rh+1),box(W-r1,Y0+3.2,BH-1,r1-r0,D-6.4,rh+1)]
    hz=e['lid_screw_head_z']
    for x,y in e['lid_screw_centers']:
        cuts+=[cyl(x,y,hz,e['lid_counterbore_diameter']/2,H-hz+1),cyl(x,y,BH-1,e['lid_screw_clearance']/2,hz-BH+1.01)]
    if e.get('lid_vent_z'):
        vz0,vz1=e['lid_vent_z']
        # A roof rib that ends on a wall must land on solid wall: a vent slot under its end left the rib floating with
        # 0.5 mm of air each side, the lid's peak stress (local safety factor 1.0 under 300 N). Skip those slots.
        keep=e['roof_ribs']['width']/2+e['vent_width']/2+2.0
        ends=[q for s_ in rib_segments() for q in (s_[:2],s_[2:])]
        def clear(wall,pos):
            near={'x0':lambda x,y:x<T+3,'x1':lambda x,y:x>W-T-3,'y0':lambda x,y:y<Y0+T+3,'y1':lambda x,y:y>Y1-T-3}[wall]
            return all(abs(pos-(y if wall[0]=='x' else x))>keep for x,y in ends if near(x,y))
        for y in vent_positions(*e['side_vent_y']):
            cuts+=[slot('x',-1,T+2,y,vz0,vz1,e['vent_width'])]*clear('x0',y)+[slot('x',W-T-1,T+2,y,vz0,vz1,e['vent_width'])]*clear('x1',y)
        for x in vent_positions(*e['panel_vent_x']):
            cuts+=[slot('y',Y0-1,T+2,x,vz0,vz1,e['vent_width'])]*clear('y0',x)+[slot('y',Y1-T-1,T+2,x,vz0,vz1,e['vent_width'])]*clear('y1',x)
    s_af=e['hex_across_flats'];cells=roof_cells()
    hexes=cq.Workplane('XY').pushPoints(cells).polygon(6,2*s_af/math.sqrt(3)).extrude(RT+2).val().translate((0,0,roof_z-1))
    # Fan-side inlet chamfer: each cell widens toward the cooler so the webs meet the airflow with a tapered edge.
    # The exterior face keeps the 10 mm A/F finger limit; in roof-down print orientation the chamfer is not an overhang.
    f,fd,ov=e['hex_inlet_flare'],e['hex_inlet_depth'],.01;ang=math.degrees(math.atan(f/fd))
    inlet=cq.Workplane('XY').workplane(offset=roof_z-ov).pushPoints(cells).polygon(6,2*(s_af+2*f+2*ov*f/fd)/math.sqrt(3)).extrude(fd+ov,taper=ang).vals()
    # Over the fan the roof is cut away to a flush grille: the fan top sits just under it.
    pocket=prism_z(fan_outline(g['clearance']),roof_z-1,H-g['thickness']-roof_z+1)
    cuts+=[hexes]+inlet+[pocket,fan_grille_openings()]
    # The band of cells next to the skirt stays closed on top (no hot exhaust right beside the intake) but is hollow
    # underneath, under a thin skin: light, and printed roof-down the skin is the first layers on the bed.
    band=[(x,y) for x,y in hex_centers() if (x,y) not in set(cells) and not inside_outline(x,y,g['clearance']+s_af/math.sqrt(3)+.3)]
    if band:cuts.append(cq.Workplane('XY').pushPoints(band).polygon(6,2*s_af/math.sqrt(3)).extrude(RT-g['band_skin']+1).val().translate((0,0,roof_z-1)))
    s=subtract(s,cuts)
    return combine([s,fan_skirt()]+roof_ribs())

def grille_gap():
    # Radial width of the grille openings (their narrow dimension; spokes make them longer around the ring).
    g=e['fan_grille'];ri,ro=g['hub_diameter']/2,c['fan']['blade_diameter']/2+.4
    return (ro-ri-g['rings']*g['ring_width'])/(g['rings']+1)

def finger_reach(width,finger=12.0):
    # How far the hemispherical tip of a test finger (IEC 60529, D12) sinks into a slot this wide.
    r=finger/2;return r if width>=finger else r-math.sqrt(r*r-(width/2)**2)

def fan_grille_openings():
    # Annulus over the blades (hub disc left solid), split by rings and spokes into openings grille_gap() wide.
    g=e['fan_grille'];f=c['fan'];cx,cy=fan_centre();z0=H-g['thickness']-1;h=g['thickness']+2
    ri,ro=g['hub_diameter']/2,f['blade_diameter']/2+.4
    open_=cyl(cx,cy,z0,ro,h).cut(cyl(cx,cy,z0-1,ri,h+2))
    n,w=g['rings'],g['ring_width'];gap=grille_gap();keep=[]
    for i in range(n):
        r=ri+(i+1)*gap+i*w;keep.append(cyl(cx,cy,z0-1,r+w,h+2).cut(cyl(cx,cy,z0-2,r,h+4)))
    sw=g['spoke_width']
    for i in range(g['spokes']):
        keep.append(box(0,-sw/2,z0-1,ro+2,sw,h+2).rotate((0,0,0),(0,0,1),360*i/g['spokes']+180/g['spokes']).translate((cx,cy,0)))
    return open_.cut(*keep).clean()

def fan_skirt():
    # Wall around the fan frame from the roof down past the fan top: seals the intake from the exhaust and frames the cut-out.
    g=e['fan_grille'];z0=FAN_TOP-g['skirt_below_fan_top'];top=H-e['roof_edge_chamfer']
    return prism_z(fan_outline(g['clearance']+g['skirt_wall']),z0,top-z0).cut(prism_z(fan_outline(g['clearance']),z0-1,top-z0+2))

def rib_segments():
    # From the fan centre to the middle of each wall ('cross') and also to the four lid-screw columns ('star').
    r=e.get('roof_ribs') or {};cx,cy=fan_centre()
    if not r:return []
    cross=[(cx,cy,T,cy),(cx,cy,W-T,cy),(cx,cy,cx,Y0+T),(cx,cy,cx,Y1-T)]
    return cross+([(cx,cy,x,y) for x,y in e['lid_screw_centers']] if r.get('layout','star')=='star' else [])

def roof_ribs():
    # Stiffening ribs under the roof, the radial pattern of the roof topology study. Like the skirt they run through the
    # roof, so where one crosses a hex cell it prints from the bed instead of bridging the hole.
    r=e.get('roof_ribs')
    if not r:return []
    w,dep=r['width'],r['depth'];top=H-e['roof_edge_chamfer'];z0=H-RT-dep;out=[];k=1.5
    # each rib runs 1.5 mm into the wall and the skirt it meets: flush (coplanar) joins tessellate with gaps
    cav=rrect(T-k,Y0+T-k,W-T+k,Y1-T+k,e['cavity_corner_radius'],z0-1,top-z0+2)
    fan=prism_z(fan_outline(e['fan_grille']['clearance']),z0-1,top-z0+3)
    g=e['fan_grille'];so=fan_outline(g['clearance']+g['skirt_wall'])
    for x0,y0,x1,y1 in rib_segments():
        L=math.hypot(x1-x0,y1-y0);ang=math.degrees(math.atan2(y1-y0,x1-x0))
        out.append(box(-k,-w/2,z0,L+2*k,w,top-z0).rotate((0,0,0),(0,0,1),ang).translate((x0,y0,0)).intersect(cav).cut(fan))
        # a round boss where the rib meets the skirt takes the sharp inside corners out of the joint (FEA stress peak)
        jx,jy=ray_exit(x0,y0,(x1-x0)/L,(y1-y0)/L,so)
        out.append(cyl(jx,jy,z0,r.get('boss_radius',4.0),top-z0).cut(fan))
    return out

def ray_exit(x,y,dx,dy,poly):
    # Where a ray from (x,y) inside a convex polygon leaves it.
    best=1e9
    for (ax,ay),(bx,by) in zip(poly,poly[1:]+poly[:1]):
        ex,ey=bx-ax,by-ay;den=dx*ey-dy*ex
        if abs(den)<1e-12:continue
        s=((ax-x)*ey-(ay-y)*ex)/den;u=((ax-x)*dy-(ay-y)*dx)/den
        if s>0 and -1e-9<=u<=1+1e-9:best=min(best,s)
    return x+best*dx,y+best*dy

# ---------------------------------------------------------------- panels
def flared(x0,z0,x1,z1,r,face_y,inward,c,depth):
    # Rounded window normal to Y with a 45-degree lead-in on the exterior face.
    cx,cz,w,h=(x0+x1)/2,(z0+z1)/2,x1-x0,z1-z0;r=min(r,w/2-.01,h/2-.01)
    pl=cq.Plane(origin=(cx,face_y,cz),xDir=(1,0,0),normal=(0,inward,0))
    def sk(a,b,rr,wp):return wp.sketch().rect(a,b).vertices().fillet(rr).finalize()
    core=sk(w,h,r,cq.Workplane(pl).workplane(offset=-1)).extrude(depth+2).val()
    if not c:return core
    flare=sk(w+2*c,h+2*c,r+c,cq.Workplane(pl)).extrude(c,taper=45).val()
    cap=sk(w+2*c,h+2*c,r+c,cq.Workplane(pl)).extrude(-1).val()
    return combine([core,flare,cap])

def port_cutters(side,gmsl,face,inward,depth):
    ports=[v for v in P['ports'][side].values() if gmsl or not v.get('gmsl_only')]
    ports=sorted(ports,key=lambda v:v['box'][0]);cuts=[];prev=None;ch=e['panel_window_chamfer']
    for v in ports:
        x0,z0,x1,z1=v['box'];cuts.append(flared(M+x0,Z+z0,M+x1,Z+z1,v['r'],face,inward,ch,depth))
        if prev and x0-prev[2]<e['min_panel_web']:
            # Gap too small for a printed web: bridge the two windows across their shared height.
            bz0,bz1=max(z0,prev[1])+.8,min(z1,prev[3])-.8
            y=min(face-inward,face+inward*(depth+1))
            cuts.append(box(M+prev[2]-1.5,y,Z+bz0,x0-prev[2]+3,depth+2,bz1-bz0))
        prev=v['box']
    return cuts

def port_labels(side,gmsl,y_face,front):
    out=[]
    for k,v in P['ports'][side].items():
        if not v.get('label') or (v.get('gmsl_only') and not gmsl):continue
        x0,z0,x1,z1=v['box'];x=M+(x0+x1)/2
        if k=='usb_a':x=M+(x0+108.75)/2  # one legend under the stacked and vertical USB-A ports
        z=Z+z1+4.2 if v.get('label_above') else min(Z+z0-3.6,Z-6.5)
        out.append(label(v['label'],x,z,y_face,front))
        # Per-pin marks (e.g. polarity) centred above the window over their pin.
        out+=[label(m['text'],M+m['x'],Z+z1+e['mark_size']/2+1.2,y_face,front,size=e['mark_size']) for m in v.get('marks',[])]
    return out

@lru_cache(maxsize=None)
def panel(front=True,gmsl=False):
    y=FY if front else RY;side='front' if front else 'rear';face=y if front else y+PT
    s=box(PX0,y,F,PX1-PX0,PT,PANEL_TOP-F);inward=1 if front else -1;vz0,vz1=e['panel_vent_z'];vw=e['panel_vent_width']
    cuts=port_cutters(side,gmsl,face,inward,PT)
    cuts+=[flared(x-vw/2,vz0,x+vw/2,vz1,vw/2,face,inward,e['panel_window_chamfer'],PT) for x in vent_positions(*e['panel_vent_x'])]
    if not front:
        adds,bcuts=button_features();s=combine([s]+adds);cuts+=bcuts
    s=subtract(s,cuts)
    return subtract(s,port_labels(side,gmsl,face,front))

def button_features():
    # Pin access to the right-angle reset / force-recovery switches. A sleeve on the plate's inside guides
    # the pin onto the actuator; it stops short of the PCB edge so the plate still slides straight down.
    sb=e['service_buttons'];face=RY+PT;y_end=M+p['depth']+sb['sleeve_gap_to_pcb_edge'];L=RY-y_end+.01
    pts=[(M+x,Z+z) for x,z in sb['actuators_pcb_xz']];r=sb['sleeve_od']/2;(xa,za),(xb,_)=pts
    adds=[cyl(xa,RY+.01,za,r,L,(0,-1,0)),cyl(xb,RY+.01,za,r,L,(0,-1,0)),box(xa,y_end,za-r,xb-xa,L,2*r)]
    cuts=[]
    for x,z in pts:
        h=sb['pin_hole']/2;c=sb['lead_in']
        cuts+=[cyl(x,face+1,z,h,PT+L+3,(0,-1,0)),cone(x,face+.01,z,h+c+.01,h,c+.01,(0,-1,0))]
    cuts+=[label(t_,x,sb['legend_z'],face,False,size=sb['label_size']) for t_,(x,_) in zip(sb['labels'],pts)]
    return adds,cuts

@lru_cache(maxsize=None)
def side_hatch():
    # Flush J17 door: fills the wall notch, V tongues on sides/bottom, lid skin captures the top.
    hc=e['hatch_clearance'];x0=W-T;a,b,m=W-T+1.2,W-T+3.2,W-T+2.2
    y0,y1,z0=HY0+hc,HY1-hc,HZ+hc
    plate=box(x0,y0,z0,T,y1-y0,PANEL_TOP-z0)
    t0=prism_z([(a,y0+.3),(a,y0),(m,y0-1.0),(b,y0),(b,y0+.3)],z0,PANEL_TOP-z0)
    t1=prism_z([(a,y1-.3),(a,y1),(m,y1+1.0),(b,y1),(b,y1-.3)],z0,PANEL_TOP-z0)
    tb=prism_y([(a,z0),(m,z0-1.0),(b,z0)],y0-1.0,y1-y0+2.0)
    s=combine([plate,t0,t1,tb])
    s=subtract(s,[slot('x',x0-1,T+2,y,*e['base_vent_z'],e['vent_width']) for y in hatch_vent_y()])
    return s

# ---------------------------------------------------------------- coupons
def rail_coupon():
    # Exact corner-post channel section: 2.5 lip, 3.5 channel, 4 mm engagement.
    s=box(0,0,0,16,9,24)
    return subtract(s,[box(10,2.5,3,7,PT+2*PC,22)])

def rail_key(): return box(0,0,0,10,PT,18)

def m3_coupon():
    s=box(0,0,0,90,20,14)
    return subtract(s,[cyl(x,10,14,d/2,11,(0,0,-1)) for x,d in zip((10,27.5,45,62.5,80),(3.7,3.8,3.9,4,4.1))])

def rpsma_coupon():
    # A strip of the spot-faced antenna wall, printed standing like the base wall, with the D hole at four
    # across-flat sizes. Use the tightest one the bulkhead's flat still pushes into; set antenna_bulkheads.across_flat.
    a=e['antenna_bulkheads'];lw=a['local_wall'];sizes=a['coupon_across_flat'];n=len(sizes);pitch=14;zc=12
    s=combine([box(0,0,0,pitch*n+4,14,2),box(0,0,0,pitch*n+4,lw,zc+8)])
    cuts=[]
    for i,af in enumerate(sizes):
        x=2+pitch*(i+.5)
        cuts.append(d_hole_x(-1,lw+2,0,zc,a['hole']/2,af,a['flat_side']).rotate((0,0,0),(0,0,1),90).translate((x,0,0)))
        cuts.append(label(f'{af:.1f}',x,zc-6.5,0,True,2.5))
    return subtract(s,cuts)

def countersink_coupon():
    # Floor + column section with the raised tie-down seat (nominal and +0.4 mm pocket), to test flat-head seating
    # and the M3 x 35 engagement before printing the base.
    hc=HS_HEAD_Z+6-F;s=combine([box(0,0,0,40,20,F),cyl(10,10,F-.01,e['heatsink_column_diameter']/2,hc),cyl(30,10,F-.01,e['heatsink_column_diameter']/2,hc)])
    cuts=[q for x,R2 in ((10,e['heatsink_countersink_diameter']/2),(30,e['heatsink_countersink_diameter']/2+.2)) for q in tiedown_cut(x,10,R2,F+hc+1)]
    return subtract(s,cuts)

def fit_template():
    # Cradle check jig: the carrier sits on it face up exactly as in the base. Same supports, landings and
    # component relief as P1, cut down to a 3 mm frame, so it proves hole pattern, landings and underside clearance.
    ht=e['fit_template_height'];z0=Z-ht;holes=board_holes();hs=heatsink_holes();shapes=[]
    for y in (holes[0][1],holes[2][1]):shapes.append(box(holes[0][0],y-3,z0,150,6,3))
    for x in (holes[0][0],holes[1][0]):shapes.append(box(x-3,holes[0][1],z0,6,130,3))
    for y in (hs[0][1],hs[2][1]):shapes.append(box(holes[0][0],y-3,z0,150,6,3))
    shapes+=[support(x,y,e['board_post_diameter'],e['board_landing_diameter'],e['board_landing_height'],z0) for x,y in holes]
    shapes+=[support(x,y,e['heatsink_column_diameter'],e['heatsink_landing_diameter'],e['board_landing_height'],z0) for x,y in hs]
    return subtract(combine(shapes),[cyl(x,y,z0-1,1.7,ht+2) for x,y in holes+hs]+underside_relief()).translate((0,0,-z0))

# ---------------------------------------------------------------- underside envelopes
S=P['storage']

def envelope_boxes(role=None):
    # Keep-out volumes under the PCB (cards in the underside slots, plug drops below the SATA connectors).
    out=[]
    for it in P['underside_envelopes']['items']:
        if role and it['role']!=role:continue
        x0,y0,z0,x1,y1,z1=it['box'];out.append((it['name'],box(M+x0,M+y0,Z+z0,x1-x0,y1-y0,z1-z0)))
    return out

def underside_relief(margin=.5):
    # Cards get a 0.5 mm margin on every side except the PCB face; plug drops are cut exactly (they open the floor).
    out=[]
    for it in P['underside_envelopes']['items']:
        x0,y0,z0,x1,y1,z1=it['box'];k=margin if it['role']=='card' else 0
        out.append(box(M+x0-k,M+y0-k,Z+z0-k,x1-x0+2*k,y1-y0+2*k,z1-z0+k))
    return out

def teardrop_y(y0,length,x,z,r):
    # Horizontal hole along Y with a 45-degree roof (floor-down printing).
    k=r/math.sqrt(2)
    return combine([cyl(x,y0,z,r,length,(0,1,0)),prism_y([(x-k,z+k),(x+k,z+k),(x,z+r*math.sqrt(2))],y0,length)])

def chimney(z0,h):
    x0,y0,x1,y1=S['chimney'];return rrect(x0,y0,x1,y1,S['chimney_radius'],z0,h)

def zip_anchor(x,y,along_x=True):
    # Cable-tie bridge: 5 mm tunnel, 2.2 mm high, prints floor-down as a short bridge.
    fl=S['floor'];L,w=10.0,5.0
    if along_x:return subtract(box(x-L/2,y-w/2,fl-.01,L,w,4.2),[box(x-2.5,y-w/2-1,fl-.02,5,w+2,2.2)])
    return subtract(box(x-w/2,y-L/2,fl-.01,w,L,4.2),[box(x-w/2-1,y-2.5,fl-.02,w+2,5,2.2)])

# ---------------------------------------------------------------- storage modules
def conn_x(kind): return S['drives'][kind]['connector_x']

def drive_holes(kind,y0):
    d=S['drives'][kind];x0=conn_x(kind)
    return [(x0+a,y0+b) for a in d['holes_from_connector'] for b in d['holes_lateral']]

def drive_box(kind,y0,z0):
    d=S['drives'][kind];L,Wd,Hd=d['size'];return box(conn_x(kind),y0,z0,L,Wd,Hd)

@lru_cache(maxsize=None)
def storage_module(kind):
    # Stackable drive tray under the base. Four M3 male-female hex standoffs hang from the part above and rest on this
    # tray's 2 mm bottom ledge; the next tray's standoffs screw up through that ledge into them, so every standoff is
    # turned while fully exposed (build upside down on the lid).
    m=S['modules'][kind];Hm=m['height'];w=S['wall'];fl=S['floor'];pad=S['pad_height']
    outer=outer_block(0,Hm,e['base_bottom_chamfer'],e['split_chamfer'])
    body=subtract(outer,[rrect(w,Y0+w,W-w,Y1-w,R-w,fl,Hm)])
    # Standoff sleeves fused to the side wall like the lid columns (buttress, fillets, floor flare).
    cols=[buttressed_column(x,y,fl-.01,Hm-fl+.01,flare_at=fl-.01,r=S['column_diameter']/2,wall=w,rf=S['column_fillet'],flare=S['column_flare']) for x,y in S['standoff_centers']]
    adds=[c.intersect(outer) for c in cols]
    cuts=[chimney(-1,fl+S['column_flare']+2)]  # through the floor and the standoff-sleeve fillet beside it
    for bay in m['bays']:
        d=S['drives'][bay['type']];L,Wd,Hd=d['size'];x0=conn_x(bay['type']);y0=bay['y'];x1,y1=x0+L,y0+Wd
        for x,y in drive_holes(bay['type'],y0):
            adds.append(cyl(x,y,fl-.01,S['pad_diameter']/2,pad+.01))
            cb,cbd=d['counterbore']
            cuts+=[cyl(x,y,-1,d['clearance']/2,fl+pad+2),cyl(x,y,-.01,cb/2,cbd+.01)]
        # Locating rails and an end stop rise from the floor to 4 mm above the pads. 2.5 in rails stop short of the
        # side-hole positions so P19 clips fit for drives without bottom holes.
        rh=pad+4.0;ri=S['rail_inset'][bay['type']]
        adds+=[box(x0+ri,y0-2.6,fl-.01,L-2*ri,2,rh),box(x0+ri,y1+.6,fl-.01,L-2*ri,2,rh),box(x1+.6,y0+20,fl-.01,2,Wd-40,rh)]
    # Cable gutter between the chimney and the drive connectors: tie anchors keep the SATA leads off the drives.
    adds+=[zip_anchor(x,y,False) for x,y in S['gutter_anchors']]
    if 'dc_jack' in m:
        adds+=[zip_anchor(110,150),zip_anchor(150,150),zip_anchor(110,170),zip_anchor(150,170)]
    body=combine([body]+adds)
    # Standoff bores: open from the top down to the bottom ledge; counterbore under the ledge for the next hex.
    cb,lg=S['foot_counterbore'],S['ledge']
    for x,y in S['standoff_centers']:
        cuts+=[cyl(x,y,cb+lg,S['column_bore']/2,Hm-cb-lg+1),cyl(x,y,-1,1.7,cb+lg+2),cyl(x,y,-1,S['column_bore']/2,cb+1)]
    vz0,vz1=S['vent_z_margin'],Hm-S['vent_z_margin']
    for y in vent_positions(*e['side_vent_y']):
        if any(abs(y-cy)<8 for _,cy in S['standoff_centers']):continue
        cuts+=[slot('x',-1,w+2,y,vz0,vz1,e['vent_width']),slot('x',W-w-1,w+2,y,vz0,vz1,e['vent_width'])]
    d,dep=e['foot_pocket'];cuts+=[cyl(x,y,-1,d/2,dep+1) for x,y in e['foot_pockets']]
    cuts.append(label('HDD '+m['label'],46,Hm/2,Y0,True))
    if 'dc_jack' in m:
        j=m['dc_jack'];zc=fl+(Hm-fl)/2
        cuts+=[teardrop_y(Y1-w-1,w+2,j['x'],zc,j['diameter']/2),label(j['label'],j['x']-17,zc,Y1,False)]
    return subtract(body,cuts)

@lru_cache(maxsize=None)
def ssd_clip():
    # L-clip for 2.5 in drives that only have side holes. Local frame: wall inner face at y=0 (drive toward +y),
    # clip axis at x=0, bottom at z=0. The foot reaches under the drive to the tray's bottom-hole line; its hole and
    # captive-nut pocket are slotted 0.5 mm in y so one part serves both sides of a drive anywhere in its width tolerance.
    k=S['ssd_clip'];d=S['drives']['d25'];L,w,tf,reach,wh=k['length'],k['wall'],k['flange_thickness'],k['flange_reach'],k['wall_height']
    s=combine([box(-L/2,-w,0,L,w+reach,tf),box(-L/2,-w,0,L,w,wh)])
    ya,yb=clip_hole_span();cuts=[]
    for yy in (ya,yb):
        cuts+=[cyl(0,yy,-1,1.7,tf+2),cq.Workplane('XY').polygon(6,k['nut_af']/0.8660254).extrude(k['nut_depth']+.01).val().translate((0,yy,tf-k['nut_depth']))]
    cuts+=[box(-1.7,ya,-1,3.4,yb-ya,tf+2),box(-k['nut_af']/2,ya,tf-k['nut_depth'],k['nut_af'],yb-ya,k['nut_depth']+.01)]
    cuts.append(cyl(0,-w-1,tf+d['side_hole_height'],1.7,w+2,(0,1,0)))
    return subtract(s,cuts)

def clip_hole_span():
    # Tray hole position seen from each clip's wall face: left clip (nominal drive side) and right clip (max width).
    d=S['drives']['d25'];g=S['ssd_clip']['side_gap'];a=d['holes_lateral'][0]+g;b2=d['size'][1]+g-d['holes_lateral'][1]
    return min(a,b2)-.05,max(a,b2)+.05

def ssd_clip_placements(y0,z):
    # (x, y, rotation_deg, z) for the four clips of a 2.5 in bay; y0 is the bay's drive side, z the clip bottom.
    d=S['drives']['d25'];x0=conn_x('d25');g=S['ssd_clip']['side_gap'];out=[]
    for a in d['side_holes_from_connector']:
        out+=[(x0+a,y0-g,0,z),(x0+a,y0+d['size'][1]+g,180,z)]
    return out

def placed_clip(x,y,rot,z):
    s=ssd_clip()
    if rot:s=s.rotate((0,0,0),(0,0,1),rot)
    return s.translate((x,y,z))

@lru_cache(maxsize=None)
def storage_mount_plate():
    # Wall/robot mounting under a storage stack: same tabs and slot pattern as P1M; M3 x 12 screws pass the plate and
    # the lowest tray's ledge into that tray's standoffs.
    t=e['mount_ear_thickness'];rim=18.0
    plate=outer_block(0,t,e['base_bottom_chamfer'],e['split_chamfer'])
    plate=subtract(plate,[rrect(rim,Y0+rim,W-rim,Y1-rim,R,-1,t+2)])
    bars=[box(rim-1,(Y0+Y1)/2-9,0,W-2*rim+2,18,t),box(W/2-9,Y0+rim-1,0,18,D-2*rim+2,t)]
    body=combine([plate]+bars+[mount_ear(x,front) for x in e['mount_ear_x'] for front in (True,False)])
    body=subtract(body,[outer_block(t,t+10,0,0)])  # gussets stop at the tray outline above the plate
    L,w=e['mount_slot'];r=w/2
    cuts=[combine([box(x-L/2+r,y-r,-1,L-w,w,t+2),cyl(x-L/2+r,y,-1,r,t+2),cyl(x+L/2-r,y,-1,r,t+2)]) for x,y in mount_slot_centers()]
    for x,y in S['standoff_centers']:cuts+=[cyl(x,y,-1,1.7,t+2),cyl(x,y,-.01,3.25,4.01)]
    return subtract(body,cuts)

@lru_cache(maxsize=None)
def chimney_cap():
    # Closes the base floor's SATA drop opening when no storage is fitted. Flange sits flush in a 0.8 mm
    # counterbore on the underside; crush ribs hold it.
    cl=S['cap_clearance'];shapes=[]
    for _,s in envelope_boxes('plug_drop'):
        b=s.BoundingBox();shapes.append(box(b.xmin+cl,b.ymin+cl,0,b.xmax-b.xmin-2*cl,b.ymax-b.ymin-2*cl,F))
    plug=combine(shapes);bb=plug.BoundingBox()
    flange=rrect(bb.xmin-1.35,bb.ymin-1.35,bb.xmax+1.35,bb.ymax+1.35,1.5,0,.8)
    # Crush ribs: 0.15 mm interference with the opening on each long side.
    ribs=[box(bb.xmin-.3,(bb.ymin+bb.ymax)/2-.5,.8,.35,1,F-1.2),box(bb.xmax-.05,(bb.ymin+bb.ymax)/2-.5,.8,.35,1,F-1.2)]
    return combine([plug,flange]+ribs)

def cap_recess():
    shapes=[s.BoundingBox() for _,s in envelope_boxes('plug_drop')]
    x0=min(b.xmin for b in shapes);y0=min(b.ymin for b in shapes);x1=max(b.xmax for b in shapes);y1=max(b.ymax for b in shapes)
    return rrect(x0-1.5,y0-1.5,x1+1.5,y1+1.5,1.6,-1,1.8)

def stack(kinds):
    # Modules in order from the base downward, in assembly coordinates (base floor at Z=0).
    out=[];z=0.0
    for i,k in enumerate(kinds):
        z-=S['modules'][k]['height'];out.append((f'{k}_{i+1}',storage_module(k).translate((0,0,z)),z))
    return out

def flat(s):
    b=s.BoundingBox();return s.translate((-b.xmin,-b.ymin,-b.zmin))

PRINT_ROTATION={'cover':((1,0,0),180),'front_no_gmsl':((1,0,0),90),'front_gmsl':((1,0,0),90),'rear_io':((1,0,0),-90),'side_hatch':((0,1,0),90)}

def print_parts():
    return {'base':base(),'base_mount':base(True),'cover':cover(),'front_no_gmsl':panel(),'front_gmsl':panel(gmsl=True),
            'rear_io':panel(front=False),'side_hatch':side_hatch(),'mount_fit_template':fit_template(),'m3_insert_coupon':m3_coupon(),
            'countersink_coupon':countersink_coupon(),'rpsma_coupon':rpsma_coupon(),'rail_coupon':rail_coupon(),'rail_key':rail_key(),
            'storage_35':storage_module('storage_35'),'storage_25':storage_module('storage_25'),'storage_mount_plate':storage_mount_plate(),'chimney_cap':chimney_cap(),'ssd_clip':ssd_clip()}

if __name__=='__main__':
    import trimesh
    parts=print_parts()
    report={};assembly=cq.Assembly(name='J501_enclosure_v05')
    for name,s in parts.items():
        print('Export',name,flush=True)
        if not s.isValid() or len(s.Solids())!=1:raise RuntimeError(f'Invalid/disconnected part: {name}')
        cq.exporters.export(s,str(OUT/(name+'.step')))
        print_shape=s
        if name in PRINT_ROTATION:axis,ang=PRINT_ROTATION[name];print_shape=s.rotate((0,0,0),axis,ang)
        print_shape=flat(print_shape)
        cq.exporters.export(print_shape,str(OUT/(name+'.stl')),tolerance=0.05,angularTolerance=0.12)
        mesh=trimesh.load_mesh(OUT/(name+'.stl'))
        keep=mesh.nondegenerate_faces(); removed=int((~keep).sum())
        if removed:
            mesh.update_faces(keep);mesh.remove_unreferenced_vertices();mesh.export(OUT/(name+'.stl'))
        report[name]={'degenerate_tessellation_faces_removed':removed,'cad_valid':s.isValid(),'solid_count':len(s.Solids()),'watertight':bool(mesh.is_watertight),
                      'print_bounds_mm':[round(float(v),3) for v in mesh.extents],'volume_cm3':round(s.Volume()/1000,2)}
        if not mesh.is_watertight:raise RuntimeError(f'Non-watertight STL: {name}')
        if name in ['base','cover','front_gmsl','rear_io','side_hatch']:assembly.add(s,name=name)
    assembly.save(str(OUT/'assembly_gmsl.step'))
    (OUT/'geometry-checks.json').write_text(json.dumps(report,indent=2)+'\n')
    # Exact plastic-to-plastic overlap check in assembly coordinates.
    main=['base_mount','cover','front_gmsl','front_no_gmsl','rear_io','side_hatch']; collisions=[]
    for i,a in enumerate(main):
        for b in main[i+1:]:
            if {a,b}=={'front_gmsl','front_no_gmsl'}:continue
            v=parts[a].intersect(parts[b]).Volume()
            collisions.append({'parts':[a,b],'intersection_mm3':round(v,6)})
            if v>0.01:raise RuntimeError(f'Assembly collision {a} / {b}: {v}')
    underside_gap=e['board_support_height']+p['lowest_component']
    cooler_top=FAN_TOP
    top_gap=H-e['fan_grille']['thickness']-cooler_top
    finger_to_fan=e['fan_grille']['thickness']+top_gap-finger_reach(grille_gap())
    keepout=fan_keepout_gaps()
    assert underside_gap>=3 and top_gap>=c['minimum_fan_clearance'] and finger_to_fan>=1,(underside_gap,top_gap,finger_to_fan)
    assert keepout['frame']>=c['minimum_fan_clearance'] and keepout['conservative']>=0.5,keepout
    (OUT/'assembly-checks.json').write_text(json.dumps({'revision':P['revision'],'plastic_intersections':collisions,
       'underside_clearance_mm':underside_gap,'assumed_cooler_top_z':round(cooler_top,3),
       'assumed_fan_to_grille_mm':round(top_gap,3),'grille_opening_mm':round(grille_gap(),2),
       'test_finger_to_fan_mm':round(finger_to_fan,2),'fan_xy_uncertainty_mm':c.get('fan_xy_uncertainty',0.0),
       'fan_moved_min_gap_mm':keepout['frame'],'fan_95mm_moved_min_gap_mm':keepout['conservative'],
       'measured_pcb_top_to_fan_top_mm':(c.get('measured') or {}).get('pcb_top_to_fan_top_mm'),
       'physical_fit_verified':False,'gmsl_position_verified':False,'cooler_identity_verified':bool(c.get('identity_confirmed'))},indent=2)+'\n')
    print(json.dumps(report,indent=2))
