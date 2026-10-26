"""Checks that run in CI without the vendor CAD files.

The CAD build needs vendor models (one behind a login), so CI cannot rebuild the parts. Instead it checks that the
committed exports are the ones the local pipeline built and checked:

1. Every print file and cad/parameters.json matches the sha256 recorded by the last pipeline run
   (the package manifest named in cad-agent.yaml, exports/<package>-manifest.json). A mismatch means a part or parameter changed without a rebuild.
2. The last pipeline run passed every design check (exports/review-validation.json).
3. Every STL loads as a single watertight mesh that fits the printer bed.
4. Every local link in ASSEMBLY.md and every README.md resolves.
5. With --tag, the tag matches the revision in cad/parameters.json.

    python tools/ci_check.py [--tag rev0.7]
"""
from pathlib import Path
import argparse, hashlib, json, re, subprocess, sys

R = Path(__file__).resolve().parents[1]
BED = 256.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tag')
    a = ap.parse_args()
    fails = []
    package = re.search(r'^\s*package:\s*\n\s*name:\s*(\S+)', (R / 'cad-agent.yaml').read_text(), re.M)[1]
    manifest = json.loads((R / f'exports/{package}-manifest.json').read_text())
    parts = list(json.loads((R / 'exports/geometry-checks.json').read_text()))
    # Only the printable parts: the manifest also lists assemblies with vendor geometry, which are not in the repo.
    tracked = ['cad/parameters.json'] + [f'exports/{p}.{ext}' for p in parts for ext in ('stl', '3mf', 'step')]
    for k in tracked:
        p = R / k
        if k not in manifest:
            fails.append(f'{k}: not in the manifest')
        elif not p.exists():
            fails.append(f'{k}: missing')
        elif hashlib.sha256(p.read_bytes()).hexdigest() != manifest[k]:
            fails.append(f'{k}: differs from the last pipeline run; rebuild with cad-agent all')
    print(f'manifest: {len(tracked)} files checked')

    val = json.loads((R / 'exports/review-validation.json').read_text())
    for k, v in val.items():
        if k.endswith('_pass') or k.startswith(('all_', 'plastic_')):
            if v is not True:
                fails.append(f'review-validation: {k} is {v}')
    print('review-validation:', 'pass' if not any(f.startswith('review') for f in fails) else 'FAIL')

    import trimesh
    for p in parts:
        m = trimesh.load(R / f'exports/{p}.stl', force='mesh')
        ext = m.bounds[1] - m.bounds[0]
        if not m.is_watertight:
            fails.append(f'{p}.stl: not watertight')
        if len(m.split(only_watertight=False)) != 1:
            fails.append(f'{p}.stl: more than one body')
        if (ext > BED).any():
            fails.append(f'{p}.stl: {ext.round(1).tolist()} exceeds the {BED:.0f} mm bed')
    print(f'stl: {len(parts)} parts loaded')

    pages = ['ASSEMBLY.md'] + [p for p in subprocess.run(['git', 'ls-files', '*README.md'], cwd=R, capture_output=True, text=True, check=True).stdout.split()]
    for page in pages:
        for link in re.findall(r'\]\(([^)\s]+)\)|(?:src|href)="([^"]+)"', (R / page).read_text()):
            link = re.split('[#?]', link[0] or link[1])[0]
            if link and not re.match(r'[a-z]+:', link) and not ((R / page).parent / link).exists():
                fails.append(f'{page}: broken link {link}')
    print(f'readme and assembly links: {len(pages)} pages checked')

    if a.tag:
        rev = 'rev' + json.loads((R / 'cad/parameters.json').read_text())['revision'].split('-')[0]
        if a.tag != rev:
            fails.append(f'tag {a.tag} does not match cad/parameters.json revision ({rev})')

    for f in fails:
        print('FAIL', f)
    print('ok' if not fails else f'{len(fails)} failure(s)')
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
