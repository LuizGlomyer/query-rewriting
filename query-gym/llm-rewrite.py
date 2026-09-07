# Based on https://github.com/ls3-lab/QueryGym/blob/main/docs/user-guide/methods-reference.md

import argparse
from pathlib import Path
import time

import querygym as qg
from querygym.core.llm import OpenAICompatibleClient


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_MODEL = "qwen3.5:9b"
DEFAULT_TECHNIQUE = "query2doc"
DEFAULT_QUERY_PATH = SCRIPT_DIR.parent / "topics" / "testqueries.txt"
OUTPUT_DIR = SCRIPT_DIR / "outputs"
OLLAMA_LLM_CONFIG = {
    "base_url": "http://127.0.0.1:11434/v1",
    "api_key": "ollama",
    "temperature": 0.7,
    "max_tokens": 256,
}

REFORMULATOR_CONFIGS = {
    "query2doc": {
        "params": {"mode": "zs"},
    },
    "genqr": {
        "params": {"n_generations": 5},
    },
    "genqr_ensemble": {
        "params": {
            "repeat_query_weight": 3,
            "parallel": True,
        },
        "llm_config": {"temperature": 0.92},
    },
    "qa_expand": {
        "params": {
            "temperature_subq": 0.7,
            "temperature_answer": 0.9,
            "temperature_refine": 0.6,
            "max_tokens": 512,
        },
    },
    "mugi": {
        "params": {
            "num_docs": 3,
            "parallel": True,
            "mode": "zs",
        },
    },
    "query2e": {
        "params": {"mode": "zs", "max_keywords": 20},
    },
}

class OllamaClient(OpenAICompatibleClient):

    def chat(self, messages, **kw):
        kw["reasoning_effort"] = "none"
        return super().chat(messages, **kw)


def attach_ollama_client(reformulator, model):
    reformulator.llm = OllamaClient(
        model=model,
        base_url=OLLAMA_LLM_CONFIG["base_url"],
        api_key=OLLAMA_LLM_CONFIG["api_key"],
    )
    return reformulator


def get_reformulator_config(technique):
    try:
        return REFORMULATOR_CONFIGS[technique]
    except KeyError as error:
        available = ", ".join(sorted(REFORMULATOR_CONFIGS))
        raise ValueError(
            f"Unknown technique {technique!r}. Available techniques: {available}"
        ) from error


def create_reformulator(technique, model):
    config = get_reformulator_config(technique)

    llm_config = {**OLLAMA_LLM_CONFIG, **config.get("llm_config", {})}
    reformulator = qg.create_reformulator(
        technique,
        model=model,
        params=config["params"],
        llm_config=llm_config,
    )
    return attach_ollama_client(reformulator, model)


def format_elapsed_time(elapsed_time):
    total_seconds = int(elapsed_time)
    days, remainder = divmod(total_seconds, 24 * 60 * 60)
    hours, remainder = divmod(remainder, 60 * 60)
    minutes, seconds = divmod(remainder, 60)

    parts = []
    if days:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if seconds or not parts:
        parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")

    return ", ".join(parts)


def print_run_output(results, elapsed_time, technique, model, iterations, config):
    if results:
        print("\n=== SAMPLE RESULT ===")
        print(f"QID: {results[0].qid}")
        print(f"Original: {results[0].original}")
        print(f"Reformulated: {results[0].reformulated}")

    print("\n=== CONFIGURATION ===")
    print(f"Model: {model}")
    print(f"Technique: {technique}")
    print(f"Iterations: {iterations}")
    print(f"Parameters: {config['params']}")
    print(f"LLM config: {config['llm_config']}")

    print("\n=== TIMING ===")
    print(f"Total time: {format_elapsed_time(elapsed_time)}")
    if results:
        total_queries = len(results) * iterations
        print(f"Average: {elapsed_time / total_queries:.2f} seconds/query")


def save_results(results, query_path, technique, iteration=None):
    output_dir = OUTPUT_DIR / query_path.stem
    output_dir.mkdir(parents=True, exist_ok=True)
    suffix = f"_{iteration}" if iteration is not None else ""
    output_path = output_dir / f"{technique}{suffix}.txt"
    qg.DataLoader.save_queries(
        [qg.QueryItem(r.qid, r.reformulated) for r in results],
        output_path,
    )
    print(f"Saved to: {output_path}")
    return output_path


def parse_args():
    parser = argparse.ArgumentParser(description="Reformulate a query collection.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="LLM model to use.")
    parser.add_argument(
        "--iterations",
        type=int,
        default=1,
        help="Number of sequential rewriting passes to run.",
    )
    parser.add_argument(
        "--technique",
        default=DEFAULT_TECHNIQUE,
        help="Rewriting technique to use.",
    )
    parser.add_argument(
        "--qrel-path",
        type=Path,
        default=DEFAULT_QUERY_PATH,
        dest="query_path",
        help="Path to the input query/qrel file.",
    )
    args = parser.parse_args()
    if args.iterations < 1:
        parser.error("--iterations must be at least 1")
    return args


def main():
    args = parse_args()

    config = get_reformulator_config(args.technique)
    effective_config = {
        "params": config["params"],
        "llm_config": {**OLLAMA_LLM_CONFIG, **config.get("llm_config", {})},
    }
    reformulator = create_reformulator(args.technique, args.model)

    start_time = time.perf_counter()
    results = []
    for iteration in range(1, args.iterations + 1):
        print(f"\n=== ITERATION {iteration} ===")
        queries = qg.load_queries(args.query_path)
        iteration_start_time = time.perf_counter()
        results = reformulator.reformulate_batch(queries)
        iteration_elapsed_time = time.perf_counter() - iteration_start_time
        print(f"Iteration time: {format_elapsed_time(iteration_elapsed_time)}")
        save_results(
            results,
            args.query_path,
            args.technique,
            iteration if args.iterations > 1 else None,
        )
        queries = [qg.QueryItem(r.qid, r.reformulated) for r in results]
    elapsed_time = time.perf_counter() - start_time

    print_run_output(
        results,
        elapsed_time,
        args.technique,
        args.model,
        args.iterations,
        effective_config,
    )
if __name__ == "__main__":
    main()

# TODO add LAMER and CSQE later