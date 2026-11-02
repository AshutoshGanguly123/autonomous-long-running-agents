# Current results (compact)

Source campaign archive: GuacaMol **Amlodipine MPO** (`results/amlodipine_mpo_20261025_summary.json`).

## Headline

| Metric | Value |
|--------|------:|
| Task | GuacaMol Amlodipine MPO |
| Committed paper nodes | **49** (plus frozen/reporting) |
| Immutable Git papers | **48** |
| Best measured score | **0.9045** |
| Model | Qwen3.8-27B-FP8 (HPC vLLM pins) |

Best molecules (scores) are listed in the JSON; the agent never receives the scoring formula—only measured oracle returns.

## Campaign inventory

`campaign_inventory.json` lists local campaign directory names from the HPC workspace (raw ledgers not published).

## Non-claims

- Not a leaderboard submission against official GuacaMol baselines in this artifact.
- Oracle access and seed SMILES are operator-configured; results are conditional on that setup.
- Full SQLite ledgers / Git object stores remain on HPC for size and IP hygiene.
