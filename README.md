# autonomous-long-running-agents

**tree_ai_scientist** — autonomous Qwen ReAct molecular research that writes **literal Git-backed experiment papers** under a hard context ceiling.

**Author:** Ashutosh Ganguly — AI researcher @ MBZUAI.

## Decisive question

Can a long-running ReAct agent maintain a **tree of experimental papers** (immutable Git commits + mutable SQLite ledger), expand strategies with workers, and improve a chemistry objective **without** an oracle campaign budget—only a **32,768-token** per-request ceiling?

## Claim (current campaigns)

On GuacaMol **Amlodipine MPO** (archived summary):

| Metric | Value |
|--------|------:|
| Committed nodes / papers | **49** nodes · **48** papers |
| Best measured oracle score | **0.9045** |
| Persistence | `ledger.sqlite` + `memory.git` (`refs/nodes/<id>`) |

See [`results/RESULTS.md`](results/RESULTS.md).

## Architecture (short)

- **One anchor molecule per node.** Qwen chooses strategies, may dispatch workers; all worker results live in the same node’s paper.
- **Branching** creates a new node from an evaluated molecule on a committed parent.
- **Actions:** `search`, `read`, `compare`, `inspect_tree`, `write`, `deep_read`, `worker`, `call_oracle`, `commit_results`, `start_node`, `checkpoint`.
- Context rollover archives the transcript and continues the same node—publication is not forced.
- Design-before-code: [`DESIGN.md`](DESIGN.md).

## Setup (HPC-oriented)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
pytest -q
cp config.hpc.example.json config.hpc.json   # point at local vLLM / embeddings
python -m tree_ai_scientist init --campaign runs/campaign-v0 --config config.hpc.json
python -m tree_ai_scientist run --campaign runs/campaign-v0
python -m tree_ai_scientist status --campaign runs/campaign-v0
python -m tree_ai_scientist verify --campaign runs/campaign-v0
```

Serving/ops helpers live in [`ops/`](ops/) (paths redacted in the example config). Model weights are **not** shipped.

## Layout

```
tree_ai_scientist/   # package
ops/                 # setup/serve/validate helpers
tests/
results/             # compact campaign metrics
releases_meta/       # small validation receipts
docs/
reference_research_papers/
```

## Limitations

- Requires chemistry oracle + pinned LLM serving; not a laptop demo.
- Seed molecule and oracle interface are operator-chosen; the model does not see the scoring formula.
- Raw multi-GB run ledgers excluded from git; reproduce by re-running campaigns.
- Dashboard excluded from this public slice.

## Reference papers

[`reference_research_papers/`](reference_research_papers/)

## License

MIT for this packaging. Upstream model / GuacaMol / tool licenses still apply.
