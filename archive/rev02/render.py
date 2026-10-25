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
    verts,tri=s.tessellate(.18,.3);pts=vtk.vtkPoints()
    for v in verts:pts.InsertNextPoint(v.x,v.y,v.z)
    cells=vtk.vtkCellArray()
    for t in tri:
        cells.InsertNextCell(3)
        for i in t:cells.InsertCellPoint(i)
    pd=vtk.vtkPolyData();pd.SetPoints(pts);pd.SetPolys(cells)
    return actor_poly(pd,col)
def actor_poly(pd,col):
    norm=vtk.vtkPolyDataNormals();norm.SetInputData(pd);norm.SetFeatureAngle(35)
    mapper=vtk.vtkPolyDataMapper();mapper.SetInputConnection(norm.GetOutputPort())
    a=vtk.vtkActor();a.SetMapper(mapper);a.GetProperty().SetColor(*col);a.GetProperty().SetSpecular(.2);a.GetProperty().SetSpecularPower(25)
    return a
def actor_stl(path,col,shift):
    path=str(path)
    if path not in cache:
        r=vtk.vtkSTLReader();r.SetFileName(path);r.Update();cache[path]=r.GetOutput()
    a=actor_poly(cache[path],col);a.SetPosition(*shift);return a

def hardware_meshes(dz=0):
    ref=ROOT/'references/hardware';shift=(b.M,b.M,b.Z+dz)
    items=[(ref/'carrier-full.stl',(.18,.22,.20),shift),(ROOT/'references/pcb-outline.stl',(.07,.32,.16),shift)]
    for n in json.loads((ref/'indices.json').read_text()):
        col=(.15,.50,.24) if 'power' in n or 'terminal' in n else (.65,.69,.72)
        if 'socket' in n or 'header' in n:col=(.14,.15,.17)
        items.append((ref/(n+'.stl'),col,shift))
    return items

def render(name,items,caption,meshes=(),view='iso',labels=(),note='',size=(1600,1100)):
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
    d.text((30,56),'REV 0.2 | FIT-CHECK PROTOTYPE | Manufacturer geometry and assumptions are identified in the register',font=ImageFont.truetype(FONT,16),fill='#b8d1dc')
    for code,label,point,xy in labels:
        ren.SetWorldPoint(*point,1);ren.WorldToDisplay();q=ren.GetDisplayPoint();qx,qy=q[0],size[1]-q[1]
        tx,ty=xy
        text=f'{code}  {label}';font=ImageFont.truetype(FONT,20);bb=d.textbbox((tx,ty),text,font=font)
        d.line((qx,qy,tx,ty+12),fill='#b75a18',width=3);d.ellipse((qx-6,qy-6,qx+6,qy+6),fill='#cf722e')
        d.rounded_rectangle((bb[0]-9,bb[1]-7,bb[2]+9,bb[3]+7),6,fill='#ffffff',outline='#b75a18',width=2);d.text((tx,ty),text,font=font,fill='#16303f')
    if note:
        d.rectangle((0,size[1]-54,size[0],size[1]),fill='white');d.text((30,size[1]-40),note,font=ImageFont.truetype(FONT,17),fill='#516571')
    im.save(out/name);win.Finalize();print(name,flush=True)

base=b.base();cover=b.cover();front=b.panel(gmsl=True);rear=b.panel(front=False)
blue=(.20,.31,.40);dark=(.16,.23,.29);teal=(.13,.57,.61);orange=(.85,.48,.20)
mounts=[]
for y in b.e['mount_ear_y']:
    mounts += [(b.ear().translate((0,y,0)),orange),(b.ear().mirror('YZ').translate((b.W,y,0)),orange)]
