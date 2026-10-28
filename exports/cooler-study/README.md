# Cooler model and fit evidence

The reComputer mini J501 heatsink with fan (G48R tower, 92 × 15 mm fan) as the project models it, split into components, plus the evidence that the Rev 0.9 lid clears it. **These are reference components, not printable parts or manufacturing drawings.**

![Cooler assembly](../../preview/cooler-study-assembly.png)

| Review asset | Purpose |
|---|---|
| [Assembly STEP](g48r-reference.step) | The cooler without board context |
| [Fit report](fit-review.json) | STEP readback, exact lid-versus-cooler intersections with the fan moved ±3 mm, the Rev 0.8 collision control and the riser; source and artifact hashes |
| [Interactive viewer data](view/README.md) | Shared cad-agent viewer meshes; board context hidden at first |
| [Low-profile envelope](ws-rdn-601-envelope.step) | The 34 mm WS-RDN-601 alternative |
| [Fit review](../../docs/cooler-fit-review.md) | Sources, assumptions, results and open measurements |

There is one cooler model, `cooler_and_module()` in [cad/hardware.py](../../cad/hardware.py), sized from the `cooler` section of [cad/parameters.json](../../cad/parameters.json); [cad/cooler_reference.py](../../cad/cooler_reference.py) only groups it into these components. Names ending in `provisional` are unconfirmed positions and names ending in `reference` are context. Pipe bends, plates and blades are illustrative. Do not choose screw lengths from these files.

`cad-agent all` regenerates this folder (step `cooler-study`, `tools/cooler_fit_review.py`); CI runs `tools/check_cooler_study.py` on the committed result.
