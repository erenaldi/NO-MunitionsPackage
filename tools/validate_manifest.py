#!/usr/bin/env python3
"""Perform local checks that complement NOMNOM's authoritative CI schema."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlparse


REQUIRED_MOD_FIELDS = {"id", "displayName", "description", "authors", "artifacts", "urls"}
REQUIRED_ARTIFACT_FIELDS = {"fileName", "version", "downloadUrl", "category", "type"}


def is_http_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def validate(path: Path, allow_draft: bool) -> list[str]:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read valid JSON: {exc}"]

    errors: list[str] = []
    if not isinstance(manifest, dict):
        return ["top-level JSON value must be an object"]

    missing = REQUIRED_MOD_FIELDS - manifest.keys()
    if missing:
        errors.append(f"missing mod fields: {', '.join(sorted(missing))}")

    if manifest.get("id") != path.stem:
        errors.append("manifest filename must match its id")

    urls = manifest.get("urls")
    if not isinstance(urls, list) or not urls:
        errors.append("urls must be a non-empty array")
    else:
        if not any(isinstance(item, dict) and item.get("name") == "info" for item in urls):
            errors.append("urls must include an info entry")
        for index, item in enumerate(urls):
            if not isinstance(item, dict) or not is_http_url(item.get("url")):
                errors.append(f"urls[{index}] has an invalid URL")

    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        errors.append("artifacts must be a non-empty array")
    else:
        for index, artifact in enumerate(artifacts):
            if not isinstance(artifact, dict):
                errors.append(f"artifacts[{index}] must be an object")
                continue
            missing_artifact = REQUIRED_ARTIFACT_FIELDS - artifact.keys()
            if missing_artifact:
                errors.append(
                    f"artifacts[{index}] missing fields: {', '.join(sorted(missing_artifact))}"
                )
            if not is_http_url(artifact.get("downloadUrl")):
                errors.append(f"artifacts[{index}] has an invalid downloadUrl")
            if artifact.get("type") == "addOn":
                extends = artifact.get("extends")
                if not isinstance(extends, dict) or not {"id", "version"} <= extends.keys():
                    errors.append(f"artifacts[{index}] addon requires extends.id and extends.version")
            artifact_hash = artifact.get("hash", "")
            if not allow_draft and (
                not isinstance(artifact_hash, str)
                or not artifact_hash.startswith("sha256:")
                or "REPLACE" in artifact_hash
            ):
                errors.append(f"artifacts[{index}] requires a release SHA-256 hash")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--allow-draft", action="store_true")
    args = parser.parse_args()

    errors = validate(args.manifest, args.allow_draft)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    state = "draft" if args.allow_draft else "release"
    print(f"Manifest passed local {state} checks: {args.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