plastic=[(base,dark),(front,teal),(rear,teal),(b.side_hatch(),teal)]+mounts
hw=[(s,col) for _,s,col in h.enclosure_hardware()]
electronics=[(s,col) for _,s,col in h.cooler_and_module()+h.gmsl()]
render('assembled.png',plastic+hw+electronics+[(cover,blue)],'Chunky J501 / GMSL assembly — connectors and fasteners installed',hardware_meshes())
render('rear.png',plastic+hw+electronics+[(cover,blue)],'Rear I/O / original carrier connector geometry retained',hardware_meshes(),view='rear')
render('no-gmsl.png',[(base,dark),(b.panel(),teal),(rear,teal),(b.side_hatch(),teal)]+mounts+hw+[(s,col) for _,s,col in h.cooler_and_module()]+[(cover,blue)],'Without GMSL / interchangeable 6 mm front panel',hardware_meshes())
render('open.png',plastic+hw+electronics,'Open assembly / power, Ethernet, I/O and two mini-FAKRA housings shown',hardware_meshes(),note='Carrier + AGX module: source STEP. Mini-FAKRA: candidate vendor STEP. Cooler and GMSL board placement: provisional.')
render('top.png',plastic+hw+electronics,'Top inspection / separate 150 × 130 and 92 × 79 mounting patterns',hardware_meshes(),view='top')
# Explode each subsystem without discarding any modeled electronics.
expl=[(b.side_hatch().translate((60,0,0)),teal),(base,dark),(front.translate((0,-85,0)),teal),(rear.translate((0,65,0)),teal),(cover.translate((0,0,155)),blue)]
for s,col in mounts:expl.append((s.translate((0,0,-40)),col))
for name,s,col in h.enclosure_hardware():
    if 'cover insert' in name:off=(-25,0,0) if 'left' in name else (25,0,0)
    elif 'cover screw' in name or 'cover washer' in name:off=(-55,0,0) if 'left' in name else (55,0,0)
    elif 'mount insert' in name:off=(0,0,-20)
    elif 'mount screw' in name or 'mount washer' in name:off=(0,0,18)
    elif 'board insert' in name:off=(0,0,30)
    elif 'board screw' in name:off=(0,0,95)
    else:off=(0,0,-20)
    expl.append((s.translate(off),col))
for name,s,col in h.cooler_and_module():expl.append((s.translate((0,0,105)),col))
for name,s,col in h.gmsl():expl.append((s.translate((0,-25,75)),col))
labels=[('P2','6 mm vented cover',(110,95,267),(25,130)),
 ('E3 / H7','Cooler + original board fasteners',(105,105,190),(1120,200)),
 ('E1','Carrier, including its connectors',(185,170,80),(1100,410)),
 ('E4','GMSL board + 2 mini-FAKRA',(65,0,113),(25,420)),
 ('H1–H3','M6 inserts / washers / screws',(-25,10,52),(25,650)),
 ('H4–H5','M3 inserts in printed supports',(30,31.5,40),(1050,670)),
 ('P3','GMSL front panel',(95,-84,35),(25,860)),
 ('P1','8 mm floor / 6 mm walls',(170,80,8),(1080,900)),
 ('P6','14 mm mounting ears',(214,134,-47),(1060,1060)),
 ('P5','6 mm rear I/O panel',(120,255,40),(1050,540)),('P10','J17 service hatch',(272,95,35),(1250,800))]
render('exploded.png',expl,'Labeled exploded assembly / every fastener family and connector retained',hardware_meshes(60),labels=labels,size=(1800,1250),note='H7 cooler retention and E4 GMSL geometry are schematic; do not select replacement hardware from the rendering.')
# Individual component previews; exact printed solids, same IDs as BOM/register.
parts=[('P1','base',base,'1 × shared base; 8 mm floor, 6 mm walls'),('P2','cover',cover,'1 × cover; print roof down'),
 ('P3','front_gmsl',front,'1 × front panel for GMSL'),('P4','front_no_gmsl',b.panel(),'Alternative front panel without GMSL'),
 ('P5','rear_io',rear,'1 × rear I/O panel'),('P6','mount_ear',b.ear(),'4 × M6 mounting ears; mirror 2 in assembly'),
 ('P7','desktop_foot',b.foot(),'4 × desktop feet, alternative to ears'),('P8','insert_coupon',b.coupon(),'5 pilot diameters: 7.3 / 7.4 / 7.5 / 7.6 / 7.7 mm'),
 ('P9','mount_fit_template',b.fit_template(),'Fit template: 150 × 130 mm center spacing'),('P10','side_hatch',b.side_hatch(),'J17 jumper access; two M6 screws'),('P11','m3_insert_coupon',b.m3_coupon(),'M3 pilots left to right: 3.7 / 3.8 / 3.9 / 4.0 / 4.1 mm')]
