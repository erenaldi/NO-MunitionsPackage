"""Focused tests for export_phantom_unity_mesh validation helpers.

Synthetic-mesh helper tests plus real-source end-to-end coverage: the
approved R5 deployed/retracted STEPs are run through main() and their
source identities are pinned by SHA-256.
"""

import hashlib
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import trimesh

from export_phantom_unity_mesh import (
    BODY_RADIUS_METERS,
    EXPECTED_LABELS,
    LABEL_GROUPS,
    LENGTH_METERS,
    MAX_TRIANGLES,
    MAXIMUM_SPAN_METERS,
    NOZZLE_RECESS_METERS,
    OUTPUT_DIRECTORY,
    OUTPUTS,
    SOURCE,
    STATES,
    classify,
    main,
    validate_bounds,
    validate_groups,
    validate_labels,
    validate_mesh,
    validate_nozzle_recess,
    validate_source,
    to_unity_mesh,
)

MM = 0.001


def all_labels():
    return sorted(EXPECTED_LABELS)


def box_at(center, size):
    mesh = trimesh.creation.box(extents=size)
    mesh.apply_translation(center)
    return mesh


def cylinder_z(radius, height):
    return trimesh.creation.cylinder(radius=radius, height=height, sections=64)


class ValidateSourceTests(unittest.TestCase):
    def test_accepts_only_r5_dart_source(self):
        validate_source(SOURCE)

    def test_rejects_r6_source(self):
        with self.assertRaisesRegex(ValueError, "accepts only"):
            validate_source(Path(__file__).with_name("RDM-9_Phantom_R6_Dart.step"))

    def test_rejects_retracted_source(self):
        with self.assertRaisesRegex(ValueError, "accepts only"):
            validate_source(Path(__file__).with_name("RDM-9_Phantom_R5_Dart_Retracted.step"))


class ValidateLabelsTests(unittest.TestCase):
    def test_ambiguous_mapping_rejected(self):
        with patch.dict(STATES["deployed"]["groups"], {"wrong_group": {"smooth_body"}}):
            with self.assertRaisesRegex(ValueError, "Ambiguous"):
                classify("smooth_body")

    def test_exact_9_labels_map_once_to_four_groups(self):
        mapping = validate_labels(all_labels())
        self.assertEqual(len(mapping), 9)
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

    def test_unknown_label_rejected(self):
        for bogus in ("wing_bogus", "tail_fin_root_4", "bogus_part"):
            with self.assertRaisesRegex(ValueError, "Unclassified"):
                classify(bogus)
        with self.assertRaisesRegex(ValueError, "Unclassified"):
            validate_labels([*all_labels(), "wing_bogus"])


class ValidateMeshTests(unittest.TestCase):
    def test_basis_maps_landmarks_without_mirroring(self):
        points = [(1000, 0, 0), (0, 1000, 0), (0, 0, 1000)]
        shape = SimpleNamespace(tessellate=lambda *args: (
            [SimpleNamespace(X=x, Y=y, Z=z) for x, y, z in points], [(0, 1, 2)]))
        mesh = to_unity_mesh(shape)
        np.testing.assert_allclose(mesh.vertices, [(0, 0, 1), (1, 0, 0), (0, 1, 0)])
        np.testing.assert_array_equal(mesh.faces, [[0, 1, 2]])

    def test_valid_mesh_accepted(self):
        validate_mesh(trimesh.creation.box(), "smooth_body")

    def test_empty_mesh_rejected(self):
        with self.assertRaisesRegex(ValueError, "empty"):
            validate_mesh(trimesh.Trimesh(), "smooth_body")

    def test_nonfinite_vertices_rejected(self):
        mesh = trimesh.creation.box()
        mesh.vertices[0, 0] = np.nan
        with self.assertRaisesRegex(ValueError, "non-finite"):
            validate_mesh(mesh, "smooth_body")

    def test_out_of_range_indices_rejected(self):
        mesh = trimesh.Trimesh(
            vertices=[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]],
            faces=[[0, 1, 2]],
            process=False,
        )
        with self.assertRaisesRegex(ValueError, "out-of-range"):
            validate_mesh(mesh, "smooth_body")

    def test_degenerate_faces_rejected(self):
        mesh = trimesh.Trimesh(
            vertices=[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [2.0, 0.0, 0.0]],
            faces=[[0, 1, 2]],
            process=False,
        )
        with self.assertRaisesRegex(ValueError, "degenerate"):
            validate_mesh(mesh, "smooth_body")


