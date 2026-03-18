\
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence

from .ingest import collapse_whitespace, load_threads_jsonl

FIRST_PERSON_RE = re.compile(r"\b(i|i'm|i’ve|i've|me|my|mine)\b", re.IGNORECASE)
DESIRE_RE = re.compile(r"\b(i want|i just want|i need|i wish|i hope|so i can)\b", re.IGNORECASE)
TRIGGER_RE = re.compile(
    r"\b(after|when|once|until|finally|at the point|started looking|started searching|desperate|fed up|couldn't take)\b",
    re.IGNORECASE,
)
OBJECTION_RE = re.compile(
    r"\b(scam|skeptic|skeptical|don't trust|too expensive|too pricey|waste of money|not buying|won't buy|afraid of)\b",
    re.IGNORECASE,
)
FAILURE_RE = re.compile(
    r"\b(tried|nothing works|didn't work|did not work|failed|waste|no relief|no change|made it worse)\b",
    re.IGNORECASE,
)
VICTORY_RE = re.compile(
    r"\b(helped|helps a bit|helped a little|some relief|finally slept|small win|got better|calmed down)\b",
    re.IGNORECASE,
)
PAIN_RE = re.compile(
    r"\b(can't sleep|cannot sleep|sleep deprivation|ringing|buzzing|hissing|screeching|anxiety|panic|miserable|driving me crazy|hopeless|depressed|exhausted)\b",
    re.IGNORECASE,
)
DAY_TO_DAY_RE = re.compile(
    r"\b(work|concentrate|focus|meeting|parent|kids|driving|shower|bedtime|quiet room|reading|watching tv|relationship|social|gym|office)\b",
    re.IGNORECASE,
)
BELIEF_RE = re.compile(
    r"\b(i think|i believe|i'm convinced|i am convinced|seems like|caused by|triggered by|stress makes|my brain|my ears|nervous system)\b",
    re.IGNORECASE,
)
EMOTION_IDENTITY_RE = re.compile(
    r"\b(normal again|my life back|feel like myself|broken|isolated|alone|trapped|authentic|belong|burden)\b",
    re.IGNORECASE,
)
VISUAL_RE = re.compile(
    r"\b(like a|sounds like|feels like|whistle|tea kettle|crickets|electric|screaming|alarm|engine|cicadas)\b",
    re.IGNORECASE,
)

CATEGORY_PATTERNS = {
    "pain_points": [PAIN_RE],
    "day_to_day_struggles": [DAY_TO_DAY_RE],
    "victories": [VICTORY_RE],
    "failures": [FAILURE_RE],
    "goals": [DESIRE_RE],
    "beliefs": [BELIEF_RE],
    "desires": [DESIRE_RE, EMOTION_IDENTITY_RE],
    "objections": [OBJECTION_RE],
    "trigger_moments": [TRIGGER_RE],
    "emotions_identity": [EMOTION_IDENTITY_RE],
    "real_customer_language": [FIRST_PERSON_RE, VISUAL_RE, PAIN_RE, DESIRE_RE],
    "visual_cues": [VISUAL_RE],
}

WHY_MAP = {
    "pain_points": "Captures acute pain, distress, or disruption caused by the condition.",
    "day_to_day_struggles": "Shows how the issue interferes with normal routines or roles.",
    "victories": "Shows a partial win or relief signal worth understanding and validating.",
    "failures": "Documents what they have already tried and where it disappointed them.",
    "goals": "Reveals the practical outcome they are trying to get back to.",
    "beliefs": "Shows the current story they tell themselves about causes or solutions.",
    "desires": "Exposes the deeper motivation behind solving the problem.",
    "objections": "Reveals friction that could block conversion or adoption.",
    "trigger_moments": "Shows the moment that pushed them to search harder or act.",
    "emotions_identity": "Reveals identity-level stakes beyond symptom relief.",
    "real_customer_language": "Contains phrasing that should travel into copy and positioning.",
    "visual_cues": "Contains imagery or metaphor that can inform creative hooks.",
}


