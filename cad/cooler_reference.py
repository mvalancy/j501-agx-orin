"""Cooler reference components for the fit study (tools/cooler_fit_review.py).

There is one cooler model: hardware.cooler_and_module(), sized from cad/parameters.json "cooler". This module only
groups its parts into named components, adds board context and builds the keep-out volumes the study tests the lid
against. Pipe bends, plates, blades and the mounting ears are original approximations, not a CFD mesh or drawings.
"""
from pathlib import Path
import math, sys
import cadquery as cq

R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / 'cad'))
import build as b  # noqa: E402
import hardware as h  # noqa: E402

C, E, B, M = b.c, b.e, b.p, b.M
SPREADER_Z = b.COOLER_SEAT
CONTACT_Z = SPREADER_Z + C['spreader']['thickness']
FAN_Z = b.FAN_TOP - C['fan']['thickness']
TOP = b.FAN_TOP
CX, CY = b.fan_centre()
# hardware.cooler_and_module() label prefix -> study component
GROUPS = {
    'spreader': ('E3 copper heat spreader', 'E3 spreader finned bar'),
    'cold_plate': ('E3 heatsink copper base',),
    'heat_pipes': ('E3 heat pipe',),
    'fins': ('E3 aluminium plate',),
    'fan_frame': ('E3 fan frame',),
    'fan_rotor': ('E3 fan hub', 'E3 fan blade'),
    'spacers': ('E3 standoff',),
    'mount_ears_provisional': ('E3 mounting ear',),
}
CONTEXT = ('module_axes_reference', 'pcb_reference', 'agx_reference')
COLORS = {
    'spreader': '#bb743e', 'cold_plate': '#c98a5a', 'heat_pipes': '#d4b896', 'fins': '#929ca3', 'fan_frame': '#303b46',
    'fan_rotor': '#111a23', 'spacers': '#d9b062', 'mount_ears_provisional': '#ac9e8b',
    'module_axes_reference': '#bd55bb', 'pcb_reference': '#347857', 'agx_reference': '#5d6970',
}


def compound(shapes):
    return cq.Compound.makeCompound(shapes)


def parts():
    items = h.cooler_and_module()
    out = {}
    for name, prefixes in GROUPS.items():
        out[name] = compound([s for label, s, _ in items if label.startswith(prefixes)])
    out['module_axes_reference'] = compound(
        [b.cyl(M + x, M + y, b.AGX_TOP - 4, 0.55, 18) for x, y in B['module_mount_centers']])
    pcb = b.box(M, M, b.Z, B['width'], B['depth'], B['thickness'])
    for x, y in B['mount_holes'] + B['module_mount_centers']:
        pcb = pcb.cut(b.cyl(M + x, M + y, b.Z - 1, 1.75, 4))
    out['pcb_reference'] = pcb
    out['agx_reference'] = compound([s for label, s, _ in items if label.startswith('E2')])
    return out


def keepouts(shift=(0.0, 0.0), conservative=False):
    """Occupied volumes the lid must clear: the fan frame (octagon; the S06 table's 95 mm size when conservative) and
    the heat-pipe/plate block below it, moved by `shift` (photo-registration uncertainty)."""
    f, hs = C['fan'], C['heatsink']
    grow = (f.get('frame_conservative', f['frame']) - f['frame']) / 2 if conservative else 0.0
    fan = b.prism_z(b.fan_outline(grow, shift), FAN_Z, f['thickness'])
    sx, sy = hs['pipe_span_x'], hs['fins'][1]
    sink = b.box(CX + shift[0] - sx / 2, CY + shift[1] - sy / 2, CONTACT_Z, sx, sy, FAN_Z - CONTACT_Z)
    return {'fan': fan, 'heat_sink': sink}


def shifts(u=None):
    u = C.get('fan_xy_uncertainty', 0.0) if u is None else u
    return [(0.0, 0.0)] + [(round(u * math.cos(math.radians(a)), 3), round(u * math.sin(math.radians(a)), 3)) for a in range(0, 360, 45)]
