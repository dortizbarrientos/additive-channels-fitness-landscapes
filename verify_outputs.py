#!/usr/bin/env python3
"""Verify figure outputs listed in commands.tsv and write checksums."""
from __future__ import annotations
import argparse
import csv
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def fmt_time(ts: float) -> str:
    return datetime.fromtimestamp(ts).isoformat(timespec="seconds")


def read_commands(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--commands", default="commands.tsv")
    ap.add_argument("--out", default="_repro_logs/output_checksums.tsv")
    args = ap.parse_args()

    commands = Path(args.commands)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if not commands.exists():
        print(f"ERROR: commands file not found: {commands}")
        return 2

    rows = []
    missing = []
    for row in read_commands(commands):
        status = row.get("status", "")
        cmd = row.get("command", "")
        if status == "TODO" or cmd == "TODO":
            continue
        fig_id = row.get("figure_id", "")
        outputs = [x.strip() for x in row.get("expected_outputs", "").split(",") if x.strip()]
        for out in outputs:
            p = Path(out)
            if not p.exists() or p.stat().st_size == 0:
                missing.append({"figure_id": fig_id, "path": out})
                rows.append({"figure_id": fig_id, "path": out, "exists": "no", "size_bytes": "", "mtime": "", "sha256": ""})
            else:
                rows.append({
                    "figure_id": fig_id,
                    "path": out,
                    "exists": "yes",
                    "size_bytes": str(p.stat().st_size),
                    "mtime": fmt_time(p.stat().st_mtime),
                    "sha256": sha256(p),
                })

    with out_path.open("w", encoding="utf-8", newline="") as fh:
        fieldnames = ["figure_id", "path", "exists", "size_bytes", "mtime", "sha256"]
        w = csv.DictWriter(fh, fieldnames=fieldnames, delimiter="\t")
        w.writeheader()
        for row in rows:
            w.writerow(row)

    print(f"Wrote checksums to {out_path}")
    print(f"Verified {sum(1 for r in rows if r['exists'] == 'yes')} output file(s).")
    if missing:
        print("Missing expected output(s):")
        for m in missing:
            print(f"  {m['figure_id']}: {m['path']}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
