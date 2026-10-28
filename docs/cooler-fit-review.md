# Mini J501 / G48R cooler fit review

The cooler in the October 27 photographs is taller and offset from the cooler used by the existing enclosure model. This study adds an original, approximate G48R assembly and reproduces the lid collision against the committed cover STEP. It leaves the printable enclosure, Rev 0.9 airflow options and running simulations unchanged.

![G48R reference assembly](../preview/cooler-study-assembly.png)

**Development study, not a print release.** Mounting axes, seating height and the copper adapter outline still need confirmation. The existing print-package checks describe the previous cooler configuration; they do not establish G48R compatibility.

## What the fit check says

![Plan and height stack](../preview/cooler-study-clearance.png)

The existing 80 mm intake ring is centered on the module. Photo registration places the actual fan about **20 mm away**, at PCB X85, Y71 mm. The placement allowance is ±3 mm in XY; the vertical stack allowance is +2 mm. These are engineering allowances, not statistical confidence intervals.

The actual committed `exports/cover.step` was checked using OpenCascade solid intersections and minimum distances against conservative rectangular cooler volumes:

| Same cover, translated upward | Nominal minimum fan gap | With placement/height allowance | Result |
|---|---:|---:|---|
| 0 mm | Intersects | Intersects | Reproduces the reported collision |
| 15 mm | 0.7 mm | Intersects by 413.1 mm³ | Insufficient allowance |
| 19 mm | 4.7 mm | 2.7 mm | Geometric candidate for a recovery spacer |

The intake ring is the lowest obstruction. Its nominal 14.3 mm interference explains why the printed lid appears roughly 15 mm too short. A **19 mm lift is a study result**, not a released spacer: its mating lips, screw reach, column strength and cable/port consequences have not been designed or checked.

A redesigned roof can avoid that deep, misplaced ring. Keeping ribs outside the fan envelope and relocating the intake gives a preliminary overall enclosure height of **101 mm**, compared with the current parameter height of 92 mm. This includes a 4.5 mm roof, 2 mm target clearance and the +2 mm stack allowance. It is a geometric lower bound rounded upward, **not a completed lid or validated airflow design**.

## Stack and datums

All coordinates use the enclosure CAD datum. PCB XY starts 15 mm inside the enclosure; PCB underside is Z20 mm.

| Surface | Z, mm | Basis |
|---|---:|---|
| AGX thermal plate top | 40.758 | Existing PCB/module stack |
| Copper spreader bottom | 41.258 | Existing assumed 0.5 mm TIM |
| Cooler contact on copper | 43.258 | User: 2 mm copper plate |
| Fin top / fan bottom | 76.558 | S06: 33.3 mm contact-to-fin height |
| Fan top | 91.558 | S06: 15 mm fan |
| Existing intake ring bottom | 77.258 | Current enclosure parameters |
| Existing rib bottom | 81.500 | Current enclosure parameters |
| Existing roof underside | 87.500 | Current enclosure parameters |

The **6.8 mm spacers support the mounting lugs**. Adding their height under the entire cooler would imply an air gap between the cooler contact and copper plate. Their actual attachment stack and any secondary TIM remain unresolved.

## Reference assembly and mounting ambiguity

![Installed reference](../preview/cooler-study-installed.png)

![Exploded cooler stack](../preview/cooler-study-exploded.png)

The model includes the copper spreader, cold plate, five rounded Ø6 mm heat pipes, fin plates, fan frame, hub and visual blades. Brass-colored spacers and adapter ears are provisional. Magenta axes show the existing module mounting positions; the PCB and module are simple original context envelopes, not redistributed vendor CAD.

The photo suggests cooler lugs on an approximately 92 × 79 mm pattern centered at PCB (90,70). The registered module axes use the same pitch but are centered at (90,90.5). **Do not assume these are interchangeable.** Confirm whether the 6.8 mm female M3 spacers share the long tie-down screw axes or attach through separate holes in the copper plate. The generic Intel 75/78 mm mounting drawings in S06 do not settle the J501 adapter pattern.

Screws are deliberately absent from this reference assembly until the mounting stack, female thread depth and short-screw length are known. The existing enclosure fastener BOM is not a validated G48R fastener selection.

## Evidence and approximation register

| Source | Used for | Limits |
|---|---|---|
| [S06 — Seeed G48R fan/heatsink PDF](https://files.seeedstudio.com/products/NVIDIA-Jetson/reComputer_Mini_J501_Fan.pdf) | 102 × 92.5 mm heatsink envelope; 33.3 mm height; five Ø6 mm pipes; fan drawings | Generic cooler hardware, not a dimensioned Seeed copper adapter |
| S05 — Seeed Mini J501 product sheet, registered in [sources.json](../references/sources.json) | Catalog assembly 110 × 100 × 50 mm | Rounded catalog envelope; does not establish seating datum |
| S03 — WS-RDN-601 datasheet, same source register | Retained 100 × 87 × 34 mm low-profile option | Different cooler from the photographs |
| User measurements, 2026-10-27 | 2 mm copper; Ø4 × 6.8 mm female M3 spacers | Thread depth and seating stack not measured |
| IMG_1852–1854, reviewed locally | Offset fan, adapter extent, rib/ring interference | Perspective and occlusion; personal images not republished |

The S06 fan drawing gives a **91.2 × 92.2 mm frame**, Ø88.24 mm rotor, Ø32.8 mm hub and 86 × 56 mm screw pitch. Its specification table instead lists **95 × 95 × 15 mm**. Fit checks use the larger 95 mm plan envelope. Fan mounting holes are not modeled because their attachment to this particular fin assembly is not established.

Heat-pipe bends, fin thickness/pitch, blades, copper outline and adapter ears are original approximations. They provide a reviewable arrangement, not machining drawings or an aerodynamic mesh. The photograph fit recovered from Claude's notes has 2.019 pixel RMS, but one fitted height plane used Z24 rather than the canonical PCB underside Z20. The ±3 mm placement allowance must remain until physical measurement replaces the fit.

S06 specifies 12 V, up to 0.19 A and 4000 rpm. Its free-air flow and shutoff pressure endpoints are **not simultaneous operating conditions**. Existing WS-RDN-601 simulations cannot establish this G48R assembly's temperature or flow performance.

## Reproduce and review

With the project's CadQuery/cad-agent environment installed:

```bash
python tools/cooler_fit_review.py
python tools/check_cooler_study.py
cad-agent site --serve --port 8766
```

Open the local site's **Cooler study** panel for assembly, top, side, installed, exploded and clearance views, plus the shared cad-agent interactive 3D viewer. Toggle context parts to inspect the module axes.

- [Assembly STEP](../exports/cooler-study/g48r-reference.step)
- [Individual components and viewer files](../exports/cooler-study/README.md)
- [Machine-readable fit report](../exports/cooler-study/fit-review.json)
- [Dimensions and assumptions](../cad/cooler-profiles.json)
- [Original model source](../cad/cooler_reference.py)

The next enclosure iteration should first confirm the fan top height, fan center and spacer axes. It can then relocate the intake, route ribs around the keepout and design either a recovery spacer or a shorter replacement lid. Retain both cooler profiles; choose the Rev 0.9 airflow option separately after its own studies finish.
