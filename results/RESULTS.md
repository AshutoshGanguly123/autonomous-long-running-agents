# Current results (compact)

Source: GuacaMol **Amlodipine MPO** campaign archive (`amlodipine_mpo_20261025_summary.json`).

## Numbers

| Metric | Value |
|--------|------:|
| Task | GuacaMol Amlodipine MPO |
| Committed paper nodes | 49 |
| Immutable Git papers | 48 |
| Best **single** measured score | **0.9045** |
| Model | Qwen3.8-27B-FP8 |

## Caveats (intentional)

1. **Not the official GuacaMol score.** GuacaMol averages top-1 / top-10 / top-100. We only logged the campaign’s single best molecule.
2. **Oracle call count** is not reported in this public summary.
3. Seed SMILES are operator-configured at `init` time (required flag/config). Do not assume a particular seed from this README.
4. Full SQLite / Git object stores remain on HPC.

## Inventory

`campaign_inventory.json` lists campaign directory names from the HPC workspace.
