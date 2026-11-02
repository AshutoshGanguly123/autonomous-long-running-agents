# Distal piperazine N-alkylation refuted for high-scoring pyridine diester scaffold

- Node: N2dac8bfd1abde760
- Research parent: N0c05b43f5289a00a
- Expansion: Xa8bbe7f04df1b3e3 (sibling 0)
- Hypothesis support (Qwen assessment): refuted
- Objective outcome (backend): decreased
- Parent reference: Cec74c6f32634804f `CCOC(=O)C1=C(COCCN2CCNCC2)NC(C)=C(C(=O)OC)C1c1ccccc1Cl` score 0.857143
- Plan hash: e7c6731a7f11460f55b2f4f0884065c24fe24ae666cb8a421386028055ad498e

## Search gist
We tested whether alkylating the distal piperazine nitrogen of a high-scoring diester pyridine scaffold would beat the parent score. Two frozen single-cell strategies replaced the distal secondary amine with methyl or ethyl, leaving the diester, methyl, chlorophenyl, and ethoxy linker unchanged. Both analogs scored below the parent: the best analog reached 0.85 while the reference was 0.86. The hypothesis was therefore refuted. The result suggests the unmodified distal piperazine NH is at least as favorable as these N-alkyl changes, but the black-box objective prevents assigning the loss to hydrogen-bond donor character, basicity, lipophilicity, or sterics. Future work should preserve that NH and probe non-alkyl heteroatom or linker modifications. These findings support a more constrained follow-up.

## 1. Introduction and hypothesis
This experiment tests a constrained follow-up to the parent observation that installing a piperazinyl side chain on the pyridine diester scaffold raised the black-box score from a lower precursor to the current campaign incumbent. The parent record could not separate whether the gain came from the piperazine ring, added basic nitrogen, lipophilicity, linker geometry, or hydrogen-bond donor capacity. A prior terminal-amine N-methyl edit was not beneficial, so this hypothesis deliberately changed a different nitrogen: the distal piperazine NH. The claim was that replacing that secondary amine with N-methyl or N-ethyl, while preserving the ethyl ester groups, methyl substituent, 4-chlorophenyl group, and ethoxy linker, would produce at least one molecule above the parent score. The challenging outcome would be that both N-alkyl analogs fail to improve, indicating that the unmodified NH is already near-optimal or that alkylation imposes a net penalty. This experiment is important because the distal piperazine nitrogen is a plausible site for tuning basicity and hydrogen-bonding without disturbing the core diester pyridine scaffold.

## 2. Methods
Parent node N0c05b43f5289a00a supplied the base molecule M1, canonical SMILES CCOC(=O)C1=C(COCCN2CCNCC2)NC(C)=C(C(=O)OC)C1c1ccccc1Cl, with known evaluation Cec74c6f32634804f and score 0.8571428571428572. The frozen matrix contained two single-candidate cells, one per strategy, under expansion Xa8bbe7f04df1b3e3 and plan hash e7c6731a7f11460f55b2f4f0884065c24fe24ae666cb8a421386028055ad498e. Strategy S1 methylated the distal piperazine nitrogen to form the 4-methylpiperazine analog. Strategy S2 ethylated the same nitrogen to form the 4-ethylpiperazine analog. The intended comparison was local: each cell changed only the distal piperazine N-substituent relative to the base. No cache was used and no invalid cells were reported. The matrix was evaluated against the same parent reference score, so deltas directly compare each candidate with the incumbent base.

## 3. Results
Cell M1|S1, receipt C4d3b2053276a93ad, candidate SMILES CCOC(=O)C1=C(COCCN2CCN(C)CC2)NC(C)=C(C(=O)OC)C1c1ccccc1Cl, status scored, score 0.848528137423857, delta versus base -0.008614719719000186. Cell M1|S2, receipt C693f7c5c084a04ce, candidate SMILES CCOC(=O)C1=C(COCCN2CCN(CC)CC2)NC(C)=C(C(=O)OC)C1c1ccccc1Cl, status scored, score 0.8360796171499412, delta versus base -0.02106323999291604. Both cells were completed. The best score in the matrix was 0.848528137423857 from the N-methyl analog, which remained below the reference score 0.8571428571428572. The mean score was 0.8423038772868991. The objective outcome was decreased, and no new campaign record was produced.

## 4. Observation and learnings
Both analogs were lower than the base, refuting the claim that at least one N-alkyl distal piperazine analog would exceed the parent. The N-methyl analog lost less score than the N-ethyl analog, which is consistent with a size or lipophilicity penalty increasing from methyl to ethyl, but this interpretation is not proven because the black-box score is a single composite readout. The result supports the learning that the unmodified distal piperazine NH is at least as favorable as these two alkyl substitutions in this scaffold. The observation also suggests that the parent side chain may be sensitive to changes at the distal nitrogen, even when the edit is chemically small. It does not show that the piperazine ring itself is unnecessary, because the ring was retained in both candidates.

