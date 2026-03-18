\
from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

from .ingest import collapse_whitespace, load_threads_jsonl


def _load_json_or_jsonl(path: Path) -> Any:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return {}
    if path.suffix == ".jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    return json.loads(text)


def _load_thread_index(path: Path) -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            thread_id = row.get("thread_id")
            if thread_id:
                rows[thread_id] = row
    return rows


def _normalized_text(value: str) -> str:
    return collapse_whitespace(re.sub(r"\s+", " ", value or "")).lower()


def _collect_evidence_dicts(payload: Any, *, path: str = "$") -> list[tuple[str, dict[str, Any]]]:
    results: list[tuple[str, dict[str, Any]]] = []
    if isinstance(payload, dict):
        if "thread_id" in payload:
            results.append((path, payload))
        for key, value in payload.items():
            results.extend(_collect_evidence_dicts(value, path=f"{path}.{key}"))
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            results.extend(_collect_evidence_dicts(value, path=f"{path}[{index}]"))
    return results


def validate_evidence_references(
    *,
    json_path: str | Path,
    thread_index_path: str | Path,
    threads_path: str | Path | None = None,
) -> dict[str, Any]:
    json_file = Path(json_path)
    index_file = Path(thread_index_path)
    threads_file = Path(threads_path) if threads_path else None

    payload = _load_json_or_jsonl(json_file)
    index = _load_thread_index(index_file)
    thread_text_by_id: dict[str, str] = {}
    if threads_file and threads_file.exists():
        for thread in load_threads_jsonl(threads_file):
            thread_text_by_id[thread["thread_id"]] = _normalized_text(
                "\n".join(
                    [
                        thread.get("submission", {}).get("title") or "",
                        thread.get("submission", {}).get("selftext") or "",
                        *[(item.get("body") or "") for item in thread.get("comments", [])],
                    ]
                )
            )

    evidence_items = _collect_evidence_dicts(payload)
    report = {
        "json_path": str(json_file),
        "evidence_items_found": len(evidence_items),
        "missing_thread_ids": [],
        "quote_mismatches": [],
        "missing_required_keys": [],
        "valid": True,
    }

    required = {"thread_id", "submission_id", "comment_id", "subreddit", "quote"}
    for path, item in evidence_items:
        missing = sorted(key for key in required if key not in item)
        if missing:
            report["missing_required_keys"].append({"path": path, "missing": missing})
            report["valid"] = False

        thread_id = item.get("thread_id")
        if thread_id not in index:
            report["missing_thread_ids"].append({"path": path, "thread_id": thread_id})
            report["valid"] = False
            continue

        quote = item.get("quote")
        if quote and thread_text_by_id:
            thread_text = thread_text_by_id.get(thread_id, "")
            normalized_quote = _normalized_text(str(quote))
            if normalized_quote and normalized_quote not in thread_text:
                report["quote_mismatches"].append(
                    {
                        "path": path,
                        "thread_id": thread_id,
                        "quote": quote,
                    }
                )
                report["valid"] = False

    return report
