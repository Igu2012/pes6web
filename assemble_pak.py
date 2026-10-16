#!/usr/bin/env python3
"""Rebuild site/assets/pes6.pak from repository-friendly binary chunks."""
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "payload" / "pes6.pak.manifest.json"


def fail(message: str) -> "NoReturn":
    print(f"PES 6 data assembly failed: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    try:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read manifest: {exc}")

    if manifest.get("format") != "pes6web-pak-chunks-v1":
        fail("unsupported or invalid manifest format")
    target = ROOT / manifest["target"]
    parts_dir = ROOT / "payload" / "pes6.pak.parts"
    expected_size = int(manifest["size"])
    expected_hash = str(manifest["sha256"])

    if target.is_file() and target.stat().st_size == expected_size:
        digest = hashlib.sha256()
        with target.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        if digest.hexdigest() == expected_hash:
            print(f"PES 6 data is ready: {target.relative_to(ROOT)}")
            return 0

    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix="pes6.pak.", suffix=".tmp", dir=target.parent)
    total = 0
    digest = hashlib.sha256()
    try:
        with os.fdopen(fd, "wb") as output:
            for item in manifest["parts"]:
                part = parts_dir / item["file"]
                try:
                    with part.open("rb") as source:
                        part_size = 0
                        for block in iter(lambda: source.read(1024 * 1024), b""):
                            output.write(block)
                            digest.update(block)
                            part_size += len(block)
                            total += len(block)
                except OSError as exc:
                    fail(f"missing/unreadable chunk {part.name}: {exc}")
                if part_size != int(item["bytes"]):
                    fail(f"wrong size for {part.name}: expected {item['bytes']}, got {part_size}")
                print(f"Added {part.name} ({part_size:,} bytes)")
            output.flush()
            os.fsync(output.fileno())

        actual_hash = digest.hexdigest()
        if total != expected_size:
            fail(f"wrong assembled size: expected {expected_size}, got {total}")
        if actual_hash != expected_hash:
            fail(f"SHA-256 mismatch: expected {expected_hash}, got {actual_hash}")
        os.replace(temporary_name, target)
    finally:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass

    print(f"Rebuilt {target.relative_to(ROOT)} ({total:,} bytes; SHA-256 verified)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
