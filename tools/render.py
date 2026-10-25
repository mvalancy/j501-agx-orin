from pathlib import Path
import sys,json,math
sys.path.insert(0,str(Path(__file__).resolve().parent))
from renderkit import *

base=b.base();mounted=b.base(True);cover=b.cover();front=b.panel(gmsl=True);rear=b.panel(front=False);hatch=b.side_hatch()
shell=(.21,.23,.26);lid=(.25,.27,.31);plate=(.55,.58,.61);accent=(.86,.47,.18)
hw=[(s,col) for _,s,col in h.enclosure_hardware()]
electronics=[(s,col) for _,s,col in h.cooler_and_module()+h.gmsl()]
plastic=[(mounted,shell),(front,plate),(rear,plate),(hatch,plate)]
rev=b.P['revision'].split('-')[0]
render('assembled.png',plastic+hw+electronics+[(cover,lid)],f'Rev {rev} / flush shell, framed I/O plates, finger-safe hex roof',hardware_meshes(),note='Four M3 lid screws from the top; four M3 board screws; four cooler tie-down screws from below. GMSL XY and cooler identity remain provisional.')
render('rear.png',plastic+hw+electronics+[(cover,lid)],'Rear I/O / per-port windows sized for mating plug overmolds',hardware_meshes(),view='rear')
render('no-gmsl.png',[(base,shell),(b.panel(),plate),(rear,plate),(hatch,plate)]+hw+[(s,col) for _,s,col in h.cooler_and_module()]+[(cover,lid)],'Desktop base / no GMSL / no dummy openings',hardware_meshes())
render('open.png',plastic+hw+electronics,'Open assembly / all carrier solids and open shells retained',hardware_meshes(),note='Source carrier and NVIDIA module; candidate mini-FAKRA STEP. GMSL component locations and cooler are provisional.')
render('top.png',plastic+hw+electronics,'Top inspection / board corner supports and cooler tie-down pattern',hardware_meshes(),view='top')
render('bottom.png',[(mounted,shell)]+[(s,col) for _,s,col in h.heatsink_tiedown()],'Underside / recessed cooler tie-downs, foot pockets, mounting tabs',view='bottom',note='Flat-head screws sit 0.43 mm below the floor, so the base stays flat on a desk or a mounting plate.')
cut=b.box(-50,66,-5,320,200,140)
sec=[(mounted.intersect(cut),shell),(cover.intersect(cut),lid)]+[(s.intersect(cut),col) for _,s,col in h.enclosure_hardware()+h.cooler_and_module() if s.BoundingBox().ymax>66]
render('heatsink-tiedown.png',sec,'Section Y66 / cooler mass carried into the floor',hardware_meshes(),view='section',clip=((0,66,0),(0,1,0)),note='Printed column under each 92 x 79 cooler hole: floor -> column -> PCB -> module/cooler stack. Screw length = original under-head length + 19.6 mm.')
expl=[(mounted,shell),(front.translate((0,-70,25)),plate),(rear.translate((0,70,25)),plate),(hatch.translate((55,0,25)),plate),(cover.translate((0,0,150)),lid)]
for name,s,col in h.enclosure_hardware():
 off=(0,0,0) if 'RP-SMA' in name else (0,0,190) if 'lid' in name and 'screw' in name else (0,0,25) if 'insert' in name else (0,0,95)
 expl.append((s.translate(off),col))
for name,s,col in h.cooler_and_module():expl.append((s.translate((0,0,-45)) if name.startswith('H7') else s.translate((0,0,110)),col))
for name,s,col in h.gmsl():expl.append((s.translate((0,-25,75)),col))
labels=[('P2','Lid: hex grille, 4 x M3 from top',(103,96,262),(25,130)),
 ('E3','Existing cooler (reference envelope)',(105,105,195),(1180,190)),
 ('E1','Carrier with complete source shells',(185,170,80),(1180,400)),
 ('E4–E8','GMSL + candidate connector models',(70,0,113),(25,400)),
 ('H1/H3','Lid inserts and M3 x 16 screws',(8.8,30,247),(25,250)),
 ('H4–H5','M3 inserts in printed supports',(30,31.5,45),(1180,640)),
 ('P3','Front I/O plate (GMSL variant)',(95,-62,60),(25,860)),
 ('P1M','Base + tabs + cooler columns',(30,100,8),(25,1020)),
 ('P5','Rear I/O plate',(140,250,60),(1180,520)),
 ('P10','Flush J17 hatch',(261,97,55),(1300,800)),
 ('H7','Cooler tie-down screws from below',(151,145,-25),(1180,1080))]
