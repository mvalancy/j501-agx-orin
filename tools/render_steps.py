"""Simple assembly-step renders for ASSEMBLY.md: what is already built in light grey, what this step adds in orange.

Added parts float above (or below) where they go, with a dashed guide to their final position and a short label.

    python tools/render_steps.py               # writes docs/assembly/*.png
    J501_RENDER_ONLY=03-inserts.png python tools/render_steps.py
"""
from pathlib import Path
import sys, os
sys.path.insert(0, str(Path(__file__).resolve().parent))
from renderkit import *

OUT = ROOT / 'docs/assembly'; OUT.mkdir(parents=True, exist_ok=True)
HL = (.96, .45, .10)
GREY = (.80, .81, .83)
PLATE = (.86, .87, .88)
DARK = (.42, .44, .47)
VIEWS = {'iso': (420, -440, 420), 'iso_low': (420, -440, 260), 'bottom': (380, -420, -380), 'left': (-420, -440, 380),
         'front_high': (60, -520, 520)}


def centre(s):
    bb = s.BoundingBox()
    return ((bb.xmin + bb.xmax) / 2, (bb.ymin + bb.ymax) / 2, (bb.zmin + bb.zmax) / 2)


def at(s, off=(0, 0, 0)):
    return tuple(c + o for c, o in zip(centre(s), off))


def near(shapes, view='iso', far=True):
    # The item farthest from the camera usually floats clear of the model, so its label is easiest to read. Parts
    # sandwiched between two others are only visible on the side nearest the camera (far=False).
    v = VIEWS[view]; key = lambda s: sum(c * w for c, w in zip(centre(s), v))
    return min(shapes, key=key) if far else max(shapes, key=key)


def step(name, title, context=(), new=(), meshes=(), guides=(), callouts=(), view='iso', note='', size=(1400, 950)):
    """context: [(shape, colour)]; new: [(shape, offset)] drawn in orange at shape+offset with a guide back to shape;
    meshes: [(stl, colour, shift)]; guides: extra [(from_xyz, to_xyz)]; callouts: [(text, xyz)]."""
    sel = os.environ.get('J501_RENDER_ONLY')
    if sel and name not in sel.split(','):
        return
    ren = vtk.vtkRenderer(); ren.SetBackground(.98, .98, .99); ren.SetTwoSidedLighting(True)
    for s, col in context:
        ren.AddActor(actor_shape(s, col))
    for s, off in new:
        ren.AddActor(actor_shape(s.translate(off), HL))
    for path, col, shift in meshes:
        ren.AddActor(actor_stl(path, col, shift))
    key = vtk.vtkLight(); key.SetLightTypeToSceneLight(); key.SetPosition(600, -900, 1200); key.SetFocalPoint(103, 96, 40); key.SetIntensity(.5); ren.AddLight(key)
    fill = vtk.vtkLight(); fill.SetLightTypeToHeadlight(); fill.SetIntensity(.65); ren.AddLight(fill)
    win = vtk.vtkRenderWindow(); win.SetOffScreenRendering(1); win.SetSize(*size); win.AddRenderer(ren); win.SetMultiSamples(4)
    cam = ren.GetActiveCamera(); v = VIEWS[view]
    cam.SetPosition(103 + v[0], 96 + v[1], 40 + v[2]); cam.SetViewUp(0, 0, 1); cam.SetFocalPoint(103, 96, 40)
    cam.ParallelProjectionOn(); ren.ResetCamera(); cam.Zoom(.80)
    win.Render(); f = vtk.vtkWindowToImageFilter(); f.SetInput(win); f.Update()
    tmp = OUT / name; wr = vtk.vtkPNGWriter(); wr.SetFileName(str(tmp)); wr.SetInputConnection(f.GetOutputPort()); wr.Write()

    def px(p):
        ren.SetWorldPoint(*p, 1); ren.WorldToDisplay(); q = ren.GetDisplayPoint(); return q[0], size[1] - q[1]

    im = Image.open(tmp).convert('RGB'); d = ImageDraw.Draw(im)
    lines = [(centre(s), tuple(c + o for c, o in zip(centre(s), off))) for s, off in new if any(off)] + list(guides)
    for a, b_ in lines:
        (x0, y0), (x1, y1) = px(a), px(b_); n = max(1, int(((x1 - x0) ** 2 + (y1 - y0) ** 2) ** .5 / 9))
        for i in range(0, n, 2):
            d.line((x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n, x0 + (x1 - x0) * (i + 1) / n, y0 + (y1 - y0) * (i + 1) / n), fill='#d2560a', width=3)
    font = ImageFont.truetype(FONT, 24); bold = ImageFont.truetype(FONT.replace('Sans.ttf', 'Sans-Bold.ttf'), 30)
    sides = {'L': [], 'R': []}
    for text, p in callouts:
        q = px(p); sides['L' if q[0] < size[0] / 2 else 'R'].append((q[1], q, text))
    for side, items in sides.items():
        y_prev = 110
        for ty, q, text in sorted(items):
            w = d.textbbox((0, 0), text, font=font)[2]
            ty = max(ty - 16, y_prev); y_prev = ty + 56
            tx = 30 if side == 'L' else size[0] - 30 - w
            ax = tx + w + 10 if side == 'L' else tx - 10
            d.line((ax, ty + 15, q[0], q[1]), fill='#d2560a', width=3); d.ellipse((q[0] - 6, q[1] - 6, q[0] + 6, q[1] + 6), fill='#d2560a')
            d.rounded_rectangle((tx - 10, ty - 6, tx + w + 10, ty + 36), 6, fill='white', outline='#d2560a', width=2)
            d.text((tx, ty), text, font=font, fill='#1d2a33')
    d.text((30, 26), title, font=bold, fill='#1d2a33')
    if note:
        d.text((30, size[1] - 46), note, font=ImageFont.truetype(FONT, 21), fill='#55626b')
    im.save(tmp); win.Finalize(); print(name, flush=True)


