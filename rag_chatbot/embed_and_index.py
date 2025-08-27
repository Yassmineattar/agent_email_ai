import sqlite3
import faiss
import pickle
from sentence_transformers import SentenceTransformer
import os
from dotenv import load_dotenv
import logging
from typing import List, Dict, Tuple
from pathlib import Path
import numpy as np

class DocumentEmbedder:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize the document embedder with environment setup and model loading."""
        self._setup_logging()
        self._load_environment()
        self.model = SentenceTransformer(model_name)
        self.logger.info("Document embedder initialized successfully")

    def _setup_logging(self) -> None:
        """Configure logging settings."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def _load_environment(self) -> None:
        """Load environment variables."""
        load_dotenv()
        self.db_path = Path(os.getenv("DB_PATH", "database.db"))
        self.index_path = Path(os.getenv("INDEX_PATH", "faiss.index"))
        self.metadata_path = Path(os.getenv("METADATA_PATH", "metadata.pkl"))

    def _fetch_data_from_db(self) -> List[Tuple]:
        """Fetch QA pairs from SQLite database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT uid, logiciel, probleme, solution FROM qa_pairs")
                return cursor.fetchall()
        except sqlite3.Error as e:
            self.logger.error(f"Database error: {e}")
            raise

    def _prepare_documents(self, rows: List[Tuple]) -> Tuple[List[str], List[Dict]]:
        """Prepare documents and metadata from database rows."""
        problems = []   # ← Stocke uniquement les problèmes
        metadata = []
        
        for i, (uid, logiciel, probleme, solution) in enumerate(rows):
            problems.append(probleme)  # ← Embedding du problème seul
            metadata.append({
                "id": i,
                "uid": uid,
                "logiciel": logiciel,
                "probleme": probleme,
                "solution": solution
            })
        return problems, metadata

    def create_and_save_index(self) -> None:
        """Main process to create and save FAISS index and metadata."""
        try:
            self.logger.info("Starting document embedding process")
            
            # Fetch and prepare data
            rows = self._fetch_data_from_db()
            problems, metadata = self._prepare_documents(rows)
            
            # Generate embeddings (seulement sur les problèmes)
            self.logger.info("Generating embeddings...")
            embeddings = self.model.encode(problems, show_progress_bar=True, convert_to_numpy=True)
            
            # Validation des embeddings
            if len(embeddings) != len(problems):
                raise ValueError(f"Mismatch embeddings/documents: {len(embeddings)} vs {len(problems)}")
            
            # Create and save FAISS index
            dimension = embeddings.shape[1]
            index = faiss.IndexFlatL2(dimension)
            index.add(embeddings.astype(np.float32))  # ← Assurance du type float32
            
            # Save index and metadata
            faiss.write_index(index, str(self.index_path))
            with open(self.metadata_path, "wb") as f:
                pickle.dump(metadata, f)
            
            self.logger.info(f"Index saved to {self.index_path}")
            self.logger.info(f"Metadata saved to {self.metadata_path}")
            self.logger.info(f"{len(problems)} problèmes indexés avec succès")
            
        except Exception as e:
            self.logger.error(f"Error during index creation: {e}")
            raise

def main():
    try:
        embedder = DocumentEmbedder()
        embedder.create_and_save_index()
    except Exception as e:
        logging.error(f"Application failed: {e}")
        raise

if __name__ == "__main__":
    main()