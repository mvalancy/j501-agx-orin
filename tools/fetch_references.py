"""Download the vendor reference files listed in references/sources.json and rebuild the derived caches.

Vendor CAD models, datasheets and schematics are not redistributed in this repository. This script fetches each one
from its original URL, verifies the recorded sha256, then rebuilds the BREP caches and hardware meshes the build uses.

    python tools/fetch_references.py            # download missing files, verify, rebuild caches
    python tools/fetch_references.py --verify   # only report which files are present and match

The NVIDIA module model (S09) sits behind a developer login: download it in a browser from the URL printed and save
it as references/Jetson_AGX_Orin_Module_3D_STEP_Model.zip, then run this script again.
"""
from pathlib import Path
import argparse, hashlib, json, subprocess, sys, urllib.request, zipfile

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / 'references'
MANUAL = {'S09'}


def sha256(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def fetch(src):
    p = REF / src['file']
    if p.exists():
        return sha256(p) == src['sha256'] or print(f"{src['id']} {src['file']}: present but sha256 differs (vendor may have revised it)")
    if src['id'] in MANUAL:
        print(f"{src['id']} {src['file']}: download manually (login required) from {src['url']}")
        return False
    print(f"{src['id']} downloading {src['file']}", flush=True)
    tmp = p.with_suffix(p.suffix + '.part')
    req = urllib.request.Request(src['url'], headers={'User-Agent': 'j501-agx-fetch/1.0'})
    with urllib.request.urlopen(req, timeout=120) as r, tmp.open('wb') as f:
        while chunk := r.read(1 << 20):
            f.write(chunk)
    tmp.rename(p)
    ok = sha256(p) == src['sha256']
    print(f"   sha256 {'ok' if ok else 'DIFFERS from the recorded value (vendor may have revised it)'}")
    return ok


def caches():
    import cadquery as cq
    def brep(step, out):
        if not out.exists():
            print('caching', out.relative_to(ROOT), flush=True)
            cq.importers.importStep(str(step)).val().exportBrep(str(out))
    z = REF / 'Jetson_AGX_Orin_Module_3D_STEP_Model.zip'
    mod = REF / 'nvidia-module'
    if z.exists() and not (mod / 'p3701-sku0-simplified.stp').exists():
        mod.mkdir(exist_ok=True)
        with zipfile.ZipFile(z) as f:
            f.extract('p3701-sku0-simplified.stp', mod)
    for step, out in [(REF / 'RESERVER_AGX_ORIN_CARRIER_BOARD.stp', REF / 'carrier.brep'),
                      (REF / 'FM4-NZRP-PCB-1.stp', REF / 'FM4-NZRP-PCB-1.brep'),
                      (mod / 'p3701-sku0-simplified.stp', mod / 'p3701-sku0-simplified.brep')]:
        if step.exists():
            brep(step, out)
    if (REF / 'carrier.brep').exists() and not (REF / 'hardware/carrier-full.stl').exists():
        for tool in ('export_hardware.py', 'export_open_shells.py'):
            subprocess.run([sys.executable, str(ROOT / 'tools' / tool)], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--verify', action='store_true')
    a = ap.parse_args()
    sources = json.loads((REF / 'sources.json').read_text())
    if a.verify:
        for s in sources:
            p = REF / s['file']
            print(f"{s['id']} {'missing' if not p.exists() else 'ok' if sha256(p) == s['sha256'] else 'differs'}  {s['file']}")
        return 0
    results = [fetch(s) for s in sources]
    caches()
    print(f'{sum(map(bool, results))}/{len(results)} reference files present and verified')
    return 0


if __name__ == '__main__':
    sys.exit(main())
