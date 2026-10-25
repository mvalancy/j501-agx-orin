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
F=e['floor']; Z=F+e['standoff']; T=e['wall']; H=e['height']; BH=e['base_height']
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
        post=combine([cyl(x,y,F,e['board_post_diameter']/2,e['standoff']-e['board_landing_height']),
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

def insert_cut(x,y,z,d):
    return [cyl(x,y,z,e['insert_pilot_diameter']/2,e['insert_pocket_depth'],d), cyl(x,y,z,3.3,14,d),
            cq.Solid.makeCone(e['insert_entry_diameter']/2,e['insert_pilot_diameter']/2,e['insert_entry_depth'],cq.Vector(x,y,z),cq.Vector(*d))]

def base():
    shapes=[box(0,0,0,W,D,F),box(0,0,F,T,D,BH-F),box(W-T,0,F,T,D,BH-F)]+board_posts()
    for x in (3,W-14):
        for y in (0,D-19):shapes.append(box(x,y,F,11,19,BH-F))
    for x in (0,W-13):
        for y in e['cover_screw_y']:shapes.append(box(x,y,BH-24,13,20,24))
    # Independent panel fasteners engage captive inserts in solid upper corner bosses.
    for x in (10,W-30):
        for y in (12.8,D-25.8):shapes.append(box(x,y,50,20,13,BH-50))
    for y in (66,130):shapes.append(box(W-13,y-10,34,13,20,20))
    s=combine(shapes);cuts=[]
    for x in (10,W-14):
        for y in (6,D-12.8):cuts.append(box(x,y,F,4,SW,BH-F+1))
    for x in (8,W-8):
        for cy in e['mount_ear_y']:
            for y in (cy-8,cy+8):cuts.append(cyl(x,y,-1,e['m6_clearance']/2,F+2))
    for y in e['cover_screw_y']:
        for x,d in [(0,(1,0,0)),(W,(-1,0,0))]:cuts+=insert_cut(x,y,e['cover_screw_z'],d)
    for x in (20,W-20):
        cuts+=insert_cut(x,12.8,60,(0,1,0))+insert_cut(x,D-12.8,60,(0,-1,0))
    for y in (66,130):cuts+=insert_cut(W,y,44,(-1,0,0))
    cuts.append(box(W-T-1,76,12,T+2,42,22))
    for y in range(46,int(D)-45,14):cuts.append(box(-1,y,27,T+2,7,24))
    return subtract(s,cuts)

def cover():
    # Overlapping cap: nominal 0.3 mm per-side sliding clearance.
    x0=-T-C;y0=-T-C;cw=W+2*(T+C);cd=D+2*(T+C);bottom=BH-e['lid_overlap']
    s=subtract(box(x0,y0,bottom,cw,cd,H-bottom),[box(-C,-C,bottom-1,W+2*C,D+2*C,H-T-bottom+1)])
    cuts=[]
    # Front/rear skirts are relieved to keep all I/O panel apertures visible.
    cuts += [box(-C,-T-C-1,bottom-1,W+2*C,T+2,BH+0.3-bottom+1),
             box(-C,D+C-1,bottom-1,W+2*C,T+2,BH+0.3-bottom+1)]
    for y in e['cover_screw_y']:
        cuts.append(cyl(-T-C-1,y,e['cover_screw_z'],3.3,W+2*(T+C)+2,(1,0,0)))
    # Roof grid, 5 x 16 mm openings with continuous ribs; print roof down.
    for x in range(18,int(W)-23,14):
        for y in range(18,int(D)-27,28):cuts.append(box(x,y,H-T-1,8,20,T+2))
    for y in range(28,int(D)-27,14):
        for x in (-T-C-1,W+C-1):cuts.append(box(x,y,74,T+2,8,24))
    for x in range(28,int(W)-27,14):
        for y in (-T-C-1,D+C-1):cuts.append(box(x,y,74,8,T+2,24))
    cuts.append(box(W+C-1,55.6,bottom-1,T+2,84.8,54.4-bottom+1))
    s=subtract(s,cuts)
    # Stops at panel ends, attached continuously to sidewalls for roof-down printing.
    stops=[]
    for x in (-C,W-14):
        for y in (0,D-19):stops.append(box(x,y,BH+0.3,14+C,19,H-T-BH-0.3))
    return combine([s]+stops)

def panel_openings(front=True,gmsl=False):
    # Exact source component envelopes + 0.6 mm; merge narrow adjacent ribs below 4 mm.
    rects=[list(v) for k,v in P['openings'].items() if k.startswith('front_' if front else 'rear_')]
    if gmsl:rects += [[x,1.878,x+12,17.578] for x in P['gmsl']['candidate_port_left_edges']]
    q=e['port_clearance'];rects=[[x-q,z-q,X+q,Zz+q] for x,z,X,Zz in rects]
    bridges=[]
    for i,a in enumerate(rects):
        for bb in rects[i+1:]:
            left,right=sorted((a,bb),key=lambda t:t[0]);gap=right[0]-left[2]
            lo=max(a[1],bb[1]);hi=min(a[3],bb[3])
            if 0<gap<4 and hi>lo:bridges.append([left[2]-.1,lo,right[0]+.1,hi])
            low,high=sorted((a,bb),key=lambda t:t[1]);gap=high[1]-low[3]
            lo=max(a[0],bb[0]);hi=min(a[2],bb[2])
            if 0<gap<4 and hi>lo:bridges.append([lo,low[3]-.1,hi,high[1]+.1])
    return rects+bridges

def panel(front=True,gmsl=False):
    y=6.4 if front else D-12.4
    s=box(10.3,y,F,W-20.6,PT,BH-F-e['panel_top_clearance'])
    cuts=[box(M+x,y-1,Z+z,X-x,PT+2,Zz-z) for x,z,X,Zz in panel_openings(front,gmsl)]
    for x in (20,W-20):cuts.append(cyl(x,y-1,60,3.3,PT+2,(0,1,0)))
    return subtract(s,cuts)

def side_hatch():
    s=box(W,56,6,6,84,48)
    return subtract(s,[cyl(W-1,y,44,3.3,8,(1,0,0)) for y in (66,130)])

def m3_coupon():
    s=box(0,0,0,90,20,14)
    return subtract(s,[cyl(x,10,14,d/2,11,(0,0,-1)) for x,d in zip((10,27.5,45,62.5,80),(3.7,3.8,3.9,4,4.1))])

def mounting_insert_cuts():
    cuts=[]
    for y in (-8,8):
        cuts += [cyl(8,y,0,3.75,11,(0,0,-1)),
                 cq.Solid.makeCone(4.1,3.75,0.6,cq.Vector(8,y,0),cq.Vector(0,0,-1))]
    return cuts

def ear():
    # Left ear: two M6 x 10 mm inserts; closed 6.6 x 14 mm external slot.
    s=box(-24,-20,-14,42,40,14)
    cuts=mounting_insert_cuts()
    cuts += [cyl(-12,y,-15,3.3,16) for y in (-3.7,3.7)]
    cuts.append(box(-15.3,-3.7,-15,6.6,7.4,16))
    return subtract(s,cuts)

def foot():
    s=box(-4,-20,-14,24,40,14)
    cuts=mounting_insert_cuts()
    cuts.append(cyl(8,0,-14.01,5,1.01))
    return subtract(s,cuts)

def coupon():
    # Same horizontally printed bore orientation as the base's cover bosses.
    s=box(0,0,0,104,18,20)
    cuts=[]
    for x,d in zip((12,32,52,72,92),(7.3,7.4,7.5,7.6,7.7)):
        cuts += [cyl(x,0,10,d/2,11,(0,1,0)),
                 cq.Solid.makeCone(4.1,d/2,0.6,cq.Vector(x,0,10),cq.Vector(0,1,0))]
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
    parts={'base':base(),'cover':cover(),'front_no_gmsl':panel(),'front_gmsl':panel(gmsl=True),
           'rear_io':panel(front=False),'mount_ear':ear(),'desktop_foot':foot(),
           'insert_coupon':coupon(),'mount_fit_template':fit_template(),'side_hatch':side_hatch(),'m3_insert_coupon':m3_coupon()}
    report={};assembly=cq.Assembly(name='J501_fit_check_v02')
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
    underside_gap=e['standoff']+p['lowest_component']
    cooler_top=Z+p['thickness']+c['seat_above_pcb_top']+c['size'][2]
    top_gap=H-T-cooler_top
    assert underside_gap>=3 and top_gap>=c['minimum_top_clearance']
    (OUT/'assembly-checks.json').write_text(json.dumps({'plastic_intersections':collisions,
       'underside_clearance_mm':underside_gap,'assumed_cooler_top_z':cooler_top,
       'assumed_cooler_to_roof_mm':top_gap,
       'physical_fit_verified':False,'gmsl_position_verified':False,'cooler_identity_verified':False},indent=2)+'\n')
    print(json.dumps(report,indent=2))
