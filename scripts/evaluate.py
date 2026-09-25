import argparse
import csv
import subprocess
import sys
import time
from pathlib import Path

from config import *
from utils import format_elapsed_time


def parse_args():
    parser = argparse.ArgumentParser(
        description="Wrapper around the Pyserini trec_eval CLI."
    )

    parser.add_argument(
        "--qrels",
        default=DEFAULT_QRELS,
        help=f"Qrels file (default: {DEFAULT_QRELS})",
    )

    parser.add_argument(
        "--runs-folder",
        default=DEFAULT_RUNS_FOLDER,
        help=f"Folder containing run files (default: {DEFAULT_RUNS_FOLDER})",
    )

    parser.add_argument(
        "--eval-folder",
        default=DEFAULT_EVAL_FOLDER,
        help=f"Folder for evaluation results (default: {DEFAULT_EVAL_FOLDER})",
    )

    return parser.parse_args()


def build_command(qrels, run_file, per_query=False):
    command = [
        sys.executable,
        "-m",
        "pyserini.eval.trec_eval",
    ]

    if per_query:
        command.append("-q")

    command.append("-c")

    for metric in EVAL_METRICS:
        command.extend(["-m", metric])

    command.extend(
        [
            str(qrels),
            str(run_file),
        ]
    )

    return command


def parse_aggregated_output(output):
    results = []

    for line in output.splitlines():
        parts = line.split()

        if len(parts) != 3:
            continue

        metric, query_id, value = parts

        if query_id != "all":
            continue

        results.append((metric, float(value)))

    return results


def parse_detailed_output(output):
    results = {}

    for line in output.splitlines():
        parts = line.split()

        if len(parts) != 3:
            continue

        metric, query_id, value = parts

        if query_id == "all":
            continue

        results.setdefault(query_id, {})[metric] = float(value)

    return results


def write_aggregated_results(output_file, results):
    with output_file.open("w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["metric", "value"],
        )

        writer.writeheader()

        for metric, value in results:
            writer.writerow(
                {
                    "metric": metric,
                    "value": value,
                }
            )


def write_detailed_results(output_file, results):
    metric_names = []

    for _, values in results.items():
        for metric in values:
            if metric not in metric_names:
                metric_names.append(metric)

    fieldnames = ["qid", *metric_names]

    with output_file.open("w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for qid in sorted(results, key=lambda value: int(value)):
            row = {"qid": qid}
            row.update(results[qid])
            writer.writerow(row)


def evaluate_run(qrels, run_file, aggregated_file, detailed_file):
    aggregated_command = build_command(
        qrels=qrels,
        run_file=run_file,
    )

    detailed_command = build_command(
        qrels=qrels,
        run_file=run_file,
        per_query=True,
    )

    print("Running aggregated evaluation...")

    aggregated_process = subprocess.run(
        aggregated_command,
        check=True,
        capture_output=True,
        text=True,
    )

    print("Running per-query evaluation...")

    detailed_process = subprocess.run(
        detailed_command,
        check=True,
        capture_output=True,
        text=True,
    )

    aggregated_results = parse_aggregated_output(
        aggregated_process.stdout
    )

    detailed_results = parse_detailed_output(
        detailed_process.stdout
    )

    write_aggregated_results(
        aggregated_file,
        aggregated_results,
    )

    write_detailed_results(
        detailed_file,
        detailed_results,
    )


def main():
    args = parse_args()

    qrels = Path(args.qrels)
    runs_folder = Path(args.runs_folder)
    eval_folder = Path(args.eval_folder)

    if not qrels.is_file():
        raise FileNotFoundError(
            f"Qrels file not found: {qrels}"
        )

    if not runs_folder.is_dir():
        raise FileNotFoundError(
            f"Runs folder not found: {runs_folder}"
        )

    run_files = sorted(
        path
        for path in runs_folder.rglob("*")
        if path.is_file()
    )

    if not run_files:
        raise FileNotFoundError(
            f"No run files found in {runs_folder}"
        )

    total_started_at = time.perf_counter()

    for run_file in run_files:
        relative_path = run_file.relative_to(runs_folder)

        aggregated_file = (
            eval_folder
            / "aggregated"
            / relative_path.parent
            / f"{relative_path.stem}.csv"
        )

        detailed_file = (
            eval_folder
            / "detailed"
            / relative_path.parent
            / f"{relative_path.stem}.csv"
        )

        aggregated_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        detailed_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        print("*" * 50)
        print(f"Processing {run_file}")

        started_at = time.perf_counter()

        evaluate_run(
            qrels=qrels,
            run_file=run_file,
            aggregated_file=aggregated_file,
            detailed_file=detailed_file,
        )

        elapsed = time.perf_counter() - started_at

        print(f"Aggregated output: {aggregated_file}")
        print(f"Detailed output: {detailed_file}")
        print(f"Finished in {format_elapsed_time(elapsed)}")
        print("*" * 50)
        print()

    total_elapsed = time.perf_counter() - total_started_at

    print(
        f"Total time for {len(run_files)} files: "
        f"{format_elapsed_time(total_elapsed)}"
    )


if __name__ == "__main__":
    main()
