"""Saved-artifact validation for the A4 side-slot restoration gate.

The A3 saved-artifact checker supplies the established geometry, contact,
topology, envelope, and 21-pose checks. Its inputs are isolated here to A4,
with independently stated A4 slot bounds; this checker then adds saved A4/A3
identity and restoration-region assertions.
"""
import contextlib
import io
import json
from pathlib import Path
import sys
import traceback

import build123d as bd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import check_interleaved_a3 as a3check  # noqa: E402

BODY = a3check.BODY
BODY_TOL_MM3 = a3check.BODY_TOL_MM3
REPORT_PATH = ROOT / "reviews/interleaved_a4_checks.json"

# These are the A4 cutters restated explicitly for the saved-body comparison.
A4_SLOT_EXTENTS_MM = (
    (-430.0, 530.0, 0.0, 100.0, 65.7, 70.3),
    (-430.0, 530.0, 0.0, 100.0, 76.2, 80.8),
    (-430.0, 530.0, -100.0, 0.0, 71.2, 75.8),
    (-430.0, 530.0, -100.0, 0.0, 81.7, 86.3),
)
RESTORATION_REGIONS_MM = {
    "starboard_rear": (-430.0, 530.0, -100.0, 0.0, 65.7, 70.3),
    "starboard_front": (-430.0, 530.0, -100.0, 0.0, 76.2, 80.8),
    "port_rear": (-430.0, 530.0, 0.0, 100.0, 71.2, 75.8),
    "port_front": (-430.0, 530.0, 0.0, 100.0, 81.7, 86.3),
}
SAVED_STATES = {
    "Stowed": "Stowed",
    "Module_Stowed": "Module_Stowed",
    "Midfold": "Midfold",
    "Deployed": "Deployed",
    "Body_Pocket": "Body_Pocket",
}
A4_PATHS = {
    state: ROOT / f"STEP/O_Interleaved_A4_{suffix}.step"
    for state, suffix in SAVED_STATES.items()
}
A3_PATHS = {
    state: ROOT / f"STEP/O_Interleaved_A3_{suffix}.step"
    for state, suffix in SAVED_STATES.items()
}
A2_STOWED_PATH = ROOT / "STEP/O_Interleaved_A2_Stowed.step"
FULL_BODY_STATES = ("Stowed", "Midfold", "Deployed", "Body_Pocket")


def volume(shape):
    return 0.0 if shape is None else float(shape.volume)


def make_box(extents):
    x0, x1, y0, y1, z0, z1 = extents
    return bd.Box(x1 - x0, y1 - y0, z1 - z0).translate(
        ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
    )


def union(shapes):
    result = shapes[0]
    for shape in shapes[1:]:
        result = result + shape
    return result.clean()


def symdiff_volume(a, b):
    return volume(a - b) + volume(b - a)


def configure_a3_checker():
    """Point the reusable A3 checks only at A4 saved artifacts and bounds."""
    a3check.A3_PATHS = dict(A4_PATHS)
    a3check.REPORT_PATH = REPORT_PATH
    a3check.SLOT_EXTENTS_MM = A4_SLOT_EXTENTS_MM