render('exploded.png',expl,'Exploded / sliding plates captured by the lid; cooler tied to the floor',hardware_meshes(60),labels=labels,size=(1800,1250),note='GMSL factory supports are separate from the printed carrier supports; their thread/height need checking.')
parts=[('P1','base',base,'The base for desktop use AND for storage stacks: 4 stacking inserts in the column feet, SATA drop opening, foot pockets'),('P1M','base_mount',mounted,'Wall/robot base WITHOUT storage: four 8 mm tabs, M6 slots. With storage use P1 + trays + P17'),
 ('P2','cover',cover,f'{len(b.hex_centers())} hex cells, 10 mm A/F (finger-safe), 6 mm deep, fan-side inlet chamfer; roof face down'),('P3','front_gmsl',front,'Audio, GMSL, 1G, 10G + LED, DC IN; debossed legends'),('P4','front_no_gmsl',b.panel(),'Audio, 1G, 10G + LED, DC IN'),
 ('P5','rear_io',rear,'I/O terminal, HDMI, USB-A x3, USB-C pair'),('P9','mount_fit_template',b.fit_template(),'Cradle jig: carrier sits on pad-sized landings, same supports and relief as P1'),
 ('P10','side_hatch',hatch,'Flush door with 45-degree V tongues; lid captures the top'),('P11','m3_insert_coupon',b.m3_coupon(),'M3 pilots: 3.7 / 3.8 / 3.9 / 4.0 / 4.1 mm'),('P12','rail_coupon',b.rail_coupon(),'Corner-post channel: 3.5 mm for the 3.0 mm plates'),('P13','rail_key',b.rail_key(),'3.0 mm sliding key'),
 ('P14','countersink_coupon',b.countersink_coupon(),'Floor + column: raised 7.0 / 7.4 mm countersink seats for the M3 x 35 flat heads'),
 ('P15','storage_35',b.storage_module('storage_35'),'One 3.5 in drive (SFF-8301 6-32 holes, all three pairs), cable gutter, 12 V IN hole, tie anchors'),
 ('P16','storage_25',b.storage_module('storage_25'),'Two 2.5 in drives up to 15 mm (SFF-8201 M3 holes), cable gutter, tie anchors'),
 ('P17','storage_mount_plate',b.storage_mount_plate(),'Wall/robot plate under a storage stack: P1M tab and slot pattern, M3 into the standoffs'),
 ('P18','chimney_cap',b.chimney_cap(),'Closes the base SATA drop opening when no storage is fitted; flush flange, crush ribs'),
 ('P19','ssd_clip',b.ssd_clip(),'Side-hole clip for 7 mm SSDs: M3 x 5 into the drive side, captive M3 nut over the tray bottom-hole pattern')]
for code,name,shape,note in parts:render('part-'+name+'.png',[(shape,plate if code in ('P3','P4','P5','P10') else shell)],code+' / '+name.replace('_',' '),note=note,size=(1100,800))
for code,name,shape,note in [('H1','M3_insert',h.board_insert(),'User M3 x 10: 3.75 mm starter, 4.2 mm body (board and lid)'),('H3','M3_lid_screw',h.screw(3,16,5.5,3,2.5),'M3 x 16 socket head: 10 mm into the lid insert'),('H5','M3_board_screw',h.screw(3,10,5.7,1.65,2),'M3 x 10 button head: 8.42 mm nominal insert engagement'),('H6','jumper_cap',h.jumper(),'Generic 2.54 mm jumper cap; no electrical configuration implied'),('H7','cooler_tiedown_screw',h.flat_screw(3,30),'M3 countersunk (ISO 10642 assumed); length = original + 19.6 mm')]:
 render('part-'+name+'.png',[(shape,h.COL['brass'] if code=='H1' else h.COL['steel'])],code+' / '+name.replace('_',' '),note=note,size=(1100,800))
