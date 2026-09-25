.PHONY: rewrite run run-baseline eval eval-baseline

rewrite:
	python scripts/llm-rewrite.py

run:
	python scripts/generate_run.py

run-baseline:
	python scripts/generate_run.py --topics-path topics/msmarco-v2-passage.dev.txt

eval:
	python scripts/evaluate.py

eval-baseline:
	python scripts/evaluate.py --runs-path runs/msmarco-v2-passage.dev.txt

