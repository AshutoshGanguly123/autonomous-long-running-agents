"""Isolated real-Qwen reader/worker/search/Git integration test, not a benchmark run."""
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tree_ai_scientist.store import Store, identity, dumps
from tree_ai_scientist.oracle import Oracle
from tree_ai_scientist.model import Model
from tree_ai_scientist.search import Search
from tree_ai_scientist.engine import Engine

project=Path(__file__).resolve().parents[1]
store=Store(project/'runs/live-integration')
oracle=Oracle(store)
root=identity('N','integration-root')
seed=oracle.evaluate('integration-init',root,'initialization',['CC1(C)C2CCC1(C)C(=O)C2'],True)[0]
store.create_node('integration-root',None,seed['smiles'])
checks=oracle.evaluate('integration-checks',root,'infrastructure reference checks',['CC1(C)C2CCC1(C)C(=O)C2','CCO'])
store.commit(root,'Infrastructure smoke: measured reference checks',
             'Infrastructure-only record of two oracle evaluations; no chemical discovery is claimed.',
             '## Methods\nDirectly score two valid inputs.\n## Results\nSee verified ledger. '
             '\n## Limitations\nThis is infrastructure validation, not a scientific optimization result.')
child=store.create_node('integration-child',root,checks[0]['smiles'])
config=json.loads((project/'config.hpc.json').read_text())
model=Model(store,config)
search=Search(store,config['embedding_model'])
engine=Engine(store,model,oracle,search)
session=engine.session('integration-controller',child['id'])
reader=engine.dispatch(session,'integration-reader','deep_read',{'node_id':root,
    'question':'What does this infrastructure-only record actually establish? Suggest a cautious next molecular experiment.'})
print(dumps({'deep_reader':'passed','artifact':reader['note_reference']}),flush=True)
worker=engine.dispatch(session,'integration-worker','worker',{
    'strategy':'Live integration check: formulate and test a local structural edit of the anchor. '
               'Inspect actual oracle feedback and return an honest report after a coherent small test.',
    'context':'This is an isolated infrastructure smoke test. Preserve your hypothesis and observations. '
              'There is no evidence for hidden scoring semantics. Reader note: '+reader['note_reference']})
print(dumps({'worker':'passed','report':worker['report_reference']}),flush=True)
retrieved=search.search('measured oracle reference evaluation')
assert retrieved['matches'][0]['node']==root
result=store.commit(child['id'],'Real Qwen integration experiment',
    'Dedicated reader and ReAct worker exercised against the real Qwen endpoint and molecular oracle.',
    '## Methods\nDedicated reader, strategy worker, hybrid search.\n## Results\n'+worker['report']+
    '\n## Limitations\nInfrastructure smoke test; no benchmark performance claim.')
assert store.git('rev-parse',result['sha']+'^')==store.node(root)['sha']
totals=[]
for row in store.db.execute("SELECT text FROM artifacts WHERE kind='model_response'"):
    totals.append(json.loads(row[0])['usage']['total_tokens'])
receipt={'status':'passed','real_qwen_calls':len(totals),'maximum_total_tokens':max(totals),
         'node':child['id'],'commit':result['sha'],'worker_evaluations':worker['evaluated_count'],
         'hybrid_retrieval':retrieved['retrieval'],'best':store.incumbent()}
store.put('live_validation',receipt)
(project/'ops/live-validation.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(dumps(receipt),flush=True)
