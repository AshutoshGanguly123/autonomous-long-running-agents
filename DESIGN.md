# tree_ai_scientist v0

## Scientific contract

Improve a hidden GuacaMol molecular score using the existing HPC Qwen3.8-27B deployment. The agent sees SMILES, oracle scores, its tools, and its research memory; it is not told the benchmark name, target name, scoring formula, or desired ring count. There is no campaign evaluation, iteration, draft-count, worker-count, or tree-depth quota. Every model request, including dedicated readers and workers, fits a 32,768-token total context including generation. Optional bounded CLI execution exists only for smoke tests and resumable operator control.

One node has one anchor molecule and its measured score. It contains k agent-chosen strategies, all candidate evaluations, reading notes, worker reports, and one natural-language paper. Strategies are not tree branches. A new node is created when Qwen selects a previously evaluated molecule from a committed parent's experiments as its next anchor. Selecting different products from the same parent creates siblings. The root begins as the initial scored molecule and a mutable research brief; it becomes its first committed paper only after actual experiments. Initialization alone is not a completed experiment.

## Lifecycle and agency

The current node is a mutable, durable workspace. Qwen runs an open-ended ReAct loop with explicit JSON tool actions and concise decision rationales. It may search, read sections, compare nodes, write/update its workspace, deep-read a paper, run a strategy worker, evaluate candidates, commit a paper, select a new child, or inspect another historical state. It is not required to follow a fixed search/plan/execute schedule. Repeated context-bounded sessions operate on the same persistent workspace.

A deep-read tool runs a dedicated fresh Qwen call on a committed paper (or a selected section if too large). It must return source-linked observations, limitations, hypotheses/ideas, and applicability notes. Its complete output is saved under the current working node and a bounded result is returned to the main loop. More detail remains readable by reference. A worker is a fresh Qwen ReAct session, not a hard-coded molecular mutation operator. It starts from the current anchor, an agent-written strategy, and selected working-node notes; it can investigate, use the oracle, revise its approach, and finish with a worker report. Worker observations and reports belong to the same node and strategy. v0 executes nested workers sequentially against the same Qwen endpoint. Dispatching a worker does not create a tree node.

## Agent action space

- search(query): BM25 + dense embedding retrieval, fused with reciprocal rank fusion; bounded excerpts and IDs.
- read(reference, offset, limit): bounded reads of immutable node papers, current workspace, reader notes, worker reports, and evaluation records.
- compare(node_ids): factual anchor/outcome/strategy summaries, without LLM-assigned quality scores.
- write(section, text): durable additions or replacements to current mutable draft sections. This is scientific memory, not a mandatory phase gate.
- deep_read(node_id, question, offset): dedicated evidence/idea extraction, persisted into current draft.
- worker(strategy, context): dedicated ReAct experimentation, with its own persisted continuation and results.
- call_oracle(smiles, strategy): deterministic parsing, canonicalization, duplicate caching, scoring, and durable evaluation receipts.
- commit_results(title, summary, paper): freeze current node, including its exact evaluated results and artifact references. Natural-language output has a concise searchable abstract plus expanded scientific sections. Negative results are retained. Numeric metrics are backend-calculated.
- start_node(parent_id, evaluation_id): select an evaluated product of a committed parent to anchor a new working child.
- inspect_tree(offset, limit): paged factual tree overview and current workspace pointer.

Parent/child relations describe molecular experiment lineage. Citations describe additional earlier evidence. All citations must already exist at publication time. The same molecule may be revisited with new strategies; exact duplicate oracle calls are cached, not treated as new experiments. No semantic novelty filter is imposed.

## Persistence and actual Git

Each campaign owns a separate Git object database. Finalized papers and node manifests are committed with git commit-tree, one Git parent equal to their experimental parent, and a durable refs/nodes/<id> reference. This preserves literal branching independently of the checkout's HEAD and avoids shared working-tree races. Each commit tree contains the full node bundle (paper, manifest, draft, reader notes, worker traces and evaluated results), not a cumulative copy of unrelated sibling files. Source code is versioned separately from campaign memory.

SQLite holds the operational ledger: node/draft state, strategy actions, canonical molecules, evaluations, model-call usage and responses, resume cursors, and search metadata. Completed Git bundles are immutable; mutable operational state is not rewritten into historical commits. Oracle receipts are persisted before returning results. Commit recovery reconciles durable node refs and manifests after interruption. One process holds an exclusive campaign lock. A global incumbent is computed from all successful evaluations, independently of the selected node or failed experiments.

## Context management

Count each complete rendered chat template with the deployed model's tokenizer, including tool descriptions and protocol messages. Reserve output capacity before every request; set max_tokens within the remainder. Count thinking tokens as generated tokens. Save all calls and outputs. As a session fills, request a compact continuation note while space remains, persist it, and open a fresh call with the node state, selected recent observations, and reference IDs. Never silently truncate the persistent scientific record. Tool returns are bounded views of durable artifacts. Dedicated readers use bounded paper sections when the full text cannot fit. Reader/worker/main calls all share the same enforced ceiling.

Context overflow causes context reconstruction, not a forced experiment commit. There is no campaign token allowance or fixed number of reads. Draft visibility is token-budgeted; the persistent queue/workspace can be larger than the model window. Malformed tool responses are logged and receive a normal corrective observation, with no scientifically invented repair.

## Minimal orchestration

The orchestrator owns persistence, token admission, JSON protocol validation, molecular validity/deduplication, oracle execution, evidence IDs, process locking, and checkpoint/resume. Qwen owns hypotheses, strategy counts, reading decisions, worker dispatch, completion, parent/product choice, and branch growth. Improvement is the objective, not a gate that deletes failures. No dashboard, training, numerical optimizer, forced sampler, or unrelated experiment modification is included.

## Validation and deployment

Reuse verified serving/tokenizer/embedding resources and molecule initialization where available. Verify the local oracle against the installed GuacaMol implementation. Tests cover real branch parents, immutable bundles, oracle caching and receipts, token overflow/rollover, dedicated reader writeback, same-node worker writeback, malformed actions, and resume without rescoring or duplicating committed work. Run an isolated scripted end-to-end smoke test, then a real Qwen smoke test before claiming the HPC campaign works. Record the model revision, source hash, runtime versions, endpoint, node, and launch identity. Preserve all earlier projects and processes.
