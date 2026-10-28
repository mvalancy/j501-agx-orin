# Assembly

Step-by-step assembly of the J501 AGX Orin enclosure. In each picture the parts you add in that step are **orange**;
everything already assembled is grey. Part numbers (P1, P2, …) and hardware are listed in the
[bill of materials](README.md#bill-of-materials).

**Tools:** soldering iron with an M3 insert tip, 2 mm and 2.5 mm hex keys, a SIM pin or paper clip.

## Before you start

### 1. Print the test parts

![Test parts](docs/assembly/01-test-prints.png)

Print P9, P11, P12, P13, P14 and P20 in the filament you will use for the enclosure.
- **P11:** heat-set an insert into each pilot hole; use the size that holds best.
- **P12 / P13:** the key should slide in the channel without rattling.
- **P14:** an M3 × 35 flat head should sit flush on its cone.
- **P20:** an RP-SMA bulkhead should push into the tightest D-hole whose flat stops it turning; set `antenna_bulkheads.across_flat` to that size.

### 2. Test-fit the board on P9

![Board on the fit template](docs/assembly/02-fit-template.png)

Set the bare carrier board on P9, face up. Every pad should touch the board and nothing else should. Check that the
four cooler holes line up with your cooler before printing the base.

## Enclosure

### 3. Heat-set the inserts

![Insert positions](docs/assembly/03-inserts.png)

Press eight M3 × 10 inserts into the base: four into the board supports and four into the tops of the tall lid
columns. Do this before any electronics go in.

### 4. Fit the board

![Board and screws](docs/assembly/04-board.png)

- **With drive trays:** first fit any Mini PCIe or M.2 cards under the board. Plug the SATA data and power leads
  straight up into the board's underside connectors (J21–J24), then feed them down through the floor opening as you
  lower the board.
- Fasten the board with four M3 × 10 button heads.

**Without drive trays,** close the floor opening with P18, pressed in from below:

![Floor cap](docs/assembly/04b-floor-cap.png)

### 5. Fit the module and cooler

![Module and cooler](docs/assembly/05-cooler.png)

Fit the AGX Orin module and its cooler as Seeed supplies them: the reComputer mini J501 heatsink's 2 mm copper
spreader on the module's thermal pad, the heat-pipe tower on its 6.8 mm standoffs, and the fan. Plug the fan into the
fan header and run its cable down the side of the cooler, below the fan top: the lid's skirt sits 6 mm outside the fan
frame. Fit the GMSL board now too, if you have one, with its supplied supports and screws.

### 6. Tie the cooler down

![Tie-down screws from below](docs/assembly/06-tiedown.png)

Replace each of the cooler's four screws with an M3 × 35 flat head, driven up from under the floor. It passes
through the column, the board, the module and the copper spreader, and threads 3 mm into the bottom of the cooler's
6.8 mm standoff, leaving the top of the standoff for the short screws from the heatsink ears. Tighten gently; the
columns are printed. In a Rev 0.8 base the seat is 1.5 mm lower, so the same screw only catches about 3 threads.

### 7. Fit the antennas

![Antenna bulkheads](docs/assembly/07-antennas.png)

Push each RP-SMA pigtail through its wall hole from the inside, with the flat on its thread at the top to match the
hole's flat, then fit the lock washer and nut outside. The flat stops the connector turning as you tighten. Wi-Fi goes
on the left wall, cellular on the right. Route the leads around the board edge to the radios.

### 8. Slide in the plates

![Plates and hatch](docs/assembly/08-plates.png)

Slide the front plate (P4, or P3 with GMSL), the rear plate (P5) and the side hatch (P10) down their channels.

### 9. Fit the lid

![Lid and screws](docs/assembly/09-lid.png)

Lower the lid and fit four M3 × 16 socket heads from the top (2.5 mm hex key, about 40 mm reach). The lid locks the
plates and hatch in place. The fan sits in the pocket under the round grille, 2.4 mm below it; if the lid does not sit
down flat, stop and check the fan cable and the cooler height (fan top 70 mm above the board's top face).

## Drive trays (optional)

Turn the closed enclosure over onto its lid and build the stack up from its floor. One P16 tray is shown; P15 (3.5 in)
trays fit the same way, in any order, up to two of each.

### Trays 1. Inserts in the base feet

![Base foot inserts](docs/assembly/10-tray-inserts.png)

Heat-set four M3 × 10 inserts into the base column feet, from below.

### Trays 2. Drives into the tray

![Drive screws](docs/assembly/11-drives.png)

Screw each drive in from under the tray: M3 × 4 button heads for 2.5 in drives, 6-32 × 3/16 in for 3.5 in drives.
7 mm SSDs without bottom holes use four P19 clips each.

### Trays 3. Cables

![Cable routing](preview/cable-routing.png)

Run each lead down the chimney and along the left-hand gutter into the drive plug. Use the board's front SATA
connector for a 3.5 in drive. Keep bends gentle: the guide allows 12 mm for data and 6 mm for power leads. A 3.5 in
drive needs its own 12 V supply through the tray's 12V IN hole; the board only supplies 5 V.

### Trays 4. Hang the tray

![Standoffs and closing screws](docs/assembly/12-stack.png)

Screw four standoffs into the base feet (M3 × 20 for P16, M3 × 30 for P15). Set the tray on them and close it with
four M3 × 6 button heads through its ledge. A second tray hangs from the first the same way, with its standoffs in
place of the closing screws.

### Trays 5. Wall or robot mount

![Mounting plate](docs/assembly/13-mount-plate.png)

For a wall or robot, fit P17 under the bottom tray with four M3 × 12 socket heads instead of the closing screws, then
fix it with M6 screws through the tab slots. Without drive trays, print the P1M base instead, which has the tabs
built in.

## Service

![Reset and recovery pin holes](preview/service-buttons.png)

Press **RST** (reset) or **REC** (recovery, for flashing) with a pin through the labelled holes in the rear plate.
For anything else, remove the four lid screws and lift the lid; the plates and hatch then lift out. The nano-SIM is
behind the front plate.
