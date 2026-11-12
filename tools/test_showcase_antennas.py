#!/usr/bin/env python3
"""Mesh readback, transform and provenance controls; no vendor files/dependencies."""
import copy
from collections import Counter, defaultdict
import json
import math
from pathlib import Path
import shutil
import struct
import tempfile
import unittest

import showcase_antennas as recipe


class ShowcaseTests(unittest.TestCase):
    def setUp(self):
        self.parameters = json.loads((recipe.ROOT / 'cad/parameters.json').read_text())

    def test_exact_existing_mounts_and_no_cellular_antenna(self):
        self.assertEqual(recipe.mounts(self.parameters), [
            {'label': 'WIFI 1', 'origin_mm': [-2.5, 46.5, 62.0], 'outward_axis': [-1, 0, 0], 'up_axis': [0, 0, 1]},
            {'label': 'WIFI 2', 'origin_mm': [-2.5, 145.5, 62.0], 'outward_axis': [-1, 0, 0], 'up_axis': [0, 0, 1]}])
        # Changing one source centre must move that mesh and leave the other alone.
        shifted = copy.deepcopy(self.parameters)
        shifted['enclosure']['antenna_bulkheads']['positions'][0]['y'] += 1
        before, after = recipe.mounts(self.parameters), recipe.mounts(shifted)
        self.assertEqual(after[0]['origin_mm'], [-2.5, 47.5, 62])
        self.assertEqual(before[1], after[1])

    def test_bad_mount_inputs(self):
        mutations = {
            'units': lambda p: p.update(units='m'),
            'missing': lambda p: p['enclosure']['antenna_bulkheads']['positions'].pop(0),
            'duplicate label': lambda p: p['enclosure']['antenna_bulkheads']['positions'][1].update(label='WIFI 1'),
            'non-Wi-Fi': lambda p: p['enclosure']['antenna_bulkheads']['positions'][0].update(label='GPS 1'),
            'wrong side': lambda p: p['enclosure']['antenna_bulkheads']['positions'][0].update(side='right'),
            'duplicate centre': lambda p: p['enclosure']['antenna_bulkheads']['positions'][1].update(y=46.5),
            'nan': lambda p: p['enclosure']['antenna_bulkheads'].update(z=math.nan),
            'inf': lambda p: p['enclosure']['antenna_bulkheads']['positions'][0].update(y=math.inf),
            'boolean': lambda p: p['enclosure']['antenna_bulkheads'].update(z=True),
            'string': lambda p: p['enclosure']['antenna_bulkheads'].update(z='62'),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                p = copy.deepcopy(self.parameters)
                mutate(p)
                with self.assertRaises(ValueError):
                    recipe.mounts(p)

    def test_stl_readback_closed_oriented_single_component(self):
        artifacts = recipe.artifacts()
        manifest = json.loads(artifacts['manifest.json'])
        for part in manifest['parts']:
            data = artifacts[part['file']]
            count = struct.unpack_from('<I', data, 80)[0]
            self.assertEqual(len(data), 84 + 50 * count)
            self.assertEqual(count, part['triangles'])
            vertices, triangles, edges = set(), [], Counter()
            directed = Counter()
            adjacency = defaultdict(set)
            volume = 0.
            for i in range(count):
                values = struct.unpack_from('<12fH', data, 84 + i * 50)
                a, b, c = [tuple(values[j:j+3]) for j in (3, 6, 9)]
                self.assertTrue(all(math.isfinite(v) for p in (a, b, c) for v in p))
                vertices.update((a, b, c))
                triangles.append((a, b, c))
                u, v = [b[j]-a[j] for j in range(3)], [c[j]-a[j] for j in range(3)]
                cross = (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
                self.assertGreater(sum(x*x for x in cross), 1e-12)
                self.assertGreater(sum(cross[j]*values[j] for j in range(3)), 0)
                volume += (a[0]*(b[1]*c[2]-b[2]*c[1]) + a[1]*(b[2]*c[0]-b[0]*c[2]) + a[2]*(b[0]*c[1]-b[1]*c[0])) / 6
                for x, y in ((a, b), (b, c), (c, a)):
                    edges[tuple(sorted((x, y)))] += 1
                    directed[x, y] += 1
                    adjacency[x].add(y)
                    adjacency[y].add(x)
            self.assertEqual(set(edges.values()), {2}, 'every edge shared by two triangles')
            self.assertTrue(all(directed[y, x] == n for (x, y), n in directed.items()), 'consistent winding')
            self.assertEqual(len(vertices) - len(edges) + count, 2, 'closed sphere topology')
            reached, queue = set(), [next(iter(vertices))]
            while queue:
                p = queue.pop()
                if p not in reached:
                    reached.add(p)
                    queue.extend(adjacency[p] - reached)
            self.assertEqual(reached, vertices, 'one connected component')
            self.assertGreater(volume, 100)
            bounds = [[min(p[i] for p in vertices) for i in range(3)], [max(p[i] for p in vertices) for i in range(3)]]
            self.assertEqual(bounds, part['bounds_mm'])
            expected = [[-19.6, part['mount']['origin_mm'][1]-3.9, 58.1],
                        [-2.5, part['mount']['origin_mm'][1]+3.9, 84.1]]
            for row, want in zip(bounds, expected):
                for actual, target in zip(row, want):
                    self.assertAlmostEqual(actual, target, places=4)
            self.assertAlmostEqual(bounds[1][2] - bounds[0][2], 26., places=4)
            self.assertEqual(recipe.sha(data), part['sha256'])
            self.assertEqual((part['category'], part['display_only'], part['visible']), ('context', True, True))

    def test_determinism_and_committed_provenance(self):
        self.assertEqual(recipe.artifacts(), recipe.artifacts())
        recipe.check()
        manifest = json.loads(recipe.artifacts()['manifest.json'])
        self.assertFalse(manifest['printable'])
        self.assertFalse(manifest['purchase_bom'])
        self.assertFalse(manifest['rf_qualified'])
        self.assertFalse(manifest['physical_fit_verified'])
        self.assertEqual(manifest['mechanical_reference']['mpn'], 'ANT-2.4-CW-RAH-RPS')

    def test_display_context_excluded_from_manufacturing_inputs(self):
        # Existing print inventory is explicit. No accessory ID may enter it or
        # the purchase BOM / release configuration just because STL exists.
        geometry = json.loads((recipe.ROOT / 'exports/geometry-checks.json').read_text())
        manufacturing = '\n'.join((recipe.ROOT / p).read_text() for p in
                                  ('cad-agent.yaml', 'docs/BOM.csv', 'exports/print-review.json'))
        for part in json.loads(recipe.artifacts()['manifest.json'])['parts']:
            self.assertNotIn(part['name'], geometry)
            self.assertNotIn(part['name'], manufacturing)
        self.assertNotIn('showcase-antennas', manufacturing)

    def test_stale_source_artifact_or_manifest_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for path in recipe.INPUTS:
                destination = root / path
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(recipe.ROOT / path, destination)
            output = root / recipe.OUTPUT
            output.mkdir(parents=True)
            original = recipe.artifacts(root)
            for name, data in original.items():
                (output / name).write_bytes(data)
            recipe.check(root)
            for path in recipe.INPUTS:
                with self.subTest(stale_input=path):
                    data = (root / path).read_bytes()
                    (root / path).write_bytes(data + b'\n')
                    with self.assertRaisesRegex(ValueError, 'stale showcase'):
                        recipe.check(root)
                    (root / path).write_bytes(data)
            for name, data in original.items():
                with self.subTest(stale_output=name):
                    (output / name).write_bytes(data + b'bad')
                    with self.assertRaisesRegex(ValueError, 'stale showcase'):
                        recipe.check(root)
                    (output / name).write_bytes(data)
            (output / 'cell_1_antenna.stl').write_bytes(b'bad')
            with self.assertRaisesRegex(ValueError, 'unexpected showcase'):
                recipe.check(root)


if __name__ == '__main__':
    unittest.main()
