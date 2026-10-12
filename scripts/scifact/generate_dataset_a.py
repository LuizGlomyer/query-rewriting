
#!/usr/bin/env python3
"""Generate Dataset A from SciFact documents using Ollama."""

import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_PATH = (
    PROJECT_ROOT
    / "collections"
    / "scifact"
    / "processed"
    / "dataset_a_inputs.jsonl"
)
OUTPUT_PATH = (
    PROJECT_ROOT
    / "collections"
    / "scifact"
    / "processed"
    / "dataset_a.jsonl"
)
MANIFEST_PATH = (
    PROJECT_ROOT
    / "collections"
    / "scifact"
    / "processed"
    / "dataset_a_manifest.json"
)
PROMPT_PATH = PROJECT_ROOT / "prompts" / "dataset_a_v1.txt"

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen3.5:9b"

TEMPERATURE = 0.2
SEED = 42
TIMEOUT_SECONDS = 300
MAX_ATTEMPTS = 3
PROMPT_VERSION = "v1"


def read_jsonl(path: Path) -> list[dict]:
    """Read JSONL and reject malformed records."""
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


def load_completed_ids() -> set[str]:
    """Read valid existing results to support resuming."""
    completed = set()

    if not OUTPUT_PATH.exists():
        return completed

    for record in read_jsonl(OUTPUT_PATH):
        if record.get("status") != "success":
            continue

        doc_id = record.get("source_doc_id")
        query = record.get("query")

        if doc_id and isinstance(query, str) and query.strip():
            completed.add(str(doc_id))

    return completed


def generate_query(
    title: str,
    abstract: str,
    prompt_template: str,
) -> str:
    """Call Ollama and return one validated query."""
    prompt = prompt_template.format(
        title=title,
        abstract=abstract,
    )

    payload = {
        "model": MODEL,
        "stream": False,
        "format": "json",
        "think": False,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
        "options": {
            "temperature": TEMPERATURE,
            "seed": SEED,
        },
    }

    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    last_error = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(
                request, timeout=TIMEOUT_SECONDS
            ) as response:
                result = json.loads(response.read().decode("utf-8"))

            content = result.get("message", {}).get("content", "")
            parsed = json.loads(content)

            query = parsed.get("query")

            if not isinstance(query, str) or not query.strip():
                raise ValueError(
                    "The response does not contain a valid query."
                )

            return " ".join(query.split())

        except (
            urllib.error.URLError,
            TimeoutError,
            json.JSONDecodeError,
            ValueError,
        ) as exc:
            last_error = exc
            if attempt < MAX_ATTEMPTS:
                wait_seconds = 2 ** (attempt - 1)
                print(
                    f"  Attempt {attempt} failed: {exc}. "
                    f"Retrying in {wait_seconds}s."
                )
                time.sleep(wait_seconds)

    raise RuntimeError(
        f"Failed after {MAX_ATTEMPTS} attempts: {last_error}"
    )


def append_jsonl(record: dict) -> None:
    """Append one record and flush it immediately."""
    with OUTPUT_PATH.open("a", encoding="utf-8") as file:
        file.write(
            json.dumps(record, ensure_ascii=False) + "\n"
        )
        file.flush()


def main() -> None:
    if not INPUT_PATH.is_file():
        raise FileNotFoundError(f"Input file not found: {INPUT_PATH}")

    if not PROMPT_PATH.is_file():
        raise FileNotFoundError(f"Prompt file not found: {PROMPT_PATH}")

    prompt_template = PROMPT_PATH.read_text(encoding="utf-8")
    documents = read_jsonl(INPUT_PATH)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    completed_ids = load_completed_ids()

    print(f"Input documents: {len(documents)}")
    print(f"Queries already generated: {len(completed_ids)}")
    print(f"Model: {MODEL}")

    failures = 0

    for index, document in enumerate(documents, start=1):
        doc_id = str(document["document_id"])

        if doc_id in completed_ids:
            continue

        print(
            f"[{index}/{len(documents)}] "
            f"Documento {doc_id}: {document['title'][:70]}"
        )

        try:
            query = generate_query(
                title=document["title"],
                abstract=document["text"],
                prompt_template=prompt_template,
            )

            record = {
                "query_id": f"synthetic_{doc_id}",
                "source_doc_id": doc_id,
                "query": query,
                "generator": MODEL,
                "prompt_version": PROMPT_VERSION,
                "status": "success",
            }

            append_jsonl(record)
            completed_ids.add(doc_id)
            print(f"  Query: {query}")

        except Exception as exc:
            failures += 1
            print(f"  ERROR: {exc}")

            # Preserve the failure for diagnosis. On the next run,
            # this document will be retried.
            append_jsonl({
                "source_doc_id": doc_id,
                "status": "error",
                "error": str(exc),
                "generator": MODEL,
                "prompt_version": PROMPT_VERSION,
            })

    successful = len(completed_ids)

    manifest = {
        "collection": "SciFact",
        "input": str(INPUT_PATH.relative_to(PROJECT_ROOT)),
        "output": str(OUTPUT_PATH.relative_to(PROJECT_ROOT)),
        "prompt": str(PROMPT_PATH.relative_to(PROJECT_ROOT)),
        "prompt_version": PROMPT_VERSION,
        "generator": MODEL,
        "ollama_endpoint": OLLAMA_URL,
        "temperature": TEMPERATURE,
        "seed": SEED,
        "started_or_updated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "input_count": len(documents),
        "successful_count": successful,
        "failures_this_run": failures,
    }

    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print("\nGeneration complete")
    print(f"Valid queries: {successful}")
    print(f"Failures in this run: {failures}")
    print(f"Output: {OUTPUT_PATH}")
    print(f"Manifest: {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
