"""Generate evidence tables and a linked review page from the working model."""
from pathlib import Path
import csv,json,hashlib,html,sys
R=Path(__file__).resolve().parents[1];D=R/'docs';D.mkdir(exist_ok=True);sys.path.insert(0,str(R/'cad'));from ports import resolve
import build as b  # tie-down seat height (HS_HEAD_Z)
P=resolve(json.loads((R/'cad/parameters.json').read_text()))
S=json.loads((R/'references/sources.json').read_text())
extra={'202003906_reServer_Industrial_J501_Carrier_Board_v1.0_SCH_PDF_20240529.pdf':'https://files.seeedstudio.com/wiki/reComputer-Jetson/J501/202003906_reServer_Industrial_J501_Carrier_Board_v1.0_SCH_PDF_20240529.pdf','samtec-qsh-qth.pdf':'https://suddendocs.samtec.com/catalog_english/qsh.pdf','Jetson_AGX_Orin_Module_3D_STEP_Model.zip':'https://developer.nvidia.com/downloads/jetson-agx-orin-module-3d-step-modelzip','FM4-NZRP-PCB-1.stp':'https://s3-us-west-2.amazonaws.com/catsy.582/FM4-NZRP-PCB-1.stp','FM4-NXRP-PCB-1.pdf':'https://s3-us-west-2.amazonaws.com/catsy.582/FM4-NXRP-PCB-1.pdf','gmsl_connectoin.png':'https://files.seeedstudio.com/wiki/reComputer-Jetson/J501/gmsl_connectoin.png','gmsl.png':'https://files.seeedstudio.com/wiki/reComputer-Jetson/J501/gmsl.png','seeed-oshw-tree.json':'https://api.github.com/repos/Seeed-Studio/OSHW-Jetson-Series/git/trees/main?recursive=1','interfaces.html':'https://wiki.seeedstudio.com/j501_carrier_board_interfaces_usage/'}
extra.update(json.loads((R/'references/extra-source-urls.json').read_text()))
for fn,url in extra.items():
 f=R/'references'/fn
 if f.exists() and fn not in [v['file'] for v in S]:S.append({'file':fn,'url':url,'retrieved':'2026-10-23','sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
for i,s in enumerate(S):s['id']='S%02d'%(i+1)
(R/'references/sources.json').write_text(json.dumps(S,indent=2)+'\n');sid={v['file']:v['id'] for v in S}
C='S01 carrier STEP';SCH=sid['202003906_reServer_Industrial_J501_Carrier_Board_v1.0_SCH_PDF_20240529.pdf'];G='S04 GMSL schematic';N=sid['Jetson_AGX_Orin_Module_3D_STEP_Model.zip'];SAM=sid['samtec-qsh-qth.pdf'];A=sid['FM4-NZRP-PCB-1.stp']
def write(name,cols,rows):
 with (D/name).open('w',newline='') as f:
  w=csv.writer(f);w.writerow(cols);w.writerows(rows)
rows=[]
def add(key,value,status,source,check,limit='No physical measurement yet'):
 rows.append([f'M{len(rows)+1:03d}',key,json.dumps(value) if not isinstance(value,str) else value,'mm unless stated',status,source,check,limit])
def flatten(obj,prefix=''):
 for k,v in obj.items():
  key=prefix+'.'+k if prefix else k
  if isinstance(v,dict):yield from flatten(v,key)
  else:yield key,v
for k,v in flatten(P):
 status='design selection';source='cad/parameters.json + cad/build.py';check='Compare parameter to exported STEP; print a coupon for fits.';limit='Nominal CAD dimension; printer/material compensation not applied.'
 if k.startswith('user_inserts'):
  status='user supplied';source='User insert dimensions, 2026-10-23';check='Caliper actual insert maximum OD, starter OD and length.';limit='Approximate starter length 1 mm; kit manufacturer unspecified.'
 elif k.startswith('pcb.'):
  status='CAD derived';source=C+'; references/solids.json and mount-features.json';check='Measure board edges and mounting centers using the printed template.';limit='Mount centers from separate proxy solids, not drilled holes in the PCB solid. M3 hole/thread suitability is unconfirmed.'
 elif k=='cooler.size':
  status='manufacturer drawing; identity confirmed by user photos 2026-10-27';source='S06 G48R drawings (97 x 102 x 48.3 mm with the 92 x 15 fan) + S05 (110 x 100 x 50 mm kit) + 2 mm copper spreader';check='Measured 2026-10-27: PCB top to fan top about 68 mm (design keeps 70.0). Fan centre: on the module centre from the photo (ears on the module holes); the lid tolerates 3 mm.';limit='Fan centre from a photo with a fitted camera model (+/-3 mm). The 34 mm WS-RDN-601 is kept as cooler.alternatives (the Rev 0.8 cover fits it).'
 elif k=='cooler.agx_top_above_pcb_top':
  status='derived nominal';source=N+' + Molex 2048430001 drawing sheet 2';check='8 mm mated module PCB spacing + 11.18 mm module PCB-bottom to TTP top.';limit='Top of the AGX thermal plate = start of the heatsink standoff threads. Module revision not measured.'
 elif k=='cooler.tim_thickness':
  status='assumed';source='User: standard thermal pad between heatsink and AGX';check='Measure the fitted pad (compressed).';limit='Raises the heatsink and reduces the roof gap; does not change the tie-down screw length.'
 elif k.startswith('cooler.alternatives'):
  status='alternative part';source='S03 (WS-RDN-601) and the fan note';check='Pick the cover that matches the fitted cooler.';limit='Not the default build.'
 elif k.startswith('cooler.'):
  status='drawing / photo derived';source='S05, S06 and user photos IMG_1852-1854 (2026-10-27)';check='Measure the spreader outline and the finned bar height (photo: 100 x 111 mm spreader, bar at the front edge).';limit='No vendor CAD; plate thickness and the finned bar height are assumed.'
 elif k=='gmsl.board_size':
  status='manufacturer';source='S02 datasheet page 2';check='Measure GMSL outline 103 x 45.'
 elif k=='gmsl.stack_between_pcb_surfaces':
  status='manufacturer connector specification';source=G+' p7 + '+SCH+' p29 + '+SAM;check='QSH-030-01 + QTH-030-04 gives 16 mm facing-surface stack.';limit='Confirm fitted connector suffixes and seating.'
 elif k.startswith('gmsl.'):
  status='provisional assembly placement';source='S02, '+G+', '+A+', gmsl_connectoin.png; carrier solids 4822/4823';check='Measure XY from carrier left/front edges; verify actual support length and thread.';limit='Mount centers (27,16)/(114,37.2) are CAD-derived candidates. GMSL outline origin and mini-FAKRA XY are photo estimates.'
 elif k.startswith('ports.'):
  status='design service aperture';source='See docs/cutout-register.csv; basis field names the source solid';check='Hold the selected mating plug in the printed plate; overmold must pass the window.';limit='Overmold envelopes are typical values, not the user\'s cables.'
 elif k=='plug_envelopes_note':
  status='design rationale';source='cad/parameters.json';check='Measure actual cable overmolds.'
 elif k.startswith('openings.'):
  status='design service aperture';source='See docs/cutout-register.csv';check='Compare labeled panel drawing with actual connector mouth and selected mating plug.';limit='Apertures intentionally group close connectors; these are not automatic full-body bounding boxes.'
 elif k.startswith('opening_notes'):
  status='design rationale';source='docs/cutout-register.csv';check='Every panel window must map to populated hardware or explicit service access.'
 elif k.startswith('printer.'):
  status='user / manufacturer' if 'filament' not in k else 'unknown';source='User: Bambu Lab P1S; https://bambulab.com/en-us/p1p';check='Confirm centered plate placement and excluded printer regions in Bambu Studio.';limit='Nominal build volume is not a guarantee of printable brim or machine clearance.'
 add(k,v,status,source,check,limit)
for args in [('assembly.pcb_under_z',20,'derived','4 mm floor + 16 mm printed support','Measure floor to PCB underside.'),('assembly.pcb_top_z',21.578,'derived',C,'20 + source PCB thickness 1.578.'),('assembly.module_pcb_under_z',29.578,'derived',N+' + Molex drawing','21.578 + 8 mm mated stack.'),('assembly.cooler_seat_z',40.758,'derived',N,'29.578 + 11.18 mm TTP height; excludes actual TIM.'),('assembly.cooler_top_z',round(40.758+P['cooler']['tim_thickness']+P['cooler']['size'][2],3),'assumed stack','S03 + derived TTP',f"Seat + {P['cooler']['size'][2]:g} mm datasheet cooler."),('assembly.roof_inside_z',P['enclosure']['height']-P['enclosure']['roof_thickness'],'design','cad/build.py',f"{P['enclosure']['height']:g} overall - {P['enclosure']['roof_thickness']:g} mm hex roof."),('assembly.cooler_roof_gap',round(P['enclosure']['height']-P['enclosure']['roof_thickness']-(40.758+P['cooler']['tim_thickness']+P['cooler']['size'][2]),3),'derived nominal','design-metrics.json','Roof underside - cooler top; check the actual cooler.'),('assembly.gmsl_under_z',37.578,'derived nominal',SAM,'21.578 + 16.'),('assembly.gmsl_top_z',39.178,'assumed thickness',SAM,'37.578 + assumed 1.6 mm PCB.'),('assembly.gmsl_pcb_to_cooler_gap',1.58,'derived nominal only','cad parameters','40.758 - 39.178; excludes GMSL components and screw heads.'),('assembly.plan_overlap_y',4.5,'derived nominal','cad parameters','GMSL back y45 vs cooler front y40.5; inspect strip physically.'),('assembly.underside_to_floor',5.5,'CAD derived',C,'12 mm support minus 6.5 mm lowest component.'),('mount.external_slot_centers',[[20,-20],[186,-20],[20,213],[186,213]],'design','base_mount STEP','166 x 233 mm pattern in enclosure frame; 6.6 x 12 slots.'),('module.source_transform','Rz(-90), then translate (48.25,131.5,9.578) in PCB coordinates','CAD registration',N,'Four inner mount centers match the 92 x 79 pattern.'),('mini_fakra.source_transform','Rx(+90), translate (port_left+6,-3,17.578-6.65) in PCB coordinates','candidate registration',A,'Candidate standoff plane is raw Y=6.65; tails extend 2.1 above GMSL underside.')]:add(*args)
for key,value,check in [
 ('base.plan',[206,181],'Rounded R8 rectangle X0..206, Y5.5..186.5; nothing projects except the optional tabs.'),
 ('base.corner_posts','X0..14 and192..206; Y5.5..14.5 and177.5..186.5; Z0..72','Channels X10..14 / 192..196 hold the plate ends; 2.5 mm lip in front.'),
 ('front.channel','X10..196; Y8.0..11.5; Z4..72 (sill groove Z4..8)','Plate Y8.25..11.25; 0.25 mm per side.'),
 ('rear.channel','X10..196; Y180.5..184.0; Z4..72','Plate Y180.75..183.75.'),
 ('panel.extent','X10.25..195.75; Z4..71.8; thickness 3','Each end engages 3.75 mm; bottom 4 mm in the sill groove; lid ledges cover the top.'),
 ('side.hatch_notch','X202..206; Y76..118; Z12..72','45-degree V grooves (1.2 deep) in both sides and the bottom.'),
 ('side.hatch','X202..206; Y76.2..117.8; Z12.2..71.8','Flush with the wall; V tongues 1.0 deep; lid outer skin stops it lifting.'),
 ('joint.tongue_rebate','Tongue X2.3..3.7 (and mirror) Z72..76.5; lid rebate X2..4 Z72..77','Locates the lid on both side walls; 0.3 mm per side.'),
 ('cover.outline',f"X0..206; Y5.5..186.5; Z72..{P['enclosure']['height']:g}; walls 4; roof {P['enclosure']['roof_thickness']:g}",'Flush with the base; 1.5 roof chamfer; 0.6 reveal chamfers at the split.'),
 ('cover.fan_grille',f"Flush {P['enclosure']['fan_grille']['thickness']:g} mm grille over the fan (hub disc D{P['enclosure']['fan_grille']['hub_diameter']:g}, {P['enclosure']['fan_grille']['rings']} rings, {P['enclosure']['fan_grille']['spokes']} spokes); skirt {P['enclosure']['fan_grille']['skirt_wall']:g} mm, {P['enclosure']['fan_grille']['clearance']:g} mm outside the fan frame",'Fan top Z91.56, grille underside 2.44 mm above it; the skirt reaches 3.5 mm below the fan top and keeps the exhaust out of the intake.'),
 ('cover.roof_grille','Hex cells 10 A/F, 1.8 webs outside the fan skirt; the band next to the skirt is blind (1.2 mm top skin); fan-side inlet chamfer 0.6 x 1.0','Finger-safe; exhaust leaves well away from the fan intake.'),
 ('cover.vents','4 x 20 stadium slots, pitch 9, Z80..100; 13 per side, 17 per end','Same rhythm as base and plate vents.'),
 ('base.side_vents','4 x 28 stadium slots, pitch 9, Y42..150, Z28..56','Right side: three slots move onto the J17 hatch.'),
 ('panel.vents','3.6 x 20 slots, pitch 9, X31..175, Z46..66','Aligned with the cooler fin exits; 45-degree lead-ins.'),
 ('lid.fastening','4 x M3 x 16 socket head from the top at (8.8,30),(8.8,162),(197.2,30),(197.2,162)','Counterbore 6.4 to Z78; M3 x 10 insert in each base column; 10 mm engagement.'),
 ('cooler.tiedown','Columns D14 / landing D7.14 (pad body) at the 92 x 79 cooler holes; 3.4 clearance; D7 pocket from the floor to a 90-degree countersink seat at Z9.76','M3 x 35 flat head into the female standoffs between the AGX module and the heatsink: AGX top Z40.76 + 4 mm engagement - head face Z9.76 = 35. Floor ribs 3 x 3 tie columns to the board posts.'),
 ('rear.service_buttons','Two D1.6 pin holes at X157.91 (REC) and X167.54 (RST), Z25.58, with 0.8 x 45-degree lead-ins; inner sleeve D4.4 to Y178.35','SW1/SW2 Alps SKQJLBA010 right-angle switches (STEP SWITCH4-8X7X7MM), actuator tips at Y175.89; sleeve stops 0.35 mm short of the PCB edge. REC is nearest the USB/IO headers, RST nearest the far board edge (user).'),
 ('base.antenna_bulkheads','4 x D6.6 D-holes (flat on top, 6.0 across) at Z62: left wall Y46.5/145.5 (WIFI 1/2), right wall Y46.5/145.5 (CELL 1/2); inner spot face D12.5 to a 2.5 mm local wall','RP-SMA bulkhead pigtails, nut outside. In the fixed base so the lid, plates and J17 door still lift off.'),
 ('supports.landings','Board landings D6.9, cooler landings D7.14','Match the carrier STEP mount-pad bodies (solids 5155-5162); nearest underside part >= 4.14 mm from each hole centre.'),
 ('underside.cards','Mini PCIe (J13) and M.2 B (J11) stacked toward +Y; M.2 E (J14) toward -X','Envelopes in parameters.json underside_envelopes; supports relieved by 0.5 mm; see storage-checks.json for gaps.'),
 ('base.sata_drop','Floor opening under the vertical SATA (J21/J24) and PH 5 V power (J22/J23) headers','Plugs mate from below; cables drop into the storage chimney. P18 closes it without storage.'),
 ('storage.interface','M3 inserts in the 4 base column feet; M3 M-F standoffs clamp each tray 2 mm ledge','Standoff length = tray height - 2: 30 (3.5 in) / 20 (2.5 in). Any order, any count.'),
 ('mount.tabs','4 tabs 32 wide x 26 projection x 8 thick; slots 12 x 6.6 at X26/180, Y-9.5/201.5','45-degree gussets; 16 mm washer and 20 mm driver envelopes clear.'),
 ('assembly.slide_clearance','Front 0.37; rear 0.25 to carrier overall protrusion','Front plate back Y11.25 vs min component Y11.62; rear front Y180.75 vs max Y180.5.'),
 ('gmsl.visual_components','MAX96724:8x8x0.9 at X36/106,Y20; coils6.5x5.6x3.5 at X54/62/74/82,Y10/20','Package footprint sourced; coil height and all XY positions assumed. Not a complete populated board model.')]:
 add(key,value,'design or explicitly provisional detail','cad/build.py / cad/hardware.py; compare source inventory',check)
metrics=json.loads((R/'exports/design-metrics.json').read_text())
for key,value in flatten(metrics,'rev05'):
 add(key,value,'CAD measurement or design calculation','exports/design-metrics.json; tools/design_metrics.py','Check against current STEP and printed coupons; read metric limits.')
write('measurement-register.csv',['id','parameter','value','units','status','source','how_to_check','limitations'],rows)
# Mechanically relevant populated connector inventory, not a fabricated official BOM.
I=[]
def inv(ref,part,role,sheet,geometry,status,missing):I.append([ref,part,role,sheet,geometry,status,missing])
for a in [
('J2','YL032-100-002','2-way 5.08 mm screw-flange power header (pin 1 DCJ_IN 12-36 V via F1, pin 2 GND)','carrier 7','solid 2897; mate Phoenix MSTB 2,5/2-STF-5,08 envelope','Schematic identity; carrier body present; mate from Phoenix 1777989 drawing','Mated plug modelled and swept (port-checks.json). Pin 1 side inferred from F1 placement: verify polarity with a meter'),
('J5','LINK-PP LPJG16459BENL','1 GbE RJ45','carrier 11','solid 4650','Schematic identity; source body present','RJ45 plug + latch lever modelled and swept (port-checks.json); boot size assumed, check your cables'),
('J12','LINK-PP LPJK9436BENL','10 GbE RJ45','carrier 10','solid 4439','Schematic identity; source body present','Independent drawing download unsuccessful; RJ45 plug + latch lever modelled and swept (port-checks.json); boot size assumed'),
('CON1/CON2','MTEP43-205AAB-19305','3.5 mm audio output/input','carrier 28','solids 5106..5113 + shells 151/152','Schematic MPN differs from STEP library Cliff FC68125','Source geometry is a library surrogate; nose axis measured (z 4.578); D8 plug overmold assumed and swept (port-checks.json)'),
('J18','ST-SIM-SP132','Nano-SIM socket on front underside','carrier 18','solid 4848; STEP product SIM7_4P_13_1X13_5X1_55MM','Corrected identity; not USB-C','No external cutout; remove front panel for card service'),
('J25 / J2_TB1','YL032-096-020 / YL032-098-020','2x10 3.81 mm industrial terminal and mating plug','carrier 22','solid 4922 / source terminal assembly','Schematic identifies both sides','Mating plug/wires not separately modeled; measure projection and screwdriver access'),
('J8','Foxconn QJ3119C-WFB1-4F','Vertical HDMI','carrier 20','solid 4863; foxconn-QJ3119C-WFB1-4F.pdf','Source geometry + manufacturer drawing downloaded','Cable overmold unspecified'),
('J7','Foxconn UAA111C-84161-4H','Dual stacked USB-A','carrier 13','solids 5170..5175 + open shell 157','Restored full shell 15.67 wide, 19.398 overall Z incl pins','Drawing web-accessible; local download 403. Cable models missing'),
('J26','USB3.0 A TYPE (generic)','Vertical single USB-A','carrier 14','solid 5154 is only 3.81 mm high; footprint says 13.85 mm','Incomplete STEP placeholder identified','Exact MPN/model missing. Bronze-colored 13.85 mm corrected-height envelope added; verify actual mouth and shell'),
('J9','UBF31-2347-1','USB-C OTG on underside','carrier 15','solid 4819','Schematic + source geometry; ref mapping inferred from footprint','Mating cable and exact MPN vendor model missing'),
('J10','USB2.0 TYPE C LONG (generic)','USB-C debug on underside','carrier 15','solid 5137','Generic schematic identity; source body present','Exact MPN and cable overmold missing'),
('J17','Header2x10Pin2.54MM','Right-angle control/jumper header beside coin cell','carrier 21','solid 4867','2x10 2.54 mm; source model present','Jumper cap generic; verify pin numbering on hardware before configuring'),
('J15','4P 1.25 mm generic','5 V fan header','carrier 21','Full source STEP, not separately indexed','Schematic pitch only; do not infer JST compatibility','Exact family, mate and user cooler voltage/wiring'),
('J20 / J28','Samtec QSH-030-01-L-D-A','CSI/GMSL mezzanine sockets','carrier 29','solids 5114/5115; catalog','Exact schematic part; source lower halves present','Which socket mates to GMSL and upper part exact STEP need confirmation'),
('Module socket','Molex 2034560003','AGX Orin carrier connector','carrier STEP product name','solid 2149','Exact source name; counterpart 2048430001 in NVIDIA module','Mated stack from Molex sheet 2, 8 mm; standalone download timed out'),
('J14','2E0BC26-F20BE-7H','M.2 Key E','carrier 16','Full source STEP','Schematic MPN; installed board options unknown','Wi-Fi card, antenna pigtails, bulkheads and fastener models not selected'),
('J6','2E0BC26-F85BM-7H','M.2 Key M SSD','carrier 17','Full source STEP','Schematic MPN','Actual SSD/heatsink and retention hardware not selected'),
('J11','2E0BC21-S85BB-7H','M.2 Key B','carrier 18','Full source STEP','Schematic MPN','Modem, antenna and cable routing not selected'),
('J13','ST-PC-002','Mini PCIe','carrier 19','Full source STEP','Schematic MPN','Optional expansion module not selected'),
('J19','Header2x7 1.27 mm','Debug/internal','carrier 24','Full source STEP','Generic part','Exact mating harness not selected'),
('J33','ST-BF-254-025-2*5P','IDC 2x5','carrier 25','Full source STEP','Schematic MPN','Mating ribbon cable not selected'),
('J21/J24','JSATA-03A125','SATA data','carrier 27','Full source STEP','Schematic MPN','SATA drives and cable bend envelopes not selected; no drive bays in this scope'),
('J22/J23','PH4P2.0 (generic)','SATA power','carrier 27','Full source STEP','Pitch/family designation only','Do not assume generic PH naming proves manufacturer interchangeability'),
('J31','Header2x5 2.54 mm','Internal debug','carrier 30','Full source STEP','Generic part','No external aperture needed'),
('GMSL J1','Samtec QTH-030-04-L-D-A','GMSL mezzanine header','GMSL 7','Catalog-based 16 mm mating envelope','Exact schematic part; exact upper STEP not obtained','Local envelope and socket choice provisional; no connector purchase required'),
('GMSL J2/J3','FAKRA min; candidate Amphenol FM4-NZRP-PCB-1','Two quad mini-FAKRA housings','GMSL 6','Downloaded Amphenol STEP + drawing','Exact candidate geometry; Seeed MPN NOT confirmed','Confirm key/color/manufacturer and camera-side latch/boot/bend envelope'),
('GMSL J4','Header2x5 2.54 mm','Optional header','GMSL 7','Not modeled; schematic generic','Population and XY unconfirmed','Check actual board; add keepout if populated'),
('GMSL U1/U5','MAX96724RGTNV','Deserializer ICs','GMSL 4/5','8x8x0.9 package envelopes','Schematic package dimensions; XY photo estimate','Exact package CAD and component XY layout absent'),
('GMSL L4/L5/L8/L11/L14/L17/L20/L23','SPM0635-151M','150 uH PoC inductors','GMSL 6','6.5x5.6 footprint; assumed 3.5 height','Package footprint from schematic; placement/height provisional','Exact supplier drawing and populated height missing'),
('GMSL PoC small inductors','AWL3225FP220MTF / PFL1005-561MRW','22 uH and 560 nH filters','GMSL 6','Not individually modeled','Schematic MPNs','Not a complete electrical BOM; no placement file available'),
('GMSL factory mounting kit','Unspecified supplied copper/brass supports and screws','Retains addon to carrier','Seeed installation photo','Two 16 mm support proxies at candidate CAD centers','Preserve existing parts; M3 depiction assumed','Measure thread, seat-to-seat length, washer and support OD'),
('Cooler','Seeed reComputer mini J501 heatsink with fan (100099421; G48R tower + 9215 fan)','110x100 mm 2 mm copper spreader, 6.8 mm M3 F-F standoffs, 5 x D6 heat pipes, 84x93x33.3 mm Al fins, 92x92x15 mm 12 V fan; 50.3 mm overall','100099421.pdf (S05); reComputer_Mini_J501_Fan.pdf (S06)','Datasheet geometry: spreader, standoffs, pipes, fin stack, octagonal fan frame; compact thermal model','Identity confirmed from the user\'s photos (2026-10-27); centred on the module (ears on the module holes); fan top measured about 68 mm over the PCB','Standoff thread depth and short-screw length'),
('Cooler (alternative)','Seeed heatsink with fan for reServer J501 (p-5970, WS-RDN-601)','100x87x34 mm: copper base, 3 heat pipes, stacked Al fins, 8015 5 V fan','323011387Jetson_AGX_Orin_Heatsink_100x87x34mm-datasheet.pdf (S03)','cooler.alternatives.ws_rdn_601; fits the Rev 0.8 cover','Datasheet only','Not the fitted cooler; it fits under the Rev 0.9 lid (ribs end at Z85.5, cooler top about Z75), airflow not simulated')]:inv(*a)
write('connector-inventory.csv',['reference','part_number_or_description','function','schematic_sheet','model_or_geometry','evidence_status','missing_or_required_check'],I)
B=[]
def bom(*a):B.append(a)
for a in [('P1','base','1 (desktop, and always with storage trays)','Printed','206x181x72 (+4.5 tongue); R8 corners; cooler columns','Print floor down'),
('P1M','base_mount','1 wall/robot without storage, instead of P1','Printed','206x233x76.5 print envelope; four 8 mm tabs','Print floor down; 11.5 mm Y margin on P1S'),
('P2','cover','1','Printed','206x181x40; hex roof; four counterbores','Print roof down'),
('P3','front_gmsl','1 if GMSL fitted','Printed','185.5x67.8x3','Print exterior face down'),
('P4','front_no_gmsl','1 if no GMSL','Printed','185.5x67.8x3','Print exterior face down'),
('P5','rear_io','1','Printed','185.5x67.8x3','Print exterior face down'),
('P10','side_hatch','1','Printed','41.6x59.6x4 + V tongues','Print exterior face down'),
('P9','mount_fit_template','1 (tool)','Printed','Cradle jig, 12 mm tall: same supports, pad-sized landings and underside relief as P1, on a 3 mm frame','Set the bare carrier on it face up; every landing must sit flat on its pad with no component touching. Then check the cooler pattern'),
('P11','m3_insert_coupon','1 (test)','Printed','3.7-4.1 pilots','Pick the pilot that retains the insert'),
('P12/P13','rail_coupon / rail_key','1 each (test)','Printed','3.5 channel / 3.0 key','Must slide without rattle'),
('P14','countersink_coupon','1 (test)','Printed','Floor + column with the raised D7.0 / D7.4 seats','The M3 x 35 head must seat on the cone at Z9.76'),
('P20','rpsma_coupon','1 (test)','Printed','2.5 mm antenna wall with D-holes 5.9 / 6.0 / 6.1 / 6.2 across the flat','Use the tightest the bulkhead flat still pushes into; set antenna_bulkheads.across_flat'),
('H1','M3 x 10 heat-set insert','8 (4 board + 4 lid)','User kit','4.2 body / 3.75 starter','Install before electronics'),
('H3','M3 x 16 ISO 4762 socket head','4','Purchase','Lid screws','2.5 mm hex, 40 mm reach'),
('H5','M3 x 10 ISO 7380 button head','4','Purchase','Board screws','8.4 mm engagement'),
('H7','M3 x 35 flat head, DIN 7991 / ISO 10642, A2','4','Purchase','Up through the floor pocket, board, module and copper spreader into the bottom of the cooler\'s 6.8 mm F-F standoffs',f'Raised countersink seat at Z{b.HS_HEAD_Z:.2f} gives {b.e["heatsink_thread_engagement"]:g} mm ({b.e["heatsink_thread_engagement"]/0.5:.0f} threads) of engagement and leaves {b.c["standoffs"]["height"]-b.e["heatsink_thread_engagement"]:.1f} mm for the short screws from the heatsink ears'),
('H10','RP-SMA female bulkhead pigtail (1/4-36 thread) to U.FL/MHF4 as the radio needs','4 (2 Wi-Fi + 2 cellular)','Purchase','D6.6 hole with a 6.0 mm flat (the thread milled flat stops it turning); 2.5 mm local wall; 8 mm nut + lock washer outside','Insert from inside; thread must cover 2.5 mm wall + washer + nut + about 4 mm for the antenna'),
('P15','storage_35 (3.5 in tray)','0-2','Printed','206x181x32; one SFF-8301 drive; 12V IN D8 hole','Print floor down; stack in any order'),
('P16','storage_25 (2.5 in tray)','0-2','Printed','206x181x22; two SFF-8201 drives up to 15 mm','Print floor down'),
('P17','storage_mount_plate','1 for wall/robot with storage','Printed','206x233x8 frame with P1M tabs','Replaces P1M when trays are fitted'),
('P18','chimney_cap','1 without storage','Printed','Plugs the base SATA drop opening','Flange flush in the 0.8 mm recess'),
('H11','M3 x 10 heat-set insert (stacking)','4 with storage','User kit','Into the base column feet from below','Same insert as H1'),
('H12','M3 male-female hex standoff, 5.5 AF, 6 mm male','4 per tray','Purchase','M3 x 30 for storage_35; M3 x 20 for storage_25','Hangs from the part above; its female end rests on the tray ledge and takes the next standoff or the H14/H15 screw'),
('H13a','6-32 UNC x 3/16 in pan head','4-6 per 3.5 in drive','Purchase','SFF-8301 bottom holes (A7 pair + A6 or A13)','2.86 mm penetration (spec 2.39-3.56)'),
('H13b','M3 x 4 ISO 7380 button head','4 per 2.5 in drive','Purchase','SFF-8201 bottom holes','1.7 mm penetration (spec max 2.5). 7 mm drives may lack bottom holes'),
('H14','M3 x 12 ISO 4762 socket head','4 with P17','Purchase','Up through P17 and the bottom tray ledge into its standoffs','4 mm (8 threads) into the female thread'),
('H15','M3 x 6 ISO 7380 button head','4 without P17','Purchase','Up through the bottom tray ledge into its standoffs','4 mm (8 threads) into the female thread; closes the stack'),
('P19','ssd_clip','4 per 7 mm SSD without bottom holes','Printed','10 x 11 x 10.5 L-clip, captive M3 nut, slotted foot','Same part on either side (rotate 180 degrees)'),
('H16','M3 x 6 ISO 7380 button head + M3 hex nut','4 + 4 per clip-mounted SSD','Purchase','Floor screw into the captive nut in each P19 clip','Uses the tray 2.5 in bottom holes'),
('H17','M3 x 5 ISO 7380 button head','4 per clip-mounted SSD','Purchase','Through the clip wall into the drive side hole','2.0 mm penetration = SFF-8201 max for 7 mm drives'),
('C1','SATA data cable, straight plug at the board end, slim round or foldable','1 per drive (2 ports)','Purchase','300-450 mm (2-tray stack); bend radius >= 12 mm assumed','Front SATA connector to the 3.5 in drive, rear to a 2.5 in drive; never crease'),
('C2','JST PH 2.0 4-pin to SATA 15-pin power lead','1 per 2.5 in drive','Purchase or make','Board SATA_5V only','Confirm the PH pinout on the board before wiring'),
('C3','12 V supply for 3.5 in drives: 8 mm panel DC jack + 12 V-to-SATA power adapter (with 5 V regulator)','1 per 3.5 in drive','Purchase','Mounts in the storage_35 12V IN hole','Do not feed raw 12-36 V DC-IN to drives unless the supply is 12 V'),
('-','Pin tool: SIM eject tool or paper clip, D<=1.2','1','Any','Reaches the reset / recovery switches through the rear plate','No printed part'),
('-','Rubber bumper D<=12 x 1 recess','4 optional','Purchase','Desktop feet','Pockets at the four corners'),
('-','M6 mounting screws + D16 washers','4 for P1M','Site-specific','Through 6.6 slots','Length and anchors depend on the surface')]:bom(*a)
write('BOM.csv',['id','part','quantity','supply','dimensions_or_specification','notes'],B)
cut=[]
for side,ports in P['ports'].items():
 for name,v in ports.items():
  cut.append([side+'.'+name,'current (GMSL plate only)' if v.get('gmsl_only') else 'current',json.dumps(v['box'])+' r'+str(v['r']),'PCB datum X/Z; add enclosure [15,20]',(v.get('label') and 'Legend "'+v['label']+'". ' or '')+v['basis']])
cut += [['front_sim','no opening','none','front underside','Nano-SIM J18: remove the front plate for card service.'],['side_hatch','current','Y76..118; Z12..72 wall notch','enclosure datum','J17 access door, flush with the wall.'],['vents','current','see measurement register','enclosure datum','Lid, base, hatch and plate vents on one 9 mm rhythm.']]
write('cutout-register.csv',['opening','status','bounds','coordinate_frame','purpose'],cut)
F=[('P1/P1M','Floor and walls','4 mm floor / 4 mm walls / R8 corners','Floor down; all features rise from the floor','Floor ribs and posts stiffen the floor'),
('P1/P1M','Board supports','16 mm body / 6.9 mm pad-sized land / M3 insert','Vertical; relief for underside parts','Unchanged concept from Rev 0.4'),
('P1/P1M','Cooler tie-down columns','14 mm body / 7.14 mm pad-sized land / 3.4 hole / D7 pocket to a raised 90-degree countersink seat','The countersink narrows upward at 45 degrees inside the column, so it prints without support','Carries the cooler mass into the floor; screw length to be confirmed'),
('P1/P1M','Lid columns','10 mm columns merged into the side walls, M3 insert at Z72','Vertical','Accessible with the base bolted down'),
('P1/P1M','Plate channels','3.5 mm channels in corner posts and sill','Vertical slots print cleanly','Rail coupon P12/P13 first'),
('P1/P1M','J17 notch','V grooves 1.2 deep','45-degree flanks; 2 mm2 groove-end ceilings','Hatch prints flat with V tongues'),
('P1/P1M','Antenna bulkhead holes','4 x D6.6 D-holes with D12.5 inner spot face','The flat is on top: a 3.8 mm bridge in place of a teardrop roof; the spot face keeps its teardrop','Base stays the fixed chassis; nothing tethers the lid or plates'),
('P5','Service pin holes','D1.6 + 45-degree lead-in, D4.4 inner guide sleeve 2.4 long','Holes vertical in print; sleeve grows from the plate','Plate slide-in sweep checked against the carrier'),
('P15/P16','Storage trays','3 mm floor/walls, R8, standoff columns D11 with 6.6 bore and 2 mm ledge, SFF hole pads, rails, chimney, tie anchors','Floor down; ledge underside is a 1.6 mm annular bridge; screw counterbores print on the bed face','Drive screws recess in counterbores so trays stack flat'),
('P17','Storage mount plate','8 mm frame + P1M tabs','Floor down; gussets trimmed at the tray outline','Carries the whole stack on wall/robot'),
('P1/P1M','Foot pockets','D12 x 1','12 mm round bridge 1 mm above bed','Optional bumpers'),
('P2','Hex roof','216 cells, 10 A/F, 1.8 webs, 6 deep; 0.6 x 1.0 fan-side inlet chamfer','Roof on bed; every web grows from the bed and the chamfer narrows the web tops, so it is not an overhang','Finger-safe; 0.6 mm web land at the top of the print; whole-lid stiffness and airflow untested'),
('P2','Ledges and rebates','45-degree chamfered ledges over plates','Self-supporting in roof-down orientation','Ledges stop the plates lifting'),
('P3/P4/P5','Windows','One rounded window per connector group; 0.6 x 45-degree lead-in','Exterior on bed; lead-in is a 45-degree bed chamfer','Sized to plug overmolds where they enter'),
('P3/P4/P5','Legends','3.6 mm DejaVu Sans Bold, 0.5 deep','Debossed into the bed face','Read from outside'),
('ALL VENTS','Stadium slots','4 mm wide, r2 ends','2 mm-radius arches bridge trivially','Same 9 mm rhythm everywhere'),
('P1M','Tabs','32 x 26 x 8, R6, 45-degree gussets','Floor down','16 mm washer + 20 mm driver envelopes clear')]
write('feature-review.csv',['part','feature','geometry','printability_review','decision_or_limit'],F)
# Evidence index and useful public model search outcomes.
write('model-search.csv',['item','result','source','next_check'],[
 ['Seeed official carrier BOM','No standalone assembly BOM found in linked product/wiki resources or OSHW repository tree','Seeed-Studio/OSHW-Jetson-Series; references/seeed-oshw-tree.json','Schematic-derived inventory is not an official procurement BOM'],
 ['Carrier STEP','5176 solids + 158 open shells; preserve both','S01','4 zero-thickness pseudo-solids and 8 mounting proxies require special handling'],
 ['NVIDIA module','Exact simplified STEP downloaded; version 20230131',N,'Confirm user module revision'],
 ['Mini-FAKRA','Amphenol exact candidate STEP + drawing downloaded',A,'Dimensions match footprint; MPN identity still unknown'],
 ['GMSL full STEP','Not found in official resources or relevant repository folder',G,'Need actual board measurements or vendor model'],
 ['Cooler complete STEP','Not found; modelled from the S05/S06 datasheets and photos','S03/S05/S06','Identity confirmed; fan top measured (about 68 mm over the PCB)'],
 ['Samtec QTH','Catalog and exact schematic suffix found; standalone 3D download not obtained',SAM,'Use 16 mm stack envelope only'],
 ['Single USB-A J26','Placeholder source extrusion does not match 13.85 mm footprint height',C,'Measure or obtain exact MPN/model before final rear plate'],
 ['Audio jacks','Source library surrogate differs from schematic MPN',SCH+' page 28','Measure mouth centers and actual plug barrels'],
 ['Mating cables / terminal plugs','Exact user parts not selected','Connector inventory','Boot, latch release, screwdriver and bend clearances must be checked']])
sections=[]
for name,title in [('BOM.csv','Enclosure bill of materials'),('fastener-sources.csv','Fastener supplier references and model fidelity'),('cutout-register.csv','Every cutout and its purpose'),('feature-review.csv','Feature-by-feature manufacturing review'),('connector-inventory.csv','Schematic-derived connector and component inventory'),('model-search.csv','Model search results and missing geometry'),('measurement-register.csv','Measurements, assumptions and checks')]:
 with (D/name).open() as f:table=list(csv.reader(f))
 rows_html=''.join('<tr>'+''.join('<td>'+html.escape(x)+'</td>' for x in row)+'</tr>' for row in table[1:])
 sections.append('<section><h2>'+title+'</h2><a href="'+name+'">CSV</a><div class="scroll"><table><thead><tr>'+''.join('<th>'+html.escape(c)+'</th>' for c in table[0])+'</tr></thead><tbody>'+rows_html+'</tbody></table></div></section>')
sources=''.join(f'<li id="{x["id"]}">{x["id"]}: <a href="../references/{html.escape(x["file"])}">{html.escape(x["file"])}</a> · <a href="{html.escape(x["url"])}">source URL</a></li>' for x in S)
(D/'engineering-review.html').write_text('''<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>J501 engineering review</title><style>body{font:15px system-ui;color:#17303e;background:#edf2f5;margin:24px}h1{font-size:30px}section{background:white;padding:20px;margin:24px 0;border-radius:8px}.scroll{overflow:auto}table{border-collapse:collapse;min-width:1000px}td,th{text-align:left;border-bottom:1px solid #ddd;padding:10px;vertical-align:top}th{background:#dce9ee}input{padding:12px;width:min(700px,90%);font:inherit}a{color:#007782}li{margin:10px}</style><h1>J501 · Rev '''+P['revision']+''' engineering review</h1><p><a href="../preview/">Previews</a> · <a href="check-sheet.pdf">Dimensioned check sheets</a> · <a href="../README.md">Assembly and limits</a></p><p>FIT-CHECK PROTOTYPE. Values are explicitly classified; CAD validity is not physical fit or thermal/vibration qualification. No official standalone Seeed assembly BOM was found.</p><input id="q" placeholder="Filter every table: J17, assumed, cooler, M3, USB…">'''+''.join(sections)+'<section><h2>Source cross references</h2><ol>'+sources+'</ol></section><script>document.querySelector("#q").oninput=e=>{let q=e.target.value.toLowerCase();document.querySelectorAll("tbody tr").forEach(r=>r.hidden=!r.textContent.toLowerCase().includes(q))}</script>')
print(len(rows),'measurement entries;',len(I),'inventory rows;',len(B),'BOM rows')
