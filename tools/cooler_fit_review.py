#!/usr/bin/env python3
"""Build an isolated cooler reference and fit study; never rebuild the enclosure/CFD."""

from pathlib import Path
import sys, json, hashlib, math
from types import SimpleNamespace
import cadquery as cq

R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / "cad"))
import cooler_reference as c
from cadagent.view import export_view
from cadagent.render import Renderer

OUT = R / "exports/cooler-study"
OUT.mkdir(parents=True, exist_ok=True)


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def bounds(s):
    b = s.BoundingBox()
    return [round(x, 4) for x in [b.xmin, b.ymin, b.zmin, b.xmax, b.ymax, b.zmax]]


def main():
    pieces = c.parts()
    metrics = {}
    for name, s in pieces.items():
        path = OUT / f"{name}.step"
        cq.exporters.export(s, str(path))
        read = cq.importers.importStep(str(path)).val()
        metrics[name] = {
            "valid": read.isValid(),
            "solid_count": len(read.Solids()),
            "volume_mm3": round(read.Volume(), 4),
            "bounds_mm": bounds(read),
        }
        assert read.isValid() and read.Volume() > 0, name
    print("reference solids exported/read back", flush=True)
    cq.exporters.export(
        c.compound(list(pieces.values())), str(OUT / "g48r-reference.step")
    )
    # The old low-profile model remains available as a separate envelope.
    old = c.Q["ws_rdn_601"]
    ox, oy = [x + c.M for x in old["fan_center_in_pcb"]]
    sx, sy, sz = old["size"]
    legacy = c.box(ox - sx / 2, oy - sy / 2, c.SPREADER_Z, sx, sy, sz)
    cq.exporters.export(legacy, str(OUT / "ws-rdn-601-envelope.step"))
    E = c.E
    roof = E["height"] - E["roof_thickness"]
    rib = roof - E["roof_ribs"]["depth"]
    ring = c.SPREADER_Z + c.C["size"][2] + E["fan_duct"]["gap_above_cooler"]
    required = max(
        c.TOP + 2 + c.G["height_stack_uncertainty"] - z for z in [roof, rib, ring]
    )
    recovery = math.ceil(required)
    # Test the actual committed cover with conservative occupied volumes. Compare
    # nominal placement against a +/-3 mm XY, +2 mm height uncertainty envelope.
    coverpath = R / "exports/cover.step"
    cover = cq.importers.importStep(str(coverpath)).val()
    nominal = c.keepouts()
    grow = c.G["photo_xy_uncertainty"]
    uncertain = {}
    for name, s in nominal.items():
        b = s.BoundingBox()
        uncertain[name] = c.box(
            b.xmin - grow,
            b.ymin - grow,
            b.zmin,
            b.xlen + 2 * grow,
            b.ylen + 2 * grow,
            b.zlen + c.G["height_stack_uncertainty"],
        )
    trials = []
    for lift in [0, 15, recovery]:
        moved = cover.translate((0, 0, lift))
        row = {"lid_lift_mm": lift, "nominal": {}, "uncertainty_envelope": {}}
        for label, items in [("nominal", nominal), ("uncertainty_envelope", uncertain)]:
            for name, s in items.items():
                vol = moved.intersect(s).Volume()
                gap = moved.distance(s)
                row[label][name] = {
                    "intersection_mm3": round(vol, 4),
                    "minimum_gap_mm": round(gap, 4),
                }
        trials.append(row)
        print("cover trial", lift, json.dumps(row), flush=True)
    # Geometric height floor with new ribs outside the cooler footprint and a
    # relocated inlet: not a completed lid, structural result or flow guarantee.
    roof_floor = (
        c.TOP
        + c.G["height_stack_uncertainty"]
        + c.G["minimum_printed_clearance"]
        + E["roof_thickness"]
    )
    report = {
        "study_valid": all(x["valid"] for x in metrics.values()),
        "current_cover_fit_pass": all(
            v["intersection_mm3"] < 1e-6
            for v in trials[0]["uncertainty_envelope"].values()
        ),
        "scope": "Reference CAD and exact committed-cover versus conservative envelope intersections; not manufacturing geometry, a selected airflow option or a release.",
        "source_sha256": {
            f: sha(R / f)
            for f in [
                "cad/cooler-profiles.json",
                "cad/cooler_reference.py",
                "cad/parameters.json",
                "tools/cooler_fit_review.py",
                "exports/cover.step",
            ]
        },
        "parts": metrics,
        "stack_z_mm": {
            "pcb_underside": c.BOARD_Z,
            "agx_thermal_plate_top": c.AGX_TOP,
            "copper_spreader_bottom": c.SPREADER_Z,
            "cooler_contact": c.CONTACT_Z,
            "fin_top_fan_bottom": c.FAN_Z,
            "fan_top": c.TOP,
            "current_roof_underside": roof,
            "current_rib_bottom": rib,
            "current_ring_bottom": ring,
        },
        "fan_offset_from_existing_inlet_mm": round(math.hypot(c.CX - ox, c.CY - oy), 3),
        "current_cover_trials": trials,
        "same_lid_recovery_lift_floor_mm": round(required, 3),
        "same_lid_study_lift_mm": recovery,
        "replacement_roof_height_floor_mm": round(roof_floor, 3),
        "replacement_roof_height_candidate_mm": math.ceil(roof_floor),
        "unresolved": [
            "Spreader/fan seating datum and secondary TIM",
            "Spacer pattern versus long tie-down axes",
            "Effective female thread depth and short-screw length",
            "Actual fan offset and top height",
            "Fin pitch and pipe bend path",
            "Replacement roof structural stiffness and airflow",
        ],
        "production_ready": False,
        "physical_fit_verified": False,
        "cfd_reused_for_g48r": False,
    }
    (OUT / "fit-review.json").write_text(json.dumps(report, indent=2) + "\n")
    renderer = Renderer(
        R / "preview",
        size=(1500, 1050),
        branding="J501 COOLER STUDY",
        subtitle="G48R reference | original approximate CAD | NOT a printable cooler",
        tessellation=(0.15, 0.3),
    )
    loaded = {k: cq.importers.importStep(str(OUT / f"{k}.step")).val() for k in pieces}

    def rgb(k):
        return tuple(int(c.COLORS[k][i : i + 2], 16) / 255 for i in (1, 3, 5))

    context = {"module_axes_reference", "pcb_reference", "agx_reference"}
    shapes = [(s, rgb(k)) for k, s in loaded.items() if k not in context]
    for mode, view in [("assembly", "iso"), ("top", "top"), ("side", "front")]:
        renderer.render(
            f"cooler-study-{mode}.png",
            shapes,
            caption="Mini J501 / G48R cooler: " + mode,
            view=view,
            note="2 mm copper spreader; 5 x diameter 6 heat pipes; 15 mm fan | bends, fins and mount positions provisional",
        )
    renderer.render(
        "cooler-study-installed.png",
        [(s, rgb(k)) for k, s in loaded.items()],
        caption="Cooler position on carrier / provisional mounting",
        note="Magenta: existing module screw axes. Adapter lugs and copper plate plan are estimates pending physical confirmation.",
    )
    exploded = []
    for k, s in loaded.items():
        if k in context:
            continue
        dz = (
            50
            if k.startswith("fan")
            else 16 if k not in ["spreader", "spacers_provisional"] else 0
        )
        exploded.append((s, rgb(k), (0, 0, dz)))
    renderer.render(
        "cooler-study-exploded.png",
        exploded,
        caption="Cooler stack / separated reference components",
        note="6.8 mm spacers and adapter ears shown provisionally; screws omitted until thread stack and mounting axes are confirmed",
    )
    project = SimpleNamespace(
        root=R,
        exports_dir=OUT,
        title="J501 G48R cooler / reference study",
        part_ids={},
        view={
            "parts": False,
            "hidden": ["module_axes_reference", "pcb_reference", "agx_reference"],
            "colors": c.COLORS,
            "extra": [
                {"name": k, "file": str((OUT / f"{k}.step").relative_to(R))}
                for k in pieces
            ],
        },
    )
    export_view(project)
    draw(report)
    artifacts = (
        list(OUT.glob("*.step"))
        + list((OUT / "view").glob("*.stl"))
        + [OUT / "view/view.json"]
        + list((R / "preview").glob("cooler-study-*.png"))
    )
    report["artifact_sha256"] = {
        str(p.relative_to(R)): sha(p) for p in sorted(artifacts)
    }
    (OUT / "fit-review.json").write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: report[k]
                for k in [
                    "fan_offset_from_existing_inlet_mm",
                    "same_lid_study_lift_mm",
                    "replacement_roof_height_candidate_mm",
                ]
            }
        ),
        flush=True,
    )


