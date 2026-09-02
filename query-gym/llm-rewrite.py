# Based on https://github.com/ls3-lab/QueryGym/blob/main/docs/user-guide/methods-reference.md

from pathlib import Path
import time

import querygym as qg
from querygym.core.llm import OpenAICompatibleClient


# Directory containing this script
BASE_DIR = Path(__file__).resolve().parent.parent


# Load data
queries = qg.load_queries(
    BASE_DIR / "topics" / "teste.txt"
)


# ----------------------------------------------------------------------
# Local Ollama client with thinking disabled
# ----------------------------------------------------------------------

class OllamaClient(OpenAICompatibleClient):

    def chat(self, messages, **kw):
        kw["reasoning_effort"] = "none"
        return super().chat(messages, **kw)


client = OllamaClient(
    model="qwen3.5:9b",
    base_url="http://127.0.0.1:11434/v1",
    api_key="ollama",
)


# ----------------------------------------------------------------------
# Create reformulator
# ----------------------------------------------------------------------

reformulator = qg.create_reformulator(
    "query2doc",
    model="qwen3.5:9b",
    # params={"mode": "zs"},
    llm_config={
        "base_url": "http://127.0.0.1:11434/v1",
        "api_key": "ollama",
        "temperature": 0.7,
        "max_tokens": 256,
    },
)


# Replace the client created by QueryGym with our customized client
reformulator.llm = client


# ----------------------------------------------------------------------
# Reformulate
# ----------------------------------------------------------------------

start_time = time.perf_counter()

results = reformulator.reformulate_batch(queries)

elapsed_time = time.perf_counter() - start_time


# ----------------------------------------------------------------------
# Print results
# ----------------------------------------------------------------------

print("\n=== RESULTS ===")

for result in results:
    print(f"QID: {result.qid}")
    print(f"Original: {result.original}")
    print(f"Reformulated: {result.reformulated}")


# ----------------------------------------------------------------------
# Timing
# ----------------------------------------------------------------------

print("\n=== TIMING ===")
print(f"Total time: {elapsed_time:.2f} seconds")

if results:
    print(f"Average: {elapsed_time / len(results):.2f} seconds/query")


# ----------------------------------------------------------------------
# Save
# ----------------------------------------------------------------------

qg.DataLoader.save_queries(
    [
        qg.QueryItem(r.qid, r.reformulated)
        for r in results
    ],
    BASE_DIR / "reformulated.tsv",
)