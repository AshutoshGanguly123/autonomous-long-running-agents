import json
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

from tree_ai_scientist.store import Store, identity
from tree_ai_scientist.oracle import Oracle, REFERENCE, canonical
from tree_ai_scientist.model import Model, ContextLimit
from tree_ai_scientist.engine import Engine
from tree_ai_scientist.search import Search


class Tokenizer:
    def encode(self,text,**kwargs): return list(text.encode())
    def decode(self,ids,**kwargs): return bytes(ids).decode(errors='ignore')
    def apply_chat_template(self,messages,**kwargs):
        return self.encode(json.dumps(messages))+[0]*12


class Scripted(Model):
    def __init__(self,store,replies):
        super().__init__(store,{'context_tokens':32768,'max_output_tokens':2048,'model':'test',
            'base_url':'http://invalid','thinking':True},Tokenizer())
        self.replies=list(replies)
        self.requests=[]
    def call(self,key,node,messages,max_tokens=None):
        assert self.count(messages)+(max_tokens or self.output)<=self.limit
        cached=self.store.get('fake:'+key)
        if cached: return cached
        self.requests.append(messages)
        text=self.replies.pop(0)
        reply={'text':text if isinstance(text,str) else json.dumps(text),'finish_reason':'stop','usage':{}}
        self.store.put('fake:'+key,reply)
        return reply


@pytest.fixture
def research(tmp_path):
    store=Store(tmp_path/'campaign')
    oracle=Oracle(store)
    node=identity('N','root')
    ev=oracle.evaluate('init',node,'initialization',[REFERENCE],True)[0]
    store.create_node('root',None,ev['smiles'])
    store.put('current_node',node)
    return store,oracle,node


def finish(store,oracle,node,key='test'):
    ev=oracle.evaluate(key,node,'S1',['CCO','CCN'])
    store.commit(node,'An experiment','Short outcome summary','## Methods\nS1\n## Results\nMeasured candidates.')
    return ev


def test_real_oracle_canonical_cache_invalid_and_replay(research):
    store,oracle,node=research
    ev=oracle.evaluate('a',node,'S1',['CCO','OCC','invalid'])
    assert ev[0]['score']==ev[1]['score']
    assert ev[1]['cached'] and ev[2]['score'] is None
    assert oracle.evaluate('a',node,'S1',['CCO','OCC','invalid'])==ev
    assert len(store.evaluations(node))==4


def test_git_branching_uses_molecules_not_strategies(research):
    store,oracle,node=research
    ev=finish(store,oracle,node)
    a=store.create_node('child-a',node,ev[0]['smiles'])
    b=store.create_node('child-b',node,ev[1]['smiles'])
    finish(store,oracle,a['id'],'a')
    finish(store,oracle,b['id'],'b')
    for child in [a,b]:
        n=store.node(child['id'])
        assert store.git('rev-parse',n['sha']+'^')==store.node(node)['sha']
    assert store.db.execute('SELECT COUNT(*) FROM nodes').fetchone()[0]==3
    assert store.git('show',store.node(a['id'])['sha']+':paper.md').startswith('# An experiment')


def test_committed_node_is_immutable(research):
    store,oracle,node=research
    finish(store,oracle,node)
    with pytest.raises(ValueError,match='immutable'):
        store.save_node(node,{'sections':{}})


def test_commit_requires_measured_experiment(research):
    store,_,node=research
    with pytest.raises(ValueError,match='oracle-backed'):
        store.commit(node,'title','summary','paper')


def test_git_ref_reconciles_interrupted_ledger_update(research):
    store,oracle,node=research
    finish(store,oracle,node)
    sha=store.node(node)['sha']
    with store.db:
        store.db.execute("UPDATE nodes SET status='draft',sha=NULL WHERE id=?",(node,))
    store.reconcile()
    assert store.node(node)['sha']==sha
    assert store.node(node)['status']=='committed'


def test_creation_is_idempotent(research):
    store,oracle,node=research
    ev=finish(store,oracle,node)
    a=store.create_node('stable-action',node,ev[0]['smiles'])
    b=store.create_node('stable-action',node,ev[0]['smiles'])
    assert a==b