for code,name,s,note in parts:render('part-'+name+'.png',[(s,orange if code in ['P6','P7'] else teal)],code+' / '+name.replace('_',' '),note=note,size=(1100,800))
for code,name,s,note in [('H1','M6_insert',h.insert(),'User M6 × 10: 7.25 mm starter, 8 mm body; thread depiction schematic'),
 ('H2','M6_washer',h.washer(),'12 mm OD × 6.6 mm ID × 1.6 mm; selected purchase assumption'),
 ('H3','M6_screw',h.screw(),'M6 × 20 socket screw; selected nominal dimensions'),
 ('H4','M3_insert',h.board_insert(),'M3 × 10 insert: user tip 3.75 mm / maximum body 4.2 mm'),
 ('H5','M3_board_screw',h.screw(3,10,5.7,1.65,2),'M3 × 10 button screw: nominal insert engagement 8.42 mm'),
 ('H6','jumper_cap',h.jumper(),'Generic 2.54 mm jumper cap; measure actual cap and verify pinout')]:
 render('part-'+name+'.png',[(s,h.COL['brass'] if code in ['H1','H4'] else h.COL['steel'])],code+' / '+name.replace('_',' '),note=note,size=(1100,800))
render('part-carrier.png',[],'E1 / manufacturer carrier board — all original connectors',hardware_meshes(),note='Only display color changes; source STEP retained in references.',size=(1400,1000))
render('part-gmsl.png',[(s,col) for _,s,col in h.gmsl()],'E4–E6 / GMSL, candidate mini-FAKRA STEP and Samtec envelope',note='Seeed board outline; Amphenol exact candidate geometry. Identity, keying and XY position need confirmation.',size=(1400,1000))
render('part-cooler.png',[(s,col) for _,s,col in h.cooler_and_module()],'E2 / E3 / H7 — module, cooler and board-mounted retention',note='110 × 100 × 50 mm reference cooler envelope; actual cooler identity and screw dimensions not confirmed.',size=(1400,1000))
render('side-access.png',[(base,dark),(b.side_hatch().translate((35,100,20)),teal)]+[(s,col) for name,s,col in h.enclosure_hardware() if 'hatch' in name]+[(h.jumper().translate((b.W+15,96,22)),h.COL['dark'])], 'Third I/O side / J17 right-angle header and removable hatch',hardware_meshes(),view='side',note='42 × 22 mm access opening; cap removed here to show header. Jumper shown loose, no electrical configuration implied.')
render('front-fit.png',[(front,teal)]+[(s,col) for _,s,col in h.gmsl()], 'Front panel / stepped connector profiles and positive M6 retention',hardware_meshes(),view='front',note='0.6 mm nominal housing clearance. Narrow intervening webs are merged; mating cables still require a fit check.')
render('rear-fit.png',[(rear,teal)],'Rear panel / terminal, HDMI and USB profiles',hardware_meshes(),view='rear')
# Remove only front half of printed base for an explicit board support section.
section=base.intersect(b.box(-1,31.5,-1,b.W+2,b.D,74))
keep=[(s,col) for name,s,col in h.enclosure_hardware() if 'board' in name]
render('board-mount.png',[(section,dark)]+keep, 'PCB attachment / M3 screws into inserts in integrated printed supports',hardware_meshes(),view='front',note='No separate spacers. 16 mm lower support, 7 mm landing, 10 mm insert. See section drawing and underside clearance report.')
render('part-module.png',[(s,col) for name,s,col in h.cooler_and_module() if name.startswith('E2')],'E2 / NVIDIA AGX Orin module STEP',note='Manufacturer geometry, rotated and located to 92 × 79 mm cooler mount pattern.',size=(1400,1000))
render('part-fakra.png',[(s,col) for name,s,col in h.gmsl() if name.startswith('E5')][:1], 'E5 / Amphenol FM4-NZRP-PCB-1 candidate STEP',note='12 × 22.55 × 15.7 mm body; Seeed footprint matches dimensions, but exact manufacturer is unconfirmed.',size=(1100,800))
print('All previews rendered',flush=True)

for name in json.loads((ROOT/'references/hardware/indices.json').read_text()):
 render('connector-'+name+'.png',[],'Source carrier connector / '+name.replace('_',' '),[(ROOT/'references/hardware'/(name+'.stl'),(.4,.55,.58),(0,0,0))],note='Exact geometry extracted from Seeed carrier STEP; see connector inventory for identity and solid index.',size=(1000,700))