def draw(report):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle, Circle

    fig, (ax, side) = plt.subplots(
        1, 2, figsize=(14, 7.5), gridspec_kw={"width_ratios": [1.25, 1]}
    )
    ax.add_patch(
        Rectangle(
            (0, c.E["front_y"]),
            c.E["width"],
            c.E["rear_y"] - c.E["front_y"],
            fill=False,
            edgecolor="#254958",
            lw=2,
        )
    )
    ax.add_patch(
        Rectangle((c.M, c.M), c.B["width"], c.B["depth"], fc="#d8e9dc", ec="#62967b")
    )
    px, py = [x + c.M for x in c.G["spreader_center_in_pcb"]]
    sx, sy = c.G["spreader_visual_xy"]
    ax.add_patch(
        Rectangle(
            (px - sx / 2, py - sy / 2),
            sx,
            sy,
            fc="#c68b59",
            alpha=0.45,
            label="2 mm copper plate (plan estimated)",
        )
    )
    ax.add_patch(
        Rectangle(
            (c.CX - 47.5, c.CY - 47.5),
            95,
            95,
            fill=False,
            ec="#187aa4",
            lw=2,
            label="95 mm fan clearance envelope",
        )
    )
    ax.add_patch(
        Circle(
            (c.CX, c.CY),
            44.12,
            fill=False,
            ec="#187aa4",
            lw=2,
            label="Photographed fan rotor",
        )
    )
    ox, oy = [x + c.M for x in c.C["center_in_pcb"]]
    ax.add_patch(
        Circle(
            (ox, oy),
            40,
            fill=False,
            ec="#aa3388",
            ls="--",
            lw=2,
            label="Existing inlet (80 mm)",
        )
    )
    for x0, y0, x1, y1 in c.E["roof_ribs"]["segments"]:
        ax.plot([x0, x1], [y0, y1], c="#aa3388", lw=2)
    for x, y in c.B["module_mount_centers"]:
        ax.plot(x + c.M, y + c.M, "+", c="#aa3388", ms=9)
    ax.plot(c.CX, c.CY, "+", c="#187aa4", ms=10)
    ax.annotate(
        "Fan shifted about 20 mm\nXY estimate: +/-3 mm",
        (c.CX, c.CY),
        xytext=(12, 192),
        arrowprops={"arrowstyle": "->"},
        fontsize=9,
    )
    ax.set(
        xlim=(-5, 211),
        ylim=(-3, 207),
        xlabel="Enclosure X (mm)",
        ylabel="Enclosure Y (mm)",
        title="Plan: existing ribs/inlet versus photographed cooler",
    )
    ax.set_aspect("equal")
    ax.legend(loc="lower left", fontsize=7)
    z = report["stack_z_mm"]
    x = 0
    for name, lo, hi, color in [
        (
            "Copper spreader",
            z["copper_spreader_bottom"],
            z["cooler_contact"],
            "#bb743e",
        ),
        (
            "G48R contact to fin top",
            z["cooler_contact"],
            z["fin_top_fan_bottom"],
            "#a4b3bc",
        ),
        ("15 mm fan", z["fin_top_fan_bottom"], z["fan_top"], "#375966"),
    ]:
        side.add_patch(Rectangle((0, lo), 55, hi - lo, fc=color, ec="white"))
        side.text(
            3,
            (lo + hi) / 2,
            name,
            va="center",
            fontsize=9,
            color="white" if name.startswith("15") else "#192a34",
        )
    for label, key, color in [
        ("Existing ring bottom", "current_ring_bottom", "#c23c35"),
        ("Existing rib bottom", "current_rib_bottom", "#ad4e93"),
        ("Existing roof underside", "current_roof_underside", "#665599"),
    ]:
        zz = z[key]
        side.plot([-2, 95], [zz, zz], ls="--", c=color)
        side.text(58, zz + 0.4, f"{label}\nZ{zz:.2f}", fontsize=8, color=color)
    side.axhline(z["fan_top"], c="#187aa4")
    side.text(
        58, z["fan_top"] + 0.3, f'Fan top Z{z["fan_top"]:.2f}', fontsize=8, c="#187aa4"
    )
    side.set(
        xlim=(-3, 100),
        ylim=(38, 104),
        xticks=[],
        ylabel="Enclosure Z (mm)",
        title="Height stack: levels, not a section through the lid",
    )
    side.text(
        1,
        100,
        f'New-roof geometric floor: {report["replacement_roof_height_candidate_mm"]} mm\nSame-lid lift study: {report["same_lid_study_lift_mm"]} mm',
        fontsize=10,
    )
    fig.suptitle(
        "G48R fit study — source dimensions plus explicitly uncertain photo placement",
        fontsize=14,
    )
    fig.text(
        0.04,
        0.02,
        "Geometric study only. New lid not built; no strength or airflow claim. Do not add the 6.8 mm lug spacers beneath the entire cooler.",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.04, 1, 0.95))
    fig.savefig(R / "preview/cooler-study-clearance.png", dpi=145)
    plt.close(fig)


if __name__ == "__main__":
    main()