render('part-carrier.png',[],'E1 / carrier STEP with all open surface shells',hardware_meshes(),size=(1400,1000))
render('part-gmsl.png',[(s,col) for _,s,col in h.gmsl()],'E4–E8 / GMSL board, candidate connector STEP and component envelopes',note='Carrier-derived support centers; board/connector XY and top component placement remain provisional.',size=(1400,1000))
render('part-cooler.png',[(s,col) for _,s,col in h.cooler_and_module()],'E2 / E3 / H7 — module, cooler and floor tie-down screws',note='Cooler 110 x 100 x 50 mm reference envelope. Tie-down screws pass the floor columns and PCB into the cooler.',size=(1400,1000))
render('part-module.png',[(s,col) for name,s,col in h.cooler_and_module() if name.startswith('E2')],'E2 / NVIDIA AGX Orin module STEP',size=(1400,1000))
render('part-fakra.png',[(s,col) for name,s,col in h.gmsl() if name.startswith('E5')][:1],'E5 / Amphenol FM4-NZRP-PCB-1 candidate STEP',note='Matches Seeed footprint size. Actual manufacturer, keying and cable-side model remain unconfirmed.',size=(1100,800))
render('side-access.png',[(base,shell),(hatch.translate((40,0,30)),plate),(h.jumper().translate((b.W+15,96,22)),h.COL['dark'])],'J17 access / lid removed; flush hatch lifts out',hardware_meshes(),view='side',note='42 mm-wide door in the wall plane. 45-degree V tongues locate it; the lid skin stops it lifting.')
render('front-fit.png',[(front,plate)]+[(s,col) for _,s,col in h.gmsl()],'Front plate / one window per connector group',hardware_meshes(),view='front',note='3 mm plate, 0.37 mm ahead of the most protruding front part. 45-degree lead-ins; debossed legends.')
render('rear-fit.png',[(rear,plate)],'Rear plate / windows sized to plug overmolds',hardware_meshes(),view='rear',note='USB-A/C and HDMI overmolds enter the window by up to 4.5 mm, so those windows follow typical overmolds, not the receptacle.')
section=base.intersect(b.box(-1,31.5,-1,b.W+20,b.D+20,74))
keep=[(s,col) for name,s,col in h.enclosure_hardware() if 'board' in name]
render('board-mount.png',[(section,shell)]+keep,'Board attachment / printed supports and M3 inserts',hardware_meshes(),view='front',note='16 mm broad support; 7 mm landing clears nearby SMT parts. No loose board spacers.')
for name in json.loads((ROOT/'references/hardware/indices.json').read_text()):
 render('connector-'+name+'.png',[],'Carrier geometry / '+name.replace('_',' '),[(ROOT/'references/hardware'/(name+'.stl'),(.4,.55,.58),(0,0,0))],note='See inventory: some source bodies are simplified. Assembly preview includes separate open shells.',size=(1000,700))
