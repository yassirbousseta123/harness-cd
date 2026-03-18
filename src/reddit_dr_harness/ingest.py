\
from __future__ import annotations

import csv
import io
import json
import re
import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence

try:
    import zstandard as zstd
except Exception:  # pragma: no cover - dependency is optional at runtime
    zstd = None


KIND_RE = re.compile(r"^(t\d)_(.+)$")
WHITESPACE_RE = re.compile(r"\s+")


@dataclass(slots=True)
class SubmissionRecord:
    id: str
    subreddit: str
    title: str
    selftext: str
    author: str | None
    created_utc: float | None
    score: int | None
    num_comments: int | None
    permalink: str | None
    url: str | None
    over_18: bool | None
    raw: dict[str, Any]


@dataclass(slots=True)
class CommentRecord:
    id: str
    subreddit: str
    link_id: str
    parent_id: str | None
    parent_kind: str | None
    parent_comment_id: str | None
    parent_submission_id: str | None
    body: str
    author: str | None
    created_utc: float | None
    score: int | None
    permalink: str | None
    raw: dict[str, Any]


def _coerce_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return None


def _coerce_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def collapse_whitespace(value: str | None) -> str:
    if not value:
        return ""
    return WHITESPACE_RE.sub(" ", value).strip()


def parse_fullname(value: str | None) -> tuple[str | None, str | None]:
    if not value:
        return None, None
    match = KIND_RE.match(str(value))
    if match:
        return match.group(1), match.group(2)
    return None, str(value)


def normalize_id(value: Any) -> str | None:
    if value is None:
        return None
    _, ident = parse_fullname(str(value))
    return ident


def ensure_parent_fields(parent_id: str | None, link_id: str) -> tuple[str | None, str | None, str | None]:
    parent_kind, parent_ident = parse_fullname(parent_id)
    if parent_kind == "t1":
        return parent_kind, parent_ident, None
    if parent_kind == "t3":
        return parent_kind, None, parent_ident
    if parent_ident and parent_ident == link_id:
        return "t3", None, parent_ident
    return parent_kind, parent_ident, None


def decode_file_bytes(path: Path) -> bytes:
    if path.suffix == ".zst":
        if zstd is None:
            raise RuntimeError(
                "zstandard is required to read .zst files. Install dependencies with `pip install zstandard`."
            )
        with path.open("rb") as fh:
            dctx = zstd.ZstdDecompressor()
            return dctx.stream_reader(fh).read()
    return path.read_bytes()