# ------------------------------------------------------------------------------------------------ parts and hardware
base = b.base(); cover = b.cover(); front = b.panel(); rear = b.panel(front=False); hatch = b.side_hatch()
hw = h.enclosure_hardware()
pick = lambda prefix: [s for n, s, _ in hw if n.startswith(prefix)]
lid_inserts, board_inserts, board_screws, lid_screws = pick('H1 '), pick('H4 '), pick('H5 '), pick('H3 ')
antennas = pick('H10 ')
cooler = [(s, DARK) for n, s, _ in h.cooler_and_module() if not n.startswith('H7')]
tiedown = [s for n, s, _ in h.heatsink_tiedown()]
board = lambda dz=0: [(ROOT / 'references/hardware/carrier-full.stl', (.55, .57, .60), (b.M, b.M, b.Z + dz)),
                      (ROOT / 'references/pcb-outline.stl', (.22, .46, .30), (b.M, b.M, b.Z + dz))]
up = lambda z: (0, 0, z)
built = [(base, GREY)] + [(s, GREY) for s in lid_inserts + board_inserts]

def place(s, x, y):
    bb = s.BoundingBox(); return s.translate((x - bb.xmin, y - bb.ymin, -bb.zmin))
tpl = b.fit_template(); tb = tpl.BoundingBox()
coupons, x = [], tb.xmin
for n, s in [('P11 insert coupon', b.m3_coupon()), ('P12 rail coupon', b.rail_coupon()), ('P13 rail key', b.rail_key()), ('P14 countersink coupon', b.countersink_coupon())]:
    s = place(s, x, tb.ymin - 75); bb = s.BoundingBox(); coupons.append((n, s)); x = bb.xmax + 18
step('01-test-prints.png', '1 · Print the test parts first',
     new=[(tpl, (0, 0, 0))] + [(s, (0, 0, 0)) for _, s in coupons],
     callouts=[('P9 fit template', (tb.xmax - 10, tb.ymax - 10, tb.zmax))] + [(n, centre(s)) for n, s in coupons],
     note='Print in the filament you will use. Pick the pilot hole that holds an insert; check the M3 × 35 head seats on P14.')

step('02-fit-template.png', '2 · Test-fit the bare board on P9',
     context=[(tpl, GREY)], meshes=board(35),
     guides=[((x, y, b.Z + 35), (x, y, b.Z)) for x, y in b.board_holes()],
     callouts=[('Every pad touches the board', (b.board_holes()[0][0], b.board_holes()[0][1], b.Z))],
     note='Check the four cooler holes line up with your cooler before printing the base.')

step('03-inserts.png', '3 · Heat-set 8 × M3 inserts',
     context=[(base, GREY)], new=[(s, up(30)) for s in board_inserts + lid_inserts],
     callouts=[('4 × board supports', at(near(board_inserts), up(30))), ('4 × lid columns', at(near(lid_inserts), up(30)))],
     note='Do this before any electronics go in. Press each insert in straight with a soldering iron.')

step('04-board.png', '4 · Fit the board: 4 × M3 × 10 button head',
     context=built, meshes=board(0), new=[(s, up(45)) for s in board_screws],
     callouts=[('4 × M3 × 10 button head', at(near(board_screws), up(45)))],
     note='With drive trays, plug the SATA leads into the board underside first and feed them down through the floor.')

cap = b.chimney_cap()
step('04b-floor-cap.png', '4b · No drive trays: plug the floor opening',
     context=[(base, GREY)], new=[(cap, up(-35))], view='bottom',
     callouts=[('P18 floor cap, pressed in from below', at(cap, up(-35)))])

step('05-cooler.png', '5 · Fit the module and cooler',
     context=built + [(s, GREY) for s in board_screws], meshes=board(0),
     new=[(s, up(60)) for s, _ in cooler],
     callouts=[('Module + cooler as Seeed supplies them', (b.M + 160, b.M + 150, 140))])

