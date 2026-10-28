#!/usr/bin/env python3
"""One 3D viewer for the whole build: printed parts, the cooler, the carrier board, the AGX module and the screws.

Writes the bought-part context into exports/view-context/ (not tracked: the module is NVIDIA's model, read from the
local reference copy that tools/fetch_references.py downloads), then runs cad-agent's view export with the sections
configured under cad.view in cad-agent.yaml (exports/view/, opened from the site's "3D model" link). Without the vendor
references the module and carrier board are listed as not exported and the rest still shows.
"""
from pathlib import Path
import sys
import cadquery as cq

R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / 'cad'))
import build as b  # noqa: E402
import hardware as h  # noqa: E402
from cadagent.project import load_project  # noqa: E402
from cadagent.view import export_view  # noqa: E402

OUT = R / 'exports/view-context'


def context():
    """name -> shapes, in assembly position (the same hardware the renders and clearance checks use)."""
    hw = h.enclosure_hardware()
    pick = lambda items, *prefixes: [s for label, s, _ in items if label.startswith(prefixes)]  # noqa: E731
    out = {'lid_screws': pick(hw, 'H1', 'H3'), 'board_screws': pick(hw, 'H4', 'H5'), 'antenna_bulkheads': pick(hw, 'H10'),
           'cooler_tiedown_screws': [s for _, s, _ in h.heatsink_tiedown()]}
    if (R / 'references/nvidia-module/p3701-sku0-simplified.brep').is_file():
        out['agx_module'] = pick(h.cooler_and_module(), 'E2')
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, shapes in context().items():
        cq.exporters.export(cq.Compound.makeCompound(shapes), str(OUT / f'{name}.step'))
    r = export_view(load_project(R))
    print(f"view: {r['parts']} parts" + (f"; not exported: {', '.join(r['skipped'])}" if r['skipped'] else ''), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