## 5. Limitations
Only two scored cells were measured, with no replicates, no negative control, and no mechanistic assays. The edit simultaneously changes hydrogen-bond donor count, basicity, steric bulk, lipophilicity, and possibly conformation. Because the objective function is unknown, the score decrease cannot be causally assigned to any one property. The comparison is also local: it tests only methyl and ethyl at the distal piperazine nitrogen and does not establish whether all N-alkyl groups are unfavorable. The parent reference was carried from a prior evaluation, so the current matrix did not remeasure the base under the same run. This is acceptable for a frozen matrix but limits the ability to separate run-to-run variation from true molecular effects.

## 6. Conclusion and future work
The distal piperazine NH should be preserved in future variants of this scaffold if the goal is to maintain the current high score. Plausible next hypotheses include testing non-alkyl modifications at the distal nitrogen, replacing the distal nitrogen with a non-basic heteroatom, or changing the ethylene linker length to probe geometry and basicity separately. Another possible direction is to test whether the proximal piperazine nitrogen or the ethylene linker contributes more to the score than the distal NH. No new test is performed in this paper.

## 7. Evidence references
Source node N2dac8bfd1abde760; parent N0c05b43f5289a00a; citation Na836a77851078745; reference evaluation Cec74c6f32634804f; observation artifacts A36caaa5f3445bf98 and A940bde29476807f4; receipts C4d3b2053276a93ad and C693f7c5c084a04ce.

## Verified matrix (backend)
| cell | base (known score) | strategy | candidate (canonical) | status | score | receipt | cache source |
|---|---|---|---|---|---|---|---|
| M1|S1 | M1 (0.857143) | S1 | `CCOC(=O)C1=C(COCCN2CCN(C)CC2)NC(C)=C(C(=O)OC)C1c1ccccc1Cl` | scored | 0.848528 | C4d3b2053276a93ad |  |
| M1|S2 | M1 (0.857143) | S2 | `CCOC(=O)C1=C(COCCN2CCN(CC)CC2)NC(C)=C(C(=O)OC)C1c1ccccc1Cl` | scored | 0.836080 | C693f7c5c084a04ce |  |

## Backend statistics
- best_score: 0.848528
- cached: 0
- cells_completed: 2
- cells_planned: 2
- delta_vs_parent_reference: -0.008615
- incumbent_at_freeze: 0.857143
- invalid: 0
- mean_score: 0.842304
- new_campaign_record: False
- objective_outcome: decreased
- reference_score: 0.857143
- scored: 2

## Appendix A: frozen hypothesis and reference
```json
{"citations": ["N0c05b43f5289a00a", "Na836a77851078745"], "hypothesis": {"challenging_observation": "Both N-methyl and N-ethyl distal piperazine analogs score at or below 0.8571428571428572, indicating that the current piperazine NH, basicity, or lipophilicity is already near-optimal or that additional alkylation is penalized.", "claim": "Replacing the secondary piperazine NH in CCOC(=O)C1=C(COCCN2CCNCC2)NC(C)=C(C(=O)OC)C1c1ccccc1Cl with N-methyl or N-ethyl, while keeping the pyridine diester, methyl, 4-chlorophenyl, and ethoxy linker unchanged, produces at least one molecule with a black-box score greater than 0.8571428571428572.", "prediction": "At least one N-methyl- or N-ethyl-piperazine analog scores above 0.8571428571428572.", "rationale": "N0c05b43f5289a00a showed that installing a piperazinyl side chain raised the score from 0.367879 to 0.857143, but it explicitly could not separate piperazine ring effects from added basicity, lipophilicity, or geometry. The earlier N-methyl terminal amine failed, so this tests a different, more constrained edit: alkylating the distal piperazine nitrogen rather than the chain-terminal amine.", "title": "Distal piperazine N-alkylation improves the high-scoring side chain"}, "inherited_notes": [], "reference": {"id": "Cec74c6f32634804f", "score": 0.8571428571428572, "smiles": "CCOC(=O)C1=C(COCCN2CCNCC2)NC(C)=C(C(=O)OC)C1c1ccccc1Cl"}}
```

