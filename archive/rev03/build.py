"""J501 printable fit-check enclosure. All dimensions in mm.
See docs/measurement-register.csv before editing or printing.
Output STLs are placed on z=0 in intended print orientation; assembly STEP
uses the enclosure datum. Vendor geometry and envelopes are NOT printed parts.
"""
from pathlib import Path
import json, math
import cadquery as cq
ROOT=Path(__file__).resolve().parents[1]
P=json.loads((ROOT/'cad/parameters.json').read_text())
p,e,c=P['pcb'],P['enclosure'],P['cooler']
M=e['pcb_margin']; W=p['width']+2*M; D=p['depth']+2*M
F=e['floor']; Z=F+e['board_support_height']; T=e['wall']; H=e['height']; BH=e['base_height']
C=e['lid_clearance']; PT=e['panel_thickness']; SW=e['panel_slot_width']
OUT=ROOT/'exports'; OUT.mkdir(exist_ok=True)

def box(x,y,z,dx,dy,dz): return cq.Solid.makeBox(dx,dy,dz,cq.Vector(x,y,z))
def cyl(x,y,z,r,h,d=(0,0,1)): return cq.Solid.makeCylinder(r,h,cq.Vector(x,y,z),cq.Vector(*d))
def combine(parts): return parts[0].fuse(*parts[1:]).clean() if len(parts)>1 else parts[0]
def subtract(s,parts): return s.cut(*parts).clean() if parts else s

def board_posts():
    posts=[]; relief=[]
    # Source boxes conservatively include every underside component. Keep 0.5 mm.
    rows=json.loads((ROOT/'references/solids.json').read_text())
    origin=p['origin_in_source_step']
    for x,y in p['mount_holes']:
        x+=M;y+=M
        post=combine([cyl(x,y,F,e['board_post_diameter']/2,e['board_support_height']-e['board_landing_height']),
                      cyl(x,y,Z-e['board_landing_height']-.2,e['board_landing_diameter']/2,e['board_landing_height']+.2)])
        for row in rows:
            if row['index'] in range(5155,5163) or row['index']==5169:continue
            bb=row['bbox']; xx,yy,zz=[bb[i]-origin[i]+[M,M,Z][i] for i in range(3)]
            X,Y,ZZ=[bb[i+3]-origin[i]+[M,M,Z][i] for i in range(3)]
            if zz>=Z-.001 or X<x-8.5 or xx>x+8.5 or Y<y-8.5 or yy>y+8.5:continue
            relief.append(box(xx-.5,yy-.5,zz-.5,X-xx+1,Y-yy+1,ZZ-zz+1))
        post=subtract(post,relief)
        post=subtract(post,[cyl(x,y,Z,e['board_insert_pilot']/2,e['board_insert_depth'],(0,0,-1)),
             cq.Solid.makeCone(2.2,e['board_insert_pilot']/2,.6,cq.Vector(x,y,Z),cq.Vector(0,0,-1))])
        posts.append(post)
    return posts

def pointed_hole(x,y,z,r,depth,d=(1,0,0)):
    # Circular seat with 45-degree relief at both Z poles, printable in either orientation.
    circle=cyl(x,y,z,r,depth,d)
    q=r/math.sqrt(2);pts=[(-q,q),(0,r*math.sqrt(2)),(q,q),(q,-q),(0,-r*math.sqrt(2)),(-q,-q)]
    # YZ plane, extrusion along X; then reverse for right side.
    extra=cq.Workplane('YZ').polyline(pts).close().extrude(depth).val()
    if d[0]<0:extra=extra.rotate((0,0,0),(0,0,1),180)
    return circle.fuse(extra.translate((x,y,z)))

def vent(x,y,z,width,height,depth,front=False):
    w=width;h=height
    s=cq.Workplane('YZ').polyline([(w/2,0),(w,w/2),(w,h-w/2),(w/2,h),(0,h-w/2),(0,w/2)]).close().extrude(depth).val()
    if front:s=s.rotate((0,0,0),(0,0,1),90).translate((w,0,0))
    return s.translate((x,y,z))

def insert_cut(x,y,z,d):
    return [pointed_hole(x,y,z,e['insert_pilot_diameter']/2,e['insert_pocket_depth'],d), pointed_hole(x,y,z,3.3,14,d),
            cq.Solid.makeCone(e['insert_entry_diameter']/2,e['insert_pilot_diameter']/2,e['insert_entry_depth'],cq.Vector(x,y,z),cq.Vector(*d))]

