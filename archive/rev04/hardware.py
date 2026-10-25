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

def enclosure_hardware():
    items=[]
    for x,y in b.e['cover_screw_locations']:
        left=x==0;ia='xp' if left else 'xm';sa='xm' if left else 'xp'
        wx=-b.T-b.C if left else b.W+b.T+b.C;hx=wx-1.6 if left else wx+1.6
        items += [('H1 cover insert',orient(insert(),ia).translate((x,y,b.e['cover_screw_z'])),COL['brass']),
                  ('H2 cover washer',orient(washer(),sa).translate((wx,y,b.e['cover_screw_z'])),COL['steel']),
                  ('H3 cover screw',orient(screw(),sa).translate((hx,y,b.e['cover_screw_z'])),COL['steel'])]
    for x,y in b.p['mount_holes']:
        x+=b.M;y+=b.M
        items += [('H4 M3 board insert',orient(board_insert(),'zm').translate((x,y,b.Z)),COL['brass']),
                  ('H5 M3 board screw',screw(3,10,5.7,1.65,2).translate((x,y,b.Z+b.p['thickness'])),COL['steel'])]
    return items

def cooler_and_module():
    c=b.c;cx,cy=c['center_in_pcb'];cx+=b.M;cy+=b.M;sx,sy,sz=c['size']
    seat=b.Z+b.p['thickness']+c['seat_above_pcb_top']
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
    for x,y in b.p['module_mount_centers']:
        items.append(('H7 existing cooler fastener - schematic',screw(3,23,6,3,2.5).translate((b.M+x,b.M+y,seat+3)),COL['steel']))
    return items

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