class BoundsTests(unittest.TestCase):
    def make_assembly(self, length=2.8, body_radius=0.1002, span=1.3987):
        assembly = cylinder_z(span * 0.5, length)
        body = cylinder_z(body_radius, length)
        return assembly, body

    def test_landmarks_accepted(self):
        assembly, body = self.make_assembly()
        length, body_radius, maximum_radius, span = validate_bounds(assembly, body)
        self.assertAlmostEqual(length, LENGTH_METERS, places=4)
        self.assertAlmostEqual(body_radius, BODY_RADIUS_METERS, places=4)
        self.assertLessEqual(span, MAXIMUM_SPAN_METERS + 0.001)

    def test_wrong_length_rejected(self):
        assembly, body = self.make_assembly(length=3.0)
        with self.assertRaisesRegex(ValueError, "length"):
            validate_bounds(assembly, body)

    def test_wrong_body_radius_rejected(self):
        assembly, body = self.make_assembly(body_radius=0.09)
        with self.assertRaisesRegex(ValueError, "body radius"):
            validate_bounds(assembly, body)

    def test_off_axis_rejected(self):
        assembly, body = self.make_assembly()
        assembly.apply_translation((0.05, 0.0, 0.0))
        with self.assertRaisesRegex(ValueError, "off-axis"):
            validate_bounds(assembly, body)

    def test_span_limit_rejected(self):
        assembly, body = self.make_assembly(span=1.5)
        with self.assertRaisesRegex(ValueError, "span"):
            validate_bounds(assembly, body)