def iter_json_records(path: str | Path) -> Iterator[dict[str, Any]]:
    """
    Yield JSON records from .jsonl/.ndjson/.json or .zst-compressed variants.

    The implementation is intentionally conservative:
    - line-delimited inputs are streamed line by line
    - JSON arrays are parsed as a whole
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(file_path)

    if file_path.suffix == ".zst":
        if zstd is None:
            raise RuntimeError(
                "zstandard is required to read .zst files. Install dependencies with `pip install zstandard`."
            )
        with file_path.open("rb") as fh:
            dctx = zstd.ZstdDecompressor()
            with dctx.stream_reader(fh) as reader:
                text_stream = io.TextIOWrapper(reader, encoding="utf-8")
                yield from _iter_json_records_from_text_stream(text_stream)
        return

    with file_path.open("r", encoding="utf-8") as fh:
        yield from _iter_json_records_from_text_stream(fh)


def _iter_json_records_from_text_stream(stream: io.TextIOBase) -> Iterator[dict[str, Any]]:
    first_non_ws = ""
    probe_buffer = []
    while True:
        char = stream.read(1)
        if char == "":
            break
        probe_buffer.append(char)
        if not char.isspace():
            first_non_ws = char
            break

    if first_non_ws == "":
        return

    if first_non_ws == "[":
        rest = stream.read()
        payload = "".join(probe_buffer) + rest
        data = json.loads(payload)
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    yield item
                else:
                    raise ValueError("JSON array input must contain objects only.")
        else:
            raise ValueError("Expected a JSON array of objects.")
        return

    prefix = "".join(probe_buffer)
    first_line_remainder = stream.readline()
    first_line = prefix + first_line_remainder
    for line in [first_line, *stream]:
        stripped = line.strip()
        if not stripped:
            continue
        record = json.loads(stripped)
        if not isinstance(record, dict):
            raise ValueError("Line-delimited inputs must contain JSON objects.")
        yield record


def normalize_submission(record: dict[str, Any]) -> SubmissionRecord | None:
    ident = normalize_id(record.get("id") or record.get("name"))
    if not ident:
        return None
    subreddit = str(record.get("subreddit") or "unknown")
    title = collapse_whitespace(str(record.get("title") or ""))
    selftext = collapse_whitespace(str(record.get("selftext") or record.get("body") or ""))
    author = record.get("author")
    created_utc = _coerce_float(record.get("created_utc") or record.get("created"))
    score = _coerce_int(record.get("score"))
    num_comments = _coerce_int(record.get("num_comments"))
    permalink = record.get("permalink")
    url = record.get("url")
    over_18 = record.get("over_18")
    if isinstance(over_18, str):
        over_18 = over_18.lower() == "true"
    return SubmissionRecord(
        id=ident,
        subreddit=subreddit,
        title=title,
        selftext=selftext,
        author=str(author) if author not in (None, "") else None,
        created_utc=created_utc,
        score=score,
        num_comments=num_comments,
        permalink=str(permalink) if permalink not in (None, "") else None,
        url=str(url) if url not in (None, "") else None,
        over_18=bool(over_18) if over_18 is not None else None,
        raw=record,
    )


def normalize_comment(record: dict[str, Any]) -> CommentRecord | None:
    ident = normalize_id(record.get("id") or record.get("name"))
    if not ident:
        return None
    link_id = normalize_id(record.get("link_id") or record.get("submission_id"))
    if not link_id:
        return None
    parent_id = record.get("parent_id")
    parent_kind, parent_comment_id, parent_submission_id = ensure_parent_fields(str(parent_id) if parent_id else None, link_id)
    subreddit = str(record.get("subreddit") or "unknown")
    body = collapse_whitespace(str(record.get("body") or ""))
    author = record.get("author")
    created_utc = _coerce_float(record.get("created_utc") or record.get("created"))
    score = _coerce_int(record.get("score"))
    permalink = record.get("permalink")
    return CommentRecord(
        id=ident,
        subreddit=subreddit,
        link_id=link_id,
        parent_id=str(parent_id) if parent_id not in (None, "") else None,
        parent_kind=parent_kind,
        parent_comment_id=parent_comment_id,
        parent_submission_id=parent_submission_id,
        body=body,
        author=str(author) if author not in (None, "") else None,
        created_utc=created_utc,
        score=score,
        permalink=str(permalink) if permalink not in (None, "") else None,
        raw=record,
    )


def load_submissions(path: str | Path) -> list[SubmissionRecord]:
    submissions: list[SubmissionRecord] = []
    for record in iter_json_records(path):
        normalized = normalize_submission(record)
        if normalized is not None:
            submissions.append(normalized)
    return submissions


def load_comments(path: str | Path) -> list[CommentRecord]:
    comments: list[CommentRecord] = []
    for record in iter_json_records(path):
        normalized = normalize_comment(record)
        if normalized is not None:
            comments.append(normalized)
    return comments


def _completeness_score(values: Sequence[Any]) -> int:
    return sum(1 for value in values if value not in (None, "", [], {}, False))


def _submission_quality(record: SubmissionRecord) -> tuple[int, int, int, int]:
    return (
        _completeness_score(
            [
                record.title,
                record.selftext,
                record.author,
                record.created_utc,
                record.score,
                record.num_comments,
                record.permalink,
                record.url,
                record.over_18,
            ]
        ),
        len(record.selftext or ""),
        len(record.title or ""),
        len(record.raw),
    )


def _comment_quality(record: CommentRecord) -> tuple[int, int, int]:
    return (
        _completeness_score(
            [
                record.parent_id,
                record.parent_kind,
                record.parent_comment_id,
                record.parent_submission_id,
                record.body,
                record.author,
                record.created_utc,
                record.score,
                record.permalink,
            ]
        ),
        len(record.body or ""),
        len(record.raw),
    )


def dedupe_submissions(records: Sequence[SubmissionRecord]) -> list[SubmissionRecord]:
    deduped: dict[str, SubmissionRecord] = {}
    for record in records:
        existing = deduped.get(record.id)
        if existing is None or _submission_quality(record) >= _submission_quality(existing):
            deduped[record.id] = record
    return [deduped[key] for key in sorted(deduped)]


def dedupe_comments(records: Sequence[CommentRecord]) -> list[CommentRecord]:
    deduped: dict[str, CommentRecord] = {}
    for record in records:
        existing = deduped.get(record.id)
        if existing is None or _comment_quality(record) >= _comment_quality(existing):
            deduped[record.id] = record
    return [deduped[key] for key in sorted(deduped)]


def ensure_sqlite(path: str | Path) -> sqlite3.Connection:
    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS submissions (
            id TEXT PRIMARY KEY,
            subreddit TEXT,
            title TEXT,
            selftext TEXT,
            author TEXT,
            created_utc REAL,
            score INTEGER,
            num_comments INTEGER,
            permalink TEXT,
            url TEXT,
            over_18 INTEGER,
            raw_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS comments (
            id TEXT PRIMARY KEY,
            subreddit TEXT,
            link_id TEXT,
            parent_id TEXT,
            parent_kind TEXT,
            parent_comment_id TEXT,
            parent_submission_id TEXT,
            body TEXT,
            author TEXT,
            created_utc REAL,
            score INTEGER,
            permalink TEXT,
            raw_json TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_comments_link_id ON comments(link_id);
        CREATE INDEX IF NOT EXISTS idx_comments_parent_comment_id ON comments(parent_comment_id);
        CREATE INDEX IF NOT EXISTS idx_submissions_subreddit ON submissions(subreddit);
        """
    )
    return conn