render('lid-detail.png',[(cover,lid)],'Lid / honeycomb grille over the cooler fan',view='rear',note='10 mm across-flats cells keep a 12 mm test finger out of the fan. Screw counterbores sit in a solid border.',size=(1500,1050))
xc,yc=min(b.hex_centers(),key=lambda q:(q[0]-103)**2+(q[1]-96)**2);pitch=b.e['hex_across_flats']+b.e['hex_web']
chunk=cover.intersect(b.box(xc,yc-1.6*pitch,b.H-b.RT-1,2.5,3.2*pitch,b.RT+2))
render('hex-inlet.png',[(chunk,(.80,.82,.84))],f'Lid detail / fan-side inlet chamfer, 2.5 mm slice at X{xc:.1f} through a column of cells (fan side down)',view=(-500,-110,-70),note=f"Fan below, outside above. Each cell opens to {b.e['hex_across_flats']+2*b.e['hex_inlet_flare']:g} mm A/F at the fan side and tapers over {b.e['hex_inlet_depth']:g} mm to the {b.e['hex_across_flats']:g} mm finger-safe opening; {b.e['hex_web']-2*b.e['hex_inlet_flare']:.1f} mm web land.",size=(1500,1050))
# Service buttons: rear plate slice, PCB edge and the two right-angle switches (source solids).
import cadquery as cq
src=cq.Shape.importBrep(str(ROOT/'references/carrier.brep')).Solids();o=b.p['origin_in_source_step'];sh=(b.M-o[0],b.M-o[1],b.Z-o[2])
sb=b.e['service_buttons'];bx=[b.M+x for x,_ in sb['actuators_pcb_xz']];bz=b.Z+sb['actuators_pcb_xz'][0][1]
crop=b.box(bx[0]-14,b.Y1-30,b.F,bx[1]-bx[0]+28,40,bz+14-b.F)  # around the REC / RST actuators
sw=[(s.translate(sh),(.15,.15,.17)) for s in cq.Shape.importBrep(str(ROOT/'references/carrier.brep')).Shells() if (lambda q:q.xmin>o[0]+130 and q.xmax<o[0]+165 and q.ymin>o[1]+148 and q.ymax<o[1]+163)(s.BoundingBox())]
render('service-buttons.png',[(rear.intersect(crop),plate),(src[5169].translate(sh).intersect(crop),(.07,.32,.16))]+sw,'REC / RST pin access (rear plate, seen from inside)',view=(-160,-260,140),note=f"Two D{sb['pin_hole']:g} pin holes with 45-degree lead-ins; guide sleeves stop {sb['sleeve_gap_to_pcb_edge']:g} mm short of the PCB edge so the plate still slides straight down.",size=(1500,1050))
ant=[(s,col) for name,s,col in h.enclosure_hardware() if 'RP-SMA' in name]
render('antennas.png',[(base,shell),(front,plate),(rear,plate),(hatch,plate),(cover.translate((0,0,60)),lid)]+ant+electronics,'RP-SMA bulkheads in the fixed base walls (lid lifted)',hardware_meshes(),view=(-420,-330,260),note='WIFI 1/2 on the left wall, CELL 1/2 on the right, at Z62. The lid, plates and J17 door lift off with antennas fitted. 2.5 mm spot-faced wall.')
# Storage: exploded stack with drives, standoffs and screws; assembled stack; underside slot envelopes.
skinds=['storage_35','storage_25'];sm=b.stack(skinds);gap=45
sx=[(base,shell),(front,plate),(rear,plate),(hatch,plate),(cover,lid)]+electronics
shw=h.storage_hardware(skinds,True)
def zshift(name):
    for i,(n,_,_) in enumerate(sm):
        if n in name:return -gap*(i+1)
    return 0
sx+=[(s.translate((0,0,-gap*(i+1))),(.36,.39,.43)) for i,(n,s,_) in enumerate(sm)]
sx+=[(s.translate((0,0,zshift(n))),col) for n,s,col in shw]
zb=sm[-1][2]-gap*len(sm);sx.append((b.storage_mount_plate().translate((0,0,zb-b.e['mount_ear_thickness']-gap)),shell))
render('storage-exploded.png',sx,'Storage expansion / stackable 3.5 in and 2.5 in trays under the base',hardware_meshes(),view=(380,-470,180),note='Hex standoffs hang from the part above; the next set screws up through each tray ledge. Build upside down on the lid. Cables drop straight down from the underside SATA connectors.',size=(1600,1300))
sa=[(base,shell),(front,plate),(rear,plate),(hatch,plate),(cover,lid)]+[(s,(.36,.39,.43)) for _,s,_ in sm]+[(b.storage_mount_plate().translate((0,0,sm[-1][2]-b.e['mount_ear_thickness'])),shell)]
render('storage-stack.png',sa,'Assembled / base + 3.5 in tray + 2.5 in tray + mount plate',view=(420,-440,260),note=f"Overall {b.H+sum(b.S['modules'][k]['height'] for k in skinds)+b.e['mount_ear_thickness']:g} mm tall with the plate. Same footprint, reveal lines and vent rhythm as the enclosure.",size=(1500,1100))
env=[(s,(.95,.55,.15,.45) if 'card' in n else (.15,.55,.95,.45)) for n,s in b.envelope_boxes()]
sl=[(base.intersect(b.box(-1,b.Y0-1,b.F+.5,b.W+2,b.D+2,b.Z)),shell)]+env
render('underside-slots.png',sl,'Under the carrier: stacked Mini PCIe + M.2 B cards, M.2 E card, SATA plug drops',hardware_meshes(),view=(260,-380,-330),note='Orange: card envelopes incl. U.FL plugs (6-7 mm above the floor for the stacked pair). Blue: SATA and SATA-power plug drops through the floor. Floor hidden.',size=(1600,1150))
# Storage options on the website: stack configurations, drive-mounting options, clip detail, cable path.
TRAY=(.36,.39,.43);CLIP=(.86,.47,.18)
def stack_items(kinds,dx,plate_under=False,ssd7=False):
    out=[(s.translate((dx,0,0)),c) for s,c in [(base,shell),(front,plate),(rear,plate),(hatch,plate),(cover,lid)]]
    mods=b.stack(kinds);out+=[(s.translate((dx,0,0)),TRAY) for _,s,_ in mods]
    if plate_under:out.append((b.storage_mount_plate().translate((dx,0,mods[-1][2]-b.e['mount_ear_thickness'])),shell))
    return out
