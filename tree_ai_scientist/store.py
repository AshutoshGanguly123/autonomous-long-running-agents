from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import time


def dumps(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)


def identity(prefix, key):
    return prefix + hashlib.sha256(key.encode()).hexdigest()[:16]


class Store:
    def __init__(self, path, readonly=False):
        self.path = Path(path)
        if readonly:
            self.git_path = self.path / "memory.git"
            self.db = sqlite3.connect(f"file:{self.path / 'ledger.sqlite'}?mode=ro", uri=True)
            self.db.row_factory = sqlite3.Row
            return
        self.path.mkdir(parents=True, exist_ok=True)
        self.git_path = self.path / "memory.git"
        if not self.git_path.exists():
            subprocess.run(["git", "init", "--bare", str(self.git_path)], check=True, capture_output=True)
        self.db = sqlite3.connect(self.path / "ledger.sqlite")
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
        PRAGMA journal_mode=DELETE;
        PRAGMA synchronous=FULL;
        CREATE TABLE IF NOT EXISTS kv(key TEXT PRIMARY KEY, data TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS nodes(id TEXT PRIMARY KEY, parent TEXT, anchor TEXT NOT NULL,
          status TEXT NOT NULL, sha TEXT, seq INTEGER UNIQUE NOT NULL, data TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS molecules(smiles TEXT PRIMARY KEY, score REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS evaluations(id TEXT PRIMARY KEY, node TEXT NOT NULL,
          strategy TEXT NOT NULL, smiles TEXT, score REAL, cached INTEGER, data TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS artifacts(id TEXT PRIMARY KEY, node TEXT, kind TEXT NOT NULL,
          text TEXT NOT NULL, created REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS embeddings(id TEXT PRIMARY KEY, model TEXT NOT NULL, data TEXT NOT NULL);
        """)
        self.db.commit()
        self.reconcile()

    def git(self, *args, input=None):
        env = dict(os.environ, GIT_AUTHOR_NAME="Qwen molecular scientist",
                   GIT_AUTHOR_EMAIL="scientist@localhost", GIT_COMMITTER_NAME="Tree experiment tracker",
                   GIT_COMMITTER_EMAIL="tracker@localhost")
        return subprocess.check_output(["git", "--git-dir", str(self.git_path), *args],
                                       input=input, env=env).decode().strip()

    def get(self, key, default=None):
        row = self.db.execute("SELECT data FROM kv WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else default

    def put(self, key, data):
        with self.db:
            self.db.execute("INSERT OR REPLACE INTO kv VALUES(?,?)", (key, dumps(data)))

    def artifact(self, key, node, kind, text):
        ref = identity("A", key)
        with self.db:
            self.db.execute("INSERT OR IGNORE INTO artifacts VALUES(?,?,?,?,?)",
                            (ref, node, kind, str(text), time.time()))
        return ref

    def node(self, id):
        row = self.db.execute("SELECT * FROM nodes WHERE id=?", (id,)).fetchone()
        if row is None:
            raise ValueError(f"Unknown node {id}")
        result = dict(row)
        result["data"] = json.loads(result["data"])
        return result

    def save_node(self, id, data):
        if self.node(id)["status"] != "draft":
            raise ValueError("Committed nodes are immutable; start a child instead")
        with self.db:
            self.db.execute("UPDATE nodes SET data=? WHERE id=?", (dumps(data), id))

    def write_section(self, node, key, section, text, append=True):
        n = self.node(node)
        if n['status'] != 'draft':
            raise ValueError('Committed nodes are immutable')
        if self.get('write:'+key):
            return
        previous = n['data']['sections'].get(section,'')
        n['data']['sections'][section] = previous+'\n'+text if append and previous else text
        with self.db:
            self.db.execute('UPDATE nodes SET data=? WHERE id=?',(dumps(n['data']),node))
            self.db.execute('INSERT INTO kv VALUES(?,?)',('write:'+key,dumps(True)))

    def create_node(self, key, parent, anchor):
        id = identity("N", key)
        if self.db.execute("SELECT 1 FROM nodes WHERE id=?", (id,)).fetchone():
            return self.node(id)
        if parent and self.node(parent)["status"] != "committed":
            raise ValueError("Parent must already be committed")
        if not self.db.execute("SELECT 1 FROM molecules WHERE smiles=?", (anchor,)).fetchone():
            raise ValueError("Anchor must have an actual oracle score")
        data = {"sections": {}, "citations": [], "created": time.time()}
        with self.db:
            seq = self.db.execute("SELECT COALESCE(MAX(seq),-1)+1 FROM nodes").fetchone()[0]
            self.db.execute("INSERT INTO nodes VALUES(?,?,?,'draft',NULL,?,?)",
                            (id, parent, anchor, seq, dumps(data)))
        return self.node(id)

    def evaluations(self, node):
        return [json.loads(r[0]) for r in self.db.execute(
            "SELECT data FROM evaluations WHERE node=? ORDER BY rowid", (node,))]

    def overview(self, offset=0, limit=20):
        rows = self.db.execute("SELECT id,parent,anchor,status,sha,seq,data FROM nodes ORDER BY seq LIMIT ? OFFSET ?",
                               (limit, offset)).fetchall()
        result = []
        for r in rows:
            n = dict(r)
            data = json.loads(n.pop("data"))
            n["score"] = self.db.execute("SELECT score FROM molecules WHERE smiles=?", (n["anchor"],)).fetchone()[0]
            n["title"] = data.get("title", "Working research node")
            n["summary"] = data.get("summary", "")
            values = [e["score"] for e in self.evaluations(n["id"]) if e.get("score") is not None]
            n["best_tested"] = max(values) if values else None
            result.append(n)
        return {"nodes": result, "offset": offset, "next_offset": offset + len(result),
                "total": self.db.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]}

    def incumbent(self):
        row = self.db.execute("SELECT smiles,score FROM molecules ORDER BY score DESC,smiles LIMIT 1").fetchone()
        return dict(row) if row else None

    def read(self, reference):
        row = self.db.execute("SELECT text FROM artifacts WHERE id=?", (reference,)).fetchone()
        if row:
            return row[0]
        if reference.startswith("E"):
            row = self.db.execute("SELECT data FROM evaluations WHERE id=?", (reference,)).fetchone()
            if row:
                return row[0]
        if reference.startswith("N"):
            n = self.node(reference)
            if n["status"] == "committed":
                return self.git("show", f"{n['sha']}:paper.md")
            return dumps(self.workspace(reference))
        raise ValueError("Unknown reference")

    def workspace(self, node):
        n = self.node(node)
        n["anchor_score"] = self.db.execute("SELECT score FROM molecules WHERE smiles=?", (n["anchor"],)).fetchone()[0]
        n["artifacts"] = [dict(r) for r in self.db.execute(
            "SELECT id,kind,length(text) AS characters FROM artifacts WHERE node=? ORDER BY rowid", (node,))]
        n["evaluations"] = self.evaluations(node)
        return n

    def commit(self, node, title, summary, paper):
        n = self.node(node)
        if n["status"] == "committed":
            return {"node": node, "sha": n["sha"], "already_committed": True}
        if not title.strip() or not summary.strip() or not paper.strip():
            raise ValueError("Supply a title, concise searchable summary, and expanded paper")
        evidence = self.evaluations(node)
        measured = [e for e in evidence if e.get("score") is not None and not e.get("initialization")]
        if not measured:
            raise ValueError("An experiment paper needs oracle-backed experimental results")
        for ref in n["data"].get("citations", []):
            cited = self.node(ref)
            if cited["status"] != "committed" or cited["seq"] >= n["seq"]:
                raise ValueError("Citations must refer to earlier committed nodes")
        n["data"].update(title=title, summary=summary, paper=paper)
        self.save_node(node, n["data"])
        bundle = self.workspace(node)
        bundle["artifacts"] = [dict(r) for r in self.db.execute(
            "SELECT id,kind,text,created FROM artifacts WHERE node=? ORDER BY rowid", (node,))]
        results = "\n".join(dumps(e) for e in evidence)
        appendices = []
        for artifact in bundle['artifacts']:
            if artifact['kind'] in {'worker_report','reading_note'}:
                appendices.append(f"### {artifact['kind']}: {artifact['id']}\n{artifact['text']}")
        for section, content in n['data'].get('sections',{}).items():
            appendices.append(f"### Working note: {section}\n{content}")
        appendix = '\n\n'.join(appendices)
        text = f"# {title}\n\n## Search summary\n{summary}\n\n{paper}\n\n## Supporting research records\n{appendix}\n\n## Verified evaluation ledger\n```jsonl\n{results}\n```\n"
        files = {"paper.md": text, "node.json": dumps(bundle)}
        entries = []
        for filename, content in sorted(files.items()):
            blob = self.git("hash-object", "-w", "--stdin", input=content.encode())
            entries.append(f"100644 blob {blob}\t{filename}\n")
        tree = self.git("mktree", input="".join(entries).encode())
        args = ["commit-tree", tree]
        if n["parent"]:
            args += ["-p", self.node(n["parent"])["sha"]]
        sha = self.git(*args, input=f"{node}: {title}\n".encode())
        self.git("update-ref", f"refs/nodes/{node}", sha)
        with self.db:
            self.db.execute("UPDATE nodes SET status='committed',sha=? WHERE id=?", (sha, node))
        return {"node": node, "sha": sha, "best": self.incumbent()}

    def reconcile(self):
        for row in self.db.execute("SELECT id FROM nodes WHERE status='draft'").fetchall():
            try:
                sha = self.git("rev-parse", "--verify", f"refs/nodes/{row[0]}")
            except subprocess.CalledProcessError:
                continue
            bundle = json.loads(self.git("show", f"{sha}:node.json"))
            if bundle["id"] != row[0]:
                raise RuntimeError("Git ref/node mismatch")
            with self.db:
                self.db.execute("UPDATE nodes SET status='committed',sha=?,data=? WHERE id=?",
                                (sha, dumps(bundle["data"]), row[0]))
