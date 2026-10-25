[J501 AGX Orin](../README.md) / **references**

# References

Vendor models, datasheets and schematics the design is measured from, plus the measurements taken from them.

**The vendor files are not in this repository**, because they are not ours to redistribute. [`sources.json`](sources.json) lists each
one with its original URL and sha256. To download them and rebuild the caches the build reads:

```bash
.venv/bin/python tools/fetch_references.py   # the NVIDIA module model needs a developer login; the script says where
```

<p align="center">
  <img src="../preview/part-carrier.png" alt="The J501 carrier board model" width="720">
</p>

## What is in the repository

| File | What it is |
|---|---|
| [`sources.json`](sources.json) | Every vendor file: ID, original URL, date retrieved, sha256 |
| [`extra-source-urls.json`](extra-source-urls.json) | Other pages consulted |
| [`seeed-oshw-tree.json`](seeed-oshw-tree.json) | Index of Seeed's open-hardware file tree, used to find the models |
| [`measurements.log`](measurements.log) | Log of the measurements taken from the board model |
| [`solids.json`](solids.json) | Every solid in the carrier board model, with its bounding box |
| [`edge-components.json`](edge-components.json) | Connectors along the board edges, which the plate cutouts follow |
| [`mount-features.json`](mount-features.json) | Mounting holes and features |
| [`pcb-circles.json`](pcb-circles.json), [`pcb-hole-fits.json`](pcb-hole-fits.json) | PCB holes and their fitted diameters |
| [`open-shells.json`](open-shells.json) | Surface shells in the board model that are not closed solids |
| [`pcb-outline.step`](pcb-outline.step), [`pcb-outline.stl`](pcb-outline.stl) | The PCB outline on its own |
| [`hardware/`](hardware/) | Connector meshes (downloaded) and their index |

## Vendor sources

| ID | File | Source |
|---|---|---|
| S01 | `RESERVER_AGX_ORIN_CARRIER_BOARD.stp` | [files.seeedstudio.com](https://files.seeedstudio.com/wiki/reComputer-Jetson/J501/RESERVER_AGX_ORIN_CARRIER_BOARD.stp) |
| S02 | `reServer_Industrial_J501_Carrier_Board_Datasheet.pdf` | [files.seeedstudio.com](https://files.seeedstudio.com/wiki/reComputer-Jetson/J501/reServer_Industrial_J501_Carrier_Board_Datasheet.pdf) |
| S03 | `323011387Jetson_AGX_Orin_Heatsink_100x87x34mm-datasheet.pdf` | [files.seeedstudio.com](https://files.seeedstudio.com/wiki/reComputer-Jetson/J501/323011387Jetson_AGX_Orin_Heatsink_100x87x34mm-datasheet.pdf) |
| S04 | `GMSL2_Adapter_Board_For_J501_v1_SCH.pdf` | [files.seeedstudio.com](https://files.seeedstudio.com/wiki/reComputer-Jetson/J501/GMSL2_Adapter_Board_For_J501_v1_SCH.pdf) |
| S05 | `100099421.pdf` | [files.seeedstudio.com](https://files.seeedstudio.com/Bazaar/product_pdf/100099421.pdf) |
| S06 | `reComputer_Mini_J501_Fan.pdf` | [files.seeedstudio.com](https://files.seeedstudio.com/products/NVIDIA-Jetson/reComputer_Mini_J501_Fan.pdf) |
| S07 | `202003906_reServer_Industrial_J501_Carrier_Board_v1.0_SCH_PDF_20240529.pdf` | [files.seeedstudio.com](https://files.seeedstudio.com/wiki/reComputer-Jetson/J501/202003906_reServer_Industrial_J501_Carrier_Board_v1.0_SCH_PDF_20240529.pdf) |
| S08 | `samtec-qsh-qth.pdf` | [suddendocs.samtec.com](https://suddendocs.samtec.com/catalog_english/qsh.pdf) |
| S09 | `Jetson_AGX_Orin_Module_3D_STEP_Model.zip` | [developer.nvidia.com](https://developer.nvidia.com/downloads/jetson-agx-orin-module-3d-step-modelzip) |
| S10 | `FM4-NZRP-PCB-1.stp` | [s3-us-west-2.amazonaws.com](https://s3-us-west-2.amazonaws.com/catsy.582/FM4-NZRP-PCB-1.stp) |
| S11 | `FM4-NXRP-PCB-1.pdf` | [s3-us-west-2.amazonaws.com](https://s3-us-west-2.amazonaws.com/catsy.582/FM4-NXRP-PCB-1.pdf) |
| S12 | `gmsl_connectoin.png` | [files.seeedstudio.com](https://files.seeedstudio.com/wiki/reComputer-Jetson/J501/gmsl_connectoin.png) |
| S13 | `gmsl.png` | [files.seeedstudio.com](https://files.seeedstudio.com/wiki/reComputer-Jetson/J501/gmsl.png) |
| S14 | `seeed-oshw-tree.json` | [api.github.com](https://api.github.com/repos/Seeed-Studio/OSHW-Jetson-Series/git/trees/main?recursive=1) |
| S15 | `interfaces.html` | [wiki.seeedstudio.com](https://wiki.seeedstudio.com/j501_carrier_board_interfaces_usage/) |
| S16 | `foxconn-QJ3119C-WFB1-4F.pdf` | [static.chipdip.ru](https://static.chipdip.ru/lib/340/DOC042340960.pdf) |

## Folders

| Folder | What is in it |
|---|---|
| [`hardware/`](hardware/) | Carrier connector meshes |
