"""Separate G48R reference assembly. Does not select a cooler for the enclosure builder.
Detailed solids support visual/fit review; fin/pipe/blade shapes are not a CFD mesh.
"""

from pathlib import Path
import json, math
import cadquery as cq

R = Path(__file__).resolve().parents[1]
P = json.loads((R / "cad/parameters.json").read_text())
Q = json.loads((R / "cad/cooler-profiles.json").read_text())
G = Q["mini_g48r"]
E = P["enclosure"]
B = P["pcb"]
C = P["cooler"]
M = E["pcb_margin"]
BOARD_Z = E["floor"] + E["board_support_height"]
AGX_TOP = BOARD_Z + B["thickness"] + C["agx_top_above_pcb_top"]
SPREADER_Z = AGX_TOP + C["tim_thickness"]
CONTACT_Z = SPREADER_Z + G["spreader_thickness"]
FAN_Z = CONTACT_Z + G["cooler_contact_to_fin_top"]
TOP = FAN_Z + G["fan_height"]
CX, CY = [x + M for x in G["fan_center_in_pcb"]]
COLORS = {
    "spreader": "#bb743e",
    "cold_plate": "#aebbc1",
    "heat_pipes": "#d4b896",
    "fins": "#929ca3",
    "fan_frame": "#303b46",
    "fan_rotor": "#111a23",
    "spacers_provisional": "#d9b062",
    "mount_brackets_provisional": "#ac9e8b",
    "module_axes_reference": "#bd55bb",
    "pcb_reference": "#347857",
    "agx_reference": "#5d6970",
}


def box(x, y, z, dx, dy, dz):
    return cq.Solid.makeBox(dx, dy, dz, cq.Vector(x, y, z))


def cyl(x, y, z, r, h):
    return cq.Solid.makeCylinder(r, h, cq.Vector(x, y, z))


def compound(shapes):
    return cq.Compound.makeCompound(shapes)


def rounded(x, y, z, dx, dy, dz, r):
    return cq.Workplane(obj=box(x, y, z, dx, dy, dz)).edges("|Z").fillet(r).val()


def pipe(y, flip):
    # Five nickel-plated 6 mm pipes: original approximate U paths, with rounded
    # bends. The actual factory bend coordinates are not provided by S06.
    rr = 11.65
    turn = 36.35
    path = (
        cq.Workplane("XZ")
        .moveTo(-25, 3)
        .lineTo(turn, 3)
        .threePointArc((48, 3 + rr), (turn, 3 + 2 * rr))
        .lineTo(-48, 3 + 2 * rr)
        .wire()
        .val()
    )
    pl = cq.Plane(origin=(-25, 0, 3), xDir=(0, 1, 0), normal=(1, 0, 0))
    s = (
        cq.Workplane(pl)
        .circle(G["heat_pipe_diameter"] / 2)
        .sweep(path, isFrenet=True)
        .val()
    )
    if flip:
        s = s.rotate((0, 0, 0), (0, 0, 1), 180)
    return s.translate((CX, y, CONTACT_Z))


