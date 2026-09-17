from pathlib import Path

# llm-rewrite.py constants
SCRIPT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_MODEL = "qwen3.5:9b"
DEFAULT_QUERY_PATH = SCRIPT_DIR.parent / "topics" / "testqueries.txt"
OUTPUT_DIR = SCRIPT_DIR.parent / "topics" / "rewritten"
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

DEFAULT_TECHNIQUES = list(REFORMULATOR_CONFIGS)

# generate_run.py constants
DEFAULT_INDEX = "indexes/lucene-index.msmarco-v2-passage"
DEFAULT_TOPICS_FOLDER = "topics/rewritten/qwen3.5-9b/testqueries"
DEFAULT_OUTPUT_FOLDER = "runs/rewritten/qwen3.5-9b/testqueries"
DEFAULT_BATCH_SIZE = 36
DEFAULT_THREADS = 12
DEFAULT_HITS = 1000

__all__ = [
    "DEFAULT_BATCH_SIZE",
    "DEFAULT_HITS",
    "DEFAULT_INDEX",
    "DEFAULT_MODEL",
    "DEFAULT_OUTPUT_FOLDER",
    "DEFAULT_QUERY_PATH",
    "DEFAULT_TECHNIQUES",
    "DEFAULT_THREADS",
    "DEFAULT_TOPICS_FOLDER",
    "OLLAMA_LLM_CONFIG",
    "OUTPUT_DIR",
    "REFORMULATOR_CONFIGS",
    "SCRIPT_DIR",
]
