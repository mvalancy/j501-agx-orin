from pathlib import Path
import sys,json,math
import vtk
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'cad'))
import build as b
import hardware as h
out=ROOT/'preview';out.mkdir(exist_ok=True)
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
cache={}
def actor_shape(s,col):
    verts,tri=s.tessellate(.18,.3);pts=vtk.vtkPoints();pts.SetDataTypeToDouble()
    for v in verts:pts.InsertNextPoint(v.x,v.y,v.z)
    cells=vtk.vtkCellArray()
    for t in tri:
        cells.InsertNextCell(3)
        for i in t:cells.InsertCellPoint(i)
    pd=vtk.vtkPolyData();pd.SetPoints(pts);pd.SetPolys(cells)
    return actor_poly(pd,col)
def actor_poly(pd,col):
    clean=vtk.vtkCleanPolyData();clean.SetInputData(pd);clean.ToleranceIsAbsoluteOn();clean.SetAbsoluteTolerance(1e-6)
    norm=vtk.vtkPolyDataNormals();norm.SetInputConnection(clean.GetOutputPort());norm.SetFeatureAngle(35)
    mapper=vtk.vtkPolyDataMapper();mapper.SetInputConnection(norm.GetOutputPort())
    a=vtk.vtkActor();a.SetMapper(mapper);a.GetProperty().SetColor(*col[:3]);a.GetProperty().SetOpacity(col[3] if len(col)>3 else 1); a.GetProperty().SetSpecular(.2);a.GetProperty().SetSpecularPower(25)
    return a
def actor_stl(path,col,shift):
    path=str(path)
    if path not in cache:
        r=vtk.vtkSTLReader();r.SetFileName(path);r.Update();cache[path]=r.GetOutput()
    a=actor_poly(cache[path],col);a.SetPosition(*shift);return a

def hardware_meshes(dz=0):
    ref=ROOT/'references/hardware';shift=(b.M,b.M,b.Z+dz)
    items=[(ref/'carrier-open-shells.stl',(.65,.69,.72),shift),(ref/'carrier-full.stl',(.18,.22,.20),shift),(ROOT/'references/pcb-outline.stl',(.07,.32,.16),shift)]
    for n in json.loads((ref/'indices.json').read_text()):
        col=(.15,.50,.24) if 'power' in n or 'terminal' in n else (.65,.69,.72)
        if 'socket' in n or 'header' in n:col=(.14,.15,.17)
        items.append((ref/(n+'.stl'),col,shift))
    items += [(ref/'J26-envelope-0.stl',(.72,.47,.30),shift),(ref/'J26-envelope-1.stl',(.1,.3,.55),shift)] if (ref/'J26-envelope-0.stl').exists() else []
    return items

