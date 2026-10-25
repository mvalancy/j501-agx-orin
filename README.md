# J501 AGX enclosure — Rev 0.6 fit-check prototype

Run `python tools/serve_preview.py` for the local review; it writes the URL to `preview/server-url.txt`. The engineering tables are in [docs/engineering-review.html](docs/engineering-review.html), and the dimensioned paper review is [docs/check-sheet.pdf](docs/check-sheet.pdf).

This design targets the **original Seeed reServer Industrial J501 carrier, SKU102991854, 176 × 163 mm**, with the optional GMSL board SKU102991855. The user's cooler is not identified; Seeed 100099421 (110 × 100 × 50 mm) is a reference envelope only.

Rev 0.5 is a redesign of the Rev 0.4 shell. The reference data, the PCB registration and the check pipeline are carried over unchanged. Rev 0.4 sources, previews and reports are archived in `archive/rev04/`.

## What changed from Rev 0.4, and why

| Rev 0.4 problem | Rev 0.5 fix |
|---|---|
| Plugs could not fully mate. The 6 mm panels put receptacle faces 7–7.6 mm behind the exterior, so overmolds had to enter the windows. The USB-C slot was 5.7 mm tall, against a typical 6.5–8 mm overmold. | The plates are 3 mm thick, with inner faces unchanged (0.37 mm front / 0.25 mm rear to the nearest part). Receptacles now sit 3.3–5 mm behind the exterior. Windows for USB-A, USB-C and HDMI are sized to overmold envelopes. |
| The cooler (most of the mass) hung only from the PCB. | **Cooler tie-down.** Four printed columns (D14, D7.14 pad-sized landing) sit under the 92 × 79 cooler holes. M3 × 35 flat-head screws enter from **below the floor**, seat on a 90° countersink raised inside each column, pass the carrier and module, and thread 8 threads (4 mm) into the female standoffs between the AGX module and the heatsink. Low floor ribs tie the columns to the board posts. |
| The roof was 67% open, but its 25 × 29 mm cells let a finger reach the fan. | 216 hexagonal cells, 10 mm across flats, 6 mm deep. A 12 mm test finger cannot pass. Each cell has a 0.6 × 1.0 mm inlet chamfer on the fan side (11.2 mm across flats at the underside) so the cooler's exhaust enters a tapered mouth instead of a sharp edge. Cooler-to-roof gap grows from 11.2 to 15.2 mm. |
| The cap overhung the base by 6.4 mm, and hatch rails protruded 11 mm. The footprint was 218.8 × 205.8 mm. | Flush R8 shell, **206 × 181 × 112 mm**, with a V reveal at the split. The J17 hatch is a flush door in the wall plane. |
| Two diagonal M6 side screws held the cover. | Four M3 × 16 screws go in from the top, into inserts in the wall columns. They stay reachable when the base is bolted to a wall or robot. |
| Base tabs spanned 253 mm in Y, leaving a 1.5 mm margin on the P1S. | Tabs are 8 mm thick, with gussets and slots on a 154 × 211 pattern. The base-plus-tabs print is 206 × 233 mm, leaving an 11.5 mm margin. |
| Large grouped windows had no legends. | One rounded window per connector group, with a 0.6 × 45° lead-in. Debossed legends: AUDIO, GMSL, 1G, 10G, DC IN, I/O, HDMI, USB, USB-C. |
| No access to the reset and force-recovery buttons. | Two Ø1.6 pin holes in the rear plate with inner guide sleeves, over the right-angle switches between the USB-C ports and the right-hand corner. REC is nearest the USB/IO headers, RST nearest the far board edge, each labelled. |
| No antenna provision. | Four RP-SMA bulkhead holes in the fixed base side walls: WIFI 1/2 left, CELL 1/2 right, with 2.5 mm spot-faced walls. |
| Vents only on the left side; pointed slots. | Stadium slots on one 9 mm rhythm across the lid, base, hatch and plates. The plate vents (Z46–66) line up with the cooler fin exits. |

## Storage expansion and the underside slots