class GroupTests(unittest.TestCase):
    def make_groups(self, size=(0.2, 0.2, 2.8)):
        return {group: box_at((0.0, 0.0, 0.0), size) for group in OUTPUTS}

    def test_nonempty_watertight_groups_accepted(self):
        total = validate_groups(self.make_groups())
        self.assertGreater(total, 0)

    def test_empty_group_rejected(self):
        grouped = self.make_groups()
        grouped["wings"] = trimesh.Trimesh()
        with self.assertRaisesRegex(ValueError, "empty"):
            validate_groups(grouped)

    def test_open_group_rejected(self):
        grouped = self.make_groups()
        grouped["wings"] = trimesh.Trimesh(
            vertices=[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
            faces=[[0, 1, 2]],
            process=False,
        )
        with self.assertRaisesRegex(ValueError, "watertight"):
            validate_groups(grouped)

    def test_triangle_budget_rejected(self):
        grouped = self.make_groups()
        grouped["wings"] = trimesh.creation.icosphere(subdivisions=6)
        with self.assertRaisesRegex(ValueError, "budget"):
            validate_groups(grouped)


class CandidateOutputTests(unittest.TestCase):
    def test_output_is_phantom_candidate_asset_root(self):
        self.assertEqual(
            OUTPUT_DIRECTORY,
            Path(__file__).parents[1]
            / "unity"
            / "BlueprinterEditor"
            / "Blueprinter-Editor"
            / "Assets"
            / "Blueprinter"
            / "Mods"
            / "PhantomMod"
            / "Models",
        )


class RetractedStateTests(unittest.TestCase):
    RETRACTED_LABELS = [
        "smooth_body",
        "stowed_wing_stack",
        "hinge_fairing",
        "tail_fin_port",
        "tail_fin_starboard",
        "dorsal_fin",
        "ventral_fin",
        "nozzle_lip",
        "nozzle_recess",
    ]

    def test_retracted_labels_classified(self):
        mapping = validate_labels(self.RETRACTED_LABELS, "retracted")
        self.assertEqual(mapping["stowed_wing_stack"], "wings")
        self.assertEqual(mapping["hinge_fairing"], "fairing")
        self.assertEqual(mapping["smooth_body"], "body")
        self.assertEqual(set(mapping.values()), {"body", "wings", "fins", "nozzle", "fairing"})

    def test_retracted_rejects_deployed_labels(self):
        with self.assertRaisesRegex(ValueError, "Unclassified"):
            classify("wing_port", "retracted")

    def test_retracted_source_accepted(self):
        validate_source(
            Path(__file__).with_name("RDM-9_Phantom_R5_Dart_Retracted.step"), "retracted"
        )

    def test_retracted_source_rejects_deployed(self):
        with self.assertRaisesRegex(ValueError, "accepts only"):
            validate_source(SOURCE, "retracted")

    def test_retracted_envelope_accepted(self):
        assembly, body = BoundsTests().make_assembly(span=0.247)
        length, body_radius, maximum_radius, span = validate_bounds(assembly, body, "retracted")
        self.assertLessEqual(maximum_radius, 0.125 + 1e-6)
        self.assertLessEqual(span, 0.247 + 0.001)

    def test_retracted_envelope_rejected(self):
        assembly = trimesh.creation.box(extents=(0.24, 0.24, 2.8))
        body = cylinder_z(BODY_RADIUS_METERS, LENGTH_METERS)
        with self.assertRaisesRegex(ValueError, "carriage"):
            validate_bounds(assembly, body, "retracted")


class NozzleRecessTests(unittest.TestCase):
    """Regression boundary for the issue-005 aft-face z-fighting defect: the
    derived nozzle lip must sit recessed inside the body aft face, never
    coplanar with it and never proud of it."""

    def body_with_aft(self, aft=-1.4):
        return cylinder_z(0.1, 2.8)

    def lip_with_aft(self, aft):
        lip = trimesh.creation.cylinder(radius=0.05, height=0.018, sections=32)
        lip.apply_translation((0.0, 0.0, aft + 0.009))
        return lip

    def test_coplanar_lip_rejected(self):
        with self.assertRaisesRegex(ValueError, "recessed"):
            validate_nozzle_recess(self.body_with_aft(), self.lip_with_aft(-1.4))

    def test_proud_lip_rejected(self):
        with self.assertRaisesRegex(ValueError, "proud"):
            validate_nozzle_recess(self.body_with_aft(), self.lip_with_aft(-1.41))

    def test_recessed_lip_accepted(self):
        validate_nozzle_recess(
            self.body_with_aft(), self.lip_with_aft(-1.4 + NOZZLE_RECESS_METERS)
        )


class RealSourceTests(unittest.TestCase):
    DEPLOYED_SHA256 = "5fb37c9c8a8e8e0c8ab4340948cc748bd5c5e1d28da575568ff2a8ec141e2fb7"
    RETRACTED_SHA256 = "6b86bc3d31891eae564dcd7e658b333fee400ed166a22699e63da99e387841cd"

    def test_deployed_source_hash_pinned(self):
        self.assertEqual(hashlib.sha256(SOURCE.read_bytes()).hexdigest(), self.DEPLOYED_SHA256)

    def test_retracted_source_hash_pinned(self):
        retracted = Path(__file__).with_name("RDM-9_Phantom_R5_Dart_Retracted.step")
        self.assertEqual(
            hashlib.sha256(retracted.read_bytes()).hexdigest(), self.RETRACTED_SHA256
        )

    def test_deployed_end_to_end_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "Models"
            report = main("deployed", output_directory=output, report_path=Path(tmp) / "report.json")
            state = report["states"]["deployed"]
            self.assertEqual(state["sourceSha256"], self.DEPLOYED_SHA256)
            self.assertEqual(set(state["groups"]), set(OUTPUTS))
            self.assertAlmostEqual(state["assembly"]["length"], LENGTH_METERS, places=4)
            self.assertEqual(state["assembly"]["triangles"], 18846)
            nozzle_aft = state["groups"]["nozzle"]["bounds"][0][2]
            body_aft = state["groups"]["body"]["bounds"][0][2]
            self.assertGreaterEqual(nozzle_aft - body_aft, NOZZLE_RECESS_METERS - 1e-6)

    def test_retracted_end_to_end_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "Models"
            report = main("retracted", output_directory=output, report_path=Path(tmp) / "report.json")
            state = report["states"]["retracted"]
            self.assertEqual(state["sourceSha256"], self.RETRACTED_SHA256)
            self.assertEqual(set(state["groups"]), {"body", "wings", "fins", "nozzle", "fairing"})
            self.assertAlmostEqual(state["assembly"]["length"], LENGTH_METERS, places=4)
            self.assertLessEqual(state["assembly"]["maximumRadius"], 0.125 + 1e-6)
            self.assertEqual(state["assembly"]["triangles"], 25192)
            nozzle_aft = state["groups"]["nozzle"]["bounds"][0][2]
            body_aft = state["groups"]["body"]["bounds"][0][2]
            self.assertGreaterEqual(nozzle_aft - body_aft, NOZZLE_RECESS_METERS - 1e-6)

    def test_report_schema_is_canonical(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = main("deployed", output_directory=Path(tmp) / "Models", report_path=Path(tmp) / "report.json")
            self.assertEqual(set(report), {"states"})


if __name__ == "__main__":
    unittest.main()