def parts():
    out = {}
    px, py = [x + M for x in G["spreader_center_in_pcb"]]
    sx, sy = G["spreader_visual_xy"]
    plate = rounded(
        px - sx / 2, py - sy / 2, SPREADER_Z, sx, sy, G["spreader_thickness"], 3
    )
    # Both hole patterns are provisional references on the plate; do not machine
    # this plate. The existing module axes remain separately visible in magenta.
    lx, ly = [x + M for x in G["cooler_lug_center_photo"]]
    dx, dy = G["cooler_lug_pattern_photo"]
    lugs = [(lx + a * dx / 2, ly + b * dy / 2) for a in [-1, 1] for b in [-1, 1]]
    for x, y in lugs:
        plate = plate.cut(cyl(x, y, SPREADER_Z - 1, 1.7, 4))
    out["spreader"] = plate
    out["cold_plate"] = rounded(CX - 20, CY - 19, CONTACT_Z, 40, 38, 5, 2)
    out["heat_pipes"] = compound(
        [pipe(CY + y, i % 2) for i, y in enumerate([-24, -12, 0, 12, 24])]
    )
    fx, fy = G["fin_pack_visual_xy"]
    pitch = G["fin_pitch_visual"]
    zf = CONTACT_Z + G["fin_start_above_contact"]
    fins = [
        box(
            CX - fx / 2 + i * pitch,
            CY - fy / 2,
            zf,
            G["fin_thickness_visual"],
            fy,
            FAN_Z - zf,
        )
        for i in range(int(fx / pitch) + 1)
    ]
    out["fins"] = compound(fins)
    wx, wy = G["fan_frame_xy"]
    frame = rounded(CX - wx / 2, CY - wy / 2, FAN_Z, wx, wy, G["fan_height"], 7)
    frame = frame.cut(cyl(CX, CY, FAN_Z - 1, 44.5, G["fan_height"] + 2))
    out["fan_frame"] = frame
    hub = cyl(CX, CY, FAN_Z + 3, G["fan_hub_diameter"] / 2, 9)
    blades = []
    for angle in range(0, 360, 30):
        # Curved swept plan blades, visual only; no aerodynamic pitch claim.
        blade = (
            cq.Workplane("XY")
            .moveTo(14, -3)
            .threePointArc((29, -5), (43, -13))
            .threePointArc((43, -3), (38, 6))
            .threePointArc((25, 9), (14, 3))
            .close()
            .extrude(1.1)
            .val()
        )
        blades.append(
            blade.rotate((0, 0, 0), (0, 0, 1), angle).translate((CX, CY, FAN_Z + 7))
        )
    out["fan_rotor"] = compound([hub, *blades])
    out["spacers_provisional"] = compound(
        [
            cyl(x, y, CONTACT_Z, 2, 6.8).cut(cyl(x, y, CONTACT_Z - 1, 1.25, 9))
            for x, y in lugs
        ]
    )
    brackets = []
    for x, y in lugs:
        # Four separately identified guessed adapter lugs connect to the cooler;
        # generic 75/78 mm Intel brackets are deliberately not passed off as J501.
        ex = CX + (-18 if x < CX else 18)
        ey = CY + (-14 if y < CY else 14)
        length = math.hypot(ex - x, ey - y)
        angle = math.degrees(math.atan2(ey - y, ex - x))
        bar = (
            box(0, -4, 0, length, 8, 1.5)
            .fuse(cyl(0, 0, 0, 4, 1.5))
            .cut(cyl(0, 0, -1, 1.7, 4))
        )
        brackets.append(
            bar.rotate((0, 0, 0), (0, 0, 1), angle).translate((x, y, CONTACT_Z + 6.8))
        )
    out["mount_brackets_provisional"] = compound(brackets)
    out["module_axes_reference"] = compound(
        [cyl(M + x, M + y, AGX_TOP - 4, 0.55, 18) for x, y in B["module_mount_centers"]]
    )
    pcb = box(M, M, BOARD_Z, B["width"], B["depth"], B["thickness"])
    for x, y in B["mount_holes"] + B["module_mount_centers"]:
        pcb = pcb.cut(cyl(M + x, M + y, BOARD_Z - 1, 1.75, 4))
    out["pcb_reference"] = pcb
    ax, ay = [v + M for v in C["center_in_pcb"]]
    module_bottom = BOARD_Z + B["thickness"] + 8
    out["agx_reference"] = box(
        ax - 50, ay - 43.5, module_bottom, 100, 87, AGX_TOP - module_bottom
    )
    return out


def keepouts():
    sx, sy = G["heatsink_envelope_xy"]
    wx, wy = G["fan_conservative_xy"]
    return {
        "heat_sink": box(
            CX - sx / 2, CY - sy / 2, CONTACT_Z, sx, sy, G["cooler_contact_to_fin_top"]
        ),
        "fan": box(CX - wx / 2, CY - wy / 2, FAN_Z, wx, wy, G["fan_height"]),
    }