cfg=[(['storage_35'],'1 total'),(['storage_35','storage_25'],'1 of each'),(['storage_35','storage_35','storage_25','storage_25'],'2 of each')]
items=[];labs=[]
for i,(k,lab) in enumerate(cfg):
    items+=stack_items(k,i*270,plate_under=(i==2))
render('storage-configs.png',items,'Storage options / 1 total, 1 of each, 2 of each (3.5 in trays over 2.5 in trays)',view=(420,-700,260),note='Left: one 3.5 in tray (144 mm). Middle: one 3.5 in + one 2.5 in (166 mm). Right: two of each on the wall/robot plate (228 mm). Any order works.',size=(1800,1000))
bays=[];x=0
for kind,ssd7,dx in (('storage_35',False,0),('storage_25',False,230),('storage_25',True,460)):
    tray=b.storage_module(kind).translate((dx,0,0));bays.append((tray,TRAY))
    for n,s,col in h.storage_hardware([kind],False,ssd7):
        if n.startswith(('D ','P19','H13','H16','H17')):
            z0=b.stack([kind])[0][2];bays.append((s.translate((dx,0,-z0)),col if not n.startswith('P19') else CLIP))
render('drive-bays.png',bays,'Drive mounting / 3.5 in HDD, two 2.5 in drives (bottom screws), two 7 mm SSDs on P19 side clips',view=(330,-430,520),note='3.5 in: 6-32 bottom screws (SFF-8301, all three hole pairs). 2.5 in up to 15 mm: M3 bottom screws (SFF-8201). 7 mm SSDs without bottom holes: four orange P19 clips each.',size=(1800,1050))
d25=b.S['modules']['storage_25']['bays'][0];det=[]
crop=b.box(b.conn_x('d25')-2,d25['y']-14,-1,32,40,30)
for n,s,col in h.storage_hardware(['storage_25'],False,True):
    z0=b.stack(['storage_25'])[0][2];s2=s.translate((0,0,-z0))
    if s2.BoundingBox().xmin<crop.BoundingBox().xmax and s2.BoundingBox().ymax>crop.BoundingBox().ymin and s2.BoundingBox().ymin<crop.BoundingBox().ymax:
        det.append((s2.intersect(crop) if n.startswith('D ') else s2,CLIP if n.startswith('P19') else col))
det.append((b.storage_module('storage_25').intersect(crop),TRAY))
render('ssd-clip-detail.png',det,'P19 clip detail / 7 mm SSD held by its side holes',view=(-160,-260,180),note='Side screw M3 x 5 (2.0 mm into the drive, SFF-8201 max for 7 mm). Floor screw M3 x 6 from under the tray into a captive nut; the slot absorbs drive-width tolerance.',size=(1500,1050))
# Cable routing: 1 of each (3.5 in tray over 2.5 in tray); port 1 -> 3.5 in HDD, port 2 -> first 2.5 in drive.
ck=['storage_35','storage_25'];links=[(0,0,0),(1,1,0)];GHOST=(.40,.44,.50,.22)
cr=[(base,GHOST),(rear,GHOST)]+[(s,GHOST) for _,s,_ in b.stack(ck)]
for n,s,col in h.storage_hardware(ck,False):
    if n.startswith('D '):cr.append((s,(.55,.58,.62)))
