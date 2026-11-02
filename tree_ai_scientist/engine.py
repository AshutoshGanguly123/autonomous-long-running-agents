from __future__ import annotations

import json
import time
from .prompts import CONTRACT, READER, WORKER
from .store import dumps, identity


class Stopped(Exception):
    pass


def action_object(text):
    """Accept the required JSON action, including deliberation the contract allows before it."""
    raw = text.strip()
    try:
        action = json.loads(raw)
    except json.JSONDecodeError:
        start, end = raw.find('{'), raw.rfind('}')
        if start < 0 or end <= start:
            raise ValueError('Expected one JSON tool-action object')
        action = json.loads(raw[start:end + 1])
    if not isinstance(action, dict) or not isinstance(action.get('args', {}), dict) or 'action' not in action:
        raise ValueError('Expected one JSON tool-action object')
    return action


class Engine:
    def __init__(self, store, model, oracle, search):
        self.store, self.model, self.oracle, self.search = store, model, oracle, search
        self.stop = False

    def session(self, id, node, mode='main', strategy='', context=''):
        key = 'session:' + id
        session = self.store.get(key)
        if session is None:
            session = {'id': id, 'node': node, 'mode': mode, 'strategy': strategy,
                       'context': context, 'turn': 0, 'messages': [], 'carry': '', 'done': False, 'rollovers': 0}
            if mode == 'worker':
                session['assignment_reference'] = self.store.artifact('assignment:'+id,node,'worker_assignment',
                    dumps({'strategy':strategy,'context':context}))
            self.store.put(key, session)
        return session

    def state(self, session):
        node = self.store.node(session['node'])
        fields = node['data'].get('sections', {})
        artifacts = [dict(r) for r in self.store.db.execute(
            'SELECT id,kind,length(text) AS characters FROM artifacts WHERE node=? ORDER BY rowid DESC LIMIT 16',
            (node['id'],))]
        anchor_score = self.store.db.execute('SELECT score FROM molecules WHERE smiles=?', (node['anchor'],)).fetchone()[0]
        core = {'current_node':node['id'],'status':node['status'],'parent':node['parent'],
                'anchor':node['anchor'],'anchor_score':anchor_score,'global_best':self.store.incumbent(),
                'brief':self.store.get('brief','Improve the black-box score of the supplied molecule.'),
                'strategy':self.model.clip(session['strategy'],1000),
                'assignment_reference':session.get('assignment_reference')}
        total = self.store.db.execute('SELECT COUNT(*) FROM nodes').fetchone()[0]
        tree = self.store.overview(max(0,total-20),20)
        result = {
                  'section_views': {k: self.model.clip(v, 250) for k,v in fields.items()},
                  'recent_artifacts': artifacts, 'recent_evaluations': self.store.evaluations(node['id'])[-8:],
                  'tree_count': total, 'assigned_context': self.model.clip(session['context'],800),
                  'continuation': session['carry'],
                  'note': 'Bounded view. read(current_node) exposes the full workspace. inspect_tree is paginated.'}
        header = dumps(core)+'\nTREE PREVIEW (inspect_tree expands it):\n'+self.model.clip(dumps(tree),self.model.limit//16)
        room = max(128,self.model.limit//6-self.model.text_tokens(header)-128)
        return header+'\nWORKING RESEARCH:\n'+self.model.clip(dumps(result),room)

    def system(self, mode):
        return CONTRACT + ('\n' + WORKER if mode == 'worker' else '')

    def request(self, key, node, messages, max_tokens=None):
        prepared = self.store.get('prepared:' + key)
        if prepared is None:
            prepared = {'messages': messages, 'max_tokens': max_tokens}
            self.store.put('prepared:' + key, prepared)
        return self.model.call(key, node, prepared['messages'], prepared['max_tokens'])

    def rollover(self, session):
        key = f"{session['id']}:rollover:{session['rollovers']}"
        message = [{'role':'system', 'content': 'Write an evidence-linked continuation note for the same scientist. '
                    'Preserve hypotheses, strategies, measured outcomes with IDs, unfinished actions, and next options. '
                    'Do not invent results. Full transcript remains archived and readable by reference.'}]
        transcript = dumps({'previous_note':session['carry'], 'transcript':session['messages']})
        ref = self.store.artifact(key+':transcript', session['node'], 'archived_session', transcript)
        room = self.model.limit - min(self.model.output, self.model.limit//4) - self.model.count(message) - 256
        message.append({'role':'user', 'content': self.model.clip(transcript, room)})
        response = self.request(key, session['node'], message, min(self.model.output, self.model.limit//4))
        carry_ref = self.store.artifact(key+':note', session['node'], 'continuation', response['text'])
        session.update(carry=response['text']+f'\nFull transcript: {ref}; note: {carry_ref}', messages=[],
                       rollovers=session['rollovers']+1)
        self.store.put('session:'+session['id'], session)

    def step(self, session):
        if self.stop or (self.store.path/'STOP').exists():
            raise Stopped('Stopped at a durable action boundary')
        mode, node = session['mode'], session['node']
        head = [{'role':'system','content':self.system(mode)}, {'role':'user','content':self.state(session)}]
        messages = head + session['messages']
        available = self.model.limit - self.model.output - min(2048, self.model.limit//8)
        if self.model.count(messages) > available:
            self.rollover(session)
            head = [{'role':'system','content':self.system(mode)}, {'role':'user','content':self.state(session)}]
            messages = head
        key = f"{session['id']}:turn:{session['turn']}"
        response = self.request(key, node, messages)
        text = response['text']
        action_key = 'action:' + key
        cached = self.store.get(action_key)
        if cached is None:
            try:
                if response.get('finish_reason') == 'length':
                    raise ValueError('Generation was truncated. Shorten your response or checkpoint; no partial action executed.')
                action = action_object(text)
                if self.stop:
                    raise Stopped('Stopped after saving model response, before executing its action')
                result = self.dispatch(session, key, action['action'], action.get('args', {}))
                cached = {'action': action, 'result': result}
            except (ValueError, KeyError, TypeError) as exc:
                cached = {'error': str(exc), 'instruction':'Return one valid JSON action using the documented argument names. No result was invented.'}
            self.store.put(action_key, cached)
        observation_ref = self.store.artifact(key+':observation', node, 'observation', dumps(cached))
        observation = self.model.clip(dumps(cached), min(2048, self.model.limit//8))
        observation += '\nFull observation: ' + observation_ref
        session['messages'].extend([{'role':'assistant','content':text}, {'role':'user','content':observation}])
        if cached.get('action',{}).get('action') == 'start_node' and 'node' in cached.get('result',{}):
            session['node'] = cached['result']['node']
            session['carry'] = ''
            session['messages'] = []
        if cached.get('action',{}).get('action') == 'checkpoint' and not cached.get('error'):
            session['carry'] = cached['result']['note']
            session['messages'] = []
        if cached.get('action',{}).get('action') == 'finish_worker' and not cached.get('error'):
            session['done'] = True
            session['report'] = cached['result']
        session['turn'] += 1
        self.store.put('session:'+session['id'], session)
        status = {'time':time.time(), 'session':session['id'], 'mode':mode, 'node':session['node'],
                  'turn':session['turn'], 'last_action':cached.get('action',{}).get('action'),
                  'error':cached.get('error'), 'best':self.store.incumbent(), 'model_usage':response.get('usage')}
        self.store.put('status', status)
        print(dumps(status), flush=True)
        return cached

    def run(self, session, steps=None):
        count = 0
        while not session['done'] and (steps is None or count < steps):
            self.step(session)
            count += 1
        return session.get('report')

    def mutable(self, node):
        n = self.store.node(node)
        if n['status'] != 'draft':
            raise ValueError('This node is committed. Choose start_node before more experiments or edits.')
        return n

    def dispatch(self, session, key, action, args):
        node, mode = session['node'], session['mode']
        if mode == 'worker' and action in {'start_node','commit_results','worker'}:
            raise ValueError('Worker results belong to the current node; finish_worker returns them to the scientist')
        if action == 'inspect_tree':
            return {**self.store.overview(max(0,int(args.get('offset',0))), max(1,int(args.get('limit',20)))),
                    'current_node':node, 'global_best':self.store.incumbent()}
        if action == 'search':
            return self.search.search(args['query'], max(1,int(args.get('limit',10))))
        if action == 'read':
            ref = args['reference']
            text = self.store.read(ref)
            offset, limit = max(0,int(args.get('offset',0))), max(1,int(args.get('limit',12000)))
            budget = max(128,min(2048,self.model.limit//8)-512)
            ids = self.model.tokenizer.encode(text[offset:offset+limit],add_special_tokens=False)
            excerpt = self.model.tokenizer.decode(ids[:budget],skip_special_tokens=True)
            return {'reference':ref, 'offset':offset, 'total_characters':len(text),
                    'text':excerpt, 'next_offset':min(offset+len(excerpt),len(text))}
        if action == 'compare':
            return [{**self.store.node(i), 'evaluations':self.store.evaluations(i)} for i in args['node_ids']]
        if action == 'write':
            n = self.mutable(node)
            section, text = str(args['section']), str(args['text'])
            self.store.write_section(node,key,section,text,args.get('append',True))
            return {'node':node,'section':section,'saved':True}
        if action == 'call_oracle':
            self.mutable(node)
            strategy = session['strategy'] if mode == 'worker' else args['strategy']
            return {'evaluations':self.oracle.evaluate(key,node,strategy,args['smiles']), 'global_best':self.store.incumbent()}
        if action == 'deep_read':
            n = self.mutable(node)
            source = self.store.node(args['node_id'])
            if source['status'] != 'committed':
                raise ValueError('Deep reading uses committed experiment papers; read() inspects mutable drafts')
            if source['seq'] >= n['seq']:
                raise ValueError('Source must predate the current working node')
            paper = self.store.read(source['id'])
            offset = max(0,int(args.get('offset',0)))
            question = str(args['question'])
            head = [{'role':'system','content':READER}, {'role':'user','content':self.state(session)+'\nResearch question: '+question}]
            room = self.model.limit-self.model.output-self.model.count(head)-512
            excerpt = self.model.tokenizer.decode(self.model.tokenizer.encode(paper[offset:],add_special_tokens=False)[:max(1,room)],skip_special_tokens=True)
            messages = head+[{'role':'user','content':f"SOURCE {source['id']}, offset {offset}:\n"+excerpt}]
            answer = self.request(key+':reader',node,messages)
            ref = self.store.artifact(key+':reader-note',node,'reading_note',answer['text'])
            if source['id'] not in n['data']['citations']:
                n['data']['citations'].append(source['id'])
                self.store.save_node(node,n['data'])
            return {'note_reference':ref,'source':source['id'],'note':self.model.clip(answer['text'],1200),
                    'source_characters':len(paper),'offset':offset,'next_offset':offset+len(excerpt)}
        if action == 'worker':
            self.mutable(node)
            worker = self.session(identity('W',key),node,'worker',str(args['strategy']),str(args.get('context','')))
            return self.run(worker)
        if action == 'finish_worker':
            if mode != 'worker':
                raise ValueError('Only a worker can finish_worker')
            measured = [e for e in self.store.evaluations(node) if e['strategy']==session['strategy'] and e['score'] is not None]
            if not measured:
                raise ValueError('Run an oracle-backed experiment before finishing the worker report')
            ref = self.store.artifact(key+':report',node,'worker_report',str(args['report']))
            return {'report_reference':ref,'report':self.model.clip(str(args['report']),1000),
                    'strategy':session['strategy'],'evaluations':measured[-3:],
                    'evaluated_count':len(measured),'best':max(e['score'] for e in measured)}
        if action == 'checkpoint':
            ref = self.store.artifact(key+':checkpoint',node,'continuation',str(args['note']))
            return {'note':str(args['note']), 'reference':ref}
        if action == 'commit_results':
            return self.store.commit(node,str(args['title']),str(args['summary']),str(args['paper']))
        if action == 'start_node':
            if self.store.node(node)['status'] != 'committed':
                raise ValueError('Commit the current working node before selecting another anchor')
            parent = self.store.node(args['parent_id'])
            found = [e for e in self.store.evaluations(parent['id']) if e['id']==args['evaluation_id'] and e['score'] is not None]
            if not found:
                raise ValueError('Select an actual scored evaluation from the chosen parent')
            child = self.store.create_node(key,parent['id'],found[0]['smiles'])
            self.store.put('current_node',child['id'])
            return {'node':child['id'],'parent':parent['id'],'anchor':child['anchor']}
        raise ValueError(f'Unknown action {action}')
