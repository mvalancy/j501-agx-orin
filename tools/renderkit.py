"""Shared VTK render helpers for tools/render.py and tools/render_steps.py."""
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
    a=vtk.vtkActor();a.SetMapper(mapper);a.GetProperty().SetColor(*col[:3]);a.GetProperty().SetOpacity(col[3] if len(col)>3 else 1); a.GetProperty().SetSpecular(.25);a.GetProperty().SetSpecularPower(30);a.GetProperty().SetDiffuse(.85);a.GetProperty().SetAmbient(.12)
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

def render(name,items,caption,meshes=(),view='iso',labels=(),note='',size=(1600,1100),clip=None):
    import os
    selected=os.environ.get('J501_RENDER_ONLY')
    if selected and name not in selected.split(','):return
    ren=vtk.vtkRenderer();ren.SetBackground(.93,.95,.97)
    actors=[actor_shape(s,col) for s,col in items]+[actor_stl(path,col,pos) for path,col,pos in meshes]
    for a in actors:
        if clip is not None:
            pl=vtk.vtkPlane();pl.SetOrigin(*clip[0]);pl.SetNormal(*clip[1]);a.GetMapper().AddClippingPlane(pl)
        ren.AddActor(a)
    ren.SetTwoSidedLighting(True)
    key=vtk.vtkLight();key.SetLightTypeToSceneLight();key.SetPosition(600,-900,1200);key.SetFocalPoint(103,96,40);key.SetIntensity(.55);ren.AddLight(key)
    fill=vtk.vtkLight();fill.SetLightTypeToHeadlight();fill.SetIntensity(.6);ren.AddLight(fill)
    win=vtk.vtkRenderWindow();win.SetOffScreenRendering(1);win.SetSize(*size);win.AddRenderer(ren);win.SetMultiSamples(4)
    cam=ren.GetActiveCamera()
    if view=='iso':cam.SetPosition(420,-440,360);cam.SetViewUp(0,0,1)
    elif view=='rear':cam.SetPosition(-300,500,350);cam.SetViewUp(0,0,1)
    elif view=='front':cam.SetPosition(103,-600,200);cam.SetViewUp(0,0,1)
    elif view=='side':cam.SetPosition(700,-80,250);cam.SetViewUp(0,0,1)
    elif view=='top':cam.SetPosition(103,96.5,700);cam.SetViewUp(0,1,0)
    elif view=='bottom':cam.SetPosition(380,-420,-380);cam.SetViewUp(0,0,1)
    elif view=='section':cam.SetPosition(103,-600,60);cam.SetViewUp(0,0,1)
    elif isinstance(view,tuple):cam.SetPosition(103+view[0],96+view[1],60+view[2]);cam.SetViewUp(0,0,1)
    cam.SetFocalPoint(103,96,60);cam.ParallelProjectionOn();ren.ResetCamera();cam.Zoom(.93 if labels else 1.04)
    win.Render();f=vtk.vtkWindowToImageFilter();f.SetInput(win);f.Update()
    wr=vtk.vtkPNGWriter();wr.SetFileName(str(out/name));wr.SetInputConnection(f.GetOutputPort());wr.Write()
    im=Image.open(out/name).convert('RGB');d=ImageDraw.Draw(im)
    d.rectangle((0,0,size[0],94),fill='#142b38');d.text((30,16),caption,font=ImageFont.truetype(FONT,26),fill='white')
    d.text((30,56),'REV '+b.P['revision'].split('-')[0]+' | FIT-CHECK PROTOTYPE | Manufacturer geometry and assumptions are identified in the register',font=ImageFont.truetype(FONT,16),fill='#b8d1dc')
    for code,label,point,xy in labels:
        ren.SetWorldPoint(*point,1);ren.WorldToDisplay();q=ren.GetDisplayPoint();qx,qy=q[0],size[1]-q[1]
        tx,ty=xy
        text=f'{code}  {label}';font=ImageFont.truetype(FONT,20);bb=d.textbbox((tx,ty),text,font=font)
        d.line((qx,qy,tx,ty+12),fill='#b75a18',width=3);d.ellipse((qx-6,qy-6,qx+6,qy+6),fill='#cf722e')
        d.rounded_rectangle((bb[0]-9,bb[1]-7,bb[2]+9,bb[3]+7),6,fill='#ffffff',outline='#b75a18',width=2);d.text((tx,ty),text,font=font,fill='#16303f')
    if note:
        d.rectangle((0,size[1]-54,size[0],size[1]),fill='white');d.text((30,size[1]-40),note,font=ImageFont.truetype(FONT,17),fill='#516571')
    im.save(out/name);win.Finalize();print(name,flush=True)
