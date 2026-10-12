
#!/usr/bin/env python3
"""Select a reproducible sample of SciFact documents."""

import json
import random
from pathlib import Path

SEED = 42
SAMPLE_SIZE = 50

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CORPUS_PATH = (
    PROJECT_ROOT
    / "collections"
    / "scifact"
    / "raw"
    / "scifact"
    / "corpus.jsonl"
)

OUTPUT_DIR = PROJECT_ROOT / "collections" / "scifact" / "processed"
OUTPUT_PATH = OUTPUT_DIR / "dataset_a_inputs.jsonl"
MANIFEST_PATH = OUTPUT_DIR / "dataset_a_inputs_manifest.json"


def load_documents() -> list[dict]:
    """Load and validate the source corpus."""
    documents = []
    seen_ids = set()

    with CORPUS_PATH.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue

            document = json.loads(line)

            for field in ("_id", "title", "text"):
                if field not in document:
                    raise ValueError(
                        f"Missing field '{field}' on line "
                        f"{line_number}"
                    )

            doc_id = str(document["_id"])

            if doc_id in seen_ids:
                raise ValueError(
                    f"Duplicate document ID: {doc_id}"
                )

            seen_ids.add(doc_id)

            if not str(document["title"]).strip():
                continue

            if not str(document["text"]).strip():
                continue

            documents.append({
                "document_id": doc_id,
                "title": document["title"].strip(),
                "text": document["text"].strip(),
            })

    return documents


def main() -> None:
    if not CORPUS_PATH.is_file():
        raise FileNotFoundError(
            f"Corpus not found: {CORPUS_PATH}"
        )

    documents = load_documents()

    if not documents:
        raise ValueError("No valid documents found.")

    sample_size = min(SAMPLE_SIZE, len(documents))
    selected = random.Random(SEED).sample(
        documents, sample_size
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        for document in selected:
            file.write(
                json.dumps(document, ensure_ascii=False) + "\n"
            )

    manifest = {
        "collection": "SciFact",
        "source": str(CORPUS_PATH.relative_to(PROJECT_ROOT)),
        "output": str(OUTPUT_PATH.relative_to(PROJECT_ROOT)),
        "selection_method": "random_sample_without_replacement",
        "seed": SEED,
        "requested_sample_size": SAMPLE_SIZE,
        "selected_count": sample_size,
        "eligible_document_count": len(documents),
        "fields": ["document_id", "title", "text"],
    }

    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print("Selection complete")
    print(f"Eligible documents: {len(documents)}")
    print(f"Selected documents: {sample_size}")
    print(f"Input dataset: {OUTPUT_PATH}")
    print(f"Manifest: {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
