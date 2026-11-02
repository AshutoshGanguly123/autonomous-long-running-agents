import argparse
import fcntl
import hashlib
import json
from pathlib import Path
import signal
import sys
from .store import Store, dumps, identity


def main():
    parser = argparse.ArgumentParser(description='Git-backed molecular AI scientist; no dashboard')
    parser.add_argument('command', choices=['init','run','status','verify'])
    parser.add_argument('--campaign', required=True)
    parser.add_argument('--config')
    parser.add_argument('--seed-smiles')
    parser.add_argument('--steps', type=int, help='Optional operator/smoke-test boundary; absent means continuous')
    args = parser.parse_args()
    path = Path(args.campaign)
    if args.command == 'status':
        store = Store(path,readonly=True)
        print(dumps({'status':store.get('status'),'best':store.incumbent(),'tree':store.overview()}))
        return
    path.mkdir(parents=True,exist_ok=True)
    with (path/'process.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        store = Store(path)
        if args.command == 'verify':
            print(store.git('fsck','--full'))
            print(dumps({'sqlite':store.db.execute('PRAGMA integrity_check').fetchone()[0]}))
            return
        from .oracle import Oracle, REFERENCE
        oracle = Oracle(store)
        if args.command == 'init':
            if store.get('current_node'):
                raise ValueError('Campaign already initialized; use run to resume')
            config = json.loads(Path(args.config).read_text())
            root = identity('N','root')
            seed = args.seed_smiles or config.get('seed_smiles') or REFERENCE
            ev = oracle.evaluate('initialization',root,'initialization',[seed],initialization=True)[0]
            if ev['score'] is None:
                raise ValueError('Invalid initial molecule')
            store.create_node('root',None,ev['smiles'])
            store.put('current_node',root)
            store.put('config',config)
            store.put('brief','Given this molecule and its measured score, discover molecules with higher black-box scores. '
                      'Preserve a useful natural-language experimental history. No campaign evaluation quota.')
            print(dumps({'root':root,'anchor':ev['smiles'],'score':ev['score']}))
            return
        from .model import Model
        from .search import Search
        from .engine import Engine, Stopped
        config = store.get('config')
        if config is None:
            raise ValueError('Initialize campaign first')
        if args.config and json.loads(Path(args.config).read_text()) != config:
            raise ValueError('Cannot change scientific configuration during resume')
        files = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).parent.glob('*.py')}
        old = store.get('source_identity')
        if old and old != files:
            raise ValueError('Source changed since first run; use a fresh campaign')
        store.put('source_identity',files)
        model = Model(store,config)
        engine = Engine(store,model,oracle,Search(store,config['embedding_model']))
        for sig in (signal.SIGTERM,signal.SIGINT):
            signal.signal(sig, lambda *_:setattr(engine,'stop',True))
        session = engine.session('main',store.get('current_node'))
        try:
            engine.run(session,args.steps)
        except Stopped as exc:
            print(dumps({'stopped':str(exc)}),flush=True)
        except Exception as exc:
            store.put('failure',{'type':type(exc).__name__,'message':str(exc)})
            raise


if __name__ == '__main__':
    main()