**Underside slots.** The Mini PCIe (J13) and M.2 Key B (J11) slots sit side by side under the front-left of the carrier, and their cards run toward the rear, one above the other. The M.2 Key E (J14) Wi-Fi card runs toward the SATA corner. Card envelopes, including U.FL plugs, are in `cad/parameters.json` under `underside_envelopes`:
- The stacked pair needs at most 10 mm below the PCB; 16 mm is available.
- The stacked pair's envelopes are 6–7 mm above the floor and needed no relief.
- The M.2 E envelope touched a support (74 mm³), which is now relieved with a 0.5 mm margin.

**SATA is on the underside.** The two SATA III receptacles (J21 port 0, J24 port 1) and their JST PH 2.0 4-pin power headers (J22, J23) are *vertical connectors on the underside* (datasheet photo, STEP solids 5061–5064). Cables plug in straight up from below. The base floor has an opening directly beneath them, so the cables drop into the storage trays. P18 plugs the opening when no storage is fitted.

**Power.** The board's SATA power headers carry switched **5 V only**, 2 A per port (schematic sheet 27):
- 2.5 in drives can run from the board.
- 3.5 in drives need 12 V. The 3.5 in tray has an 8 mm **12V IN** hole and tie anchors for a 12 V-to-SATA power adapter.
- Board input is 12–36 V, so DC-IN can only be shared with the drives if your supply is 12 V.

**Trays.** P15 holds one 3.5 in drive (SFF-8301, all three 6-32 hole pairs). P16 holds two 2.5 in drives up to 15 mm (SFF-8201 M3 holes); 7 mm drives without bottom holes need side mounting.

Stack any mix, in any order:
- M3 heat-set inserts go in the four base column feet.
- Each tray is clamped by four M3 male-female hex standoffs: M3 × 30 for P15, M3 × 20 for P16.
- Each standoff's male end clamps the tray's 2 mm ledge to the part above, and its female end receives the next tray.
- Drive connectors face a cable gutter on the left side that runs the full depth of the tray. A chimney lines up through every tray floor.
- P17 replaces P1M for wall or robot mounting under a stack.
- Two of each tray adds 108 mm, for 220 mm overall.
- The board has two SATA ports; more drives need an M.2 Key M SATA adapter or USB.

**Drive mounting.**
- 3.5 in drives use bottom 6-32 screws.
- 2.5 in drives up to 15 mm use bottom M3 screws.
- Skinny 7 mm SSDs that only have side holes use four P19 clips each. Each clip takes an M3 × 5 through its wall into the drive side and an M3 × 6 from under the tray into a captive nut, using the same tray holes.
- Drive connector ends sit at X 48 (3.5 in) and X 62 (2.5 in) to leave room for the cable bend.

**Cable routing.**
- Leads plug straight up into J21–J24, drop through the base floor opening and each tray's chimney, then turn in the left gutter and run straight into the drive plug.
- Assumed minimum bend radii: 12 mm SATA data, 6 mm PH power, 8 mm 12 V. No SATA standard publishes one.
- Wire a 3.5 in drive from the front SATA connector and a 2.5 in drive from the rear one. From the rear connector, the turn into a 3.5 in drive's data plug only allows about a 9 mm bend.
- Every route is modelled and checked for bend radius and plastic clearance.
- A 2D route diagram is at `preview/cable-route-diagram.png`.

`exports/storage-checks.json` covers seven stack combinations. Each passes with no plastic or hardware overlap and an open chimney. It also records the envelope gaps and drive-screw engagement.

## Parts

- **Which base:** P1 for desktop use and for every storage stack; P1M only for wall/robot mounting without storage. With storage on a wall or robot, use P1 + trays + P17.
- **Desktop:** P1 `base`, P2 `cover`, P3 `front_gmsl` or P4 `front_no_gmsl`, P5 `rear_io`, P10 `side_hatch`. Optional rubber bumpers (≤ D12 × 1) fit four floor pockets.
- **Storage (optional):** P15 `storage_35` and/or P16 `storage_25` trays, plus P17 `storage_mount_plate` for wall/robot use, or P18 `chimney_cap` when no storage is fitted.
- **Wall/robot:** substitute P1M `base_mount`. External M6 screws, D16 washers and anchors are site-specific.
- **Calibration:**
  - P11: M3 pilot coupon.
  - P12/P13: plate channel and key.
  - **P14: countersink coupon.** Check that the flat head sits at or below the floor.
  - P9: cradle fit jig. It has the same supports, pad-sized landings (Ø6.9 board / Ø7.14 cooler) and underside relief as P1 on a 3 mm frame, so the bare carrier sits on it exactly as it will in the base.