def add_restoration_checks(report):
    failures = report.setdefault("failures", [])

    def fail(check, **detail):
        failures.append({"check": check, **detail})

    result = {
        "a4_vs_a3_label_identity": {},
        "a4_vs_a3_nonbody_identity_mm3": {},
        "body_restoration_by_saved_artifact": {},
        "restoration_regions_mm": {
            label: list(extents) for label, extents in RESTORATION_REGIONS_MM.items()
        },
        "tolerance_mm3": BODY_TOL_MM3,
    }
    a4_parts = {}
    a3_parts = {}
    try:
        for state, path in A4_PATHS.items():
            try:
                a4_parts[state], duplicates = a3check.parts_from_step(path)
                if duplicates:
                    fail("duplicate A4 labels", state=state, labels=duplicates)
            except Exception as exc:
                fail("A4 supplemental STEP import", state=state, path=str(path), error=repr(exc))
                a4_parts[state] = {}
            try:
                a3_parts[state], duplicates = a3check.parts_from_step(A3_PATHS[state])
                if duplicates:
                    fail("duplicate A3 reference labels", state=state, labels=duplicates)
            except Exception as exc:
                fail("A3 reference STEP import", state=state, path=str(A3_PATHS[state]), error=repr(exc))
                a3_parts[state] = {}

            current, reference = a4_parts[state], a3_parts[state]
            # STEP exports of the isolated Body_Pocket use the enclosing
            # document label rather than the body's component label. Validate
            # its one-body inventory and geometry separately below.
            pocket_artifact = state == "Body_Pocket"
            label_identity = set(current) == set(reference)
            if pocket_artifact:
                label_identity = len(current) == len(reference) == 1
            if not label_identity:
                fail("A4/A3 saved labels differ", state=state,
                     missing=sorted(set(reference) - set(current)),
                     extra=sorted(set(current) - set(reference)))
            body_expected = state in FULL_BODY_STATES[:-1]
            if (BODY in current) != body_expected:
                fail("A4 saved body label presence", state=state,
                     expected=body_expected, actual=BODY in current)
            result["a4_vs_a3_label_identity"][state] = {
                "a4_labels": sorted(current),
                "a3_labels": sorted(reference),
                "identical_or_single_body_document": label_identity,
                "body_document_root_label_alias": pocket_artifact,
                "body_label_present": BODY in current,
                "single_body_artifact": pocket_artifact and len(current) == 1 and len(reference) == 1,
            }

            nonbody_deltas = {}
            for label in sorted((set(current) & set(reference)) - {BODY}) if not pocket_artifact else ():
                try:
                    delta = symdiff_volume(current[label], reference[label])
                    nonbody_deltas[label] = delta
                    if delta > BODY_TOL_MM3:
                        fail("A4 nonbody geometry differs from saved A3", state=state,
                             label=label, difference_mm3=delta)
                except Exception as exc:
                    fail("A4/A3 nonbody comparison failed", state=state,
                         label=label, error=repr(exc))
            if not pocket_artifact:
                result["a4_vs_a3_nonbody_identity_mm3"][state] = {
                    "part_count": len(nonbody_deltas),
                    "part_symmetric_difference_mm3": nonbody_deltas,
                    "maximum_difference_mm3": max(nonbody_deltas.values()) if nonbody_deltas else None,
                }
            else:
                pocket_delta = None
                if len(current) == 1 and len(reference) == 1:
                    pocket_delta = symdiff_volume(next(iter(current.values())), next(iter(reference.values())))
                result["body_pocket_vs_a3_delta_mm3"] = pocket_delta

        # Each body-bearing A4 artifact retains the complete A3 body and adds
        # material only inside the four opposite-side channels, within A2.
        a2_parts, a2_duplicates = a3check.parts_from_step(A2_STOWED_PATH)
        if a2_duplicates:
            fail("duplicate A2 body source labels", labels=a2_duplicates)
        original = a2_parts.get(BODY)
        if original is None:
            fail("original A2 body label missing", label=BODY)

        allowed = union([make_box(extents) for extents in RESTORATION_REGIONS_MM.values()])
        for state in FULL_BODY_STATES:
            current = a4_parts.get(state, {})
            reference = a3_parts.get(state, {})
            if state == "Body_Pocket":
                a4_body = next(iter(current.values())) if len(current) == 1 else None
                a3_body = next(iter(reference.values())) if len(reference) == 1 else None
            else:
                a4_body, a3_body = current.get(BODY), reference.get(BODY)
            if a4_body is None or a3_body is None or original is None:
                fail("body restoration comparison unavailable", state=state,
                     has_a4_body=a4_body is not None, has_a3_body=a3_body is not None,
                     has_a2_body=original is not None)
                continue
            try:
                removed_from_a3 = volume(a3_body - a4_body)
                restored = (a4_body - a3_body).clean()
                outside_a2 = volume(a4_body - original)
                changed = union([restored, (a3_body - a4_body).clean()])
                outside_allowed = volume((changed - allowed).clean())
                slot_volumes = {
                    label: volume(restored & make_box(extents))
                    for label, extents in RESTORATION_REGIONS_MM.items()
                }
                result["body_restoration_by_saved_artifact"][state] = {
                    "a3_material_removed_mm3": removed_from_a3,
                    "restored_material_mm3": volume(restored),
                    "a4_material_outside_original_a2_mm3": outside_a2,
                    "material_change_outside_four_opposite_side_slots_mm3": outside_allowed,
                    "restored_volume_by_channel_mm3": slot_volumes,
                }
                if removed_from_a3 > BODY_TOL_MM3:
                    fail("A3 body material removed in A4", state=state,
                         removed_mm3=removed_from_a3)
                if outside_a2 > BODY_TOL_MM3:
                    fail("A4 body adds material beyond original A2", state=state,
                         outside_a2_mm3=outside_a2)
                if outside_allowed > BODY_TOL_MM3:
                    fail("A4 body changes material outside four opposite-side slots",
                         state=state, outside_allowed_mm3=outside_allowed)
                for label, restored_volume in slot_volumes.items():
                    if restored_volume <= 0.0:
                        fail("opposite-side channel has no positive restored volume",
                             state=state, channel=label, restored_mm3=restored_volume)
            except Exception as exc:
                fail("body restoration measurement failed", state=state, error=repr(exc),
                     traceback=traceback.format_exc())
    except Exception as exc:
        fail("A4 supplemental checks aborted", error=repr(exc), traceback=traceback.format_exc())

    report["a4_restoration_checks"] = result
    report["artifact_prefix"] = "O_Interleaved_A4"
    report["scope"] = (
        "Five saved A4 STEP artifacts; exact A2 body-minus-well-and-side-slots; "
        "A4/A3 nonbody identity in all four component states; retained A3 body "
        "and channel-limited restoration; topology, datums, contacts, and 21 "
        "simultaneous rigid-motion samples. Continuous sweep, strength, actuation, locks, and rack are unverified."
    )


def main():
    configure_a3_checker()
    # The inherited checker writes its structured report; suppress its interim
    # console summary so only the final augmented result is emitted.
    with contextlib.redirect_stdout(io.StringIO()):
        status = a3check.main()
    try:
        report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        print(json.dumps({"passed": False, "report": str(REPORT_PATH),
                          "failure": "could not reload inherited report", "error": repr(exc)}, indent=2))
        return 1

    add_restoration_checks(report)
    report["passed"] = not report.get("failures")
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    restoration = report.get("a4_restoration_checks", {})
    body = restoration.get("body_restoration_by_saved_artifact", {})
    nonbody = restoration.get("a4_vs_a3_nonbody_identity_mm3", {})
    print(json.dumps({
        "passed": report["passed"],
        "inherited_checker_status": status,
        "report": str(REPORT_PATH),
        "saved_artifacts_checked": len(report.get("artifacts", {})),
        "a4_a3_nonbody_states_checked": len(nonbody),
        "a4_a3_nonbody_max_delta_mm3_by_state": {
            state: data.get("maximum_difference_mm3") for state, data in nonbody.items()
        },
        "body_restoration_artifacts_checked": len(body),
        "body_restoration_metrics": body,
        "motion_samples": len(report.get("motion_samples", [])),
        "failure_count": len(report.get("failures", [])),
        "failures": report.get("failures", []),
    }, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
