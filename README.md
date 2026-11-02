# autonomous-long-running-agents

**tree_ai_scientist** — a ReAct molecular research agent that writes **Git-backed experiment papers** under a hard context ceiling.

**Author:** Ashutosh Ganguly — AI researcher @ MBZUAI.

## What it does

Keeps a tree of experimental nodes (immutable Git commits + mutable SQLite ledger), expands strategies with workers, and optimizes a black-box chemistry objective under a **32,768-token** per-request ceiling.

## Campaign snapshot (GuacaMol Amlodipine MPO)

Archived run summary (`results/amlodipine_mpo_20261025_summary.json`):

| Metric | Value |
|--------|------:|
| Committed nodes / papers | **49** / **48** |
| Best single molecule score | **0.9045** |
| Model | Qwen3.8-27B-FP8 (local vLLM) |

### How to read that number

- GuacaMol’s **official** Amlodipine MPO score averages the top **1 / 10 / 100** molecules. Here we only report the **single best** measured score from the campaign ledger — not the official GuacaMol aggregate.
- Oracle-call budgets and totals are **not** published in this artifact (ledger size / hygiene). Treat 0.9045 as an internal campaign best, not a leaderboard claim.
- The scoring function uses a fixed target fingerprint (GuacaMol task definition). Campaign **seed SMILES must be set explicitly** (`--seed-smiles` or `seed_smiles` in config); there is no silent default to the target molecule.

Details: [`results/RESULTS.md`](results/RESULTS.md).

## Architecture

- One anchor molecule per node; workers write into the same node’s paper.
- Branching creates a new node from an evaluated molecule on a committed parent.
- Actions include search, read, compare, write, worker, call_oracle, commit_results, start_node, checkpoint.
- Design notes: [`DESIGN.md`](DESIGN.md).

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
pytest -q
cp config.hpc.example.json config.hpc.json
python -m tree_ai_scientist init --campaign runs/demo --config config.hpc.json --seed-smiles 'CC1(C)C2CCC1(C)C(=O)C2'
python -m tree_ai_scientist run --campaign runs/demo
```

## Limitations

- Needs a chemistry oracle and pinned LLM serving.
- Not a GuacaMol leaderboard submission.
- Raw multi-GB ledgers stay on HPC; only compact metrics are here.

## License

MIT for this packaging. Upstream model / GuacaMol licenses still apply.
