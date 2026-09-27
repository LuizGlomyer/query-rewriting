.PHONY: rewrite run run-baseline run-baseline-dev2 eval eval-baseline eval-baseline-dev2

rewrite:
	python scripts/llm-rewrite.py

run:
	python scripts/generate_run.py

run-baseline:
	python scripts/generate_run.py --topics-path topics/baseline/msmarco-v2-passage.dev.txt

run-baseline-dev2:
	python scripts/generate_run.py --topics-path topics/baseline/msmarco-v2-passage.dev2.txt

eval:
	python scripts/evaluate.py

eval-baseline:
	python scripts/evaluate.py --qrels qrels/msmarco-v2-passage.dev.txt --runs-path runs/baseline/msmarco-v2-passage.dev.txt

eval-baseline-dev2:
	python scripts/evaluate.py --qrels qrels/msmarco-v2-passage.dev2.txt --runs-path runs/baseline/msmarco-v2-passage.dev2.txt

