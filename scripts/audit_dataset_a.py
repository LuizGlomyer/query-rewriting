
#!/usr/bin/env python3
"""Audit Dataset A and prepare examples for manual review."""

import json
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "collections" / "scifact" / "processed"

INPUT_PATH = PROCESSED / "dataset_a_inputs.jsonl"
OUTPUT_PATH = PROCESSED / "dataset_a.jsonl"
REPORT_PATH = PROCESSED / "dataset_a_audit_report.json"
REVIEW_PATH = PROCESSED / "dataset_a_review.jsonl"


def read_jsonl(path: Path) -> list[dict]:
    records = []

    with path.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON in {path}, line {line_number}"
                ) from exc

    return records


def normalize(text: str) -> str:
    """Normalize text for exact-match and duplicate checks."""
    return " ".join(re.findall(r"\w+", text.casefold()))


def main() -> None:
    inputs = read_jsonl(INPUT_PATH)
    outputs = read_jsonl(OUTPUT_PATH)

    # Index the input documents by their original IDs.
    input_by_id = {}
    for record in inputs:
        doc_id = str(record["document_id"])
        if doc_id in input_by_id:
            raise ValueError(f"Duplicate input ID: {doc_id}")
        input_by_id[doc_id] = record

    # Keep the most recent record for each source document.
    # This supports output files containing historical failures
    # followed by a successful retry.
    latest_by_id = {}
    for record in outputs:
        doc_id = record.get("source_doc_id")
        if doc_id is not None:
            latest_by_id[str(doc_id)] = record

    successful = [
        record for record in latest_by_id.values()
        if record.get("status") == "success"
        and isinstance(record.get("query"), str)
        and record["query"].strip()
    ]

    failed = [
        record for record in latest_by_id.values()
        if record.get("status") != "success"
        or not isinstance(record.get("query"), str)
        or not record["query"].strip()
    ]

    input_ids = set(input_by_id)
    output_ids = set(latest_by_id)
    success_ids = {
        str(record["source_doc_id"]) for record in successful
    }

    missing_ids = sorted(input_ids - output_ids)
    unexpected_ids = sorted(output_ids - input_ids)
    without_success = sorted(input_ids - success_ids)

    # Detect exact duplicates after normalization.
    query_groups = defaultdict(list)
    title_matches = []
    query_lengths = []

    for record in successful:
        doc_id = str(record["source_doc_id"])
        query = record["query"].strip()
        document = input_by_id.get(doc_id)

        query_groups[normalize(query)].append(doc_id)
        query_lengths.append(len(query.split()))

        if document and normalize(query) == normalize(
            document["title"]
        ):
            title_matches.append(doc_id)

    duplicate_groups = {
        query: ids
        for query, ids in query_groups.items()
        if query and len(ids) > 1
    }

    # Prepare a review file linking each query to its source text.
# Preserve the original input order in the review file.
    with REVIEW_PATH.open("w", encoding="utf-8") as file:
        successful_by_id = {
            str(record["source_doc_id"]): record
            for record in successful
        }

        for document in inputs:
            doc_id = str(document["document_id"])
            record = successful_by_id.get(doc_id)

            if record is None:
                continue

            review_record = {
                "query_id": record.get("query_id"),
                "source_doc_id": doc_id,
                "query": record["query"],
                "title": document["title"],
                "text": document["text"],
            }

            file.write(
                json.dumps(review_record, ensure_ascii=False) + "\n"
            )

    report = {
        "input_document_count": len(inputs),
        "output_record_count": len(outputs),
        "unique_output_document_count": len(latest_by_id),
        "successful_query_count": len(successful),
        "latest_failed_document_count": len(failed),
        "input_documents_without_success": len(without_success),
        "missing_output_ids": missing_ids,
        "unexpected_output_ids": unexpected_ids,
        "successful_queries_identical_to_title": len(title_matches),
        "title_match_document_ids": title_matches,
        "unique_normalized_queries": len(
            {normalize(r["query"]) for r in successful}
        ),
        "duplicate_query_group_count": len(duplicate_groups),
        "duplicate_query_groups": list(
            duplicate_groups.values()
        ),
        "query_word_count": {
            "min": min(query_lengths) if query_lengths else None,
            "median": (
                statistics.median(query_lengths)
                if query_lengths else None
            ),
            "max": max(query_lengths) if query_lengths else None,
        },
        "review_file": str(REVIEW_PATH.relative_to(ROOT)),
    }

    REPORT_PATH.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print("Dataset A audit")
    print("----------------------")
    print(f"Input documents: {len(inputs)}")
    print(f"Output records: {len(outputs)}")
    print(f"Valid queries: {len(successful)}")
    print(f"Documents without a valid query: {len(without_success)}")
    print(f"IDs missing from output: {len(missing_ids)}")
    print(f"Unexpected IDs: {len(unexpected_ids)}")
    print(f"Duplicate query groups: {len(duplicate_groups)}")
    print(f"Queries identical to titles: {len(title_matches)}")
    print(f"Report: {REPORT_PATH}")
    print(f"Review file: {REVIEW_PATH}")


if __name__ == "__main__":
    main()
