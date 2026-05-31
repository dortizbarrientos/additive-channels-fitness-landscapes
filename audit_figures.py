#!/usr/bin/env python3
r"""
Audit figure provenance for the Additive Channels / GENETICS manuscript.

v3 changes relative to the earlier audit script
----------------------------------------------
1. Uses smart defaults for the actual mixed working tree:
   code/, figures/, toSubmit/, revision/additive_channels_final_verification_package/,
   revision/figures/, and revision/tex/additiveChannels/additiveChannels/.
2. Avoids Path.rglob() and catches cloud-sync timeouts.
3. Reads TeX \graphicspath entries and scans existing graphicspath folders too.
4. Inspects zip archives without extracting them. This matters because this project
   contains figure2.zip, figure3.zip, figure4.zip, and final-verification packages.
5. Produces two kinds of evidence:
   - exact final figure locations, including files inside zip archives;
   - likely source-code candidates and likely old-name/renamed-figure candidates.

Typical run from the 5_geneticsS1 repository root:

    python audit_figures.py \
      --root . \
      --tex toSubmit/main_paper_with_page_lines.tex \
      --exclude figsPaper2 \
      --exclude oldMain \
      --exclude supportingOnline \
      --exclude channelSwitching \
      --exclude dynamicClosure

If you want to be very explicit instead of using smart defaults, add repeated --scan-dir
arguments. Zip inspection is on by default; disable with --no-inspect-zips.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import os
import re
import sys
import zipfile
from dataclasses import dataclass
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Sequence, Tuple

FIG_EXTS = {".pdf", ".png", ".jpg", ".jpeg", ".svg", ".eps", ".tif", ".tiff"}
CODE_EXTS = {".py", ".r", ".R", ".jl", ".m", ".sh", ".slim", ".wl", ".nb", ".ipynb", ".tex"}
ZIP_EXTS = {".zip"}
DEFAULT_IGNORE_DIRS = {
    ".git", "__pycache__", ".Rproj.user", ".ipynb_checkpoints",
    "_figure_audit", "_repro_logs", "node_modules", ".snakemake",
}
RETIRE_TOKENS = {"retired", "old", "archive", "deprecated"}
DEFAULT_EXCLUDES = ["figsPaper2", "oldMain", "supportingOnline", "channelSwitching", "dynamicClosure"]
SMART_SCAN_DIRS = [
    "toSubmit",
    "code",
    "figures",
    "additiveChannels",
    "revision/additive_channels_final_verification_package",
    "revision/figures",
    "revision/tex/additiveChannels/additiveChannels",
    "revision/tex/additiveChannels/additive_channels_v3_CG_fixed_package",
]
INCLUDE_RE = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}")
GRAPHICSPATH_RE = re.compile(r"\\graphicspath\s*\{((?:\s*\{[^{}]*\}\s*)+)\}")
BRACED_PATH_RE = re.compile(r"\{([^{}]+)\}")


@dataclass(frozen=True)
class CodeCandidate:
    display_path: str
    text: str
    location_type: str


@dataclass(frozen=True)
class FigureCandidate:
    display_path: str
    basename: str
    stem: str
    location_type: str
    size_bytes: str = ""
    mtime: str = ""
    sha1_first_mb: str = ""


def fmt_time(ts: Optional[float]) -> str:
    if ts is None:
        return ""
    try:
        return datetime.fromtimestamp(ts).isoformat(timespec="seconds")
    except Exception:
        return ""


def stat_times(path: Path) -> Dict[str, str]:
    try:
        st = path.stat()
    except OSError:
        return {"mtime": "", "ctime_metadata_change": "", "birthtime_if_available": "", "size_bytes": ""}
    birth = getattr(st, "st_birthtime", None)
    return {
        "mtime": fmt_time(st.st_mtime),
        "ctime_metadata_change": fmt_time(st.st_ctime),
        "birthtime_if_available": fmt_time(birth),
        "size_bytes": str(st.st_size),
    }


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")


def clean_path_text(s: str) -> str:
    return s.strip().replace("\\", "/")


def tokens(s: str) -> set[str]:
    stem = Path(str(s)).stem.lower()
    return {t for t in re.split(r"[^a-z0-9]+", stem) if t and len(t) > 1}


def read_text_safely(path: Path, max_bytes: int = 2_000_000) -> str:
    try:
        return path.read_bytes()[:max_bytes].decode("utf-8", errors="ignore")
    except Exception:
        return ""


def sha1_file(path: Path, max_bytes: Optional[int] = None) -> str:
    h = hashlib.sha1()
    try:
        with path.open("rb") as fh:
            if max_bytes is None:
                for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                    h.update(chunk)
            else:
                h.update(fh.read(max_bytes))
        return h.hexdigest()
    except OSError:
        return ""


def sha1_zip_member(zf: zipfile.ZipFile, member: str, max_bytes: Optional[int] = None) -> str:
    h = hashlib.sha1()
    try:
        with zf.open(member, "r") as fh:
            remaining = max_bytes
            while True:
                if remaining is None:
                    chunk = fh.read(1024 * 1024)
                else:
                    if remaining <= 0:
                        break
                    chunk = fh.read(min(1024 * 1024, remaining))
                    remaining -= len(chunk)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return ""


def write_tsv(path: Path, rows: List[Dict[str, str]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow(row)


def path_matches_exclude(path: Path, root: Path, excludes: Sequence[str]) -> Optional[str]:
    try:
        rel_s = rel(path, root).lower().strip("/")
    except Exception:
        rel_s = str(path).replace("\\", "/").lower().strip("/")
    parts = set(rel_s.split("/")) | {p.lower() for p in path.parts}
    for ex in excludes:
        exn = clean_path_text(ex).lower().strip("/")
        if not exn:
            continue
        if exn in parts or rel_s == exn or rel_s.startswith(exn + "/") or ("/" + exn + "/") in ("/" + rel_s + "/"):
            return ex
    return None


def safe_scandir(path: Path, root: Path, skipped: List[Dict[str, str]]) -> List[os.DirEntry]:
    try:
        with os.scandir(path) as it:
            return list(it)
    except BaseException as e:  # includes TimeoutError from cloud folders
        skipped.append({"path": rel(path, root), "reason": f"scandir failed: {type(e).__name__}: {e}"})
        return []


def iter_tree(start: Path, root: Path, excludes: Sequence[str], include_retired: bool,
              max_depth: Optional[int], skipped: List[Dict[str, str]]) -> Iterator[Path]:
    stack: List[Tuple[Path, int]] = [(start.resolve(), 0)]
    seen: set[Path] = set()
    while stack:
        current, depth = stack.pop()
        if current in seen:
            continue
        seen.add(current)
        ex = path_matches_exclude(current, root, excludes)
        if ex:
            skipped.append({"path": rel(current, root), "reason": f"excluded by --exclude {ex}"})
            continue
        if max_depth is not None and depth > max_depth:
            skipped.append({"path": rel(current, root), "reason": f"max depth {max_depth} reached"})
            continue
        for ent in safe_scandir(current, root, skipped):
            p = Path(ent.path)
            if ent.name in DEFAULT_IGNORE_DIRS:
                skipped.append({"path": rel(p, root), "reason": "default ignored"})
                continue
            try:
                is_dir = ent.is_dir(follow_symlinks=False)
                is_file = ent.is_file(follow_symlinks=False)
            except OSError as e:
                skipped.append({"path": rel(p, root), "reason": f"stat failed: {type(e).__name__}: {e}"})
                continue
            if is_dir:
                lower_parts = {part.lower() for part in p.parts}
                if (not include_retired) and (lower_parts & RETIRE_TOKENS):
                    skipped.append({"path": rel(p, root), "reason": "retired/old/archive skipped; use --include-retired"})
                    continue
                stack.append((p, depth + 1))
            elif is_file:
                yield p.resolve()


def resolve_scan_roots(root: Path, scan_dirs: Sequence[str], skipped: List[Dict[str, str]]) -> List[Path]:
    out: List[Path] = []
    for sd in scan_dirs:
        p = Path(sd)
        if not p.is_absolute():
            p = root / p
        if p.exists() and p.is_dir():
            rp = p.resolve()
            if rp not in out:
                out.append(rp)
        else:
            skipped.append({"path": rel(p, root), "reason": "scan-dir does not exist"})
    return out


def parse_includes(tex_path: Path) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for i, line in enumerate(tex_path.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
        for m in INCLUDE_RE.finditer(line):
            inc = m.group(1).strip()
            rows.append({
                "tex_line": str(i),
                "include": inc,
                "basename": Path(inc).name,
                "stem": Path(inc).stem,
                "extension": Path(inc).suffix,
            })
    return rows


def parse_graphicspaths(tex_path: Path) -> List[Dict[str, str]]:
    text = tex_path.read_text(encoding="utf-8", errors="ignore")
    rows: List[Dict[str, str]] = []
    for m in GRAPHICSPATH_RE.finditer(text):
        line = text[:m.start()].count("\n") + 1
        for pm in BRACED_PATH_RE.finditer(m.group(1)):
            rows.append({"tex_line": str(line), "graphicspath": pm.group(1).strip()})
    return rows


def graphicspath_scan_dirs(root: Path, tex_path: Path, graphicspaths: List[Dict[str, str]]) -> List[str]:
    out: List[str] = []
    for row in graphicspaths:
        gp = clean_path_text(row["graphicspath"]).strip()
        # Do not add bare ./ or . from \graphicspath; that would turn a focused
        # audit back into a whole-tree crawl on large OneDrive directories.
        if gp in {".", "./", ""}:
            continue
        # TeX graphicspaths can be interpreted relative to the compile dir or the TeX file.
        for base in (root, tex_path.parent):
            p = (base / gp).resolve()
            if p.exists() and p.is_dir():
                try:
                    out.append(rel(p, root))
                except Exception:
                    out.append(str(p))
    # Keep order but remove duplicates.
    seen: set[str] = set()
    unique: List[str] = []
    for x in out:
        if x not in seen:
            seen.add(x)
            unique.append(x)
    return unique


def find_tex(root: Path, tex_arg: str, skipped: List[Dict[str, str]]) -> Path:
    tex = Path(tex_arg)
    if not tex.is_absolute():
        tex = root / tex
    if tex.exists():
        return tex.resolve()
    # Focused fallback: common locations, not a full crawl.
    for cand in [root / "toSubmit" / Path(tex_arg).name, root / Path(tex_arg).name]:
        if cand.exists():
            return cand.resolve()
    print(f"ERROR: TeX file not found: {tex.resolve()}", file=sys.stderr)
    return tex.resolve()


def collect_files(root: Path, scan_dirs: Sequence[str], exts: set[str], excludes: Sequence[str],
                  include_retired: bool, max_depth: Optional[int], skipped: List[Dict[str, str]]) -> List[Path]:
    roots = resolve_scan_roots(root, scan_dirs, skipped)
    out: List[Path] = []
    low_exts = {e.lower() for e in exts}
    for sr in roots:
        for p in iter_tree(sr, root, excludes, include_retired, max_depth, skipped):
            if p.suffix.lower() in low_exts:
                out.append(p)
    return sorted(set(out), key=lambda p: rel(p, root))


def read_zip_text(zf: zipfile.ZipFile, member: str, max_bytes: int = 2_000_000) -> str:
    try:
        with zf.open(member, "r") as fh:
            return fh.read(max_bytes).decode("utf-8", errors="ignore")
    except Exception:
        return ""


def inspect_zips(zip_files: List[Path], root: Path, wanted_basenames: set[str]) -> Tuple[List[Dict[str, str]], List[FigureCandidate], List[CodeCandidate], List[Dict[str, str]]]:
    inventory: List[Dict[str, str]] = []
    fig_members: List[FigureCandidate] = []
    code_members: List[CodeCandidate] = []
    errors: List[Dict[str, str]] = []
    for zp in zip_files:
        try:
            with zipfile.ZipFile(zp, "r") as zf:
                for info in zf.infolist():
                    if info.is_dir():
                        continue
                    member = info.filename
                    base = Path(member).name
                    stem = Path(member).stem
                    suffix = Path(member).suffix.lower()
                    ftype = "other"
                    if base in wanted_basenames:
                        ftype = "exact_final_figure"
                    elif suffix in {e.lower() for e in FIG_EXTS}:
                        ftype = "figure"
                    elif suffix in {e.lower() for e in CODE_EXTS}:
                        ftype = "code"
                    elif suffix in {e.lower() for e in ZIP_EXTS}:
                        ftype = "nested_zip"
                    if ftype != "other":
                        display = f"zip://{rel(zp, root)}!{member}"
                        dt = ""
                        try:
                            dt = datetime(*info.date_time).isoformat(timespec="seconds")
                        except Exception:
                            pass
                        inventory.append({
                            "zip_path": rel(zp, root),
                            "member": member,
                            "basename": base,
                            "type": ftype,
                            "size_bytes": str(info.file_size),
                            "zip_member_mtime": dt,
                            "sha1_first_mb": sha1_zip_member(zf, member, max_bytes=1_000_000),
                        })
                        if suffix in {e.lower() for e in FIG_EXTS} or base in wanted_basenames:
                            fig_members.append(FigureCandidate(display, base, stem, "zip", str(info.file_size), dt, sha1_zip_member(zf, member, max_bytes=1_000_000)))
                        if suffix in {e.lower() for e in CODE_EXTS}:
                            code_members.append(CodeCandidate(display, read_zip_text(zf, member), "zip"))
        except Exception as e:
            errors.append({"path": rel(zp, root), "reason": f"zip inspect failed: {type(e).__name__}: {e}"})
    return inventory, fig_members, code_members, errors


def concept_hints_for(stem: str) -> List[str]:
    s = stem.lower()
    hints = []
    mapping = {
        "figure1_channel": ["channel", "concept", "landscape", "ellipse", "log-fitness", "3d", "curvature"],
        "figure2_validation": ["validation", "ag", "r2", "architecture", "gaussian", "polygenic", "rare", "selected", "identity"],
        "figure3_framework": ["framework", "overview", "selection", "inheritance", "operator", "bulmer", "recursion", "level"],
        "figure4_trajectory": ["trajectory", "directional", "maintained", "optimum", "mutation", "rho", "time"],
        "figure5_natural_vs_breeding": ["natural", "breeding", "episodic", "sustained", "trajectory", "rho", "mutation", "moving"],
        "multiseed": ["multiseed", "replicate", "seed", "slim", "4trait", "moving", "stochastic"],
        "cv_": ["coefficient", "variation", "cv", "replicate", "across"],
        "geom_invariants": ["keff", "condition", "invariant", "eigen", "lambda", "geometry"],
    }
    for key, vals in mapping.items():
        if key in s:
            hints.extend(vals)
    # fall back to stem tokens
    hints.extend(sorted(tokens(stem)))
    return sorted(set(hints))


def score_code(fig: Dict[str, str], cand: CodeCandidate) -> Tuple[int, str]:
    fig_base = fig["basename"]
    fig_stem = fig["stem"]
    display = cand.display_path
    text = cand.text
    lower_text = text.lower()
    lower_display = display.lower()
    score = 0
    reasons: List[str] = []
    if fig_base in text or fig_base.lower() in lower_text:
        score += 150
        reasons.append("mentions exact final output filename")
    if fig_stem in text or fig_stem.lower() in lower_text:
        score += 75
        reasons.append("mentions final output stem")
    if fig_stem.lower() in lower_display:
        score += 65
        reasons.append("path contains final output stem")

    fig_toks = tokens(fig_stem)
    path_toks = tokens(lower_display)
    overlap = fig_toks & path_toks
    if overlap:
        score += 8 * len(overlap)
        reasons.append("path token overlap: " + ",".join(sorted(overlap)))

    hint_hits = [h for h in concept_hints_for(fig_stem) if h.lower() in lower_text or h.lower() in lower_display]
    if hint_hits:
        score += 10 * len(set(hint_hits))
        reasons.append("concept hints: " + ",".join(sorted(set(hint_hits))[:12]))

    # Reward scripts that save figures.
    save_markers = ["savefig", "ggsave", "pdf(", "png(", "cairo_pdf", "write_image", "exportgraphics"]
    if any(m in lower_text for m in save_markers):
        score += 12
        reasons.append("contains figure-save call")

    if any(part in lower_display for part in ["retired", "/old/", "archive"]):
        score -= 20
        reasons.append("retired/old path penalty")
    return score, "; ".join(reasons)


def score_existing_figure(fig: Dict[str, str], cand: FigureCandidate) -> Tuple[int, str]:
    final_stem = fig["stem"].lower()
    cand_stem = cand.stem.lower()
    final_base = fig["basename"].lower()
    cand_base = cand.basename.lower()
    score = 0
    reasons: List[str] = []
    if final_base == cand_base:
        score += 200
        reasons.append("exact final filename")
    if final_stem == cand_stem:
        score += 160
        reasons.append("exact final stem")
    ratio = SequenceMatcher(None, final_stem, cand_stem).ratio()
    score += int(60 * ratio)
    if ratio >= 0.55:
        reasons.append(f"name similarity {ratio:.2f}")
    overlap = tokens(final_stem) & tokens(cand_stem)
    if overlap:
        score += 12 * len(overlap)
        reasons.append("name token overlap: " + ",".join(sorted(overlap)))
    hint_hits = [h for h in concept_hints_for(final_stem) if h in cand.display_path.lower()]
    if hint_hits:
        score += 9 * len(set(hint_hits))
        reasons.append("concept hints in path: " + ",".join(sorted(set(hint_hits))[:12]))
    if any(x in cand.display_path.lower() for x in ["retired", "/old/", "archive"]):
        score -= 15
        reasons.append("retired/old path penalty")
    return score, "; ".join(reasons)


def make_commands_template(includes: List[Dict[str, str]], outdir: Path) -> None:
    rows: List[Dict[str, str]] = []
    for idx, inc in enumerate(includes, start=1):
        fid = f"F{idx}" if idx <= 5 else f"S5.{idx-5}"
        rows.append({
            "figure_id": fid,
            "command": "TODO",
            "expected_outputs": f"additiveChannels/figures/{inc['basename']}",
            "status": "TODO",
            "notes": f"TeX line {inc['tex_line']}; include {inc['include']}. Fill after checking candidate_matches.tsv and figure_name_candidates.tsv.",
        })
    write_tsv(outdir / "commands.template.tsv", rows, ["figure_id", "command", "expected_outputs", "status", "notes"])


def write_summary(outdir: Path, root: Path, tex: Path, scan_dirs: List[str], includes: List[Dict[str, str]],
                  exact_rows: List[Dict[str, str]], fig_files_count: int, code_files_count: int,
                  zip_count: int, skipped_count: int) -> None:
    lines = []
    lines.append("# Figure provenance audit summary\n")
    lines.append(f"TeX file: `{rel(tex, root)}`\n")
    lines.append(f"Figures included in TeX: **{len(includes)}**\n")
    lines.append(f"Exact final figure filename locations found: **{len(exact_rows)}**\n")
    lines.append(f"Figure-like files scanned: **{fig_files_count}**\n")
    lines.append(f"Code-like files scanned: **{code_files_count}**\n")
    lines.append(f"Zip archives inspected: **{zip_count}**\n")
    lines.append(f"Skipped / errored directories recorded: **{skipped_count}**\n")
    lines.append("\n## Scan roots used\n")
    for sd in scan_dirs:
        lines.append(f"- `{sd}`\n")
    lines.append("\n## What to inspect next\n")
    lines.append("\nStart with these files:\n")
    lines.append("\n```bash\n")
    lines.append("cat _figure_audit/exact_figure_locations.tsv\n")
    lines.append("cat _figure_audit/figure_name_candidates.tsv\n")
    lines.append("cat _figure_audit/candidate_matches.tsv\n")
    lines.append("cat _figure_audit/zip_inventory.tsv\n")
    lines.append("```\n")
    lines.append("\nThen copy `_figure_audit/commands.template.tsv` to `commands.tsv` and replace each TODO command with the verified command.\n")
    (outdir / "audit_summary.md").write_text("".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="Repository root")
    ap.add_argument("--tex", default="toSubmit/main_paper_with_page_lines.tex", help="Manuscript TeX path")
    ap.add_argument("--out", default="_figure_audit", help="Output directory")
    ap.add_argument("--scan-dir", action="append", default=[], help="Directory to scan; repeat as needed")
    ap.add_argument("--exclude", action="append", default=[], help="Directory/path token to exclude; repeat as needed")
    ap.add_argument("--include-retired", action="store_true", help="Include paths containing retired/old/archive")
    ap.add_argument("--max-depth", type=int, default=None, help="Maximum depth below each scan root")
    ap.add_argument("--no-smart-defaults", action="store_true", help="Only use explicit --scan-dir values")
    ap.add_argument("--no-tex-graphicspaths", action="store_true", help="Do not automatically add existing TeX graphicspath dirs to scan roots")
    ap.add_argument("--no-inspect-zips", action="store_true", help="Do not inspect zip archive contents")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    skipped: List[Dict[str, str]] = []
    tex = find_tex(root, args.tex, skipped)
    if not tex.exists():
        return 2

    outdir = (root / args.out).resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    includes = parse_includes(tex)
    graphicspaths = parse_graphicspaths(tex)
    wanted = {r["basename"] for r in includes}

    scan_dirs: List[str] = []
    if args.scan_dir:
        scan_dirs.extend(args.scan_dir)
    elif not args.no_smart_defaults:
        scan_dirs.extend(SMART_SCAN_DIRS)
    else:
        scan_dirs.append(".")
    if not args.no_tex_graphicspaths:
        scan_dirs.extend(graphicspath_scan_dirs(root, tex, graphicspaths))

    # Remove duplicates but preserve order.
    deduped: List[str] = []
    seen: set[str] = set()
    for sd in scan_dirs:
        sd_norm = clean_path_text(sd).strip("/") or "."
        if sd_norm not in seen:
            seen.add(sd_norm)
            deduped.append(sd_norm)
    scan_dirs = deduped

    excludes = DEFAULT_EXCLUDES + args.exclude

    write_tsv(outdir / "figure_includes.tsv", includes, ["tex_line", "include", "basename", "stem", "extension"])
    write_tsv(outdir / "graphicspaths.tsv", graphicspaths, ["tex_line", "graphicspath"])
    write_tsv(outdir / "scan_roots.tsv", [{"scan_dir": sd} for sd in scan_dirs], ["scan_dir"])

    fig_paths = collect_files(root, scan_dirs, FIG_EXTS, excludes, args.include_retired, args.max_depth, skipped)
    code_paths = collect_files(root, scan_dirs, CODE_EXTS, excludes, args.include_retired, args.max_depth, skipped)
    zip_paths = collect_files(root, scan_dirs, ZIP_EXTS, excludes, args.include_retired, args.max_depth, skipped)

    fig_candidates: List[FigureCandidate] = []
    fig_rows: List[Dict[str, str]] = []
    for p in fig_paths:
        row = {"location_type": "filesystem", "path": rel(p, root), "basename": p.name, "stem": p.stem, "sha1_first_mb": sha1_file(p, max_bytes=1_000_000)}
        row.update(stat_times(p))
        fig_rows.append(row)
        fig_candidates.append(FigureCandidate(rel(p, root), p.name, p.stem, "filesystem", row.get("size_bytes", ""), row.get("mtime", ""), row.get("sha1_first_mb", "")))
    write_tsv(outdir / "figure_files.tsv", fig_rows, ["location_type", "path", "basename", "stem", "size_bytes", "mtime", "ctime_metadata_change", "birthtime_if_available", "sha1_first_mb"])

    code_candidates: List[CodeCandidate] = []
    code_rows: List[Dict[str, str]] = []
    for p in code_paths:
        text = read_text_safely(p)
        code_candidates.append(CodeCandidate(rel(p, root), text, "filesystem"))
        row = {"location_type": "filesystem", "path": rel(p, root), "sha1_first_mb": sha1_file(p, max_bytes=1_000_000)}
        row.update(stat_times(p))
        code_rows.append(row)
    write_tsv(outdir / "code_files.tsv", code_rows, ["location_type", "path", "size_bytes", "mtime", "ctime_metadata_change", "birthtime_if_available", "sha1_first_mb"])

    zip_inventory: List[Dict[str, str]] = []
    if not args.no_inspect_zips:
        inv, zip_figs, zip_codes, zip_errors = inspect_zips(zip_paths, root, wanted)
        zip_inventory.extend(inv)
        fig_candidates.extend(zip_figs)
        code_candidates.extend(zip_codes)
        skipped.extend(zip_errors)
    write_tsv(outdir / "zip_inventory.tsv", zip_inventory, ["zip_path", "member", "basename", "type", "size_bytes", "zip_member_mtime", "sha1_first_mb"])

    # Exact locations, from filesystem or zip members.
    exact_rows: List[Dict[str, str]] = []
    for fc in fig_candidates:
        if fc.basename in wanted:
            exact_rows.append({
                "basename": fc.basename,
                "location_type": fc.location_type,
                "path": fc.display_path,
                "size_bytes": fc.size_bytes,
                "mtime": fc.mtime,
                "sha1_first_mb": fc.sha1_first_mb,
            })
    exact_rows.sort(key=lambda r: (r["basename"], r["path"]))
    write_tsv(outdir / "exact_figure_locations.tsv", exact_rows, ["basename", "location_type", "path", "size_bytes", "mtime", "sha1_first_mb"])

    # Candidate scripts for each final include.
    candidate_rows: List[Dict[str, str]] = []
    for fig in includes:
        scored: List[Tuple[int, CodeCandidate, str]] = []
        for cc in code_candidates:
            sc, why = score_code(fig, cc)
            if sc > 0:
                scored.append((sc, cc, why))
        scored.sort(reverse=True, key=lambda x: x[0])
        for rank, (sc, cc, why) in enumerate(scored[:25], start=1):
            candidate_rows.append({
                "include": fig["include"],
                "tex_line": fig["tex_line"],
                "rank": str(rank),
                "score": str(sc),
                "candidate_code": cc.display_path,
                "location_type": cc.location_type,
                "reason": why,
            })
    write_tsv(outdir / "candidate_matches.tsv", candidate_rows, ["include", "tex_line", "rank", "score", "candidate_code", "location_type", "reason"])

    # Existing figure candidates that may have old names or be renamed final outputs.
    rename_rows: List[Dict[str, str]] = []
    for fig in includes:
        scored_figs: List[Tuple[int, FigureCandidate, str]] = []
        for fc in fig_candidates:
            sc, why = score_existing_figure(fig, fc)
            if sc > 35:
                scored_figs.append((sc, fc, why))
        scored_figs.sort(reverse=True, key=lambda x: x[0])
        for rank, (sc, fc, why) in enumerate(scored_figs[:25], start=1):
            rename_rows.append({
                "include": fig["include"],
                "tex_line": fig["tex_line"],
                "rank": str(rank),
                "score": str(sc),
                "candidate_figure": fc.display_path,
                "candidate_basename": fc.basename,
                "location_type": fc.location_type,
                "size_bytes": fc.size_bytes,
                "mtime": fc.mtime,
                "reason": why,
            })
    write_tsv(outdir / "figure_name_candidates.tsv", rename_rows, ["include", "tex_line", "rank", "score", "candidate_figure", "candidate_basename", "location_type", "size_bytes", "mtime", "reason"])

    write_tsv(outdir / "skipped_dirs.tsv", skipped, ["path", "reason"])
    make_commands_template(includes, outdir)
    write_summary(outdir, root, tex, scan_dirs, includes, exact_rows, len(fig_candidates), len(code_candidates), len(zip_paths), len(skipped))

    print(f"Wrote audit outputs to {outdir}")
    print(f"TeX file: {rel(tex, root)}")
    print(f"Figures included in TeX: {len(includes)}")
    print(f"Graphicspath entries: {len(graphicspaths)}")
    print(f"Scan roots used: {len(scan_dirs)}")
    print(f"Exact final figure filename locations found: {len(exact_rows)}")
    print(f"Figure-like files found, including zip members: {len(fig_candidates)}")
    print(f"Code-like files found, including zip members: {len(code_candidates)}")
    print(f"Zip archives inspected: {len(zip_paths) if not args.no_inspect_zips else 0}")
    print(f"Skipped/errored directories recorded: {len(skipped)}")
    print("Next: inspect _figure_audit/audit_summary.md, candidate_matches.tsv, figure_name_candidates.tsv, and zip_inventory.tsv.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
