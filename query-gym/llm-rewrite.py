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

class OllamaClient(OpenAICompatibleClient):

    def chat(self, messages, **kw):
        kw["reasoning_effort"] = "none"
        return super().chat(messages, **kw)


def query2doc_reformulator(model):
    reformulator = qg.create_reformulator(
        "query2doc",
        model=model,
        params={"mode": "zs"},
        llm_config={
            "base_url": "http://127.0.0.1:11434/v1",
            "api_key": "ollama",
            "temperature": 0.7,
            "max_tokens": 256,
        },
    )
    reformulator.llm = OllamaClient(
        model=model,
        base_url="http://127.0.0.1:11434/v1",
        api_key="ollama",
    )
    return reformulator


def create_reformulator(technique, model):
    reformulators = {
        "query2doc": query2doc_reformulator,
    }
    try:
        return reformulators[technique](model)
    except KeyError as error:
        available = ", ".join(sorted(reformulators))
        raise ValueError(
            f"Unknown technique {technique!r}. Available techniques: {available}"
        ) from error


def parse_args():
    parser = argparse.ArgumentParser(description="Reformulate a query collection.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="LLM model to use.")
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
    return parser.parse_args()


def main():
    args = parse_args()
    queries = qg.load_queries(args.query_path)
    reformulator = create_reformulator(args.technique, args.model)

    start_time = time.perf_counter()
    results = reformulator.reformulate_batch(queries)
    elapsed_time = time.perf_counter() - start_time

    if results:
        print("\n=== SAMPLE RESULT ===")
        print(f"QID: {results[0].qid}")
        print(f"Original: {results[0].original}")
        print(f"Reformulated: {results[0].reformulated}")

    print("\n=== TIMING ===")
    print(f"Total time: {elapsed_time:.2f} seconds")
    if results:
        print(f"Average: {elapsed_time / len(results):.2f} seconds/query")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / (
        f"{args.query_path.stem}-{args.technique}"
        f"{args.query_path.suffix}"
    )
    qg.DataLoader.save_queries(
        [qg.QueryItem(r.qid, r.reformulated) for r in results],
        output_path,
    )
    print(f"Saved to: {output_path}")


if __name__ == "__main__":
    main()