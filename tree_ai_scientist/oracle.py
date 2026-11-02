"""Operator-only oracle adapter. Never inject this source into agent context.

Formula reused from the user's PABLO/exp9 oracle, verified against GuacaMol.
"""
import math
from rdkit import Chem, rdBase
from rdkit.Chem import AllChem, DataStructs, rdMolDescriptors
from .store import dumps, identity

REFERENCE = r"Clc1ccccc1C2C(=C(/N/C(=C2/C(=O)OCC)COCCN)C)\C(=O)OC"


def canonical(smiles):
    if not isinstance(smiles, str):
        return None
    with rdBase.BlockLogs():
        mol = Chem.MolFromSmiles(smiles)
    return Chem.MolToSmiles(mol) if mol is not None else None


class Oracle:
    def __init__(self, store):
        self.store = store
        self.target = AllChem.GetMorganFingerprint(Chem.MolFromSmiles(REFERENCE), 2)

    def score(self, smiles):
        mol = Chem.MolFromSmiles(smiles)
        sim = DataStructs.TanimotoSimilarity(self.target, AllChem.GetMorganFingerprint(mol, 2))
        ring = math.exp(-0.5 * ((rdMolDescriptors.CalcNumRings(mol) - 3) / .5) ** 2)
        return math.sqrt(max(sim, 0) * ring)

    def evaluate(self, key, node, strategy, smiles, initialization=False):
        if not isinstance(smiles, list) or not smiles:
            raise ValueError("smiles must be a nonempty list of SMILES strings")
        results = []
        for i, raw in enumerate(smiles):
            ref = identity("E", f"{key}:{i}")
            prior = self.store.db.execute("SELECT data FROM evaluations WHERE id=?", (ref,)).fetchone()
            if prior:
                import json
                saved = json.loads(prior[0])
                if saved['input'] != raw or saved['node'] != node or saved['strategy'] != strategy:
                    raise ValueError('Evaluation receipt key reused with different arguments')
                results.append(saved)
                continue
            c = canonical(raw)
            previous = self.store.db.execute("SELECT score FROM molecules WHERE smiles=?", (c,)).fetchone() if c else None
            score = previous[0] if previous else self.score(c) if c else None
            record = {"id": ref, "node": node, "strategy": strategy, "input": raw,
                      "smiles": c, "score": score, "cached": bool(previous), "initialization": initialization}
            if c is None:
                record["error"] = "Invalid SMILES; not sent to scoring function"
            with self.store.db:
                if c:
                    self.store.db.execute("INSERT OR IGNORE INTO molecules VALUES(?,?)", (c, score))
                self.store.db.execute("INSERT INTO evaluations VALUES(?,?,?,?,?,?,?)",
                    (ref, node, strategy, c, score, int(bool(previous)), dumps(record)))
            results.append(record)
        return results
