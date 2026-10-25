from pathlib import Path
import json,sys,math,textwrap
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle,Circle,Polygon,FancyBboxPatch,RegularPolygon
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'cad'));import build as b;import hardware as h
e=b.e;rev=b.P['revision'].split('-')[0]
plt.rcParams.update({'font.size':9,'axes.titlesize':14})
SHELL='#3a4049';PLATE='#9aa3ab';CU='#d98942';PCB='#23965c'
def page(title):
 fig=plt.figure(figsize=(11.69,8.27));fig.suptitle(title,fontsize=17,y=.96)
 fig.text(.05,.035,f'J501 Rev {rev} | dimensions in mm | NOT TO SCALE | fit-check prototype | cross reference measurement-register.csv',fontsize=9,color='#536779')
 return fig
def notes(fig,text,x=.70,y=.80):fig.text(x,y,text,va='top',linespacing=1.6)
def rr(ax,x0,y0,x1,y1,r,**kw):ax.add_patch(FancyBboxPatch((x0,y0),x1-x0,y1-y0,boxstyle=f'round,pad=0,rounding_size={min(r,(x1-x0)/2,(y1-y0)/2)}',**kw))
seat=b.COOLER_SEAT;hz=h.heatsink_screw_head_z()
with PdfPages(R/'docs/check-sheet.pdf') as pdf:
 fig=page('01 — Datum, board supports and cooler tie-down pattern');ax=fig.add_axes([.08,.14,.6,.72]);ax.set_aspect('equal');ax.add_patch(Rectangle((0,0),176,163,fill=False,lw=2))
 for k,(x,y) in enumerate(b.p['mount_holes']):ax.add_patch(Circle((x,y),3.5,fill=False,color='teal'));ax.text(x+4,y,f'B{k+1} ({x:g}, {y:g})',fontsize=8)
 for k,(x,y) in enumerate(b.p['module_mount_centers']):ax.add_patch(Circle((x,y),3.5,fill=False,color='darkorange'));ax.add_patch(Circle((x,y),7,fill=False,color='darkorange',ls='--'));ax.text(x+8,y,f'C{k+1} ({x:g}, {y:g})',fontsize=8)
 ax.set(xlim=(-12,195),ylim=(-12,175),xlabel='PCB X from left edge',ylabel='PCB Y from front edge');ax.grid(alpha=.15)
 notes(fig,'PCB 176 × 163\nB1–B4: carrier-to-housing\n150 × 130 pitch, M3 inserts\n\nC1–C4: cooler tie-down\n92 × 79 pitch\nD14 printed column (dashed)\nScrew from below the floor,\nthrough PCB, into the cooler.\n\nEnclosure translation:\nPCB underside → (15, 15, 20)\nP9 template has both patterns.')
 pdf.savefig(fig);plt.close(fig)
 fig=page('02 — Vertical stack');ax=fig.add_axes([.1,.15,.52,.7]);ax.set_aspect('equal')
 for x,z,w,hh,label,col in [(0,0,130,b.F,'4 mm floor',SHELL),(15,b.Z,100,b.p['thickness'],'Carrier PCB',PCB),(40,29.578,70,1.57,'Module PCB',PCB),(35,seat,80,50,'Reference cooler 50 high',CU),(5,37.578,45,1.6,'GMSL PCB',PCB),(0,b.H-b.RT,130,b.RT,'6 mm hex roof',SHELL),(0,b.BH-.3,130,.6,'Lid / base split Z72','#c33')]:
  ax.add_patch(Rectangle((x,z),w,hh,color=col,alpha=.75));ax.text(x+2,z+hh/2,label,fontsize=8,va='center')
 for z in (b.F,b.Z,21.578,29.578,seat,seat+50,b.BH,b.H-b.RT,b.H):ax.plot([0,130],[z,z],color='gray',alpha=.2)
 ax.set(xlim=(-5,140),ylim=(-4,118),ylabel='Enclosure Z');ax.set_xticks([])
 notes(fig,f'PCB underside {b.Z:.3f}\nPCB top 21.578\nModule underside 29.578\nTTP/cooler seat {seat:.3f}\nReference cooler top {seat+50:.3f}\nRoof underside {b.H-b.RT:.3f}\nCooler → roof {b.H-b.RT-seat-50:.3f}\n\nUnderside clearance {e["board_support_height"]+b.p["lowest_component"]:.1f}\n(lowest part −6.5 below PCB)\n\nGMSL PCB top 39.178 is 1.58\nbelow the cooler seat where\nthey overlap by 4.5 mm in plan:\nmeasure before printing P3.',x=.66)
 pdf.savefig(fig);plt.close(fig)
 fig=page('03 — Cooler tie-down column and board support');ax=fig.add_axes([.06,.14,.6,.74]);ax.set_aspect('equal')
 cr=e['heatsink_column_diameter']/2;lr=e['heatsink_landing_diameter']/2;lh=e['board_landing_height'];cs=e['heatsink_countersink_diameter']/2;hr=e['heatsink_clearance']/2
 for px,(col_r,land_r,label) in ((0,(cr,lr,'Cooler column C1–C4')),(40,(8,3.5,'Board support B1–B4'))):
  ax.add_patch(Rectangle((px-14,0),28,b.F,color=SHELL,alpha=.8))
  ax.add_patch(Rectangle((px-col_r,b.F),2*col_r,b.Z-b.F-lh,color=SHELL,alpha=.8));ax.add_patch(Rectangle((px-land_r,b.Z-lh),2*land_r,lh,color=SHELL,alpha=.8))
  ax.add_patch(Rectangle((px-14,b.Z),28,b.p['thickness'],color=PCB));ax.text(px,-5,label,ha='center',fontsize=9)
 ax.add_patch(Rectangle((-hr,-.01),2*hr,b.Z+1.6,color='white'))
 z0=hz-(2*cs-6.72)/2;ax.add_patch(Polygon([(-cs,0),(cs,0),(cs,z0),(hr,z0+cs-hr),(-hr,z0+cs-hr),(-cs,z0)],color='white'))
 ax.add_patch(Polygon([(-3.36,hz),(3.36,hz),(1.5,hz+1.86),(-1.5,hz+1.86)],color='#9aa'));ax.add_patch(Rectangle((-1.5,hz+1.86),3,seat+3-hz-1.86,color='#9aa',alpha=.8))
 ax.add_patch(Rectangle((-14,29.578),28,1.57,color=PCB,alpha=.6));ax.add_patch(Rectangle((-14,seat),28,3,color=CU))
 ax.add_patch(Rectangle((38.5,b.Z-11),3,11,color='#bb954e'));ax.add_patch(Rectangle((37.15,21.578),5.7,1.65,color='#9aa'))
 ax.set(xlim=(-20,60),ylim=(-8,48),ylabel='Enclosure Z');ax.grid(alpha=.15)
 notes(fig,f'Cooler tie-down (user request)\nD{2*cr:g} column, D{2*lr:g} landing\nD{2*hr:g} clearance hole\nD{2*cs:g} pocket, 90° countersink\nseat raised to Z{hz:.2f} in the column\n\nLoad path: floor → column → carrier\n→ module → heatsink standoffs\n\nSCREW: M3 × {h.heatsink_screw_length():g} flat head. AGX top\nZ{b.AGX_TOP:.2f} + {e["heatsink_thread_engagement"]:g} mm (8 threads) − seat\nZ{hz:.2f} = {b.AGX_TOP+e["heatsink_thread_engagement"]-hz:.1f}. Thermal pad\n{b.c["tim_thickness"]:g} mm lifts the heatsink only.\n\nBoard support: D16 / D7 land,\nM3 × 10 insert, M3 × 10 button.')
 pdf.savefig(fig);plt.close(fig)
 for front,gmsl,title in [(True,False,'04 — Front plate WITHOUT GMSL'),(True,True,'05 — Front plate WITH GMSL'),(False,False,'06 — Rear plate')]:
  fig=page(title+' (viewed from outside)');ax=fig.add_axes([.06,.34,.88,.5]);ax.set_aspect('equal')
  rr(ax,b.PX0,b.F,b.PX1,b.PANEL_TOP,0,facecolor=PLATE,edgecolor='black',lw=1.5)
  ax.add_patch(Rectangle((0,b.F),14,b.BH-b.F,facecolor=SHELL,alpha=.35));ax.add_patch(Rectangle((b.W-14,b.F),14,b.BH-b.F,facecolor=SHELL,alpha=.35));ax.add_patch(Rectangle((0,0),b.W,b.F+e['sill_height'],facecolor=SHELL,alpha=.35))
  side='front' if front else 'rear';ports=[(k,v) for k,v in b.P['ports'][side].items() if gmsl or not v.get('gmsl_only')];lines=[]
  prev=None
  for i,(k,v) in enumerate(sorted(ports,key=lambda kv:kv[1]['box'][0])):
   x0,z0,x1,z1=v['box'];x0+=b.M;x1+=b.M;z0+=b.Z;z1+=b.Z;ex0,ex1=x0,x1
   if prev and x0-prev[2]<e['min_panel_web']:
    bz0,bz1=max(z0,prev[1])+.8,min(z1,prev[3])-.8;bx0,bx1=prev[2]-1.5,x0+1.5
    if not front:bx0,bx1=b.W-bx1,b.W-bx0
    ax.add_patch(Rectangle((bx0,bz0),bx1-bx0,bz1-bz0,facecolor='white',edgecolor='none',zorder=3))
   prev=(x0,z0,x1,z1)
   if not front:x0,x1=b.W-x1,b.W-x0
   rr(ax,x0,z0,x1,z1,v['r'],facecolor='white',edgecolor='#147d82')
   ax.text((x0+x1)/2,(z0+z1)/2,str(i+1),ha='center',va='center',fontsize=11,color='#147d82')
   lines.append(f'{i+1}. {k}: enclosure X {ex0:.2f}..{ex1:.2f}, Z {z0:.2f}..{z1:.2f}, r{v["r"]}. {v["basis"]}')
  if not front:
   sb=e['service_buttons']
   for x,z in sb['actuators_pcb_xz']:
    xx=b.W-(b.M+x);ax.add_patch(Circle((xx,b.Z+z),sb['pin_hole']/2+sb['lead_in'],facecolor='white',edgecolor='#b75a18',zorder=4))
   xs=[b.W-(b.M+x) for x,_ in sb['actuators_pcb_xz']]
   ax.annotate(f"REC / RST pin holes D{sb['pin_hole']:g}\nX {b.M+sb['actuators_pcb_xz'][0][0]:.2f} / {b.M+sb['actuators_pcb_xz'][1][0]:.2f}, Z {b.Z+sb['actuators_pcb_xz'][0][1]:.2f}",(sum(xs)/2,b.Z+sb['actuators_pcb_xz'][0][1]),(sum(xs)/2-38,b.Z+42),fontsize=8,color='#b75a18',arrowprops=dict(arrowstyle='->',color='#b75a18'))
  for x in b.vent_positions(*e['panel_vent_x']):
   xx=x if front else b.W-x;w=e['panel_vent_width'];rr(ax,xx-w/2,e['panel_vent_z'][0],xx+w/2,e['panel_vent_z'][1],w/2,facecolor='white',edgecolor='#999')
  ax.set(xlim=(-2,208),ylim=(-2,80),xlabel='X along plate as seen from outside',ylabel='Enclosure Z');ax.grid(alpha=.12)
  fig.text(.06,.29,'\n'.join(textwrap.fill(l,150) for l in lines),va='top',linespacing=1.5,fontsize=8)
  fig.text(.06,.07,'3 mm plate printed exterior face down; 0.6 × 45° lead-in on every window. Plate inner face 0.37 (front) / 0.25 (rear) from the most protruding carrier part.\nShaded: corner posts and sill that frame the plate. Windows narrower than a 1.8 mm web are bridged.',fontsize=9)
  pdf.savefig(fig);plt.close(fig)
 fig=page('07 — Print orientation and assembly order');ax=fig.add_axes([.06,.12,.9,.74]);ax.axis('off')
 lines=['P1 / P1M: floor on bed. 206 × 181 (P1M 206 × 233) × 76.5. Columns, posts and channels rise from the floor.','P2 lid: roof on bed, 206 × 181 × 40. Hex webs grow from the bed; ledges are 45° in this orientation.','P3 / P4 / P5: exterior face on bed, 3 mm. Legends and window lead-ins print on the bed face.','P10 hatch: exterior face on bed; its V tongues have 45° undersides.','Coupons first: P11 (M3 pilot), P12/P13 (plate channel), P14 (countersink seating).','',
  'Assembly: 1. Heat-set 4 board inserts + 4 lid inserts.  2. Place PCB; 4 × M3 × 10 button heads.',
  '3. Fit module and cooler; drive the 4 M3 × 35 flat heads up the floor pockets into the heatsink standoffs (8 threads).','4. Fit 4 RP-SMA bulkheads (WIFI 1/2 left wall, CELL 1/2 right wall, Z62), nut outside.  Slide front, rear plates and J17 hatch down their channels.  5. Lower the lid; 4 × M3 × 16 from the top.','For wall/robot use, bolt P1M down first: the lid screws stay accessible from above.','',
  'Unresolved: filament, creep of printed columns under clamp load, insert pullout, vibration and load capacity.','Unresolved: exact cooler (thread, original screw length), GMSL XY, J26 USB-A model, user cable overmolds.','','Printer/profile __________________  Material __________________  Rail fit ______________','Countersink seat ____________  Cooler screw length ____________  Cable fit ____________']
 ax.text(0,1,'\n'.join(lines),va='top',fontsize=11,linespacing=1.65);pdf.savefig(fig);plt.close(fig)
 fig=page('08 — Lid: finger-safe honeycomb');ax=fig.add_axes([.07,.13,.6,.73]);ax.set_aspect('equal')
 rr(ax,0,b.Y0,b.W,b.Y1,e['outer_corner_radius'],facecolor='#2c323a',edgecolor='black')
 s=e['hex_across_flats']
 for x,y in b.hex_centers():ax.add_patch(RegularPolygon((x,y),6,radius=s/math.sqrt(3),orientation=math.pi/6,facecolor='white',edgecolor='none'))
 for x,y in e['lid_screw_centers']:ax.add_patch(Circle((x,y),e['lid_counterbore_diameter']/2,facecolor='#888'))
 ax.set(xlim=(-10,216),ylim=(-5,195),xlabel='Enclosure X',ylabel='Enclosure Y');ax.grid(alpha=.1)
 m=json.loads((R/'exports/design-metrics.json').read_text())['roof']
 notes(fig,f'{m["hex_cells"]} cells, {s:g} mm across flats\n{e["hex_web"]} mm webs, {e["roof_thickness"]:g} mm deep\nFan-side inlet chamfer {e["hex_inlet_flare"]:g} × {e["hex_inlet_depth"]:g}\n({s+2*e["hex_inlet_flare"]:g} A/F at the underside)\nOpen area {m["open_area_mm2"]:.0f} mm² ({m["open_percent_of_lid_plan"]}% of plan)\n+ 60 wall slots on the lid\n\n12 mm test finger cannot pass\n(Rev 0.4: 25 × 29 mm cells)\n\nRoof underside Z{b.H-b.RT:g}\nCooler gap {m["nominal_cooler_clearance_mm"]}\n\nGrey: M3 counterbores D6.4')
 pdf.savefig(fig);plt.close(fig)
 fig=page('09 — Mounting tabs (P1M): screw, washer and driver access');ax=fig.add_axes([.06,.12,.6,.75]);ax.set_aspect('equal')
 rr(ax,0,b.Y0,b.W,b.Y1,e['outer_corner_radius'],facecolor='#d5e1e7',edgecolor='#264552')
 w=e['mount_ear_width'];pr=e['mount_ear_projection'];L,sw=e['mount_slot']
 for x,y in b.mount_slot_centers():
  front=y<b.Y0;py=b.Y0-pr if front else b.Y1
  rr(ax,x-w/2,py,x+w/2,py+pr,6,facecolor='#98b7bf',edgecolor='#264552')
  ax.add_patch(Circle((x,y),e['mount_tool_envelope_diameter']/2,fill=False,color='darkorange',ls='--'));ax.add_patch(Circle((x,y),e['mount_washer_envelope_diameter']/2,fill=False,color='teal'))
  rr(ax,x-L/2,y-sw/2,x+L/2,y+sw/2,sw/2,facecolor='white',edgecolor='black');ax.text(x,y+(-14 if front else 12),f'({x:g}, {y:g})',ha='center',fontsize=8)
 xs=e['mount_ear_x'];ys=[y for _,y in b.mount_slot_centers()]
 ax.annotate('',xy=(xs[0],-32),xytext=(xs[1],-32),arrowprops={'arrowstyle':'<->'});ax.text(sum(xs)/2,-30,f'{xs[1]-xs[0]:g} center pitch',ha='center',fontsize=8)
 ax.annotate('',xy=(222,min(ys)),xytext=(222,max(ys)),arrowprops={'arrowstyle':'<->'});ax.text(226,96,f'{max(ys)-min(ys):g} center pitch',rotation=90,va='center',fontsize=8)
 ax.set(xlim=(-12,240),ylim=(-40,230),xlabel='Enclosure X',ylabel='Enclosure Y');ax.grid(alpha=.1)
 notes(fig,f'Tabs: {w:g} wide / {e["mount_ear_thickness"]:g} thick\nProjection: {pr:g}; R6 plan corners\n45° gusset to the frame\nSlots: {L:g} along X / {sw:g} wide\n\nTeal: 16 mm washer envelope\nOrange: 20 mm driver envelope\nNothing overhangs the tabs\n(flush lid)\n\nP1M print: 206 × 233 × 76.5\nP1S Y margin 11.5 each side')
 pdf.savefig(fig);plt.close(fig)
 S=b.S
 for kind in ('storage_35','storage_25'):
  m=S['modules'][kind];fig=page(f"{'10' if kind=='storage_35' else '11'} — Storage tray {m['label']} in (top view, drives from below)");ax=fig.add_axes([.06,.12,.6,.75]);ax.set_aspect('equal')
  rr(ax,0,b.Y0,b.W,b.Y1,e['outer_corner_radius'],facecolor='#d5e1e7',edgecolor='#264552')
  rr(ax,S['wall'],b.Y0+S['wall'],b.W-S['wall'],b.Y1-S['wall'],e['outer_corner_radius']-S['wall'],facecolor='white',edgecolor='#264552')
  x0,y0,x1,y1=S['chimney'];rr(ax,x0,y0,x1,y1,S['chimney_radius'],facecolor='#bfe0f5',edgecolor='#1d6fa5');ax.text((x0+x1)/2,y1+3,'chimney',ha='center',fontsize=8,color='#1d6fa5')
  for x,y in S['standoff_centers']:ax.add_patch(Circle((x,y),S['column_diameter']/2,facecolor=SHELL,alpha=.5));ax.add_patch(Circle((x,y),1.7,facecolor='white'))
  lines=[]
  for bay in m['bays']:
   d=S['drives'][bay['type']];L,Wd,Hd=d['size'];dx=b.conn_x(bay['type']);dy=bay['y']
   ax.add_patch(Rectangle((dx,dy),L,Wd,facecolor='#e7e2d8',edgecolor='#6b5d45'));ax.plot([dx,dx],[dy,dy+Wd],color='black',lw=3)
   ax.text(dx+L/2,dy+Wd/2,f"{d['name']}\n{L:g} × {Wd:g}",ha='center',va='center',fontsize=8)
   for hx,hy in b.drive_holes(bay['type'],dy):ax.add_patch(Circle((hx,hy),d['clearance']/2,facecolor='white',edgecolor='black'));ax.add_patch(Circle((hx,hy),d['counterbore'][0]/2,fill=False,ls=':'))
   lines.append(f"Bay at Y{dy:g}: holes {', '.join(f'{v:g}' for v in d['holes_from_connector'])} from the connector end (X{dx:g}); lateral {', '.join(f'{v:g}' for v in d['holes_lateral'])}.")
  if 'dc_jack' in m:j=m['dc_jack'];ax.plot([j['x']-4,j['x']+4],[b.Y1,b.Y1],color='red',lw=4);ax.text(j['x'],b.Y1+4,'12V IN D8',ha='center',fontsize=8,color='red')
  ax.set(xlim=(-5,215),ylim=(0,195),xlabel='Enclosure X (connector ends face the left gutter)',ylabel='Enclosure Y');ax.grid(alpha=.1)
  d=S['drives'][m['bays'][0]['type']]
  notes(fig,f"Height {m['height']:g}; floor {S['floor']:g} + pads {S['pad_height']:g}\nStandoffs: M3 M-F {m['standoff_length']:g} mm\n(5.5 AF, 6 mm male) in D{S['column_bore']:g} bores,\n{S['ledge']:g} mm ledge under the part above\n\nDrive screws from below:\n{d['screw']}\nclearance D{d['clearance']:g}, counterbore\nD{d['counterbore'][0]:g} × {d['counterbore'][1]:g}\n\n"+'\n'.join(textwrap.fill(l,40) for l in lines))
  pdf.savefig(fig);plt.close(fig)
 fig=page('12 — Under the carrier: card envelopes and SATA plug drops');ax=fig.add_axes([.06,.30,.88,.6]);ax.axis('off')
 sc=json.loads((R/'exports/storage-checks.json').read_text())
 rows=[[x['name'],x['ref'],x['role'],', '.join(f'{v:g}' for v in x['enclosure_box']),f"{x['intrusion_before_relief_mm3']:g}",'-' if x['gap_to_base_after_relief_mm'] is None else f"{x['gap_to_base_after_relief_mm']:g}",'-' if x['lowest_point_above_floor_mm'] is None else f"{x['lowest_point_above_floor_mm']:g}"] for x in sc['underside_envelopes']]
 tb=ax.table(cellText=rows,colLabels=['envelope','ref','role','enclosure box x0, y0, z0, x1, y1, z1','pre-relief overlap mm3','gap after relief','above floor'],loc='upper center',cellLoc='left',colWidths=[.12,.07,.08,.33,.15,.11,.10]);tb.auto_set_font_size(False);tb.set_fontsize(8);tb.scale(1,1.6)
 fig.text(.06,.25,'\n'.join(textwrap.fill(f"{x['name']}: {x['basis']}",170) for x in sc['underside_envelopes']),va='top',fontsize=7.5,linespacing=1.4)
 fig.text(.06,.08,f"Under-board space {sc['underside_space']['clear_height_mm']:g} mm; stacked cards need {sc['underside_space']['stacked_cards_need_mm']:g} mm. Board SATA power is 5 V only; 3.5 in drives need 12 V (tray 12V IN).",fontsize=9)
 pdf.savefig(fig);plt.close(fig)
print('Wrote docs/check-sheet.pdf')
