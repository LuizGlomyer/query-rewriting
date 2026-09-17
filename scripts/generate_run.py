import argparse
import subprocess
import time
from pathlib import Path

from config import *
from utils import format_elapsed_time



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
        "--topics-folder",
        default=DEFAULT_TOPICS_FOLDER,
        help=f"Folder containing topics/query files (default: {DEFAULT_TOPICS_FOLDER})",
    )

    parser.add_argument(
        "--output-folder",
        default=DEFAULT_OUTPUT_FOLDER,
        help=f"Folder for output run files (default: {DEFAULT_OUTPUT_FOLDER})",
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
    topics_folder = Path(args.topics_folder)
    output_folder = Path(args.output_folder)
    topic_files = sorted(path for path in topics_folder.iterdir() if path.is_file())

    if not topic_files:
        raise FileNotFoundError(f"No topic files found in {topics_folder}")

    output_folder.mkdir(parents=True, exist_ok=True)
    total_started_at = time.perf_counter()

    for topic_file in topic_files:
        output_file = output_folder / topic_file.name
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