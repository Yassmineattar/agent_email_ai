import sqlite3
import faiss
import pickle
from sentence_transformers import SentenceTransformer
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

DB_PATH = os.getenv("DB_PATH")
INDEX_PATH = os.getenv("INDEX_PATH")
METADATA_PATH = os.getenv("METADATA_PATH")

# 1. Charger le modèle d'embedding BERT
model = SentenceTransformer("all-MiniLM-L6-v2")

# 2. Connexion à SQLite
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 3. Récupération des données
cursor.execute("SELECT uid, logiciel, probleme, solution FROM qa_pairs")
rows = cursor.fetchall()

documents = []
metadata = []

# 4. Préparation des documents et métadonnées
for uid, logiciel, probleme, solution in rows:
    content = f"Logiciel: {logiciel}\nProblème: {probleme}\nSolution: {solution}"
    documents.append(content)
    metadata.append({
        "uid": uid,
        "logiciel": logiciel,
        "probleme": probleme,
        "solution": solution
    })

# 5. Générer les embeddings
print("- Génération des embeddings...")
embeddings = model.encode(documents, show_progress_bar=True)

# 6. Créer l’index FAISS
dimension = embeddings[0].shape[0]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)

# 7. Sauvegarder l’index FAISS et les métadonnées
faiss.write_index(index, INDEX_PATH)
with open(METADATA_PATH, "wb") as f:
    pickle.dump(metadata, f)

print(f"- FAISS index saved to {INDEX_PATH}")
print(f"- Metadata saved to {METADATA_PATH}")
