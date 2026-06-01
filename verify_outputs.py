#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path
import sys


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify figure outputs listed in commands.tsv.")
    parser.add_argument("--manifest", default="commands.tsv")
    parser.add_argument("--out", default="_repro_logs/output_checksums.tsv")
    args = parser.parse_args()

    manifest = Path(args.manifest)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    if not manifest.exists():
        print(f"ERROR: missing manifest: {manifest}", file=sys.stderr)
        return 1

    rows_out = []
    missing = []

    with manifest.open(newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        required = {"figure_id", "expected_outputs"}
        if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
            print(f"ERROR: {manifest} does not look like a tab-separated manifest with columns {sorted(required)}", file=sys.stderr)
            print(f"Observed columns: {reader.fieldnames}", file=sys.stderr)
            return 1
        for row in reader:
            fig_id = row["figure_id"]
            outputs = [x.strip() for x in row["expected_outputs"].replace(";", ",").split(",") if x.strip()]
            for item in outputs:
                p = Path(item)
                if not p.exists():
                    missing.append((fig_id, item))
                    rows_out.append({
                        "figure_id": fig_id,
                        "output": item,
                        "exists": "NO",
                        "size_bytes": "",
                        "sha256": "",
                    })
                else:
                    rows_out.append({
                        "figure_id": fig_id,
                        "output": item,
                        "exists": "YES",
                        "size_bytes": str(p.stat().st_size),
                        "sha256": sha256_file(p),
                    })

    with out.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["figure_id", "output", "exists", "size_bytes", "sha256"],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(rows_out)

    if missing:
        print("ERROR: missing expected outputs:", file=sys.stderr)
        for fig_id, item in missing:
            print(f"  {fig_id}: {item}", file=sys.stderr)
        return 1

    print(f"Verified {len(rows_out)} output file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