def test_worker_uses_same_node_and_returns_scored_report(research):
    store,oracle,node=research
    replies=[{'action':'call_oracle','args':{'smiles':['CCO'],'strategy':'ignored'}},
             {'action':'finish_worker','args':{'report':'Measured one candidate; retain uncertainty.'}}]
    engine=Engine(store,Scripted(store,replies),oracle,None)
    session=engine.session('main',node)
    result=engine.dispatch(session,'dispatch1','worker',{'strategy':'S2: edit','context':'Test directly.'})
    assert result['strategy']=='S2: edit'
    assert result['evaluations'][0]['node']==node
    assert store.db.execute('SELECT COUNT(*) FROM nodes').fetchone()[0]==1
    assert store.db.execute("SELECT COUNT(*) FROM artifacts WHERE node=? AND kind='worker_report'",(node,)).fetchone()[0]==1
    # Replaying outer dispatch resumes the completed worker, rather than rescoring.
    again=engine.dispatch(session,'dispatch1','worker',{'strategy':'S2: edit'})
    assert again==result
    assert len(store.evaluations(node))==2


def test_reader_writes_lessons_to_current_node(research):
    store,oracle,node=research
    ev=finish(store,oracle,node)
    child=store.create_node('child',node,ev[0]['smiles'])
    model=Scripted(store,['Observations: measured. Idea: test a related edit; uncertain applicability.'])
    engine=Engine(store,model,oracle,None)
    result=engine.dispatch(engine.session('main',child['id']),'read1','deep_read',{'node_id':node,'question':'What transfers?'})
    assert 'Idea:' in store.read(result['note_reference'])
    assert store.node(child['id'])['data']['citations']==[node]
    assert 'possible hypotheses/experiments' in model.requests[0][0]['content']


def test_action_json_may_follow_deliberation(research):
    store,oracle,node=research
    text=('The next measurement should be a small local edit.\n'
          '{"reason":"measure one candidate","action":"call_oracle","args":{"smiles":["CCO"],"strategy":"S1"}}')
    engine=Engine(store,Scripted(store,[text]),oracle,None)
    result=engine.step(engine.session('main',node))
    assert result['result']['evaluations'][0]['score'] is not None


def test_unknown_action_recovers_with_observation(research):
    store,oracle,node=research
    model=Scripted(store,[{'action':'invented_tool','args':{}}, {'action':'call_oracle','args':{'smiles':['CCO'],'strategy':'S1'}}])
    engine=Engine(store,model,oracle,None)
    session=engine.session('main',node)
    assert 'Unknown action' in engine.step(session)['error']
    assert engine.step(session)['result']['evaluations'][0]['score'] is not None


def test_rollover_preserves_workspace_and_transcript(research):
    store,oracle,node=research
    model=Scripted(store,['Continue S1, read the recorded evidence before the next test.',
                          {'action':'write','args':{'section':'methods','text':'Fresh context, same experiment.'}}])
    engine=Engine(store,model,oracle,None)
    session=engine.session('main',node)
    session['messages']=[{'role':'user','content':'x'*29000}]
    engine.step(session)
    assert session['rollovers']==1
    assert store.node(node)['data']['sections']['methods']=='Fresh context, same experiment.'
    assert store.db.execute("SELECT COUNT(*) FROM artifacts WHERE kind='archived_session'").fetchone()[0]==1


def test_model_rejects_overflow_before_http(research):
    store,_,node=research
    model=Model(store,{'model':'test','base_url':'http://invalid','max_output_tokens':1024},Tokenizer())
    with patch('urllib.request.urlopen') as http:
        with pytest.raises(ContextLimit):
            model.call('too-big',node,[{'role':'user','content':'x'*40000}])
        http.assert_not_called()


def test_model_records_usage_and_caches_response(research):
    store,_,node=research
    model=Model(store,{'model':'test','base_url':'http://invalid','max_output_tokens':1024},Tokenizer())
    messages=[{'role':'user','content':'hello'}]
    result={'choices':[{'message':{'content':'{}'},'finish_reason':'stop'}],
            'usage':{'prompt_tokens':model.count(messages),'completion_tokens':2,'total_tokens':model.count(messages)+2}}
    import io
    with patch('urllib.request.urlopen',return_value=io.BytesIO(json.dumps(result).encode())) as http:
        one=model.call('stable',node,messages)
        assert model.call('stable',node,messages)==one
        assert http.call_count==1


def test_server_tokenizer_mismatch_is_not_silently_accepted(research):
    store,_,node=research
    model=Model(store,{'model':'test','base_url':'http://invalid'},Tokenizer())
    result={'choices':[{'message':{'content':'{}'},'finish_reason':'stop'}],
            'usage':{'prompt_tokens':999,'total_tokens':1000}}
    import io
    with patch('urllib.request.urlopen',return_value=io.BytesIO(json.dumps(result).encode())):
        with pytest.raises(RuntimeError,match='mismatch'):
            model.call('mismatch',node,[{'role':'user','content':'hi'}])


