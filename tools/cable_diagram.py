"""2D cable-route diagram for the preview: side elevation (Y-Z) and tray plan (X-Y) -> preview/cable-route-diagram.png."""
from pathlib import Path
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,FancyArrowPatch
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'cad'));import build as b;import hardware as h
S=b.S;ck=['storage_35','storage_25'];links=[(0,0,0),(1,1,0)];mods=b.stack(ck)
SHELL='#3a4049';TRAY='#59616b';PCB='#23965c';DRV='#aeb4ba';RED='#cc1f1f';YEL='#e0b000';ORG='#f07010'
fig,(ax,bx)=plt.subplots(1,2,figsize=(17,8.2),gridspec_kw={'width_ratios':[1.25,1]})
fig.suptitle('Cable routing between the J501 carrier and the storage trays (1 of each shown)',fontsize=15)
# Side elevation, seen from the left: Y across, Z up.
ax.add_patch(Rectangle((b.Y0,0),b.D,b.F,color=SHELL));ax.add_patch(Rectangle((b.M,b.Z),b.p['depth'],b.p['thickness'],color=PCB))
op=[s.BoundingBox() for _,s in b.envelope_boxes('plug_drop')];oy0=min(q.ymin for q in op);oy1=max(q.ymax for q in op)
ax.add_patch(Rectangle((oy0,-.5),oy1-oy0,b.F+1,color='white'));ax.text((oy0+oy1)/2,b.F+1.5,'floor opening',ha='center',fontsize=8)
bp=h.board_sata_ports()
for k,(x,y,z) in enumerate(bp['data']):ax.add_patch(Rectangle((y-8,z),16,3.8,color='#222'))
for k,(x,y,z) in enumerate(bp['power']):ax.add_patch(Rectangle((y-5,z-.3),10,3.8,color='#f2f2f2',ec='#555',lw=.8))
ax.text(39,b.Z+3.2,'SATA data J21/J24 + PH 5 V power J22/J23 under the board',ha='left',fontsize=8)
for n,_,z in mods:
    k=n.rsplit('_',1)[0];m=S['modules'][k];Hm=m['height']
    ax.add_patch(Rectangle((b.Y0,z),b.D,S['floor'],color=TRAY));ax.add_patch(Rectangle((b.Y0,z),S['wall'],Hm,color=TRAY));ax.add_patch(Rectangle((b.Y1-S['wall'],z),S['wall'],Hm,color=TRAY))
    cx0,cy0,cx1,cy1=S['chimney'];ax.add_patch(Rectangle((cy0,z-.5),cy1-cy0,S['floor']+1,color='white'))
    for bay in m['bays']:
        d=S['drives'][bay['type']];ax.add_patch(Rectangle((bay['y'],z+S['floor']+S['pad_height']),d['size'][1],d['size'][2] if bay['type']=='d35' else 9.5,color=DRV,alpha=.8))
    ax.text(b.Y1+3,z+Hm/2,f"{'P15 3.5 in tray' if k=='storage_35' else 'P16 2.5 in tray'}",va='center',fontsize=9)
COL={'data':RED,'power':YEL,'dc12':ORG}
for name,sig,pts,c,(tx,ty,tz),board in h.cable_routes(ck,links):
    fp,_=h.fillet_path(pts,c['min_bend_radius'])
    ax.plot([q[1] for q in fp],[q[2] for q in fp],color=COL[sig],lw=3,solid_capstyle='round');ax.plot([ty],[tz],'o',color=COL[sig],ms=8)
    if sig=='dc12':ax.text(b.Y1-14,fp[0][2]+2.5,'12V IN',color=ORG,fontsize=9,ha='right')
