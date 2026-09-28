"""Focused tests for export_halberd_unity_mesh validation helpers.

Synthetic meshes only; no CAD sources, no exporter runs, no file writes.
"""

import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import trimesh

from export_halberd_unity_mesh import (
    BOOSTER_GROUPS,
    EXPECTED_LABELS,
    LABEL_GROUPS,
    OUTPUT_DIRECTORY,
    OUTPUTS,
    RADIAL_LIMIT_METERS,
    UPPER_STAGE_GROUPS,
    UNITY_ROOT,
    assert_candidate_output,
    classify,
    validate_bounds,
    validate_labels,
    validate_mesh,
    validate_stage_placement,
    to_unity_mesh,
)
from generate_halberd_detailed import BODY_RADIUS, HALF_LENGTH, LENGTH, SEAM_X

MM = 0.001


def all_labels():
    return sorted(EXPECTED_LABELS)


def box_at(center, size):
    mesh = trimesh.creation.box(extents=size)
    mesh.apply_translation(center)
    return mesh


def cylinder_z(radius, height):
    return trimesh.creation.cylinder(radius=radius, height=height, sections=64)


class ValidateLabelsTests(unittest.TestCase):
    def test_ambiguous_mapping_rejected(self):
        with patch.dict(LABEL_GROUPS, {"wrong_group": {"radome"}}):
            with self.assertRaisesRegex(ValueError, "Ambiguous"):
                classify("radome")

    def test_exact_41_labels_map_once_to_nine_groups(self):
        mapping = validate_labels(all_labels())
        self.assertEqual(len(mapping), 41)
        self.assertEqual(set(mapping.values()), set(OUTPUTS))
        for label, group in mapping.items():
            self.assertIn(label, LABEL_GROUPS[group])

    def test_duplicate_label_rejected(self):
        labels = all_labels()
        labels.append(labels[0])
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            validate_labels(labels)

    def test_missing_label_rejected(self):
        labels = all_labels()[:-1]
        with self.assertRaisesRegex(ValueError, "Missing"):
            validate_labels(labels)

    def test_unknown_prefix_label_rejected(self):
        for bogus in ("intake_bogus", "booster_fin_root_4", "sustainer_fin_4", "bogus_part"):
            with self.assertRaisesRegex(ValueError, "Unclassified"):
                classify(bogus)
        with self.assertRaisesRegex(ValueError, "Unclassified"):
            validate_labels([*all_labels(), "intake_bogus"])


class ValidateMeshTests(unittest.TestCase):
    def test_basis_maps_landmarks_without_mirroring(self):
        points = [(1000, 0, 0), (0, 1000, 0), (0, 0, 1000)]
        shape = SimpleNamespace(tessellate=lambda *args: (
            [SimpleNamespace(X=x, Y=y, Z=z) for x, y, z in points], [(0, 1, 2)]))
        mesh = to_unity_mesh(shape)
        np.testing.assert_allclose(mesh.vertices, [(0, 0, 1), (1, 0, 0), (0, 1, 0)])
        np.testing.assert_array_equal(mesh.faces, [[0, 1, 2]])

    def test_valid_mesh_accepted(self):
        validate_mesh(trimesh.creation.box(), "ramjet_body")

    def test_empty_mesh_rejected(self):
        with self.assertRaisesRegex(ValueError, "empty"):
            validate_mesh(trimesh.Trimesh(), "ramjet_body")

    def test_nonfinite_vertices_rejected(self):
        mesh = trimesh.creation.box()
        mesh.vertices[0, 0] = np.nan
        with self.assertRaisesRegex(ValueError, "non-finite"):
            validate_mesh(mesh, "ramjet_body")

    def test_out_of_range_indices_rejected(self):
        mesh = trimesh.Trimesh(
            vertices=[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]],
            faces=[[0, 1, 2]],
            process=False,
        )
        with self.assertRaisesRegex(ValueError, "out-of-range"):
            validate_mesh(mesh, "ramjet_body")

    def test_degenerate_faces_rejected(self):
        mesh = trimesh.Trimesh(
            vertices=[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [2.0, 0.0, 0.0]],
            faces=[[0, 1, 2]],
            process=False,
        )
        with self.assertRaisesRegex(ValueError, "degenerate"):
            validate_mesh(mesh, "ramjet_body")


