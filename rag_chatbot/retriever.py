import faiss
import numpy as np
import torch
from sentence_transformers import SentenceTransformer
import pickle
from typing import List
from dataclasses import dataclass
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    uid: str
    logiciel: str
    probleme: str
    solution: str
    distance: float

class SemanticSearcher:
    def __init__(self, model_name: str, index_path: str, metadata_path: str):
        self.model = SentenceTransformer(model_name, device='cuda' if torch.cuda.is_available() else 'cpu')
        self.index_path = Path(index_path)
        self.metadata_path = Path(metadata_path)
        self._load_resources()

    def _load_resources(self) -> None:
        """Load and validate all required resources."""
        try:
            if not all(p.exists() for p in [self.index_path, self.metadata_path]):
                raise FileNotFoundError("Required files not found")
            
            self.index = faiss.read_index(str(self.index_path))
            with open(self.metadata_path, "rb") as f:
                self.metadata = pickle.load(f)

            if not (isinstance(self.metadata, list) and 
                   len(self.metadata) == self.index.ntotal and
                   all(isinstance(m, dict) and {'uid', 'logiciel', 'probleme', 'solution'} <= m.keys() 
                       for m in self.metadata)):
                raise ValueError("Invalid metadata format")

        except Exception as e:
            logger.error(f"Initialization error: {e}")
            raise

    def search(self, query: str, k: int = 3) -> List[SearchResult]:
        """Perform semantic search."""
        try:
            query_vector = self.model.encode([query], convert_to_numpy=True, show_progress_bar=False)
            distances, indices = self.index.search(query_vector.astype(np.float32), k)
            
            return [
                SearchResult(
                    **{k: self.metadata[idx][k] for k in ['uid', 'logiciel', 'probleme', 'solution']},
                    distance=float(dist)
                )
                for idx, dist in zip(indices[0], distances[0])
                if 0 <= idx < len(self.metadata)
            ]
        except Exception as e:
            logger.error(f"Search error: {e}")
            raise

def main():
    try:
        searcher = SemanticSearcher(
            "all-MiniLM-L6-v2",
            "db/faiss_index.index",
            "db/metadata.pkl"
        )
        
        results = searcher.search("Comment générer un rapport")
        
        for i, res in enumerate(results, 1):
            print(f"\nResult #{i} (distance={res.distance:.4f})")
            print(f"UID: {res.uid}")
            print(f"Software: {res.logiciel}")
            print(f"Problem: {res.probleme}")
            print(f"Solution: {res.solution}")

    except Exception as e:
        logger.error(f"Main error: {e}")
        raise

if __name__ == "__main__":
    main()
