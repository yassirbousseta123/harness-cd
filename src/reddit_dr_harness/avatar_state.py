from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from .ingest import collapse_whitespace, extract_thread_text, load_threads_jsonl


def load_avatar_config(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_threads_from_paths(paths: Iterable[str | Path]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for path in paths:
        items.extend(load_threads_jsonl(path))
    return items


def _compile_states(states: list[dict[str, Any]]) -> list[dict[str, Any]]:
    compiled: list[dict[str, Any]] = []
    for state in states:
        compiled.append(
            {
                **state,
                "patterns_compiled": [re.compile(pattern, re.IGNORECASE) for pattern in state.get("patterns", [])],
            }
        )
    return compiled


def compile_avatar_config(config: dict[str, Any]) -> dict[str, Any]:
    return {
        **config,
        "core_states_compiled": _compile_states(config.get("core_states", [])),
        "adjacent_states_compiled": _compile_states(config.get("adjacent_states", [])),
        "min_core_score": float(config.get("min_core_score", 0.0)),
        "min_core_states": int(config.get("min_core_states", 1)),
        "priority_min_core_score": float(config.get("priority_min_core_score", config.get("min_core_score", 0.0))),
        "priority_core_state_groups": config.get("priority_core_state_groups", []),
    }


def _collect_matches(text: str, states: list[dict[str, Any]]) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for state in states:
        terms: list[str] = []
        for pattern in state["patterns_compiled"]:
            for hit in pattern.finditer(text):
                token = collapse_whitespace(hit.group(0))
                if token and token.lower() not in {item.lower() for item in terms}:
                    terms.append(token)
                if len(terms) >= 8:
                    break
            if len(terms) >= 8:
                break
        if terms:
            matches.append(
                {
                    "id": state["id"],
                    "label": state.get("label") or state["id"],
                    "weight": float(state.get("weight", 1.0)),
                    "matched_terms": terms,
                }
            )
    return matches


def _thread_title(thread: dict[str, Any]) -> str:
    submission = thread.get("submission") or {}
    return str(submission.get("title") or "")


def _thread_created_utc(thread: dict[str, Any]) -> float | None:
    submission = thread.get("submission") or {}
    created = submission.get("created_utc")
    if created not in (None, ""):
        return float(created)
    comments = thread.get("comments") or []
    if not comments:
        return None
    values = [item.get("created_utc") for item in comments if item.get("created_utc") not in (None, "")]
    if not values:
        return None
    return float(min(values))


def score_thread(thread: dict[str, Any], compiled_config: dict[str, Any]) -> dict[str, Any]:
    text = extract_thread_text(thread)
    core_matches = _collect_matches(text, compiled_config.get("core_states_compiled", []))
    adjacent_matches = _collect_matches(text, compiled_config.get("adjacent_states_compiled", []))
    core_ids = {item["id"] for item in core_matches}
    core_score = round(sum(item["weight"] for item in core_matches), 2)
    adjacent_score = round(sum(item["weight"] for item in adjacent_matches), 2)
    qualifies = core_score >= compiled_config["min_core_score"] and len(core_matches) >= compiled_config["min_core_states"]
    priority_qualifies = qualifies and core_score >= compiled_config["priority_min_core_score"]
    for group in compiled_config.get("priority_core_state_groups", []):
        if group and not any(state_id in core_ids for state_id in group):
            priority_qualifies = False
            break
    return {
        "avatar_id": compiled_config["avatar_id"],
        "thread_id": thread.get("thread_id"),
        "submission_id": thread.get("submission_id"),
        "subreddit": thread.get("subreddit"),
        "title": _thread_title(thread),
        "created_utc": _thread_created_utc(thread),
        "source_kind": "orphan" if thread.get("missing_submission") else "thread",
        "missing_submission": bool(thread.get("missing_submission")),
        "core_score": core_score,
        "adjacent_score": adjacent_score,
        "score": round(core_score + (0.35 * adjacent_score), 2),
        "matched_core_states": core_matches,
        "matched_adjacent_states": adjacent_matches,
        "matched_terms": sorted(
            {
                term
                for item in [*core_matches, *adjacent_matches]
                for term in item.get("matched_terms", [])
            },
            key=str.lower,
        ),
        "qualifies": qualifies,
        "priority_qualifies": priority_qualifies,
        "markdown_path": thread.get("markdown_path"),
    }


def build_avatar_slice(
    threads: Iterable[dict[str, Any]],
    config: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    compiled = compile_avatar_config(config)
    matched_threads: list[dict[str, Any]] = []
    priority_threads: list[dict[str, Any]] = []
    core_counts: Counter[str] = Counter()
    adjacent_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    subreddit_counts: Counter[str] = Counter()
    cooccurrence: Counter[tuple[str, str]] = Counter()
    near_miss: list[dict[str, Any]] = []
    total_threads = 0

    for thread in threads:
        total_threads += 1
        metadata = score_thread(thread, compiled)
        if metadata["qualifies"]:
            thread_copy = dict(thread)
            thread_copy["slice_metadata"] = metadata
            matched_threads.append(thread_copy)
            if metadata["priority_qualifies"]:
                priority_threads.append(thread_copy)
            source_counts[metadata["source_kind"]] += 1
            if metadata.get("subreddit"):
                subreddit_counts[str(metadata["subreddit"])] += 1
            core_ids = [item["id"] for item in metadata["matched_core_states"]]
            adjacent_ids = [item["id"] for item in metadata["matched_adjacent_states"]]
            core_counts.update(core_ids)
            adjacent_counts.update(adjacent_ids)
            for index, left in enumerate(core_ids):
                for right in core_ids[index + 1 :]:
                    pair = tuple(sorted((left, right)))
                    cooccurrence[pair] += 1
        elif metadata["matched_core_states"] or len(metadata["matched_adjacent_states"]) >= 2:
            near_miss.append(metadata)

    matched_threads.sort(
        key=lambda item: (
            -(item["slice_metadata"]["score"]),
            -(item["slice_metadata"]["created_utc"] or 0.0),
            item.get("thread_id") or "",
        )
    )
    near_miss.sort(
        key=lambda item: (
            -(len(item["matched_core_states"])),
            -(len(item["matched_adjacent_states"])),
            -(item["score"]),
            item.get("thread_id") or "",
        )
    )

    report = {
        "avatar_id": compiled["avatar_id"],
        "label": compiled.get("label"),
        "description": compiled.get("description"),
        "total_threads_scored": total_threads,
        "matched_threads": len(matched_threads),
        "priority_threads": len(priority_threads),
        "matched_by_source_kind": dict(source_counts),
        "matched_by_subreddit": dict(subreddit_counts.most_common()),
        "core_state_counts": dict(core_counts.most_common()),
        "adjacent_state_counts": dict(adjacent_counts.most_common()),
        "core_state_cooccurrence": [
            {"state_ids": list(pair), "thread_count": count}
            for pair, count in cooccurrence.most_common()
        ],
        "top_threads": [
            {
                "thread_id": item["thread_id"],
                "title": item["slice_metadata"]["title"],
                "subreddit": item["slice_metadata"]["subreddit"],
                "score": item["slice_metadata"]["score"],
                "matched_core_states": [match["id"] for match in item["slice_metadata"]["matched_core_states"]],
                "priority_qualifies": item["slice_metadata"]["priority_qualifies"],
            }
            for item in matched_threads[:25]
        ],
        "near_miss_threads": [
            {
                "thread_id": item["thread_id"],
                "title": item["title"],
                "subreddit": item["subreddit"],
                "score": item["score"],
                "matched_core_states": [match["id"] for match in item["matched_core_states"]],
                "matched_adjacent_states": [match["id"] for match in item["matched_adjacent_states"]],
            }
            for item in near_miss[:25]
        ],
    }
    return matched_threads, report


def write_avatar_slice(
    threads: list[dict[str, Any]],
    *,
    out_threads_path: str | Path,
    out_manifest_path: str | Path,
    out_report_path: str | Path | None = None,
) -> None:
    out_threads = Path(out_threads_path)
    out_threads.parent.mkdir(parents=True, exist_ok=True)
    out_manifest = Path(out_manifest_path)
    out_manifest.parent.mkdir(parents=True, exist_ok=True)

    with out_threads.open("w", encoding="utf-8") as fh:
        for thread in threads:
            fh.write(json.dumps(thread, ensure_ascii=False) + "\n")

    with out_manifest.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "thread_id",
                "submission_id",
                "source_kind",
                "subreddit",
                "created_utc",
                "score",
                "core_score",
                "adjacent_score",
                "priority_qualifies",
                "matched_core_states",
                "matched_adjacent_states",
                "matched_terms",
                "title",
                "markdown_path",
            ],
        )
        writer.writeheader()
        for thread in threads:
            metadata = thread["slice_metadata"]
            writer.writerow(
                {
                    "thread_id": metadata["thread_id"],
                    "submission_id": metadata["submission_id"],
                    "source_kind": metadata["source_kind"],
                    "subreddit": metadata["subreddit"],
                    "created_utc": metadata["created_utc"],
                    "score": metadata["score"],
                    "core_score": metadata["core_score"],
                    "adjacent_score": metadata["adjacent_score"],
                    "priority_qualifies": metadata["priority_qualifies"],
                    "matched_core_states": "|".join(item["id"] for item in metadata["matched_core_states"]),
                    "matched_adjacent_states": "|".join(item["id"] for item in metadata["matched_adjacent_states"]),
                    "matched_terms": "|".join(metadata["matched_terms"]),
                    "title": metadata["title"],
                    "markdown_path": metadata["markdown_path"],
                }
            )

    if out_report_path is not None:
        out_report = Path(out_report_path)
        out_report.parent.mkdir(parents=True, exist_ok=True)
        report = {
            "avatar_id": threads[0]["slice_metadata"]["avatar_id"] if threads else None,
            "matched_threads": len(threads),
            "top_threads": [
                {
                    "thread_id": thread["thread_id"],
                    "score": thread["slice_metadata"]["score"],
                    "matched_core_states": [item["id"] for item in thread["slice_metadata"]["matched_core_states"]],
                }
                for thread in threads[:25]
            ],
        }
        out_report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