cr+=[(s,col) for _,s,col in h.storage_cables(ck,links)]
render('cable-routing.png',cr,'Cable routing / board underside connectors -> floor opening -> chimney -> tray gutter -> drives',hardware_meshes(),view=(-380,-420,140),note='Red: SATA data (front connector -> 3.5 in HDD, rear -> 2.5 in drive). Yellow: board 5 V PH power to the 2.5 in drive. Orange: 12 V from the tray 12V IN hole to the 3.5 in HDD. Plastic shown translucent.',size=(1700,1200))
cr2=[(s.intersect(b.box(-1,b.Y0-1,-200,60,b.D+2,260)),GHOST) for s,_ in [(base,0)]+[(s,0) for _,s,_ in b.stack(ck)]]
cr2+=[(s,col) for _,s,col in h.storage_cables(ck,links)]+[(s,(.55,.58,.62)) for n,s,_ in h.storage_hardware(ck,False) if n.startswith('D ')]
render('cable-routing-side.png',cr2,'Cable routing / left side, plastic cut at X60',hardware_meshes(),view=(-600,-60,40),note='Leads plug straight up into the vertical underside connectors, drop through the base floor and each tray floor, then turn into the tray gutter to the drive connector end.',size=(1700,1100))
# P1 underside: the storage-stacking interface, labelled.
bs=[(base,shell)]+[(s,col) for n,s,col in h.storage_hardware(['storage_35'],False) if n.startswith(('H11','H12'))]
cx=[(x,y) for x,y in b.S['standoff_centers']];ob=[s.BoundingBox() for _,s in b.envelope_boxes('plug_drop')]
oc=((min(q.xmin for q in ob)+max(q.xmax for q in ob))/2,(min(q.ymin for q in ob)+max(q.ymax for q in ob))/2,0)
labels=[('1','M3 stacking insert + hex counterbore (x4)',(cx[0][0],cx[0][1],0),(70,170)),('2','M3 x 30 / x 20 hex standoff hangs here',(cx[2][0],cx[2][1],-20),(1060,190)),
        ('3','SATA drop opening (P18 cap when no storage)',oc,(80,880)),('4','Cooler tie-down screw pockets (M3 x 35)',(b.heatsink_holes()[0][0],b.heatsink_holes()[0][1],0),(780,960))]
render('base-stacking.png',bs,'P1 underside / the storage-stacking interface',view='bottom',labels=labels,note='P1 is the base for desktop use and for storage stacks. Standoffs screw into the four column-foot inserts; trays hang on them. P1M (tabs) is for wall/robot use without storage.',size=(1500,1100))
colc=b.box(-1,b.Y0-1,-1,48,60,b.BH+6)
render('lid-column-detail.png',[(base.intersect(colc),shell)],'Lid-screw column / fused to the side wall',view=(330,-260,200),note='Lid column: full-height buttress, 4 mm wall fillets, 3 mm floor fillet. Board post (front): 3 mm floor fillet and 2 mm fillet under the pad landing.',size=(1400,1050))
hx,hy=b.heatsink_holes()[1];sup=base.intersect(b.box(hx-14,hy-14,-1,28,14,b.Z+2))
bx_,by_=b.board_holes()[1];sup2=base.intersect(b.box(bx_-14,by_-14,-1,28,14,b.Z+2))
render('support-detail.png',[(sup,shell),(sup2.translate((-60,0,0)),shell)],'Supports / radius fillets at the floor and under each pad landing (half cut)',view=(0,-600,40),note='Left: board post (D16, D6.9 landing). Right: cooler tie-down column (D14, D7.14 landing, M3 x 35 seat). 3 mm floor fillet, 2 mm landing fillet.',size=(1400,1000))
access=[(mounted,shell),(cover,lid)]
for x,y in b.mount_slot_centers():
 t=b.e['mount_ear_thickness']
 access += [(h.washer(6.6,16,1.6).translate((x,y,t)),h.COL['steel']),(h.screw(6,25).translate((x,y,t+1.6)),h.COL['steel']),
            (b.cyl(x,y,t+8,10,100),(.95,.58,.15,.18))]
render('mount-clearance.png',access,'Mounting tabs / M6 screw, washer and driver access',note='Orange: 20 mm driver envelope; nothing overhangs the tabs. Screw length shown is illustrative.',size=(1600,1100))
print('All previews rendered',flush=True)