step('06-tiedown.png', '6 · Tie the cooler down: 4 × M3 × 35 flat head from below',
     context=[(base, GREY)], new=[(s, up(-40)) for s in tiedown], view='bottom',
     callouts=[('4 × M3 × 35 flat head', at(near(tiedown, 'bottom'), up(-40)))],
     note='Each screw replaces a cooler screw: up through the floor, board and module, 4 mm into the heatsink standoff.')

step('07-antennas.png', '7 · Antennas: 4 × RP-SMA bulkheads',
     context=built + [(s, GREY) for s in board_screws] + cooler, meshes=board(0), new=[(s, (0, 0, 0)) for s in antennas],
     callouts=[('WIFI 1', (0, 46, 62)), ('WIFI 2', (0, 145, 62)), ('CELL 1', (206, 46, 62)), ('CELL 2', (206, 145, 62))],
     note='Push each pigtail through from inside; lock washer and nut outside.', view='front_high')

step('08-plates.png', '8 · Slide in the plates and hatch',
     context=built + [(s, GREY) for s in board_screws + antennas] + cooler, meshes=board(0),
     new=[(front, up(80)), (rear, up(80)), (hatch, up(80))],
     callouts=[('Front plate P4 (P3 with GMSL)', tuple(c + o for c, o in zip(centre(front), up(80)))),
               ('Rear plate P5', tuple(c + o for c, o in zip(centre(rear), up(80)))),
               ('Side hatch P10', tuple(c + o for c, o in zip(centre(hatch), up(80))))])

step('09-lid.png', '9 · Fit the lid: 4 × M3 × 16 socket head from the top',
     context=built + [(s, GREY) for s in board_screws + antennas] + [(front, PLATE), (rear, PLATE), (hatch, PLATE)] + cooler,
     meshes=board(0), new=[(cover, up(70)), *[(s, up(130)) for s in lid_screws]],
     callouts=[('P2 cover', tuple(c + o for c, o in zip(centre(cover), up(70)))),
               ('4 × M3 × 16 socket head', tuple(c + o for c, o in zip(centre(lid_screws[1]), up(130))))])

# ------------------------------------------------------------------------------------------------ drive trays (one P16)
tray = b.stack(['storage_25'])[0][1]
shw = h.storage_hardware(['storage_25'])
sp = lambda prefix: [s for n, s, _ in shw if n.startswith(prefix)]
feet, standoffs, closers, dscrews = sp('H11'), sp('H12'), sp('H15'), sp('H13')
drives = [(s, DARK) for n, s, _ in shw if n.startswith('D ')]
closed = [(base, GREY), (cover, GREY), (front, PLATE), (rear, PLATE), (hatch, PLATE)]

step('10-tray-inserts.png', 'Trays 1 · Heat-set 4 × M3 inserts into the base feet',
     context=closed, new=[(s, up(-30)) for s in feet], view='bottom',
     callouts=[('4 × M3 insert, from below', at(near(feet, 'bottom'), up(-30)))])

step('11-drives.png', 'Trays 2 · Screw the drives into the tray from below',
     context=[(tray, GREY)] + drives, new=[(s, up(-25)) for s in dscrews], view='bottom',
     callouts=[('M3 × 4 button head, 4 per 2.5 in drive', at(near(dscrews, 'bottom'), up(-25)))],
     note='3.5 in drives in P15 use 6-32 × 3/16 in screws. 7 mm SSDs without bottom holes use P19 clips.')

step('12-stack.png', 'Trays 3 · Hang the tray from the base',
     context=closed + [(tray.translate(up(-60)), GREY)] + [(s.translate(up(-60)), c) for s, c in drives],
     new=[(s, up(-25)) for s in standoffs] + [(s, up(-115)) for s in closers], view='bottom',
     callouts=[('4 × M3 × 20 standoffs into the base feet', at(near(standoffs, 'bottom', far=False), up(-25))), ('P16 tray', at(tray, up(-60))),
               ('4 × M3 × 6 button head close the stack', at(near(closers, 'bottom'), up(-115)))],
     note='Work with the enclosure upside down on its lid. A second tray hangs from this one the same way.')

zb = b.stack(['storage_25'])[-1][2]
mplate = b.storage_mount_plate().translate((0, 0, zb - b.e['mount_ear_thickness']))
pscrews = [s for n, s, _ in h.storage_hardware(['storage_25'], True) if n.startswith('H14')]
step('13-mount-plate.png', 'Trays 4 · Wall or robot mount: P17 plate',
     context=closed + [(tray, GREY)] + drives + [(s, GREY) for s in standoffs],
     new=[(mplate, up(-40))] + [(s, up(-95)) for s in pscrews], view='bottom',
     callouts=[('P17 mounting plate', at(mplate, up(-40))), ('4 × M3 × 12 socket head', at(near(pscrews, 'bottom'), up(-95)))],
     note='Use instead of the M3 × 6 closing screws. M6 screws through the tab slots fix it to the wall or robot.')