def render(name,items,caption,meshes=(),view='iso',labels=(),note='',size=(1600,1100)):
    import os
    selected=os.environ.get('J501_RENDER_ONLY')
    if selected and name not in selected.split(','):return
    ren=vtk.vtkRenderer();ren.SetBackground(.93,.95,.97)
    for s,col in items:ren.AddActor(actor_shape(s,col))
    for path,col,pos in meshes:ren.AddActor(actor_stl(path,col,pos))
    win=vtk.vtkRenderWindow();win.SetOffScreenRendering(1);win.SetSize(*size);win.AddRenderer(ren);win.SetMultiSamples(4)
    cam=ren.GetActiveCamera()
    if view=='iso':cam.SetPosition(420,-440,360);cam.SetViewUp(0,0,1)
    elif view=='rear':cam.SetPosition(-300,500,350);cam.SetViewUp(0,0,1)
    elif view=='front':cam.SetPosition(103,-600,200);cam.SetViewUp(0,0,1)
    elif view=='side':cam.SetPosition(700,-80,250);cam.SetViewUp(0,0,1)
    elif view=='top':cam.SetPosition(103,96.5,700);cam.SetViewUp(0,1,0)
    cam.SetFocalPoint(103,96.5,60);cam.ParallelProjectionOn();ren.ResetCamera();cam.Zoom(.93 if labels else 1.04)
    win.Render();f=vtk.vtkWindowToImageFilter();f.SetInput(win);f.Update()
    wr=vtk.vtkPNGWriter();wr.SetFileName(str(out/name));wr.SetInputConnection(f.GetOutputPort());wr.Write()
    im=Image.open(out/name).convert('RGB');d=ImageDraw.Draw(im)
    d.rectangle((0,0,size[0],94),fill='#142b38');d.text((30,16),caption,font=ImageFont.truetype(FONT,26),fill='white')
    d.text((30,56),'REV 0.4 | FIT-CHECK PROTOTYPE | Manufacturer geometry and assumptions are identified in the register',font=ImageFont.truetype(FONT,16),fill='#b8d1dc')
    for code,label,point,xy in labels:
        ren.SetWorldPoint(*point,1);ren.WorldToDisplay();q=ren.GetDisplayPoint();qx,qy=q[0],size[1]-q[1]
        tx,ty=xy
        text=f'{code}  {label}';font=ImageFont.truetype(FONT,20);bb=d.textbbox((tx,ty),text,font=font)
        d.line((qx,qy,tx,ty+12),fill='#b75a18',width=3);d.ellipse((qx-6,qy-6,qx+6,qy+6),fill='#cf722e')
        d.rounded_rectangle((bb[0]-9,bb[1]-7,bb[2]+9,bb[3]+7),6,fill='#ffffff',outline='#b75a18',width=2);d.text((tx,ty),text,font=font,fill='#16303f')
    if note:
        d.rectangle((0,size[1]-54,size[0],size[1]),fill='white');d.text((30,size[1]-40),note,font=ImageFont.truetype(FONT,17),fill='#516571')
    im.save(out/name);win.Finalize();print(name,flush=True)


base=b.base();mounted=b.base(True);cover=b.cover();front=b.panel(gmsl=True);rear=b.panel(front=False);hatch=b.side_hatch()
blue=(.20,.31,.40);dark=(.16,.23,.29);teal=(.13,.57,.61);orange=(.85,.48,.20)
hw=[(s,col) for _,s,col in h.enclosure_hardware()]
electronics=[(s,col) for _,s,col in h.cooler_and_module()+h.gmsl()]
plastic=[(mounted,dark),(front,teal),(rear,teal),(hatch,teal)]
render('assembled.png',plastic+hw+electronics+[(cover,blue)],'Rev 0.4 / open ribbed lid, rounded shell and larger mounting tabs',hardware_meshes(),note='Two M6 cover screws; four M3 PCB screws. GMSL placement and actual cooler dimensions remain provisional.')
render('rear.png',plastic+hw+electronics+[(cover,blue)],'Rear I/O / surface shells restored from manufacturer STEP',hardware_meshes(),view='rear')
render('no-gmsl.png',[(base,dark),(b.panel(),teal),(rear,teal),(hatch,teal)]+hw+[(s,col) for _,s,col in h.cooler_and_module()]+[(cover,blue)],'Desktop base / no GMSL / no dummy GMSL or SIM openings',hardware_meshes())
render('open.png',plastic+hw+electronics,'Open assembly / all carrier solids and open shells retained',hardware_meshes(),note='Source carrier and NVIDIA module; candidate mini-FAKRA STEP. GMSL component locations and cooler are provisional.')
render('top.png',plastic+hw+electronics,'Top inspection / separate board and cooler mounting patterns',hardware_meshes(),view='top')
expl=[(mounted,dark),(front.translate((0,-70,30)),teal),(rear.translate((0,65,30)),teal),(hatch.translate((60,20,40)),teal),(cover.translate((0,0,160)),blue)]
for name,s,col in h.enclosure_hardware():
 if 'cover' in name:off=(-30,0,0) if s.Center().x<100 else (30,0,0)
 elif 'insert' in name:off=(0,0,30)
 else:off=(0,0,95)
 expl.append((s.translate(off),col))