Print orientations:

- P1/P1M: floor down.
- P2: roof down.
- P3/P4/P5/P10: exterior face down.

Print sizes, all within the P1S's 256 mm cube:

- P1M: 206 × 233 × 76.5 mm.
- P2: 206 × 181 × 40 mm.

The filament is unspecified, so fits, heat resistance, creep and insert retention are not qualified.

## Assembly

1. Print P11, P12/P13 and P14 in the intended filament and profile. The nominal M3 pilot is 3.9 mm.
2. Set the bare carrier face up on P9. Every landing should sit flat on its pad with nothing else touching. Then check the 92 × 79 holes against the actual cooler.
3. Heat-set eight M3 × 10 inserts: four into the board supports and four into the tops of the lid columns. Do this before installing electronics.
4. Place the PCB on its four supports and fasten with M3 × 10 button heads (8.4 mm engagement).
   - **With storage:** before lowering the board, fit the underside cards (Mini PCIe / M.2 B / M.2 E). Then plug the SATA data and PH power leads straight up into J21–J24 and thread them down through the floor opening as the board goes in.
   - **Without storage:** press P18 into the floor opening from below.
5. **Cooler tie-down.**
   - Install the module and cooler as originally designed.
   - Replace each of the four cooler screws with a flat-head screw driven up from beneath the floor.
   - Each screw passes the column, the carrier and the module, then threads into the **female standoff between the AGX module and the heatsink**. That thread starts at the top of the AGX thermal plate (Z 40.76).
   - **Screw: M3 × 35 flat head (DIN 7991 / ISO 10642), 4 places.** M3 matches the module holes (Ø3.5 PCB, Ø3.7 thermal plate).
   - The length is set by the assembly: bottom of the housing to the AGX top, plus 8 threads (4 mm). Flush with the floor that would be 44.3 mm, which is an uncommon size. So the countersink seat is raised to Z 9.76 inside each column, up a Ø7 pocket from the floor, and a standard 35 mm screw gives exactly 4.0 mm of engagement.
   - The thermal pad (0.5 mm nominal, `cooler.tim_thickness`) lifts the heatsink, not the standoff thread, so it does not change the length.
   - Tighten gently; these are printed columns.
6. For GMSL, use its supplied supports and screws. The 16 mm stack is implied by the Samtec suffixes; verify it.
7. Fit the four RP-SMA bulkhead pigtails from inside the base walls: body against the spot face, lock washer and nut outside. Route the leads around the PCB edge to the radios.
8. Slide the front and rear plates and the J17 hatch down their channels.
9. Lower the lid. The tongue-and-rebate joint locates it. Fit four M3 × 16 socket heads from the top (2.5 mm hex, about 40 mm reach). The ledges over the plates and the lid's skin over the hatch keep all three from lifting.
10. **Storage stack.**
    - Heat-set four M3 × 10 inserts into the base column feet, from below.
    - For each tray from the top down: drive-screw the drives in from below (6-32 × 3/16 in for 3.5 in, M3 × 4 button head for 2.5 in).
    - Route the leads down the chimney and along the gutter to the drive connectors.
    - Offer the tray up and fit four M3 M-F standoffs through its ledges into the part above.
    - Finish with rubber bumpers in the bottom tray's pockets, or P17 and four M3 × 8 screws for wall/robot use.
11. Service: the reset and recovery switches are reached with a pin through the rear plate. Remove the four lid screws, lift the lid, then lift the plate or hatch. The nano-SIM (J18) is reached by removing the front plate.

## Port windows

The windows are defined in `cad/parameters.json` under `ports`, in the PCB X/Z datum. Each entry records its source solid and sizing basis, and the full list is in [docs/cutout-register.csv](docs/cutout-register.csv).

How the windows are sized:

- **Plug fits fully inside the receptacle face** (RJ45, terminals, audio): the window follows the housing face + 0.5 mm.
- **Overmold enters the window** (USB-A, USB-C, HDMI): the window follows a typical overmold envelope. These are 16.5 × 8.5 mm (USB-A), 13 × 8 mm (USB-C) and 11.5 × 21.5 mm (HDMI, rotated).
- **Webs narrower than 1.8 mm** are bridged instead:
  - Front: 10G, LED4 and DC IN.
  - Rear: HDMI and USB-A.

All of this still needs checking against the user's actual cables.

## Geometry provenance

This section is carried over from Rev 0.4 and still applies. [docs/connector-inventory.csv](docs/connector-inventory.csv) is a schematic-derived mechanical inventory, not an official BOM.

The carrier STEP contains 5176 solids and 158 open shells. Eight mount proxies and four zero-thickness pseudo-solids are handled as recorded in the reports.

Two source models are not mechanically authoritative:

- **J26:** the source STEP is a 3.81 mm placeholder. A 13.85 mm footprint-height envelope is used instead.
- **Audio:** the STEP library model differs from the schematic part number.

The GMSL XY position, port positions and top-component placement remain provisional. The provisional GMSL PCB top is only 1.58 mm below the cooler seat where they overlap by 4.5 mm; measure this before printing P3. Sources are listed in [references/sources.json](references/sources.json).

## Coordinates

All units are millimeters. In the carrier frame, X starts at the left PCB edge, Y at the front edge and Z at the PCB underside.

- Convert source STEP coordinates by subtracting `(32.199, -510.506, -1.578)`, then adding `(15, 15, 20)` to reach the enclosure datum.
- The enclosure outline spans X0–206, Y5.5–186.5, Z0–112, with the split at Z72.
- Key heights: PCB underside Z20 (4 mm floor + 16 mm supports); cooler seat Z40.758; reference cooler top Z90.758; roof underside Z106.

## Checks (`exports/`)

| Report | Result |
|---|---|
| `geometry-checks.json` | 12 printable parts, each one valid solid, watertight STL |
| `assembly-checks.json`, `mount-checks.json` | 0 mm³ plastic overlap across all part pairs, both front variants and P1M |
| `carrier-clearances.json` | 0 carrier-solid collisions. 0 collisions between plastic and the modeled screws, module, cooler or GMSL. 8 intended insert interferences |
| `shell-clearances.json` | open-shell intrusion check |
| `assembly-paths.json` | plates slide vertically: 0.37 front / 0.25 rear |
| `print-review.json` | downward-face screen. Flagged areas are the 4 mm vent arches, the 12 mm foot-pocket bridges and two 2 mm² groove ends |
| `design-metrics.json` | roof, vents, tie-down, fasteners, mounts |
| `storage-checks.json` | underside card envelopes and gaps, SATA drop, 7 stack configurations, cable routes and bend radii, chimney path, drive-screw engagement |

None of these checks covers slicer validation, insert pullout, thermal performance, vibration, creep under the cooler clamp load, or mounting load capacity.

## Reproduce

Vendor CAD models, datasheets and schematics are not redistributed here. Fetch them from their original URLs,
checksum-verified against `references/sources.json`, and rebuild the caches the build reads:

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python tools/fetch_references.py   # NVIDIA module model needs a developer login; the script prints where
```

The project runs on the [`cad-agent`](https://github.com/Valpatel/cad-agent) toolkit, configured by `cad-agent.yaml`. Without the toolkit, run the scripts
listed under `steps:` in that file in order with `.venv/bin/python`.

```bash
.venv/bin/pip install -e <path-to>/cad-agent      # cadagent toolkit
.venv/bin/cad-agent all       # every build step in cad-agent.yaml, 3MF export, checks, report, package
.venv/bin/cad-agent serve     # local preview with STL/3MF/Bambu Studio links
```

`cad-agent check` gives a pass/fail table of every part, print file, design check and review-page link.
`docs/cad-agent-report.html` is the standalone report.

`cad/parameters.json` is the parameter authority.

## License

MIT (see `LICENSE`) for the enclosure design, source and generated files in this repository. Vendor files fetched
by `tools/fetch_references.py` stay under their owners' terms and are not covered.