def base(with_ears=False):
    shapes=[box(0,0,0,W,D,F),box(0,0,F,T,D,BH-F),box(W-T,0,F,T,D,BH-F)]+board_posts()
    for x in (3,W-14):
        for y in (0,D-19):shapes.append(box(x,y,F,11,19,BH-F))
    # Cover bosses rise directly from the floor. No floating horizontal shelves.
    for x,y in e['cover_screw_locations']:shapes.append(box(0 if x==0 else W-13,y-10,F,13,20,BH-F))
    # Side hatch rails start on the bed plane; wide lips retain the thick sliding panel.
    for y in (66,118):shapes.append(box(W-T,y,0,17,10,BH))
    if with_ears:
        for cy in e['mount_ear_y']:
            shapes += [box(-22,cy-18,0,28,36,12),box(W-6,cy-18,0,28,36,12)]
    cuts=[]
    for x in (10,W-14):
        for y in (5,D-12.5):cuts.append(box(x,y,F,4,SW,BH-F+1))
    for x,y in e['cover_screw_locations']:cuts+=insert_cut(x,y,e['cover_screw_z'],(1,0,0) if x==0 else (-1,0,0))
    for y in (72,118):cuts.append(box(W,y,F,6.5,4,BH-F+1))
    # J17 service opening has a 45-degree upper arch; no unsupported 38 mm bridge.
    cuts.append(cq.Workplane('YZ',origin=(W-T-1,78,12)).polyline([(0,0),(38,0),(38,22),(19,41),(0,22)]).close().extrude(T+2).val())
    for y in range(46,int(D)-45,14):cuts.append(vent(-1,y,27,7,24,T+2))
    if with_ears:
        for x in (-13,W+13):
            for cy in e['mount_ear_y']:
                cuts += [cyl(x,cy-2.7,-1,3.3,14),cyl(x,cy+2.7,-1,3.3,14),box(x-3.3,cy-2.7,-1,6.6,5.4,14)]
    return subtract(combine(shapes),cuts)

def cover():
    # Overlapping cap: nominal 0.4 mm per-side sliding clearance.
    x0=-T-C;y0=-T-C;cw=W+2*(T+C);cd=D+2*(T+C);bottom=BH-e['lid_overlap']
    s=subtract(box(x0,y0,bottom,cw,cd,H-bottom),[box(-C,-C,bottom-1,W+2*C,D+2*C,H-T-bottom+1)])
    cuts=[]
    # Front/rear skirts are relieved to keep all I/O panel apertures visible.
    cuts += [box(-C,-T-C-1,bottom-1,W+2*C,T+2,BH+0.3-bottom+1),
             box(-C,D+C-1,bottom-1,W+2*C,T+2,BH+0.3-bottom+1)]
    for x,y in e['cover_screw_locations']:
        xx=-T-C-1 if x==0 else W+C-1
        cuts.append(pointed_hole(xx,y,e['cover_screw_z'],3.3,T+2))
    # Roof grid, 8 x 20 mm openings with continuous ribs; print roof down.
    for x in range(18,int(W)-23,14):
        for y in range(18,int(D)-27,28):cuts.append(box(x,y,H-T-1,8,20,T+2))
    for y in range(28,int(D)-27,14):
        for x in (-T-C-1,W+C-1):cuts.append(vent(x,y,74,8,24,T+2))
    for x in range(28,int(W)-27,14):
        for y in (-T-C-1,D+C-1):cuts.append(vent(x,y,74,8,24,T+2,front=True))
    cuts.append(box(W+C-1,65.75,bottom-1,T+2,62.5,BH-bottom+1))
    s=subtract(s,cuts)
    # Stops at panel ends, attached continuously to sidewalls for roof-down printing.
    stops=[]
    for x in (-C,W-14):
        for y in (0,D-19):stops.append(box(x,y,BH,14+C,19,H-T-BH))
    return combine([s]+stops)

def panel_openings(front=True,gmsl=False):
    keys=['front_audio','front_network_power'] if front else ['rear_terminal','rear_hdmi_usb','rear_usb_c_pair']
    if gmsl:keys=['front_audio_gmsl','front_network_power']
    return [P['openings'][k] for k in keys]

def panel(front=True,gmsl=False):
    y=e['front_panel_y'] if front else e['rear_panel_y']
    s=box(10.25,y,F,W-20.5,PT,BH-F-e['panel_top_clearance'])
    cuts=[box(M+x,y-1,Z+z,X-x,PT+2,Zz-z) for x,z,X,Zz in panel_openings(front,gmsl)]
    return subtract(s,cuts)

def side_hatch():
    # Edges slide down continuous channels; cover captures the top edge.
    plate=box(W+.25,72.25,F,6,49.5,BH-F-.2)
    pull=box(W+6.25,90,54,6,14,6)
    return plate.fuse(pull).clean()

def rail_coupon():
    # Short exact front-panel channel and sliding key, exported separately.
    s=box(0,0,0,20,20,24)
    return subtract(s,[box(8,6,3,13,6.5,22)])