for name,s,col in h.cooler_and_module():expl.append((s.translate((0,0,110)),col))
for name,s,col in h.gmsl():expl.append((s.translate((0,-25,75)),col))
labels=[('P2','Vented cover; two M6 screws',(110,95,272),(25,130)),
 ('E3 / H7','Existing cooler and retention',(105,105,195),(1120,200)),
 ('E1','Carrier with complete source shells',(185,170,80),(1100,410)),
 ('E4–E8','GMSL + candidate connector models',(70,0,113),(25,420)),
 ('H1–H3','M6 inserts / washers / screws',(-25,24,60),(25,650)),
 ('H4–H5','M3 inserts in printed supports',(30,31.5,50),(1050,670)),
 ('P3','Sliding GMSL/audio front panel',(95,-60,65),(25,860)),
 ('P1M','Base + integral mounting ears',(180,80,8),(1100,1050)),
 ('P5','Sliding rear I/O panel',(120,255,65),(1050,540)),
 ('P10','Sliding J17 hatch',(270,115,55),(1250,820))]
render('exploded.png',expl,'Labeled assembly / thick sliding interlocks; no panel screws',hardware_meshes(60),labels=labels,size=(1800,1250),note='GMSL factory supports are shown separately from integrated enclosure-to-PCB supports; their thread/height need checking.')
parts=[('P1','base',base,'Desktop base, flat underside; all rails and bosses rise from the floor'),('P1M','base_mount',mounted,'Wall/robot base: integral 16 mm front/rear tabs; no ear screws'),
 ('P2','cover',cover,'67.37% open roof; 2.4 mm-wide x 10 mm-deep ribs; roof face down'),('P3','front_gmsl',front,'Two purposeful windows: audio + GMSL; network + power'),('P4','front_no_gmsl',b.panel(),'Two purposeful windows: audio; network + power'),
 ('P5','rear_io',rear,'Terminal / HDMI + USB-A / underside USB-C pair'),('P8','insert_coupon',b.coupon(),'Horizontal M6 seats: 7.3 / 7.4 / 7.5 / 7.6 / 7.7 mm'),('P9','mount_fit_template',b.fit_template(),'150 x 130 mm carrier mount pattern'),
 ('P10','side_hatch',hatch,'Thick sliding panel and grip; no snap arm or fastener'),('P11','m3_insert_coupon',b.m3_coupon(),'M3 pilots: 3.7 / 3.8 / 3.9 / 4.0 / 4.1 mm'),('P12','rail_coupon',b.rail_coupon(),'Test the same 6.5 mm channel as the panels'),('P13','rail_key',b.rail_key(),'6 mm sliding key; no sanding assumed')]
for code,name,shape,note in parts:render('part-'+name+'.png',[(shape,teal)],code+' / '+name.replace('_',' '),note=note,size=(1100,800))
for code,name,shape,note in [('H1','M6_insert',h.insert(),'User M6 x 10: 7.25 starter, 8 mm body; model thread is schematic'),('H2','M6_washer',h.washer(),'12 OD x 6.6 ID x 1.6 mm selected nominal washer; verify purchased part'),('H3','M6_screw',h.screw(),'M6 x 20 socket cap screw; 5 mm hex'),('H4','M3_insert',h.board_insert(),'User M3 x 10: 3.75 mm starter, 4.2 mm body'),('H5','M3_board_screw',h.screw(3,10,5.7,1.65,2),'M3 x 10 button head: 8.42 mm nominal insert engagement'),('H6','jumper_cap',h.jumper(),'Generic 2.54 mm jumper cap; no electrical configuration implied')]:
 render('part-'+name+'.png',[(shape,h.COL['brass'] if code in ['H1','H4'] else h.COL['steel'])],code+' / '+name.replace('_',' '),note=note,size=(1100,800))
