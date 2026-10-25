[J501 AGX Orin](../README.md) / **cad**

# CAD source

The enclosure is modelled in Python with [CadQuery](https://cadquery.readthedocs.io/). These three files produce every printed part.

<p align="center">
  <img src="../preview/open.png" alt="Open enclosure with the carrier board and cooler" width="720">
</p>

| File | What it is |
|---|---|
| [`parameters.json`](parameters.json) | Every dimension the design uses: board, enclosure, cooler, GMSL board, inserts, printer, ports, storage. **Edit this first.** |
| [`build.py`](build.py) | Builds each printed part and writes its STL (in print orientation) and STEP (in assembly position) to [`exports/`](../exports/) |
| [`hardware.py`](hardware.py) | Simplified models of the bought parts (inserts, screws, jumper cap, cooler) for renders and clearance checks. Not for manufacturing |

**Coordinates.** All dimensions are in mm. The origin is set so the board's lower-left corner sits at the PCB margin, with Z measured from the underside of the PCB.

**Before changing a dimension,** check [`docs/measurement-register.csv`](../docs/measurement-register.csv): it says which values were measured and which are assumptions.

**Rebuilding.** `build.py` reads the vendor board model, which is not in the repository. Fetch it first, then run the whole pipeline so the checks, renders and manifest stay in step:

```bash
.venv/bin/python tools/fetch_references.py
.venv/bin/cad-agent all
```

The scripts that check and render the build are in [`tools/`](../tools/).
