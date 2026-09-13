# Query Rewriting

This project uses [QueryGym](https://github.com/ls3-lab/QueryGym/blob/main/docs/user-guide/methods-reference.md) and an Ollama-compatible LLM to generate query
rewrites. Start Ollama locally before running the script.

## Run

```bash
python query-gym/llm-rewrite.py \
  --techniques query2doc mugi \
  --model qwen3.5:9b \
  --iterations 2 \
  --qrel-path topics/testqueries.txt
```

`--techniques` accepts one or more techniques. If omitted, all configured
techniques are run. `--iterations` controls how many rewrite passes are made
for each technique and defaults to `1`.

Results are saved under:

```text
query-gym/outputs/<query-file>/<technique>.txt
```

With multiple iterations, files are numbered, for example
`query2doc_1.txt` and `query2doc_2.txt`.

## Long-Running Jobs With tmux

Creating a tmux session is encouraged because rewriting can take several
hours or even days, depending on the model, techniques, query collection,
and parameters. The process continues running after disconnecting from the
terminal.

```bash
tmux new -s query_rewriting
python query-gym/llm-rewrite.py --techniques query2doc --iterations 3
```

Detach with `Ctrl+B`, then `D`. Reconnect later with:

```bash
tmux attach -t query_rewriting
```