render('part-carrier.png',[],'E1 / carrier STEP with all open surface shells',hardware_meshes(),size=(1400,1000))
render('part-gmsl.png',[(s,col) for _,s,col in h.gmsl()],'E4–E8 / GMSL board, candidate connector STEP and component envelopes',note='Carrier-derived support centers; board/connector XY and top component placement remain provisional.',size=(1400,1000))
render('part-cooler.png',[(s,col) for _,s,col in h.cooler_and_module()],'E2 / E3 / H7 — module, cooler and board-mounted retention',note='Cooler 110 x 100 x 50 mm reference envelope. Keep original cooler hardware; visual screws are not purchase specifications.',size=(1400,1000))
render('part-module.png',[(s,col) for name,s,col in h.cooler_and_module() if name.startswith('E2')],'E2 / NVIDIA AGX Orin module STEP',size=(1400,1000))
render('part-fakra.png',[(s,col) for name,s,col in h.gmsl() if name.startswith('E5')][:1],'E5 / Amphenol FM4-NZRP-PCB-1 candidate STEP',note='Matches Seeed footprint size. Actual manufacturer, keying and cable-side model remain unconfirmed.',size=(1100,800))
render('side-access.png',[(base,dark),(hatch.translate((35,100,30)),teal),(h.jumper().translate((b.W+15,96,22)),h.COL['dark'])],'J17 access / cover removed; hatch slides upward',hardware_meshes(),view='side',note='38 mm-wide opening with 45-degree arch. No horizontal bridge over the header.')
render('front-fit.png',[(front,teal)]+[(s,col) for _,s,col in h.gmsl()],'Front GMSL panel / two deliberate connector groups',hardware_meshes(),view='front',note='Audio + two mini-FAKRA in left window. Ethernet, indicators and power in right window. No SIM slit.')
render('rear-fit.png',[(rear,teal)],'Rear panel / terminal, HDMI + USB-A and USB-C access',hardware_meshes(),view='rear',note='The low opening is for two real underside USB-C connectors; no ventilation slots in this panel.')
section=base.intersect(b.box(-1,31.5,-1,b.W+20,b.D,74))
keep=[(s,col) for name,s,col in h.enclosure_hardware() if 'board' in name]
render('board-mount.png',[(section,dark)]+keep,'Board attachment / printed supports and M3 inserts',hardware_meshes(),view='front',note='16 mm broad support; short 7 mm landing clears nearby SMT parts. No loose board spacers.')
for name in json.loads((ROOT/'references/hardware/indices.json').read_text()):
 render('connector-'+name+'.png',[],'Carrier geometry / '+name.replace('_',' '),[(ROOT/'references/hardware'/(name+'.stl'),(.4,.55,.58),(0,0,0))],note='See inventory: some source bodies are simplified. Assembly preview includes separate open shells.',size=(1000,700))
print('All previews rendered',flush=True)

# Close inspection of the new ribs and the mounting screw access.
render('lid-detail.png',[(cover,blue)],'Open lid / narrow upright ribs joined into a stiff grid',view='rear',note='67.37% projected roof area open; 2.4 mm web width, 10 mm depth. Rigidity is a design intent, not a tested load rating.',size=(1500,1050))
access=[(mounted,dark),(cover,blue)]
for x in b.e['mount_ear_x']:
 for y in (-b.e['mount_hole_offset'],b.D+b.e['mount_hole_offset']):
  access += [(h.washer().translate((x,y,16)),h.COL['steel']),(h.screw(6,30).translate((x,y,17.6)),h.COL['steel']),
             (b.cyl(x,y,24,10,90),(.95,.58,.15,.18)),(b.cyl(x,y,16.01,8,.3),(.15,.65,.7,.4))]
render('mount-clearance.png',access,'Chunky mounting tabs / external M6 screw and tool access',note='Orange: 20 mm driver envelope. Teal: 16 mm washer envelope. Screw length shown is illustrative; select for actual mounting surface.',size=(1600,1100))
