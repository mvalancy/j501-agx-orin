#!/usr/bin/env python3
"""Check the committed cooler study without vendor files or a CAD installation.

These checks catch stale evidence and lost negative controls. The builder performs
native STEP readback and exact intersections; this checker does not replace it.
"""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check():
    report = json.loads((ROOT / "exports/cooler-study/fit-review.json").read_text())
    profile = json.loads((ROOT / "cad/cooler-profiles.json").read_text())["mini_g48r"]
    errors = []

    def require(condition, message):
        if not condition:
            errors.append(message)

    for field in ("source_sha256", "artifact_sha256"):
        hashes = report.get(field, {})
        require(bool(hashes), f"missing {field}")
        for relative, digest in hashes.items():
            path = (ROOT / relative).resolve()
            require(
                ROOT in path.parents and path.is_file(), f"missing/unsafe {relative}"
            )
            if ROOT in path.parents and path.is_file():
                require(
                    hashlib.sha256(path.read_bytes()).hexdigest() == digest,
                    f"stale {relative}",
                )

    require(report["study_valid"] is True, "native reference validation failed")
    require(
        report["current_cover_fit_pass"] is False,
        "lost current-lid collision negative control",
    )
    for key in ("production_ready", "physical_fit_verified", "cfd_reused_for_g48r"):
        require(report[key] is False, f"unsupported approval: {key}")
    parts = report["parts"]
    require(
        parts["heat_pipes"]["solid_count"] == profile["heat_pipe_count"] == 5,
        "pipe count",
    )
    for name, dimension in (
        ("spreader", "spreader_thickness"),
        ("fan_frame", "fan_height"),
        ("spacers_provisional", "spacer_height"),
    ):
        bounds = parts[name]["bounds_mm"]
        require(
            abs(bounds[5] - bounds[2] - profile[dimension]) < 0.001, f"{name} height"
        )
    for name, part in parts.items():
        require(part["valid"] and part["volume_mm3"] > 0, f"invalid STEP {name}")
    trials = {row["lid_lift_mm"]: row for row in report["current_cover_trials"]}
    require(
        trials[0]["nominal"]["fan"]["intersection_mm3"] > 100,
        "missing observed collision",
    )
    require(
        trials[15]["uncertainty_envelope"]["fan"]["intersection_mm3"] > 0,
        "15 mm lift no longer reproduces documented insufficient allowance",
    )
    candidate = trials[report["same_lid_study_lift_mm"]]["uncertainty_envelope"]
    for name, result in candidate.items():
        require(result["intersection_mm3"] < 0.0001, f"candidate intersects {name}")
        require(
            result["minimum_gap_mm"] >= profile["minimum_printed_clearance"],
            f"candidate clearance insufficient: {name}",
        )
    require(len(report["unresolved"]) >= 4, "lost unresolved dimension register")

    for error in errors:
        print("FAIL:", error)
    print(
        f"Cooler study: {len(parts)} native component records, source/artifact hashes, "
        f"collision controls and candidate clearance: {'FAIL' if errors else 'PASS'}"
    )
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(check())