class StagePlacementTests(unittest.TestCase):
    def make_grouped(self, upper_z=0.0, booster_z=-1.0):
        grouped = {}
        for group in OUTPUTS:
            if group in UPPER_STAGE_GROUPS:
                grouped[group] = box_at((0.0, 0.0, upper_z), (0.2, 0.2, 0.5))
            else:
                grouped[group] = box_at((0.0, 0.0, booster_z), (0.2, 0.2, 1.0))
        return grouped

    def test_correct_placement_accepted(self):
        validate_stage_placement(self.make_grouped(), SEAM_X * MM)

    def test_upper_group_aft_of_seam_rejected(self):
        grouped = self.make_grouped()
        grouped["body"] = box_at((0.0, 0.0, -2.0), (0.2, 0.2, 1.0))
        with self.assertRaisesRegex(ValueError, "aft of the stage seam"):
            validate_stage_placement(grouped, SEAM_X * MM)

    def test_booster_group_forward_of_seam_rejected(self):
        grouped = self.make_grouped()
        grouped["booster_body"] = box_at((0.0, 0.0, 0.0), (0.2, 0.2, 1.0))
        with self.assertRaisesRegex(ValueError, "forward of the stage seam"):
            validate_stage_placement(grouped, SEAM_X * MM)


class BoundsTests(unittest.TestCase):
    def make_assembly(self, assembly_radius=0.1005, body_radius=0.1005, height=3.367, seam=-0.3367):
        assembly = cylinder_z(assembly_radius, height)
        body = cylinder_z(body_radius, height)
        return assembly, body, seam

    def test_landmarks_accepted(self):
        assembly, body, seam = self.make_assembly()
        length, body_radius, maximum_radius = validate_bounds(assembly, body, seam)
        self.assertAlmostEqual(length, LENGTH * MM, places=4)
        self.assertAlmostEqual(body_radius, BODY_RADIUS * MM, places=4)
        self.assertLessEqual(maximum_radius, RADIAL_LIMIT_METERS)

    def test_wrong_length_rejected(self):
        assembly, body, seam = self.make_assembly(height=3.0)
        with self.assertRaisesRegex(ValueError, "length"):
            validate_bounds(assembly, body, seam)

    def test_wrong_body_radius_rejected(self):
        assembly, body, seam = self.make_assembly(body_radius=0.09)
        with self.assertRaisesRegex(ValueError, "body radius"):
            validate_bounds(assembly, body, seam)

    def test_radial_limit_rejected(self):
        assembly, body, seam = self.make_assembly(assembly_radius=0.22)
        with self.assertRaisesRegex(ValueError, "maximum radius"):
            validate_bounds(assembly, body, seam)

    def test_wrong_seam_rejected(self):
        assembly, body, seam = self.make_assembly(seam=-0.3)
        with self.assertRaisesRegex(ValueError, "seam"):
            validate_bounds(assembly, body, seam)


class CandidateOutputTests(unittest.TestCase):
    def test_default_output_is_candidate_directory(self):
        self.assertEqual(OUTPUT_DIRECTORY, Path(__file__).parents[1] / "candidates" / "halberd")

    def test_unity_assets_output_forbidden(self):
        assets = UNITY_ROOT / "BlueprinterEditor" / "Blueprinter-Editor" / "Assets"
        with self.assertRaisesRegex(ValueError, "must not write under"):
            assert_candidate_output(assets)

    def test_candidate_output_allowed(self):
        assert_candidate_output(OUTPUT_DIRECTORY)


if __name__ == "__main__":
    unittest.main()
