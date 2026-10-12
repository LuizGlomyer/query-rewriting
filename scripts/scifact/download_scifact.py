
#!/usr/bin/env python3
"""Download and validate the SciFact collection from BEIR."""

import json
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

URL = (
    "https://public.ukp.informatik.tu-darmstadt.de/"
    "thakur/BEIR/datasets/scifact.zip"
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "collections" / "scifact"
ZIP_PATH = DATA_DIR / "scifact.zip"
RAW_DIR = DATA_DIR / "raw"
CORPUS_PATH = RAW_DIR / "scifact" / "corpus.jsonl"


def download_dataset() -> None:
    """Download the archive if it does not already exist."""
    if ZIP_PATH.exists():
        print(f"Archive already exists: {ZIP_PATH}")
        return

    print(f"Downloading SciFact from:\n{URL}")
    request = urllib.request.Request(
        URL,
        headers={"User-Agent": "query-rewriting-poc/1.0"},
    )

    with urllib.request.urlopen(request, timeout=120) as response:
        with ZIP_PATH.open("wb") as destination:
            while chunk := response.read(1024 * 1024):
                destination.write(chunk)

    print(f"Download complete: {ZIP_PATH}")


def extract_dataset() -> None:
    """Extract the archive without overwriting existing files."""
    if CORPUS_PATH.exists():
        print(f"Corpus already extracted: {CORPUS_PATH}")
        return

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(ZIP_PATH) as archive:
        members = archive.infolist()

        # Reject absolute paths and directory traversal.
        for member in members:
            member_path = PurePosixPath(member.filename)
            if (
                member_path.is_absolute()
                or ".." in member_path.parts
            ):
                raise ValueError(
                    f"Unsafe path in ZIP archive: "
                    f"{member.filename}"
                )

        archive.extractall(RAW_DIR)

    if not CORPUS_PATH.exists():
        raise FileNotFoundError(
            "The corpus.jsonl file was not found at the expected path: "
            f"{CORPUS_PATH}. Check the ZIP archive structure."
        )

    print(f"Extraction complete: {RAW_DIR}")


def validate_corpus() -> None:
    """Check the corpus format and report basic statistics."""
    document_count = 0
    empty_text_count = 0
    sample = None

    with CORPUS_PATH.open(encoding="utf-8") as corpus_file:
        for line_number, line in enumerate(corpus_file, start=1):
            if not line.strip():
                continue

            try:
                document = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON on line {line_number}"
                ) from exc

            required_fields = {"_id", "title", "text"}
            missing = required_fields - document.keys()

            if missing:
                raise ValueError(
                    f"Missing fields on line {line_number}: "
                    f"{sorted(missing)}"
                )

            document_count += 1

            if not document["text"].strip():
                empty_text_count += 1

            if sample is None:
                sample = document

    if document_count == 0:
        raise ValueError("The corpus is empty.")

    print("\nSciFact validation")
    print("--------------------")
    print(f"File: {CORPUS_PATH}")
    print(f"Documents: {document_count}")
    print(f"Documents without text: {empty_text_count}")
    print(f"First document ID: {sample['_id']}")
    print(f"Title: {sample['title'][:150]}")

    if empty_text_count:
        print(
            "WARNING: some documents have no text; "
            "inspect them before generation."
        )


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    download_dataset()

    if not zipfile.is_zipfile(ZIP_PATH):
        raise ValueError(
            f"Downloaded file is not a valid ZIP archive: {ZIP_PATH}"
        )

    extract_dataset()
    validate_corpus()


if __name__ == "__main__":
    main()
