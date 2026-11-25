"""Evidence collection and citation validation."""

import re

MAX_EVIDENCE_ITEMS = 20
MAX_SOURCE_CHARS = 2500
MAX_CONTEXT_CHARS = 14000


def collect_evidence(
    existing: list[dict],
    result,
) -> list[dict]:
    evidence = [dict(item) for item in existing]

    candidates = result if isinstance(result, list) else [result]

    for item in candidates:
        if not isinstance(item, dict):
            continue

        required = {
            "file_path",
            "start_line",
            "end_line",
            "content",
        }

        if not required.issubset(item):
            continue

        if not isinstance(item["content"], str):
            continue

        if not item["content"].strip():
            continue

        key = (
            item["file_path"],
            item["start_line"],
            item["end_line"],
        )

        duplicate = any(
            (
                source["file_path"],
                source["start_line"],
                source["end_line"],
            )
            == key
            for source in evidence
        )

        if duplicate:
            continue

        if len(evidence) >= MAX_EVIDENCE_ITEMS:
            break

        evidence.append(
            {
                "id": f"S{len(evidence) + 1}",
                "file_path": item["file_path"],
                "start_line": item["start_line"],
                "end_line": item["end_line"],
                "content": item["content"][:MAX_SOURCE_CHARS],
                "truncated": (len(item["content"]) > MAX_SOURCE_CHARS),
            }
        )

    return evidence


def select_evidence(evidence: list[dict]) -> list[dict]:
    selected = []
    used = 0

    for source in evidence:
        size = len(source["content"]) + 200

        if used + size > MAX_CONTEXT_CHARS:
            break

        selected.append(source)
        used += size

    return selected


def format_evidence(evidence: list[dict]) -> str:
    sections = []

    for source in evidence:
        sections.append(
            f"[{source['id']}]\n"
            f"File: {source['file_path']}\n"
            f"Lines: {source['start_line']}-"
            f"{source['end_line']}\n"
            f"Truncated: {source['truncated']}\n"
            f"Code:\n{source['content']}"
        )

    return "\n\n".join(sections)


def validate_citations(
    answer: str,
    evidence: list[dict],
) -> bool:
    cited = set(re.findall(r"\[(S\d+)\]", answer))

    available = {source["id"] for source in evidence}

    return bool(cited) and cited.issubset(available)