def rail_key():return box(0,0,0,10,6,18)

def m3_coupon():
    s=box(0,0,0,90,20,14)
    return subtract(s,[cyl(x,10,14,d/2,11,(0,0,-1)) for x,d in zip((10,27.5,45,62.5,80),(3.7,3.8,3.9,4,4.1))])

def coupon():
    s=box(0,0,0,104,18,20);cuts=[]
    for x,d in zip((12,32,52,72,92),(7.3,7.4,7.5,7.6,7.7)):
        seat=pointed_hole(0,0,0,d/2,11).rotate((0,0,0),(0,0,1),90).translate((x,0,10))
        cuts += [seat,cq.Solid.makeCone(4.1,d/2,.6,cq.Vector(x,0,10),cq.Vector(0,1,0))]
    return subtract(s,cuts)

def fit_template():
    # 3 mm sparse frame reproduces carrier mounting pattern and enclosure datum.
    holes=[(M+x,M+y) for x,y in p['mount_holes']]
    shapes=[]
    for x,y in holes:shapes.append(cyl(x,y,0,6,3))
    for y in (holes[0][1],holes[2][1]):shapes.append(box(holes[0][0],y-3,0,150,6,3))
    for x in (holes[0][0],holes[1][0]):shapes.append(box(x-3,holes[0][1],0,6,130,3))
    return subtract(combine(shapes),[cyl(x,y,-1,1.7,5) for x,y in holes])

def flat(s):
    b=s.BoundingBox();return s.translate((-b.xmin,-b.ymin,-b.zmin))

if __name__=='__main__':
    import trimesh
    parts={'base':base(),'base_mount':base(True),'cover':cover(),'front_no_gmsl':panel(),'front_gmsl':panel(gmsl=True),
           'rear_io':panel(front=False),
           'insert_coupon':coupon(),'mount_fit_template':fit_template(),'side_hatch':side_hatch(),'m3_insert_coupon':m3_coupon(),'rail_coupon':rail_coupon(),'rail_key':rail_key()}
    report={};assembly=cq.Assembly(name='J501_fit_check_v03')
    for name,s in parts.items():
        print('Export',name,flush=True)
        if not s.isValid() or len(s.Solids())!=1:raise RuntimeError(f'Invalid/disconnected part: {name}')
        cq.exporters.export(s,str(OUT/(name+'.step')))
        print_shape=s
        if name=='cover':print_shape=s.rotate((0,0,0),(1,0,0),180)
        if name=='side_hatch':print_shape=s.rotate((0,0,0),(0,1,0),-90)
        if name.startswith('front_') or name=='rear_io':print_shape=s.rotate((0,0,0),(1,0,0),90)
        print_shape=flat(print_shape)
        cq.exporters.export(print_shape,str(OUT/(name+'.stl')),tolerance=0.08,angularTolerance=0.15)
        mesh=trimesh.load_mesh(OUT/(name+'.stl'))
        report[name]={'cad_valid':s.isValid(),'solid_count':len(s.Solids()),'watertight':bool(mesh.is_watertight),
                      'print_bounds_mm':[round(float(v),3) for v in mesh.extents],
                      'volume_cm3':round(s.Volume()/1000,2)}
        if not mesh.is_watertight:raise RuntimeError(f'Non-watertight STL: {name}')
        if name in ['base','cover','front_gmsl','rear_io','side_hatch']:assembly.add(s,name=name)
    assembly.save(str(OUT/'assembly_gmsl.step'))
    (OUT/'geometry-checks.json').write_text(json.dumps(report,indent=2)+'\n')
    # Exact plastic-to-plastic overlap check in assembly coordinates.
    main=['base','cover','front_gmsl','rear_io','side_hatch']; collisions=[]
    for i,a in enumerate(main):
        for b in main[i+1:]:
            v=parts[a].intersect(parts[b]).Volume()
            collisions.append({'parts':[a,b],'intersection_mm3':round(v,6)})
            if v>0.01:raise RuntimeError(f'Assembly collision {a} / {b}: {v}')
    underside_gap=e['board_support_height']+p['lowest_component']
    cooler_top=Z+p['thickness']+c['seat_above_pcb_top']+c['size'][2]
    top_gap=H-T-cooler_top
    assert underside_gap>=3 and top_gap>=c['minimum_top_clearance']
    (OUT/'assembly-checks.json').write_text(json.dumps({'plastic_intersections':collisions,
       'underside_clearance_mm':underside_gap,'assumed_cooler_top_z':cooler_top,
       'assumed_cooler_to_roof_mm':top_gap,
       'physical_fit_verified':False,'gmsl_position_verified':False,'cooler_identity_verified':False},indent=2)+'\n')
    print(json.dumps(report,indent=2))
