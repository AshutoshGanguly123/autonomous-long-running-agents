"""BM25 and cached dense embeddings with reciprocal rank fusion."""
from collections import Counter
import json
import math
import re
import numpy as np


def words(text):
    return re.findall(r"[\w]+", text.lower())


class Search:
    def __init__(self, store, model_path):
        self.store, self.model_path, self._model = store, model_path, None

    def encode(self, texts):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_path, device="cpu", local_files_only=True)
        return self._model.encode(texts, normalize_embeddings=True, show_progress_bar=False)

    def search(self, query, limit=10):
        rows = self.store.db.execute("SELECT id,parent,data FROM nodes WHERE status='committed' ORDER BY seq").fetchall()
        if not rows:
            return {"matches": [], "retrieval": "BM25+dense/RRF; archive is empty"}
        docs = []
        for row in rows:
            d = json.loads(row["data"])
            docs.append("\n".join([d.get("title", ""), d.get("summary", ""), d.get("paper", "")]))
        corpus = [words(t) for t in docs]
        avg = sum(map(len, corpus)) / len(corpus) or 1
        df = Counter(w for doc in corpus for w in set(doc))
        scores = []
        for doc in corpus:
            counts = Counter(doc)
            scores.append(sum(math.log(1 + (len(corpus)-df[w]+.5)/(df[w]+.5)) *
                counts[w]*2.5/(counts[w]+1.5*(.25+.75*len(doc)/avg)) for w in set(words(query)) if counts[w]))
        vectors = []
        for row, text in zip(rows, docs):
            found = self.store.db.execute("SELECT model,data FROM embeddings WHERE id=?", (row["id"],)).fetchone()
            if found and found["model"] == self.model_path:
                vec = json.loads(found["data"])
            else:
                d = json.loads(row['data'])
                vec = self.encode([d.get('title','')+'\n'+d.get('summary','')])[0].tolist()
                with self.store.db:
                    self.store.db.execute("INSERT OR REPLACE INTO embeddings VALUES(?,?,?)",
                                          (row["id"], self.model_path, json.dumps(vec)))
            vectors.append(vec)
        dense = np.asarray(vectors) @ np.asarray(self.encode([query])[0])
        ranks = Counter()
        for order in (sorted((i for i in range(len(rows)) if scores[i]>0), key=lambda i: -scores[i]), np.argsort(-dense)):
            for rank, index in enumerate(order, 1):
                ranks[int(index)] += 1/(60+rank)
        result = []
        for i in sorted(ranks, key=lambda i: -ranks[i])[:limit]:
            d = json.loads(rows[i]["data"])
            result.append({"node": rows[i]["id"], "parent": rows[i]["parent"], "title": d.get("title"),
                           "summary": d.get("summary"), "rrf": ranks[i]})
        return {"matches": result, "retrieval": "BM25+dense/RRF"}