def test_hybrid_retrieval_caches_embeddings(research):
    store,oracle,node=research
    finish(store,oracle,node)
    search=Search(store,'test-embedding')
    calls=[]
    def encode(texts):
        calls.append(texts)
        return np.asarray([[1.,0.] for _ in texts])
    search.encode=encode
    assert search.search('candidate')['matches'][0]['node']==node
    assert search.search('candidate')['matches'][0]['node']==node
    assert len(calls)==3 # document once; query twice


def test_full_scripted_react_commit_and_branch(research):
    store,oracle,node=research
    ev=oracle.evaluate('preflight',node,'S1',['CCO'])[0]
    actions=[{'action':'write','args':{'section':'hypotheses','text':'S1 is a falsifiable local edit.'}},
             {'action':'call_oracle','args':{'strategy':'S1','smiles':['CCO','CCN']}},
             {'action':'commit_results','args':{'title':'S1 test','summary':'Two measured edits.','paper':'## Methods\nS1\n## Results\nSee verified ledger.'}},
             {'action':'start_node','args':{'parent_id':node,'evaluation_id':ev['id']}}]
    engine=Engine(store,Scripted(store,actions),oracle,None)
    session=engine.session('main',node)
    engine.run(session,4)
    restored=Store(store.path)
    assert restored.node(node)['status']=='committed'
    assert restored.node(session['node'])['parent']==node
    assert restored.get('session:main')['turn']==4
    assert restored.git('fsck','--full')==''


def test_draft_write_is_atomic_and_idempotent(research):
    store,_,node=research
    store.write_section(node,'write-a','ideas','A')
    store.write_section(node,'write-a','ideas','A')
    store.write_section(node,'write-b','ideas','B')
    assert store.node(node)['data']['sections']['ideas']=='A\nB'


def test_paper_contains_reader_worker_and_draft_records(research):
    store,oracle,node=research
    store.artifact('reader',node,'reading_note','Source-supported lesson')
    store.artifact('worker',node,'worker_report','Strategy B negative outcome')
    store.write_section(node,'draft','methods','Shared experimental method')
    finish(store,oracle,node)
    paper=store.read(node)
    assert all(s in paper for s in ['Source-supported lesson','Strategy B negative outcome',
                                   'Shared experimental method','Verified evaluation ledger'])


def test_empty_archive_search_does_not_load_embedding_model(research):
    store,_,_=research
    search=Search(store,'does-not-exist')
    assert search.search('anything')['matches']==[]
    assert search._model is None


def test_readonly_status_never_reconciles_or_writes(research):
    store,oracle,node=research
    finish(store,oracle,node)
    reader=Store(store.path,readonly=True)
    assert reader.overview()['total']==1
    with pytest.raises(Exception,match='readonly'):
        reader.put('forbidden',True)


def test_optional_installed_guacamol_parity(research,monkeypatch):
    import importlib.util
    if importlib.util.find_spec('guacamol') is None:
        pytest.skip('GuacaMol reference package is optional locally; required on HPC')
    import scipy
    # Legacy GuacaMol imports scipy.histogram for unrelated distribution metrics.
    # Its historical alias is numpy.histogram. This import-only shim does not
    # alter any objective or fingerprint implementation under comparison.
    if not hasattr(scipy,'histogram'):
        monkeypatch.setattr(scipy,'histogram',np.histogram,raising=False)
    # Load the unmodified released function definition without importing all
    # unrelated distribution benchmarks (which require the obsolete FCD stack).
    import ast
    import guacamol
    from guacamol.common_scoring_functions import TanimotoScoringFunction, RdkitScoringFunction
    from guacamol.scoring_function import GeometricMeanScoringFunction
    from guacamol.score_modifier import GaussianModifier
    from guacamol.utils.descriptors import num_rings
    from guacamol.goal_directed_benchmark import GoalDirectedBenchmark
    from guacamol.goal_directed_score_contributions import uniform_specification
    path=Path(guacamol.__file__).parent/'standard_benchmarks.py'
    tree=ast.parse(path.read_text())
    definition=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='amlodipine_rings')
    namespace={k:v for k,v in locals().items()}
    exec(compile(ast.Module(body=[definition],type_ignores=[]),str(path),'exec'),namespace)
    store,oracle,node=research
    benchmark=namespace['amlodipine_rings']()
    for smiles in [REFERENCE,'CCO','c1ccccc1','C1CCCCC1C2CCCCC2C3CCCCC3','CCO.CC']:
        assert oracle.score(smiles)==pytest.approx(benchmark.objective.score(smiles),abs=1e-12)
