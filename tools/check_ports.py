"""Mated-plug check: every external port's plug is swept in along its axis against the printed parts.

Windows come from the plug models (cad/ports.py), so this proves them in 3D: zero overlap, the stated
clearance all round (corner radii included), the window centred where it should be, and no plug-to-plug clash.
Writes exports/port-checks.json and preview/port-fit.png.
"""
from pathlib import Path
import sys,json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'cad'));import build as b;import ports as pt
from cadagent.connectors import check_ports,draw_ports
P=b.P;shell={'base':b.base(),'cover':b.cover()}
configs=[('front_no_gmsl','front',b.panel()),('front_gmsl','front',b.panel(gmsl=True)),('rear_io','rear',b.panel(False))]
report={'revision':P['revision'],'method':'Each plug envelope (cadagent.connectors) is swept from its mated position out to its far end and '
        'intersected with the base, cover and plate; the sweep grown by the port clearance must also be clear. '
        'Plug dimensions are catalogue or typical values, listed per port with their basis.','configs':{}}
for name,side,plate in configs:
    ports={k:v['mate'] for k,v in P['ports'][side].items() if 'mate' in v}
    wall=pt.wall_w(P,side);fr=pt.frame(P,side)
    r=check_ports(ports,{k:fr for k in ports},{**shell,name:plate},{k:wall for k in ports},{k:P['ports'][side][k]['box'] for k in ports})
    report['configs'][name]=r
    for k,row in r['ports'].items():
        print(f"{name:14s} {k:15s} {'PASS' if row['pass'] else 'FAIL'}  window {row['window']}  min margin {row['min_margin_mm']:.2f}"
              f"  sweep {sum(row['sweep_interference_mm3'].values()):.3f} mm3",flush=True)
report['pass']=all(c['pass'] for c in report['configs'].values())
(R/'exports/port-checks.json').write_text(json.dumps(report,indent=2)+'\n')

# Evidence: both plates seen from outside, with PCB lines, receptacle faces, plug sections and windows.
fig,axs=plt.subplots(2,1,figsize=(13,7.5))
for ax,side,title in [(axs[0],'front','Front plate (seen from outside)'),(axs[1],'rear','Rear plate (seen from outside)')]:
    ports={k:v['mate'] for k,v in P['ports'][side].items() if 'mate' in v};wall=pt.wall_w(P,side)
    f=(lambda u,v:(b.M+u,b.Z+v)) if side=='front' else (lambda u,v:(b.W-(b.M+u),b.Z+v))
    ax.add_patch(Rectangle((b.PX0,b.F),b.PX1-b.PX0,b.PANEL_TOP-b.F,facecolor='#eef0f2',edgecolor='#9aa3ab',zorder=0))
    for z,lab in [(b.Z,'PCB underside'),(b.Z+b.p['thickness'],'PCB top')]:
        ax.axhline(z,color='#23965c',lw=.6,ls='--',zorder=1);ax.text(b.PX0+1,z+.3,lab,fontsize=6,color='#23965c')
    draw_ports(ax,ports,{k:P['ports'][side][k]['box'] for k in ports},{k:wall for k in ports},
               {k:P['ports'][side][k]['r'] for k in ports},to_xy=f)
    for k,v in P['ports'][side].items():  # windows with no plug (light pipes, provisional GMSL mouths): dashed
        if 'mate' in v:continue
        (x0,y0),(x1,y1)=f(v['box'][0],v['box'][1]),f(v['box'][2],v['box'][3])
        ax.add_patch(Rectangle((min(x0,x1),y0),abs(x1-x0),y1-y0,fill=False,ls='--',lw=.8,edgecolor='#555'))
        ax.annotate(k,((x0+x1)/2,y1),xytext=(0,3),textcoords='offset points',ha='center',fontsize=7,color='#555')
    ax.set_title(title,fontsize=10);ax.set_aspect('equal');ax.set_xlim(b.PX0-2,b.PX1+2);ax.set_ylim(b.F,b.Z+28)
    ax.set_xlabel('enclosure X (mm)',fontsize=7);ax.set_ylabel('Z (mm)',fontsize=7);ax.tick_params(labelsize=6)
ok=report['pass']
fig.suptitle(f"Mated-plug fit: windows (black), receptacle faces (grey), plug sections that pass the plate (orange) — "
             f"{'all ports PASS' if ok else 'FAIL'}",fontsize=10)
fig.tight_layout();fig.savefig(R/'preview/port-fit.png',dpi=150);plt.close(fig)
print('Port check','PASS' if ok else 'FAIL')