def split_passages(text: str) -> Iterator[str]:
    collapsed = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not collapsed:
        return
    for paragraph in re.split(r"\n{2,}", collapsed):
        paragraph = collapse_whitespace(paragraph)
        if not paragraph:
            continue
        if len(paragraph) <= 320:
            yield paragraph
            continue
        sentences = re.split(r"(?<=[.!?])\s+", paragraph)
        buffer: list[str] = []
        current_len = 0
        for sentence in sentences:
            sentence = collapse_whitespace(sentence)
            if not sentence:
                continue
            if current_len + len(sentence) + 1 > 320 and buffer:
                chunk = " ".join(buffer).strip()
                if len(chunk) >= 24:
                    yield chunk
                buffer = [sentence]
                current_len = len(sentence)
            else:
                buffer.append(sentence)
                current_len += len(sentence) + 1
        if buffer:
            chunk = " ".join(buffer).strip()
            if len(chunk) >= 24:
                yield chunk


def _matched_signals(text: str, category: str) -> list[str]:
    matched: list[str] = []
    for pattern in CATEGORY_PATTERNS[category]:
        for hit in pattern.findall(text):
            if isinstance(hit, tuple):
                token = " ".join(str(part) for part in hit if part)
            else:
                token = str(hit)
            token = collapse_whitespace(token)
            if token and token.lower() not in {item.lower() for item in matched}:
                matched.append(token)
    return matched


def quote_categories(text: str) -> list[str]:
    categories: list[str] = []
    for category, patterns in CATEGORY_PATTERNS.items():
        if any(pattern.search(text) for pattern in patterns):
            categories.append(category)

    if FIRST_PERSON_RE.search(text):
        for category in ("pain_points", "failures", "goals", "beliefs", "desires", "real_customer_language"):
            if category in categories:
                break
        else:
            categories.append("real_customer_language")

    return categories


def _quote_strength(text: str, categories: list[str]) -> float:
    score = 0.0
    if FIRST_PERSON_RE.search(text):
        score += 1.0
    if len(categories) > 1:
        score += 0.5
    if len(text) >= 40:
        score += 0.25
    if VISUAL_RE.search(text):
        score += 0.25
    return round(score, 2)


def iter_quote_candidates(threads: Iterable[dict[str, Any]]) -> Iterator[dict[str, Any]]:
    for thread in threads:
        submission = thread.get("submission", {})
        submission_id = thread.get("submission_id")
        thread_id = thread.get("thread_id")
        subreddit = thread.get("subreddit") or submission.get("subreddit") or "unknown"
        title = submission.get("title") or ""

        sources: list[tuple[str, str, str | None, int | None, str | None]] = []
        if submission.get("selftext"):
            sources.append(("submission_body", submission["selftext"], None, submission.get("score"), submission.get("author")))
        if title:
            sources.append(("submission_title", title, None, submission.get("score"), submission.get("author")))
        for comment in thread.get("comments", []):
            body = comment.get("body") or ""
            if body:
                sources.append(("comment", body, comment.get("id"), comment.get("score"), comment.get("author")))

        for source_type, body, comment_id, score, author in sources:
            for passage in split_passages(body):
                categories = quote_categories(passage)
                if not categories:
                    continue
                strength = _quote_strength(passage, categories)
                for category in categories:
                    yield {
                        "quote_id": f"{thread_id}:{comment_id or 'submission'}:{category}:{abs(hash((passage, category))) % 10_000_000}",
                        "thread_id": thread_id,
                        "submission_id": submission_id,
                        "comment_id": comment_id,
                        "source_type": source_type,
                        "subreddit": subreddit,
                        "author": author,
                        "score": score,
                        "category": category,
                        "quote": passage,
                        "title": title,
                        "why_it_matters": WHY_MAP[category],
                        "signals": _matched_signals(passage, category),
                        "quote_strength": strength,
                    }


def extract_quote_candidates(
    threads_path: str | Path | Sequence[str | Path],
    *,
    out_path: str | Path | None = None,
) -> list[dict[str, Any]]:
    thread_paths = [threads_path] if isinstance(threads_path, (str, Path)) else list(threads_path)
    threads: list[dict[str, Any]] = []
    for path in thread_paths:
        threads.extend(load_threads_jsonl(path))
    items = list(iter_quote_candidates(threads))
    if out_path is not None:
        output = Path(out_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("w", encoding="utf-8") as fh:
            for item in items:
                fh.write(json.dumps(item, ensure_ascii=False) + "\n")
    return items
