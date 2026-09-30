import argparse
import subprocess
import time
from pathlib import Path

from config import *
from utils import derive_mapped_folder, format_elapsed_time



def parse_args():
    parser = argparse.ArgumentParser(
        description="Wrapper around the Pyserini Lucene search CLI."
    )

    parser.add_argument(
        "--index",
        default=DEFAULT_INDEX,
        help=f"Pyserini index (default: {DEFAULT_INDEX})",
    )

    parser.add_argument(
        "--topics-path",
        default=DEFAULT_TOPICS_FOLDER,
        help=f"Path containing topics/query files (default: {DEFAULT_TOPICS_FOLDER})",
    )

    parser.add_argument(
        "--output-folder",
        default=None,
        help="Folder for output run files (derived from --topics-path by default)",
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"Pyserini batch size (default: {DEFAULT_BATCH_SIZE})",
    )

    parser.add_argument(
        "--threads",
        type=int,
        default=DEFAULT_THREADS,
        help=f"Number of Pyserini search threads (default: {DEFAULT_THREADS})",
    )

    parser.add_argument(
        "--hits",
        type=int,
        default=DEFAULT_HITS,
        help=f"Number of hits per query (default: {DEFAULT_HITS})",
    )

    return parser.parse_args()


def main():
    args = parse_args()
    topics_path = Path(args.topics_path)

    if not topics_path.exists():
        raise FileNotFoundError(f"Topics path not found: {topics_path}")

    if topics_path.is_file():
        topic_files = [topics_path]
        topics_root = topics_path.parent
    else:
        topic_files = sorted(path for path in topics_path.rglob("*") if path.is_file())
        topics_root = topics_path

    output_folder = (
        Path(args.output_folder)
        if args.output_folder
        else derive_mapped_folder(topics_path, "topics", "runs")
    )

    if not topic_files:
        raise FileNotFoundError(f"No topic files found in {topics_path}")

    output_folder.mkdir(parents=True, exist_ok=True)
    total_started_at = time.perf_counter()

    for topic_file in topic_files:
        output_file = output_folder / topic_file.relative_to(topics_root)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        command = [
            "python",
            "-m",
            "pyserini.search.lucene",
            "--index",
            args.index,
            "--topics",
            str(topic_file),
            "--output",
            str(output_file),
            "--batch-size",
            str(args.batch_size),
            "--threads",
            str(args.threads),
            "--hits",
            str(args.hits),
            "--bm25",
        ]

        print("*" * 50)
        print(f"Processing {topic_file}")
        started_at = time.perf_counter()
        subprocess.run(command, check=True)
        elapsed = time.perf_counter() - started_at
        print(f"Output written to {output_file}")
        print(f"Finished in {format_elapsed_time(elapsed)}")
        print("*" * 50)
        print()

    total_elapsed = time.perf_counter() - total_started_at
    print(
        f"Total time for {len(topic_files)} files: "
        f"{format_elapsed_time(total_elapsed)}"
    )


if __name__ == "__main__":
    main()