## Appendix B: frozen plan
```json
{"bases": [{"base_id": "M1", "canonical_smiles": "CCOC(=O)C1=C(COCCN2CCNCC2)NC(C)=C(C(=O)OC)C1c1ccccc1Cl", "input_smiles": "CCOC(=O)C1=C(COCCN2CCNCC2)NC(C)=C(C(=O)OC)C1c1ccccc1Cl", "known_evaluation_id": "Cec74c6f32634804f", "known_score": 0.8571428571428572}], "cells": [{"base_id": "M1", "candidate_smiles": "CCOC(=O)C1=C(COCCN2CCN(C)CC2)NC(C)=C(C(=O)OC)C1c1ccccc1Cl", "cell_id": "M1|S1", "strategy_id": "S1", "transformation_rationale": "Replace the distal piperazine NH in COCCN2CCNCC2 with N-methyl to form COCCN2CCN(C)CC2, leaving the pyridine diester, methyl, ethoxy linker, and 4-chlorophenyl unchanged."}, {"base_id": "M1", "candidate_smiles": "CCOC(=O)C1=C(COCCN2CCN(CC)CC2)NC(C)=C(C(=O)OC)C1c1ccccc1Cl", "cell_id": "M1|S2", "strategy_id": "S2", "transformation_rationale": "Replace the distal piperazine NH in COCCN2CCNCC2 with N-ethyl to form COCCN2CCN(CC)CC2, leaving the pyridine diester, methyl, ethoxy linker, and 4-chlorophenyl unchanged."}], "strategies": [{"control": false, "description": "Methylate the distal piperazine nitrogen (the secondary NH in the piperazine ring) to give the 4-methylpiperazine analog.", "expected_effect": "If the distal piperazine nitrogen's H-bond donor character is not required and added lipophilicity/alkyl substitution is favorable, score should exceed 0.8571428571428572; otherwise it may stay lower.", "strategy_id": "S1"}, {"control": false, "description": "Ethylate the distal piperazine nitrogen (the secondary NH in the piperazine ring) to give the 4-ethylpiperazine analog.", "expected_effect": "A larger N-alkyl group may further increase lipophilicity or introduce steric/basicity penalty; at least one of S1/S2 is predicted to beat 0.8571428571428572.", "strategy_id": "S2"}]}
```

## Appendix C: observation submission
```json
{"artifact": "A36caaa5f3445bf98", "evidence": ["C4d3b2053276a93ad", "C693f7c5c084a04ce", "Cec74c6f32634804f"], "findings": "Both distal piperazine N-alkyl analogs scored below the parent/base reference. S1 N-methyl scored 0.848528, delta -0.008615. S2 N-ethyl scored 0.836080, delta -0.021063. Neither exceeded 0.857143, so the hypothesis is refuted. The objective outcome is decreased, not improved. The lower N-ethyl score relative to N-methyl suggests added N-alkyl size/lipophilicity is not beneficial here, but the black-box score does not prove whether loss of H-bond donor character, altered basicity, conformation, or lipophilicity caused the decrease.", "learnings": "In this scaffold, the unmodified distal piperazine NH appears at least as favorable as N-methyl or N-ethyl substitution. Future edits should preserve that NH or test non-alkyl modifications that separately probe basicity, H-bond donor character, or linker geometry.", "limitations": "Only two single-score cells were tested; no replicates, controls, or mechanistic readouts. The objective function is unknown, so the decrease cannot be causally attributed to H-bond donor loss, basicity, lipophilicity, or steric effects.", "measured_claims": [{"evidence_id": "C4d3b2053276a93ad", "score": 0.848528137423857}, {"evidence_id": "C693f7c5c084a04ce", "score": 0.8360796171499412}, {"evidence_id": "Cec74c6f32634804f", "score": 0.8571428571428572}], "next_hypotheses": "Preserve the distal piperazine NH and test whether the benefit depends on basicity or H-bond donor character by replacing the distal nitrogen with a non-basic heteroatom or by changing the ethylene linker length.", "support": "refuted"}
```

## Appendix D: cell receipts
```jsonl
{"base_id": "M1", "canonical_smiles": "CCOC(=O)C1=C(COCCN2CCN(C)CC2)NC(C)=C(C(=O)OC)C1c1ccccc1Cl", "cell_id": "M1|S1", "id": "C4d3b2053276a93ad", "input_smiles": "CCOC(=O)C1=C(COCCN2CCN(C)CC2)NC(C)=C(C(=O)OC)C1c1ccccc1Cl", "node": "N2dac8bfd1abde760", "oracle_evaluation_id": "C4d3b2053276a93ad", "plan_hash": "e7c6731a7f11460f55b2f4f0884065c24fe24ae666cb8a421386028055ad498e", "score": 0.848528137423857, "source_evaluation_id": null, "status": "scored", "strategy_id": "S1", "validation_error": null}
{"base_id": "M1", "canonical_smiles": "CCOC(=O)C1=C(COCCN2CCN(CC)CC2)NC(C)=C(C(=O)OC)C1c1ccccc1Cl", "cell_id": "M1|S2", "id": "C693f7c5c084a04ce", "input_smiles": "CCOC(=O)C1=C(COCCN2CCN(CC)CC2)NC(C)=C(C(=O)OC)C1c1ccccc1Cl", "node": "N2dac8bfd1abde760", "oracle_evaluation_id": "C693f7c5c084a04ce", "plan_hash": "e7c6731a7f11460f55b2f4f0884065c24fe24ae666cb8a421386028055ad498e", "score": 0.8360796171499412, "source_evaluation_id": null, "status": "scored", "strategy_id": "S2", "validation_error": null}
```
