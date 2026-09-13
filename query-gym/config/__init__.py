from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_MODEL = "qwen3.5:9b"
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

DEFAULT_TECHNIQUES = list(REFORMULATOR_CONFIGS)

__all__ = [
    "DEFAULT_MODEL",
    "DEFAULT_QUERY_PATH",
    "DEFAULT_TECHNIQUES",
    "OLLAMA_LLM_CONFIG",
    "OUTPUT_DIR",
    "REFORMULATOR_CONFIGS",
    "SCRIPT_DIR",
]