def write_sqlite(
    submissions: Sequence[SubmissionRecord],
    comments: Sequence[CommentRecord],
    sqlite_path: str | Path,
) -> None:
    conn = ensure_sqlite(sqlite_path)
    with conn:
        conn.executemany(
            """
            INSERT OR REPLACE INTO submissions (
                id, subreddit, title, selftext, author, created_utc, score, num_comments,
                permalink, url, over_18, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    item.id,
                    item.subreddit,
                    item.title,
                    item.selftext,
                    item.author,
                    item.created_utc,
                    item.score,
                    item.num_comments,
                    item.permalink,
                    item.url,
                    int(item.over_18) if item.over_18 is not None else None,
                    json.dumps(item.raw, ensure_ascii=False),
                )
                for item in submissions
            ],
        )
        conn.executemany(
            """
            INSERT OR REPLACE INTO comments (
                id, subreddit, link_id, parent_id, parent_kind, parent_comment_id,
                parent_submission_id, body, author, created_utc, score, permalink, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    item.id,
                    item.subreddit,
                    item.link_id,
                    item.parent_id,
                    item.parent_kind,
                    item.parent_comment_id,
                    item.parent_submission_id,
                    item.body,
                    item.author,
                    item.created_utc,
                    item.score,
                    item.permalink,
                    json.dumps(item.raw, ensure_ascii=False),
                )
                for item in comments
            ],
        )
    conn.close()


def submission_to_dict(submission: SubmissionRecord) -> dict[str, Any]:
    return {
        "id": submission.id,
        "fullname": f"t3_{submission.id}",
        "subreddit": submission.subreddit,
        "title": submission.title,
        "selftext": submission.selftext,
        "author": submission.author,
        "created_utc": submission.created_utc,
        "score": submission.score,
        "num_comments": submission.num_comments,
        "permalink": submission.permalink,
        "url": submission.url,
        "over_18": submission.over_18,
    }


