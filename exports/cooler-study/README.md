# G48R cooler reference and fit evidence

Original approximate CAD for reviewing the installed Mini J501 cooler. **These are reference components, not printable enclosure parts or manufacturing drawings.**

![Cooler assembly](../../preview/cooler-study-assembly.png)

| Review asset | Purpose |
|---|---|
| [Assembly STEP](g48r-reference.step) | Cooler plus optional board/module context and mounting-axis references |
| [Fit report](fit-review.json) | Source hashes, STEP readback checks, actual-cover intersection trials and unresolved dimensions |
| [Interactive viewer data](view/README.md) | Shared cad-agent viewer meshes; context hidden initially |
| [Low-profile envelope](ws-rdn-601-envelope.step) | Keeps the existing 34 mm WS-RDN-601 option distinct |
| [Study guide](../../docs/cooler-fit-review.md) | Sources, assumptions, clearance results and next measurements |

Individual STEP files are named by component. Names ending in `provisional` are explicitly unconfirmed hardware positions; names ending in `reference` are context. Pipe bends, fins and blades are illustrative. Do not select screw lengths from these files.

Regenerate with `python tools/cooler_fit_review.py`; validate with `python tools/check_cooler_study.py`. This path is separate from the released print package and existing thermal simulation outputs.