ax.annotate('plug straight up into the\nvertical underside connectors',(bp['data'][0][1],bp['data'][0][2]-1),(95,11),fontsize=9,arrowprops=dict(arrowstyle='->'))
ax.text(130,-57,'Vertical drops run in the left gutter beside the drives, not through them (see plan).',fontsize=8,style='italic')
ax.annotate('drop through the base floor\nand each tray floor (chimney)',((oy0+oy1)/2,-10),(85,-18),fontsize=9,arrowprops=dict(arrowstyle='->'))
ax.set(xlim=(0,215),ylim=(-60,28),xlabel='Enclosure Y (front → rear)',ylabel='Enclosure Z',title='Side elevation, seen from the left (vertical exaggerated)');ax.grid(alpha=.15)
# Tray plan: X across, Y up.
k='storage_35';m=S['modules'][k];bay=m['bays'][0];d=S['drives']['d35']
bx.add_patch(Rectangle((0,b.Y0),b.W,b.D,fill=False,lw=2,color=TRAY))
cx0,cy0,cx1,cy1=S['chimney'];bx.add_patch(Rectangle((cx0,cy0),cx1-cx0,cy1-cy0,color='#bfe0f5'));bx.text((cx0+cx1)/2,cy1+3,'chimney',ha='center',fontsize=8,color='#1d6fa5')
bx.add_patch(Rectangle((S['wall'],b.Y0+S['wall']),b.conn_x('d35')-S['wall'],b.D-2*S['wall'],color='#e9f3f6',zorder=0));bx.text(18,170,'cable\ngutter',ha='center',fontsize=9)
x0=b.conn_x('d35');bx.add_patch(Rectangle((x0,bay['y']),d['size'][0],d['size'][1],color=DRV,alpha=.8));bx.plot([x0,x0],[bay['y'],bay['y']+d['size'][1]],color='k',lw=4)
bx.text(x0+d['size'][0]/2,bay['y']+d['size'][1]/2,'3.5 in HDD\n(connector end at left)',ha='center',va='center',fontsize=9)
j=m['dc_jack']
for name,sig,pts,c,(tx,ty,tz),board in h.cable_routes(ck,links):
    if 'storage_35' not in name:continue
    fp,_=h.fillet_path(pts,c['min_bend_radius']);bx.plot([q[0] for q in fp],[q[1] for q in fp],color=COL[sig],lw=3)
    if board:bx.plot([board[0]],[board[1]],'o',color=COL[sig],ms=9)
    bx.add_patch(Rectangle((tx-c['drive_plug_length'],ty-8),c['drive_plug_length'],16,color='#222'))
bx.text(60,25,f"Bends: data >= {S['cables']['data']['min_bend_radius']:g} mm, PH power >= {S['cables']['power']['min_bend_radius']:g} mm, 12 V >= {S['cables']['dc12']['min_bend_radius']:g} mm\nPlugs: {S['cables']['data']['board_plug_length']:g} mm at the board, {S['cables']['data']['drive_plug_length']:g} mm at the drive, then a straight lead",fontsize=8)
bx.text(j['x'],b.Y1+3,'12V IN',ha='center',color=ORG,fontsize=9)
for a in S['gutter_anchors']:bx.add_patch(Rectangle((a[0]-2.5,a[1]-5),5,10,color='#888'))
bx.text(13,112,'tie\nanchors',fontsize=8)
bx.set(xlim=(-5,215),ylim=(0,195),aspect='equal',xlabel='Enclosure X',ylabel='Enclosure Y',title='P15 tray plan: data drops in the chimney, 12 V runs round the drive');bx.grid(alpha=.15)
from matplotlib.lines import Line2D
fig.legend([Line2D([],[],color=c,lw=3) for c in (RED,YEL,ORG)],['SATA data (J21 / J24, 2 ports)','5 V SATA power from board PH header (J22 / J23) - the only SATA power on the board','12 V from the tray 12V IN hole - 3.5 in only'],loc='lower center',ncol=3,fontsize=10)
fig.tight_layout(rect=(0,.06,1,.95));fig.savefig(R/'preview/cable-route-diagram.png',dpi=110);print('Wrote preview/cable-route-diagram.png')