def comment_to_dict(
    comment: CommentRecord,
    *,
    depth: int,
    children_count: int,
    ancestry_comment_ids: list[str],
    orphaned_parent_comment_id: str | None = None,
) -> dict[str, Any]:
    return {
        "id": comment.id,
        "fullname": f"t1_{comment.id}",
        "subreddit": comment.subreddit,
        "link_id": comment.link_id,
        "parent_id": comment.parent_id,
        "parent_kind": comment.parent_kind,
        "parent_comment_id": comment.parent_comment_id,
        "parent_submission_id": comment.parent_submission_id,
        "orphaned_parent_comment_id": orphaned_parent_comment_id,
        "author": comment.author,
        "body": comment.body,
        "created_utc": comment.created_utc,
        "score": comment.score,
        "permalink": comment.permalink,
        "depth": depth,
        "children_count": children_count,
        "ancestry_comment_ids": ancestry_comment_ids,
    }


def _comment_sort_key(comment: CommentRecord) -> tuple[float, str]:
    return (comment.created_utc or 0.0, comment.id)


def _flatten_thread_comments(comments: Sequence[CommentRecord]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    comments_by_id: dict[str, CommentRecord] = {item.id: item for item in comments}
    children: dict[str, list[CommentRecord]] = defaultdict(list)
    roots: list[CommentRecord] = []
    orphaned_roots: set[str] = set()

    for comment in sorted(comments, key=_comment_sort_key):
        if comment.parent_comment_id and comment.parent_comment_id in comments_by_id:
            children[comment.parent_comment_id].append(comment)
        else:
            roots.append(comment)
            if comment.parent_comment_id and comment.parent_comment_id not in comments_by_id:
                orphaned_roots.add(comment.id)

    flat_comments: list[dict[str, Any]] = []
    max_depth = 0

    def visit(node: CommentRecord, depth: int, ancestry: list[str]) -> None:
        nonlocal max_depth
        child_nodes = sorted(children.get(node.id, []), key=_comment_sort_key)
        orphaned_parent = node.parent_comment_id if node.id in orphaned_roots else None
        flat_comments.append(
            comment_to_dict(
                node,
                depth=depth,
                children_count=len(child_nodes),
                ancestry_comment_ids=ancestry.copy(),
                orphaned_parent_comment_id=orphaned_parent,
            )
        )
        max_depth = max(max_depth, depth)
        next_ancestry = ancestry + [node.id]
        for child in child_nodes:
            visit(child, depth + 1, next_ancestry)

    for root_comment in sorted(roots, key=_comment_sort_key):
        visit(root_comment, 0, [])

    stats = {
        "comment_count": len(flat_comments),
        "top_level_comment_count": sum(1 for item in flat_comments if item["depth"] == 0),
        "max_depth": max_depth,
        "orphaned_root_count": len(orphaned_roots),
    }

    return flat_comments, stats


def build_thread_record(
    submission: SubmissionRecord,
    comments: Sequence[CommentRecord],
    *,
    markdown_path: str | None = None,
) -> dict[str, Any]:
    flat_comments, stats = _flatten_thread_comments(comments)

    return {
        "thread_id": f"t3_{submission.id}",
        "submission_id": submission.id,
        "subreddit": submission.subreddit,
        "submission": submission_to_dict(submission),
        "comments": flat_comments,
        "stats": stats,
        "markdown_path": markdown_path,
        "missing_submission": False,
    }


def build_orphan_thread_record(
    thread_id: str,
    comments: Sequence[CommentRecord],
    *,
    markdown_path: str | None = None,
) -> dict[str, Any]:
    _, submission_id = parse_fullname(thread_id)
    subreddit = comments[0].subreddit if comments else "unknown"
    flat_comments, stats = _flatten_thread_comments(comments)
    submission = {
        "id": submission_id,
        "fullname": thread_id,
        "subreddit": subreddit,
        "title": "",
        "selftext": "",
        "author": None,
        "created_utc": None,
        "score": None,
        "num_comments": None,
        "permalink": None,
        "url": None,
        "over_18": None,
        "missing": True,
    }
    return {
        "thread_id": thread_id,
        "submission_id": submission_id,
        "subreddit": subreddit,
        "submission": submission,
        "comments": flat_comments,
        "stats": stats,
        "markdown_path": markdown_path,
        "missing_submission": True,
    }


def extract_thread_text(thread: dict[str, Any]) -> str:
    submission = thread.get("submission") or {}
    parts = [
        submission.get("title") or "",
        submission.get("selftext") or "",
    ]
    for comment in thread.get("comments", []):
        parts.append(comment.get("body") or "")
    return "\n".join(part for part in parts if part)


def render_thread_markdown(thread: dict[str, Any], *, max_comments: int | None = None) -> str:
    submission = thread.get("submission") or {}
    missing_submission = bool(thread.get("missing_submission") or submission.get("missing"))
    title = submission.get("title") or ("[missing submission]" if missing_submission else "[untitled submission]")
    lines = [
        f"# {title}",
        "",
        f"- thread_id: `{thread['thread_id']}`",
        f"- submission_id: `{thread['submission_id']}`",
        f"- subreddit: `{thread.get('subreddit', 'unknown')}`",
        f"- missing_submission: `{missing_submission}`",
        f"- author: `{submission.get('author') or 'unknown'}`",
        f"- created_utc: `{submission.get('created_utc')}`",
        f"- score: `{submission.get('score')}`",
        f"- num_comments: `{submission.get('num_comments')}`",
        f"- permalink: `{submission.get('permalink') or ''}`",
        "",
        "## Submission body",
        "",
    ]

    body = submission.get("selftext") or ("[submission missing from source export]" if missing_submission else "[no selftext]")
    lines.append(body)
    lines.append("")
    lines.append("## Comments")
    lines.append("")

    comments = thread.get("comments", [])
    if max_comments is not None:
        shown = comments[:max_comments]
    else:
        shown = comments

    if not shown:
        lines.append("_No comments captured._")
    else:
        for index, comment in enumerate(shown, start=1):
            depth = int(comment.get("depth", 0))
            indent = "  " * depth
            header = (
                f"{indent}- comment_id: `{comment.get('id')}` | "
                f"author: `{comment.get('author') or 'unknown'}` | "
                f"score: `{comment.get('score')}` | depth: `{depth}`"
            )
            lines.append(header)
            lines.append(f"{indent}  {comment.get('body') or '[deleted/empty]'}")
            lines.append("")
        if max_comments is not None and len(comments) > len(shown):
            remaining = len(comments) - len(shown)
            lines.append(f"_Truncated after {len(shown)} comments; {remaining} additional comments omitted._")

    return "\n".join(lines).strip() + "\n"


def write_threads_artifacts(
    submissions: Sequence[SubmissionRecord],
    comments: Sequence[CommentRecord],
    *,
    threads_jsonl_path: str | Path,
    threads_md_dir: str | Path,
    manifest_path: str | Path,
) -> dict[str, int]:
    threads_jsonl = Path(threads_jsonl_path)
    threads_jsonl.parent.mkdir(parents=True, exist_ok=True)
    threads_md_root = Path(threads_md_dir)
    threads_md_root.mkdir(parents=True, exist_ok=True)
    manifest = Path(manifest_path)
    manifest.parent.mkdir(parents=True, exist_ok=True)
    orphan_threads_jsonl = threads_jsonl.with_name("orphan_threads.jsonl")
    orphan_threads_md_root = threads_md_root.parent / "orphans_md"
    orphan_threads_md_root.mkdir(parents=True, exist_ok=True)
    orphan_manifest = manifest.with_name("orphan_thread_index.csv")

    comments_by_link_id: dict[str, list[CommentRecord]] = defaultdict(list)
    for comment in comments:
        comments_by_link_id[comment.link_id].append(comment)

    submission_ids = {submission.id for submission in submissions}
    rows: list[dict[str, Any]] = []
    orphan_rows: list[dict[str, Any]] = []
    thread_count = 0
    linked_comment_count = 0
    orphan_thread_count = 0
    orphan_comment_count = 0
    with threads_jsonl.open("w", encoding="utf-8") as jsonl_fh:
        for submission in sorted(submissions, key=lambda item: ((item.created_utc or 0.0), item.id)):
            thread_comments = comments_by_link_id.get(submission.id, [])
            markdown_file = threads_md_root / f"{submission.subreddit}__{submission.id}.md"
            markdown_rel = markdown_file.relative_to(threads_jsonl.parent.parent.parent) if _can_relative_to(markdown_file, threads_jsonl.parent.parent.parent) else markdown_file
            thread = build_thread_record(submission, thread_comments, markdown_path=str(markdown_rel).replace("\\", "/"))
            markdown_file.write_text(render_thread_markdown(thread), encoding="utf-8")
            jsonl_fh.write(json.dumps(thread, ensure_ascii=False) + "\n")
            thread_count += 1
            linked_comment_count += len(thread_comments)
            rows.append(
                {
                    "thread_id": thread["thread_id"],
                    "submission_id": submission.id,
                    "subreddit": submission.subreddit,
                    "created_utc": submission.created_utc,
                    "score": submission.score,
                    "num_comments_submission": submission.num_comments,
                    "comment_count_reconstructed": thread["stats"]["comment_count"],
                    "max_depth": thread["stats"]["max_depth"],
                    "orphaned_root_count": thread["stats"]["orphaned_root_count"],
                    "title": submission.title,
                    "markdown_path": thread["markdown_path"],
                }
            )

    with orphan_threads_jsonl.open("w", encoding="utf-8") as orphan_jsonl_fh:
        for thread_id in sorted(
            (link_id for link_id in comments_by_link_id if link_id not in submission_ids),
            key=lambda item: (comments_by_link_id[item][0].created_utc or 0.0, item),
        ):
            thread_comments = comments_by_link_id[thread_id]
            thread_fullname = f"t3_{thread_id}"
            subreddit = thread_comments[0].subreddit if thread_comments else "unknown"
            markdown_file = orphan_threads_md_root / f"{subreddit}__orphan__{thread_id}.md"
            markdown_rel = markdown_file.relative_to(threads_jsonl.parent.parent.parent) if _can_relative_to(markdown_file, threads_jsonl.parent.parent.parent) else markdown_file
            thread = build_orphan_thread_record(thread_fullname, thread_comments, markdown_path=str(markdown_rel).replace("\\", "/"))
            markdown_file.write_text(render_thread_markdown(thread), encoding="utf-8")
            orphan_jsonl_fh.write(json.dumps(thread, ensure_ascii=False) + "\n")
            orphan_thread_count += 1
            orphan_comment_count += len(thread_comments)
            orphan_rows.append(
                {
                    "thread_id": thread["thread_id"],
                    "submission_id": thread["submission_id"],
                    "subreddit": thread["subreddit"],
                    "created_utc": "",
                    "score": "",
                    "num_comments_submission": "",
                    "comment_count_reconstructed": thread["stats"]["comment_count"],
                    "max_depth": thread["stats"]["max_depth"],
                    "orphaned_root_count": thread["stats"]["orphaned_root_count"],
                    "title": "",
                    "markdown_path": thread["markdown_path"],
                }
            )

    with manifest.open("w", encoding="utf-8", newline="") as manifest_fh:
        fieldnames = [
            "thread_id",
            "submission_id",
            "subreddit",
            "created_utc",
            "score",
            "num_comments_submission",
            "comment_count_reconstructed",
            "max_depth",
            "orphaned_root_count",
            "title",
            "markdown_path",
        ]
        writer = csv.DictWriter(manifest_fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    with orphan_manifest.open("w", encoding="utf-8", newline="") as orphan_manifest_fh:
        fieldnames = [
            "thread_id",
            "submission_id",
            "subreddit",
            "created_utc",
            "score",
            "num_comments_submission",
            "comment_count_reconstructed",
            "max_depth",
            "orphaned_root_count",
            "title",
            "markdown_path",
        ]
        writer = csv.DictWriter(orphan_manifest_fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(orphan_rows)

    return {
        "threads": thread_count,
        "comments": len(comments),
        "thread_comments": linked_comment_count,
        "orphan_threads": orphan_thread_count,
        "orphan_comments": orphan_comment_count,
        "submissions": len(submissions),
    }


def load_threads_jsonl(path: str | Path) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as fh:
        for line in fh:
            stripped = line.strip()
            if not stripped:
                continue
            items.append(json.loads(stripped))
    return items


def _can_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False
