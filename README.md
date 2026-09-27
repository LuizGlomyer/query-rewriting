# Query Rewriting

This repository runs retrieval experiments over a Pyserini/Lucene index. The
pipeline is: prepare an index, optionally rewrite a query set with
[QueryGym](https://github.com/ls3-lab/QueryGym/blob/main/docs/user-guide/methods-reference.md)
and Ollama, search the index to produce a ranked run, then evaluate that run
against relevance judgments (qrels). Run commands below from the repository
root. Python dependencies are listed in [pyproject.toml](pyproject.toml); the
rewrite step also requires a running local Ollama server and a model available
to Ollama.

## Project Structure

- [collections/](collections/) contains downloaded source collections used to
  build indexes. These are the documents to be indexed, not the searchable
  index itself.
- [eval/](eval/) contains evaluation CSVs. `aggregated/` stores collection-level
  metrics; `detailed/` stores per-query metric values.
- [indexes/](indexes/) contains Pyserini-managed indexes, such as the Lucene
  index for MS MARCO V2 Passage.
- [qrels/](qrels/) contains query relevance judgments used to score runs. The
  [Castorini eval qrels](https://github.com/castorini/eval/tree/master/qrels)
  repository provides qrels for supported test collections.
- [runs/](runs/) contains search result artifacts: ranked documents retrieved
  for each topic/query file.
- [scripts/](scripts/) contains the pipeline wrappers:
  [llm-rewrite.py](scripts/llm-rewrite.py),
  [generate_run.py](scripts/generate_run.py), and
  [evaluate.py](scripts/evaluate.py).
- [topics/](topics/) contains query/topic files, including rewritten query
  files. Original topic sets are available from the
  [Castorini eval topics](https://github.com/castorini/eval/tree/master/topics)
  repository.

The rewrite, run, and evaluation scripts preserve the relevant input path
structure. For example, rewriting `topics/testqueries.txt` with model
`qwen3.5:9b` and technique `mugi` creates
`topics/qwen3.5-9b/testqueries/mugi.txt`; the colon in the model name is
replaced with a hyphen in the folder name.

## Pipeline

### 1. Set Up an Index

Pyserini provides [prebuilt indexes](https://github.com/castorini/pyserini/blob/master/docs/usage-index.md)
for some collections. When a suitable prebuilt index is unavailable, download
the collection and build a Lucene index. For MS MARCO V2 Passage:

```bash
mkdir -p collections
wget -P collections --header "X-Ms-Version: 2019-12-12" \
  https://msmarco.z22.web.core.windows.net/msmarcoranking/msmarco_v2_passage.tar
tar -xvf collections/msmarco_v2_passage.tar -C collections

python -m pyserini.index.lucene \
  --collection MsMarcoV2PassageCollection \
  --input collections/msmarco_v2_passage \
  --index indexes/lucene-index.msmarco-v2-passage \
  --generator DefaultLuceneDocumentGenerator \
  --threads 12
```

See the [Pyserini indexing guide](https://github.com/castorini/pyserini/blob/master/docs/usage-index.md)
for supported collection types and index options. The example uses 12 indexing
threads; adjust it to the machine and available resources.

### 2. Rewrite Queries (Optional)

[scripts/llm-rewrite.py](scripts/llm-rewrite.py) reads a query file, applies one
or more QueryGym reformulation techniques through Ollama's OpenAI-compatible
API, and writes reformulated query files. Start Ollama and ensure the requested
model is available before running it. Example:

```bash
python scripts/llm-rewrite.py \
  --qrel-path topics/testqueries.txt \
  --model qwen3.5:9b \
  --techniques mugi \
  --iterations 1
```

Despite its name, `--qrel-path` is the **input query file**, not a qrels file.
The available techniques are `query2doc`, `genqr`, `genqr_ensemble`,
`qa_expand`, `mugi`, and `query2e`. If `--techniques` is omitted, all six
configured techniques run. The default model is `qwen3.5:9b`, the default input
is `topics/testqueries.txt`, and the default iteration count is `1`.

With the example above, output is saved as
`topics/qwen3.5-9b/testqueries/mugi.txt`. With more than one iteration, files
are numbered, for example `mugi_1.txt` and `mugi_2.txt`. Each iteration starts
from the original input query file; iterations are not chained from the
previous iteration's rewritten output.

Accepted options:

- `--qrel-path PATH`: input query file (default: `topics/testqueries.txt`).
- `--model NAME`: Ollama model name (default: `qwen3.5:9b`).
- `--techniques TECHNIQUE [TECHNIQUE ...]`: one or more configured methods
  (default: all configured methods).
- `--iterations N`: number of runs per technique (default: `1`; must be at
  least `1`).

### 3. Search the Index

[scripts/generate_run.py](scripts/generate_run.py) passes each topic file in the
specified directory (or the single specified file) to
[Pyserini's Lucene searcher](https://github.com/castorini/pyserini/blob/master/docs/usage-search.md).
Topic files contain tab-separated query ID and query text fields; this project
uses `.txt` filenames for those files. Point it at the rewritten-query
directory to search those rewrites:

```bash
python scripts/generate_run.py \
  --index indexes/lucene-index.msmarco-v2-passage \
  --topics-path topics/qwen3.5-9b/testqueries \
  --batch-size 36 \
  --threads 12 \
  --hits 1000
```

By default, `--index` is `indexes/lucene-index.msmarco-v2-passage` and
`--topics-path` is `topics/qwen3.5-9b/testqueries`. Unless `--output-folder` is
provided, runs are written to the matching path under `runs/`, here
`runs/qwen3.5-9b/testqueries/`, with the same filenames as the topic files.
When passing a directory, the script processes its immediate files; use a
directory containing only the query files you intend to search.

Accepted options:

- `--index PATH`: Pyserini index (default: `indexes/lucene-index.msmarco-v2-passage`).
- `--topics-path PATH`: one query file or a directory of query files (default:
  `topics/qwen3.5-9b/testqueries`).
- `--output-folder PATH`: run output directory (default: derived by replacing
  `topics` with `runs` in the input path).
- `--batch-size N`: search batch size (default: `36`).
- `--threads N`: search threads (default: `12`).
- `--hits N`: number of ranked results per query (default: `1000`).

Each output is a ranked run in the standard six-column TREC run format used by
the Pyserini search CLI: query ID, `Q0`, document ID, rank, score, and run tag.
Runs can be large; size depends on the number of queries, requested hits, and
the collection.

### 4. Evaluate Runs

[scripts/evaluate.py](scripts/evaluate.py) evaluates one run file or every file
under a run directory against qrels, and writes aggregated and per-query CSVs:

```bash
python scripts/evaluate.py \
  --qrels qrels/qrels.msmarco-v2-passage.dev.txt \
  --runs-path runs/qwen3.5-9b/testqueries
```

The default qrels file is `qrels/qrels.msmarco-v2-passage.dev.txt`; the
default run directory is `runs/qwen3.5-9b/testqueries`. Unless
`--eval-folder` is set, output mirrors the run path under `eval/`. The example
creates files under `eval/aggregated/qwen3.5-9b/testqueries/` and
`eval/detailed/qwen3.5-9b/testqueries/`.

The configured metrics are `map_cut.100`, `recip_rank`, `recall.100,1000`,
`ndcg_cut.10`, and `P.10,100`. Aggregated CSVs contain metric/value pairs;
detailed CSVs contain one row per query ID. Evaluation is performed by
[Pyserini's trec_eval wrapper](https://github.com/castorini/pyserini/tree/master/pyserini/eval).

Accepted options:

- `--qrels PATH`: relevance judgments (default:
  `qrels/qrels.msmarco-v2-passage.dev.txt`).
- `--runs-path PATH`: one run file or a directory of run files (default:
  `runs/qwen3.5-9b/testqueries`).
- `--eval-folder PATH`: evaluation output root (default: derived by replacing
  `runs` with `eval` in the run path).

## Long-Running Jobs

Rewriting and indexing can take a while, depending on model, collection, and
machine resources. To keep a rewrite job running after disconnecting from a
terminal, use `tmux`:

```bash
tmux new -s query_rewriting
python scripts/llm-rewrite.py --techniques mugi --iterations 3
```

Detach with `Ctrl+B`, then `D`. Reconnect with:

```bash
tmux attach -t query_rewriting
```
