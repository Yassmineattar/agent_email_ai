import sqlite3
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

# Configuration
model_name = "all-MiniLM-L6-v2"
db_path = "db/qa_database.db"
index_path = "db/faiss_index.bin"

# Charger le modèle SBERT
model = SentenceTransformer(model_name)

def get_qa_pairs():
    """Récupère les paires Q/R depuis SQLite"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT uid, probleme, solution FROM qa_pairs")
    return cursor.fetchall()

# Génération des embeddings
qa_pairs = get_qa_pairs()
questions = [pair[1] for pair in qa_pairs]
embeddings = model.encode(questions, show_progress_bar=True)

# Création de l'index FAISS
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)

# Sauvegarde
faiss.write_index(index, index_path)

# Sauvegarde des métadonnées
with open("db/metadata.pkl", "wb") as f:
    import pickle
    pickle.dump({pair[0]: pair[2] for pair in qa_pairs}, f)