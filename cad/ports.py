"""Panel windows derived from the mated plug of each port (cadagent.connectors).

Panel frame per side: u = PCB x, v = height above the PCB underside, w = outward along the mating axis
(front: w = -PCB y, rear: w = +PCB y). A port with a 'mate' spec gets its 'box' computed here; a port without
one (LED light pipes, the provisional GMSL mouths) keeps its hand-set 'box'.
"""
from cadagent.connectors import window, PanelFrame

def wall_w(P,side):
    # Span of the plate along w, from its inner face to its outer face.
    e,M=P['enclosure'],P['enclosure']['pcb_margin'];PT=e['panel_thickness']
    if side=='front':return (M-(e['front_panel_y']+PT),M-e['front_panel_y'])
    return (e['rear_panel_y']-M,e['rear_panel_y']+PT-M)

def frame(P,side):
    e=P['enclosure'];M=e['pcb_margin'];Z=e['floor']+e['board_support_height']
    return PanelFrame((M,M,Z),(1,0,0),(0,0,1),(0,-1,0) if side=='front' else (0,1,0))

def resolve(P):
    # Fill each mated port's window in place; returns P for chaining.
    for side,ports in P['ports'].items():
        for v in ports.values():
            if 'mate' in v:v['box']=window(v['mate'],wall_w(P,side))
    return P
