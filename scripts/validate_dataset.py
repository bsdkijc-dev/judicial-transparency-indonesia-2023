#!/usr/bin/env python3
"""Validate a judicial open-data package: metadata.json + CSV files.

Standard library only (runs on a clean CI runner without pip installs).

Usage:
    python validate_dataset.py <dataset_dir> [--report validation_report.md]
           [--id-column court_id] [--required-columns a,b,c]

Exit codes: 0 = no critical errors, 1 = critical errors, 2 = usage error.
This script checks STRUCTURE only. A passing run never means the data is
VERIFIED against its sources; verification_status is reported, not inferred.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REQUIRED_META = [
    "dataset_id", "dataset_title", "description", "research_domain", "jurisdiction",
    "reporting_period", "source_institution", "source_url", "extraction_method",
    "verification_status", "data_license", "publication_status", "schema_version",
    "dataset_version", "last_updated",
]
ENUMS = {
    "verification_status": {"VERIFIED", "PARTIALLY_VERIFIED", "UNVERIFIED", "CONFLICT"},
    "publication_status": {"PUBLISH", "REVISE", "PRIVATE", "ARCHIVE"},
    "research_domain": {
        "INDONESIA_JUDICIARY_OPEN_DATA", "RULE_OF_LAW_JUDICIAL_GOVERNANCE",
        "COMPUTATIONAL_LEGAL_RESEARCH", "AI_JUDICIAL_KNOWLEDGE_ENGINEERING",
    },
}
URL_RE = re.compile(r"^https?://[^\s/$.?#].[^\s]*$")
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}([T ][\d:.]+(Z|[+-]\d{2}:?\d{2})?)?$")
SECRET_RE = re.compile(
    r"(ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|AKIA[0-9A-Z]{16}|"
    r"sk-[A-Za-z0-9]{32,}|AIza[0-9A-Za-z_\-]{35}|-----BEGIN [A-Z ]*PRIVATE KEY)"
)
GENERIC_BIO_MARKERS = ("Learning. Researching. Innovating",)
# Rule of Law 2045 schema is established; never rename these.
ROL2045_COLUMNS = ["entity_id", "topic", "pillar", "program", "kpi", "jurisdiction",
                   "year", "value", "source_url", "verification_status",
                   "github_version", "wiki_url"]


class Report:
    def __init__(self) -> None:
        self.critical: list[str] = []
        self.warnings: list[str] = []
        self.info: list[str] = []

    def crit(self, m: str) -> None: self.critical.append(m)
    def warn(self, m: str) -> None: self.warnings.append(m)
    def note(self, m: str) -> None: self.info.append(m)


def validate_metadata(path: Path, r: Report) -> dict:
    if not path.exists():
        r.crit(f"metadata.json missing at {path}")
        return {}
    try:
        meta = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        r.crit(f"metadata.json is not valid UTF-8 JSON: {e}")
        return {}
    for k in REQUIRED_META:
        if k not in meta or meta[k] in (None, "", []):
            r.crit(f"metadata: required field '{k}' missing or empty")
    for k, allowed in ENUMS.items():
        if k in meta and meta[k] not in allowed:
            r.crit(f"metadata: '{k}'='{meta[k]}' not in {sorted(allowed)}")
    for k in ("source_url", "github_repository", "kaggle_url", "wiki_url"):
        v = meta.get(k)
        if v and not URL_RE.match(str(v)):
            r.crit(f"metadata: '{k}' is not a valid URL: {v}")
    lu = meta.get("last_updated")
    if lu and not ISO_DATE_RE.match(str(lu)):
        r.crit(f"metadata: last_updated '{lu}' is not ISO 8601")
    desc = str(meta.get("description", ""))
    if any(m in desc for m in GENERIC_BIO_MARKERS):
        r.warn("metadata: description is the generic organisation bio, not a dataset description")
    elif 0 < len(desc) < 80:
        r.warn("metadata: description shorter than 80 characters")
    if meta.get("publication_status") == "PUBLISH" and meta.get("verification_status") in ("UNVERIFIED", "CONFLICT"):
        r.crit("metadata: publication_status PUBLISH is not allowed with verification_status "
               f"{meta.get('verification_status')}")
    r.note(f"declared verification_status: {meta.get('verification_status', 'n/a')} (reported, not inferred)")
    return meta


def validate_csv(path: Path, r: Report, id_column: str | None, required: list[str]) -> None:
    rel = path.name
    try:
        raw = path.read_bytes()
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        r.crit(f"{rel}: not UTF-8 encoded")
        return
    if SECRET_RE.search(text):
        r.crit(f"{rel}: contains a string matching a credential pattern")
    rows = list(csv.reader(text.splitlines()))
    if not rows:
        r.crit(f"{rel}: empty file")
        return
    header, body = rows[0], rows[1:]
    if len(set(header)) != len(header):
        dups = sorted({h for h in header if header.count(h) > 1})
        r.crit(f"{rel}: duplicate column names {dups}")
    if any(h.strip() == "" for h in header):
        r.crit(f"{rel}: blank column name in header")
    for col in required:
        if col not in header:
            r.crit(f"{rel}: required column '{col}' missing")
    if len(set(ROL2045_COLUMNS) & set(header)) >= 6:
        missing = [c for c in ROL2045_COLUMNS if c not in header]
        if missing:
            r.crit(f"{rel}: Rule of Law 2045 schema columns missing/renamed: {missing}")
    width = len(header)
    ragged = [i + 2 for i, row in enumerate(body) if row and len(row) != width]
    if ragged:
        r.crit(f"{rel}: {len(ragged)} rows have wrong field count (first at line {ragged[0]})")
    body = [row for row in body if row and len(row) == width]
    r.note(f"{rel}: {len(body)} rows × {width} columns")

    def col(name: str) -> list[str]:
        i = header.index(name)
        return [row[i] for row in body]

    idc = id_column if id_column in header else next(
        (h for h in header if h.lower() in ("id", "dataset_id", "entity_id", "court_id", "finding_id", "record_id")), None)
    if idc:
        vals = [v for v in col(idc) if v.strip()]
        seen, dups = set(), set()
        for v in vals:
            (dups if v in seen else seen).add(v)
        if dups:
            msg = f"{rel}: {len(dups)} duplicate values in id column '{idc}' (e.g. {sorted(dups)[:3]})"
            if id_column == idc:
                r.crit(msg)
            else:
                full = len({tuple(row) for row in body}) < len(body)
                if full:
                    r.crit(msg + " - includes fully identical rows")
                else:
                    r.warn(msg + " - fine if this is a long-format table; pass --id-column to enforce uniqueness")
        if len(vals) < len(body):
            r.crit(f"{rel}: {len(body) - len(vals)} rows with empty '{idc}'")
    for h in header:
        values = col(h)
        empty = sum(1 for v in values if v.strip() == "")
        if body and empty / len(body) > 0.5:
            r.warn(f"{rel}: column '{h}' is {empty / len(body):.0%} empty")
        hl = h.lower()
        if "url" in hl:
            bad = [v.strip() for v in values if v.strip() and not URL_RE.match(v.strip())]
            spaced = [v for v in bad if re.match(r"^https?://\S+\s", v)]
            if spaced:
                r.warn(f"{rel}: {len(spaced)} URLs in '{h}' contain unencoded spaces (e.g. {spaced[0][:60]!r})")
            bad = [v for v in bad if v not in spaced]
            if bad:
                r.crit(f"{rel}: {len(bad)} non-public or invalid URLs in '{h}' (e.g. {bad[0][:60]!r})")
        if hl in ("date", "last_updated", "extraction_date") or hl.endswith("_date"):
            bad = [v for v in values if v.strip() and not ISO_DATE_RE.match(v.strip())]
            status_words = [v for v in bad if re.fullmatch(r"[A-Z_]+", v.strip())]
            if status_words:
                r.warn(f"{rel}: {len(status_words)} status codes stored in date column '{h}' "
                       f"(e.g. {status_words[0]!r}) - leave the date blank and record status in its own column")
                bad = [v for v in bad if v not in status_words]
            if bad:
                r.crit(f"{rel}: {len(bad)} non-ISO-8601 values in '{h}' (e.g. {bad[0]!r})")
        if hl == "verification_status":
            allowed = ENUMS["verification_status"] | {"PENDING_VERIFICATION"}
            odd = sorted({v.strip() for v in values if v.strip() and v.strip() not in allowed})
            if odd:
                r.warn(f"{rel}: non-standard verification_status values {odd} - map to VERIFIED / "
                       "PARTIALLY_VERIFIED / UNVERIFIED / CONFLICT and keep the method or workflow state "
                       "(SOURCE, CALCULATION, RECONCILED, REQUIRES_MANUAL_REVIEW) in a separate column")
        if hl == "jurisdiction":
            variants = {}
            for v in values:
                variants.setdefault(re.sub(r"[^a-z]", "", v.lower()), set()).add(v)
            inconsistent = [sorted(s) for s in variants.values() if len(s) > 1]
            if inconsistent:
                r.warn(f"{rel}: inconsistent jurisdiction spellings {inconsistent[:3]}")
        if hl.endswith(("_name", "satker")) or hl == "satker_name":
            looks_numeric = [v for v in values if re.fullmatch(r"\d+\s*(cases?|kasus)?", v.strip(), re.I)]
            if looks_numeric:
                r.warn(f"{rel}: column '{h}' holds count-like values {looks_numeric[:2]} (possible column shift)")


def write_report(path: Path, target: Path, r: Report) -> None:
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    status = "FAIL" if r.critical else "PASS (structure only — not source verification)"
    lines = [f"# Validation report — {target.name}", "", f"- Generated: {ts}", f"- Result: **{status}**",
             f"- Critical: {len(r.critical)} · Warnings: {len(r.warnings)}", ""]
    for title, items in (("Critical errors", r.critical), ("Warnings", r.warnings), ("Info", r.info)):
        lines += [f"## {title}", ""] + ([f"- {i}" for i in items] or ["- none"]) + [""]
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("dataset_dir", type=Path)
    ap.add_argument("--report", type=Path, default=None)
    ap.add_argument("--id-column", default=None)
    ap.add_argument("--required-columns", default="")
    ap.add_argument("--csv-only", action="store_true",
                    help="skip metadata.json checks (for repos that have not adopted the metadata standard yet)")
    a = ap.parse_args(argv)
    if not a.dataset_dir.is_dir():
        print(f"not a directory: {a.dataset_dir}", file=sys.stderr)
        return 2
    r = Report()
    if a.csv_only:
        r.note("metadata.json checks skipped (--csv-only)")
    else:
        validate_metadata(a.dataset_dir / "metadata.json", r)
    req = [c for c in a.required_columns.split(",") if c]
    csvs = sorted(a.dataset_dir.rglob("*.csv"))
    if not csvs:
        r.warn("no CSV files found")
    for p in csvs:
        validate_csv(p, r, a.id_column, req)
    report_path = a.report or (a.dataset_dir / "validation_report.md")
    write_report(report_path, a.dataset_dir, r)
    for m in r.critical:
        print("CRITICAL:", m)
    for m in r.warnings:
        print("WARNING:", m)
    print(f"{len(r.critical)} critical, {len(r.warnings)} warnings -> {report_path}")
    return 1 if r.critical else 0


if __name__ == "__main__":
    sys.exit(main())
