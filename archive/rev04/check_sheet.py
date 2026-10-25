from pathlib import Path
import json,sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle,Circle,Polygon
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'cad'));import build as b
plt.rcParams.update({'font.size':9,'axes.titlesize':14})
def page(title):
 fig=plt.figure(figsize=(11.69,8.27));fig.suptitle(title,fontsize=17,y=.96)
 fig.text(.05,.035,'J501 Rev 0.4 | dimensions in mm | NOT TO SCALE | fit-check prototype | cross reference measurement-register.csv',fontsize=9,color='#536779')
 return fig
with PdfPages(R/'docs/check-sheet.pdf') as pdf:
 fig=page('01 — Datum, board mounting and independent cooler pattern');ax=fig.add_axes([.08,.14,.6,.72]);ax.set_aspect('equal');ax.add_patch(Rectangle((0,0),176,163,fill=False,lw=2));
 for k,(x,y) in enumerate(b.p['mount_holes']):ax.add_patch(Circle((x,y),3.5,fill=False,color='teal'));ax.text(x+4,y,f'B{k+1} ({x:g}, {y:g})',fontsize=8)
 for k,(x,y) in enumerate(b.p['module_mount_centers']):ax.add_patch(Circle((x,y),3.5,fill=False,color='darkorange'));ax.text(x+4,y,f'C{k+1} ({x:g}, {y:g})',fontsize=8)
 ax.set(xlim=(-12,195),ylim=(-12,175),xlabel='PCB X from left edge',ylabel='PCB Y from front edge');ax.grid(alpha=.15)
 fig.text(.70,.75,'PCB 176 × 163\nB1–B4: carrier-to-housing\n150 × 130 center pitch\nM3 assumed; verify holes.\n\nC1–C4: existing cooler mounts\n92 × 79 center pitch\nReuse original retention.\n\nEnclosure translation:\nPCB underside → (15,15,20)\n\nSource: carrier STEP\nMount proxy solids 5155–5162\nPCB solid: 5169\n\nMeasured carrier pitch:\nX __________ Y __________\nHole size ________________',va='top',linespacing=1.6)
 pdf.savefig(fig);plt.close(fig)
 fig=page('02 — Vertical stack and unresolved cooler/GMSL clearance');ax=fig.add_axes([.1,.15,.52,.7]);ax.set_aspect('equal')
 for x,z,w,h,label,col in [(0,0,130,8,'8 mm floor','#718999'),(15,20,100,1.578,'Carrier PCB','#23965c'),(40,29.578,70,1.57,'Module PCB','#23965c'),(35,40.758,80,50,'Reference cooler 50 high','#d98942'),(5,37.578,45,1.6,'GMSL PCB','#23965c'),(0,102,130,10,'10 mm rib depth','#718999')]:
  ax.add_patch(Rectangle((x,z),w,h,color=col,alpha=.7));ax.text(x+2,z+h/2,label,fontsize=8,va='center')
 for z in (8,20,21.578,29.578,37.578,39.178,40.758,90.758,102,112):ax.plot([0,130],[z,z],color='gray',alpha=.2)
 ax.set(xlim=(-5,140),ylim=(-4,118),ylabel='Enclosure Z');ax.set_xticks([])
 fig.text(.65,.79,'Exact/derived nominal levels\nPCB underside 20.000\nPCB top 21.578\nModule underside 29.578\nTTP/cooler seat 40.758\nReference cooler top 90.758\nRib underside 102.000\n\n16 mm GMSL board spacing\nAssumed GMSL PCB thickness 1.6\nPCB top → cooler seat gap 1.580\n4.5 mm overlap strip in plan\n\nThis does NOT include actual TIM,\nGMSL top components or screw heads.\n\nMeasured cooler seat ________\nMeasured cooler top _________\nMinimum GMSL gap ___________',va='top',linespacing=1.5)
 pdf.savefig(fig);plt.close(fig)
 fig=page('03 — Printed PCB support and insert engagement');ax=fig.add_axes([.1,.15,.5,.72]);ax.set_aspect('equal')
 for patch in [Rectangle((-8,0),16,8,color='#718999'),Rectangle((-8,8),16,7.5,color='#718999'),Rectangle((-3.5,15.5),7,4.5,color='#718999'),Rectangle((-2.1,10),4.2,10,color='#bb954e'),Rectangle((-10,20),20,1.578,color='#23965c'),Rectangle((-1.5,11.578),3,10,color='#aaa'),Rectangle((-2.85,21.578),5.7,1.65,color='#aaa')]:ax.add_patch(patch)
 ax.set(xlim=(-12,12),ylim=(-1,26),xlabel='Section about mount center',ylabel='Enclosure Z');ax.grid(alpha=.15)
 fig.text(.63,.78,'Support is part of P1/P1M\n16 mm lower diameter\n7 mm landing diameter\n4.5 mm landing neck height\n12 mm support above floor\n\nH4: M3 × 10 insert\n3.9 mm nominal pilot × 11 deep\n4.4 mm entry × 0.6 chamfer\n\nH5: M3 × 10 button screw\nPCB thickness 1.578\nInsert engagement 8.422 nominal\n\nSource underside-component boxes\nplus 0.5 mm relief. Closest SMT\nfeature constrains the landing size.\n\nCoupon pilot chosen __________\nInsert installed OD/fit _________',va='top',linespacing=1.6)
 pdf.savefig(fig);plt.close(fig)
 for front,gmsl,title in [(True,False,'04 — Front WITHOUT GMSL'),(True,True,'05 — Front WITH GMSL'),(False,False,'06 — Rear I/O')]:
  fig=page(title+' — every window has a named purpose');ax=fig.add_axes([.06,.34,.88,.5]);ax.set_aspect('equal');ax.add_patch(Rectangle((10.25,8),185.5,63.8,fill=False,lw=2))
  keys=['front_audio','front_network_power'] if front else ['rear_terminal','rear_hdmi_usb','rear_usb_c_pair']
  if gmsl:keys=['front_audio_gmsl','front_network_power']
  for i,k in enumerate(keys):
   x,z,X,Z=b.P['openings'][k];x+=b.M;X+=b.M;z+=b.Z;Z+=b.Z
   ax.add_patch(Rectangle((x,z),X-x,Z-z,facecolor='#b9e0df',edgecolor='#147d82'));ax.text((x+X)/2,(z+Z)/2,f'{i+1}',ha='center',va='center',fontsize=13)
   ax.annotate(f'X {x:.2f}..{X:.2f}\nZ {z:.2f}..{Z:.2f}',xy=((x+X)/2,z),xytext=((x+X)/2,2-i*7),ha='center',fontsize=8,arrowprops={'arrowstyle':'-','lw':.7})
  ax.set(xlim=(0,206),ylim=(-20,78),xlabel='Enclosure X',ylabel='Enclosure Z');ax.grid(alpha=.12)
  notes='\n'.join(f'{i+1}. {b.P["opening_notes"][k]}' for i,k in enumerate(keys))
  import textwrap
  fig.text(.08,.25,'\n'.join(textwrap.fill(line,125) for line in notes.splitlines()),va='top',linespacing=1.6,fontsize=9)
  fig.text(.08,.09,'All panel windows print through the 6 mm thickness. Rail clearance: 0.25 mm per side. Top capture clearance: 0.2 mm.\nMeasure connector mouths, cable overmolds and latch travel; cutouts are service envelopes, not a claim of certified fit.',fontsize=9)
  pdf.savefig(fig);plt.close(fig)
 fig=page('07 — Print orientations and feature review');ax=fig.add_axes([.06,.12,.9,.74]);ax.axis('off')
 lines=['P1 / P1M: floor on bed. All rails and cover bosses rise from the floor.', 'P1M: 217 × 253 × 72 mm. Center on P1S plate; brim and excluded areas must be checked.', 'P2: roof on bed. Roof grid prints directly on bed. Pointed vent ends close at 45 degrees.', 'P3 / P4 / P5: inner face on bed, 6 mm thick. No bridge or support across connector openings.', 'P10: inner face on bed, grip facing upward. Rigid sliding retention; no thin snap arm.', 'M6 pilot: pointed relief at both vertical poles; print the same horizontal coupon first.', 'M3 pilot: vertical. Print coupon with the selected material and profile.', 'P12/P13: 6.5 mm channel and 6 mm key. Verify free sliding without rattle.', '', 'Assembly: insert PCB hardware → install board/cooler → slide front/rear/hatch down → fit cover.', 'The two cover screws retain the cover; the cover captures every sliding panel.', 'For wall/robot use, choose P1M and appropriate site mounting hardware.', '', 'Unresolved: actual filament, thermal creep, insert pullout, vibration and load capacity.', 'Unresolved: exact user cooler, GMSL XY/retention, J26 USB-A model and mating cable envelopes.', 'A watertight STL and collision check do not establish these physical properties.', '', 'Printer/profile __________________________  Material __________________________', 'Rail fit _________________________________  Insert coupon _____________________', 'All cable latches accessible ______________  Cooler/GMSL clearance ______________']
 ax.text(0,1,'\n'.join(lines),va='top',fontsize=11,linespacing=1.65);pdf.savefig(fig);plt.close(fig)
 fig=page('08 — Open lid: deep ribs and a rounded perimeter');ax=fig.add_axes([.07,.13,.6,.73]);ax.set_aspect('equal')
 from matplotlib.patches import FancyBboxPatch
 ax.add_patch(FancyBboxPatch((-6.4,-6.4),218.8,205.8,boxstyle='round,pad=0,rounding_size=4',facecolor='#244859',edgecolor='black'))
 for x,y,dx,dy in b.roof_windows():ax.add_patch(FancyBboxPatch((x,y),dx,dy,boxstyle='round,pad=0,rounding_size=1.2',facecolor='white',edgecolor='none'))
 ax.set(xlim=(-15,220),ylim=(-15,208),xlabel='Enclosure X',ylabel='Enclosure Y');ax.grid(alpha=.1)
 fig.text(.70,.80,'42 openings / 7 x 6 cells\n2.4 mm-wide vertical webs\n10 mm rib depth\nR1.2 cell corners\nR4 outer lid corners\nReinforced corner lands\n\nRoof open area: 67.37%\nPrevious roof: 25.58%\nOpening area ratio: 2.633x\n\nRibs occupy Z102..112\nReference cooler gap: 11.242\n\nPrint roof face on the bed.\nNo unsupported roof bridges.\n\nWhole-lid stiffness and airflow\nare not physically measured.\nMaterial: __________________',va='top',linespacing=1.6)
 pdf.savefig(fig);plt.close(fig)
 fig=page('09 — Projecting tabs: screw, washer and driver access');ax=fig.add_axes([.06,.12,.6,.75]);ax.set_aspect('equal')
 ax.add_patch(Rectangle((0,0),206,193,facecolor='#d5e1e7',edgecolor='#264552'))
 ax.add_patch(FancyBboxPatch((-6.4,-6.4),218.8,205.8,boxstyle='round,pad=0,rounding_size=4',fill=False,edgecolor='#264552',linestyle='--'))
 for x in b.e['mount_ear_x']:
  for front in (True,False):
   y=-20 if front else 213; py=-30 if front else 189
   ax.add_patch(FancyBboxPatch((x-20,py),40,34,boxstyle='round,pad=0,rounding_size=4',facecolor='#98b7bf',edgecolor='#264552'))
   ax.add_patch(Circle((x,y),10,fill=False,color='darkorange',linestyle='--'))
   ax.add_patch(Circle((x,y),8,fill=False,color='teal'))
   ax.add_patch(FancyBboxPatch((x-6,y-3.3),12,6.6,boxstyle='round,pad=0,rounding_size=3.3',facecolor='white',edgecolor='black'))
   ax.text(x,y+12,f'({x}, {y})',ha='center',fontsize=8)
 ax.annotate('',xy=(20,-40),xytext=(186,-40),arrowprops={'arrowstyle':'<->'});ax.text(103,-38,'166 center pitch',ha='center',fontsize=8)
 ax.annotate('',xy=(230,-20),xytext=(230,213),arrowprops={'arrowstyle':'<->'});ax.text(234,96.5,'233 center pitch',rotation=90,va='center',fontsize=8)
 ax.set(xlim=(-12,248),ylim=(-48,235),xlabel='Enclosure X',ylabel='Enclosure Y');ax.grid(alpha=.1)
 fig.text(.70,.80,'Tabs: 40 wide / 16 thick\nProjection beyond base: 30\nR4 plan corners / R1.2 top rim\nSlots: 12 along X / 6.6 wide\n\nTeal: 16 mm washer envelope\nOrange: 20 mm driver envelope\nDriver modeled from Z24 up\nTool-to-lid clearance: 3.6\n\nBase print: 217 x 253 x 72\nP1S nominal Y margin: 1.5 each\nCheck centering, brim and\nexcluded machine regions.\n\nSite screw/anchor length is\nnot specified by this model.\n\nMeasured tool OD: __________\nActual washer OD: __________',va='top',linespacing=1.6)
 pdf.savefig(fig);plt.close(fig)
print('Wrote docs/check-sheet.pdf')
