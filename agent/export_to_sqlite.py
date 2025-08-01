import sqlite3
import pandas as pd
import os

# Chemin du fichier CSV
csv_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'mails_data_cleaned_final.csv')

# Charger les données
df = pd.read_csv(csv_file)

# Connexion à la base SQLite (elle sera créée si elle n'existe pas)
db_path = os.path.join(os.path.dirname(__file__), '..','db', 'qa_database.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Créer la table (si elle n'existe pas déjà)
cursor.execute('''
    CREATE TABLE IF NOT EXISTS qa_pairs (
        uid INTEGER PRIMARY KEY AUTOINCREMENT,
        logiciel TEXT,
        probleme TEXT,
        solution TEXT,
        type_probleme TEXT
    )
''')


# Insérer les données
for _, row in df.iterrows():
    cursor.execute('''
    INSERT INTO qa_pairs (uid, logiciel, probleme, solution, type_probleme)
    VALUES (?, ?, ?, ?, ?)
''', (row['uid'], row['logiciel'], row['probleme'], row['solution'], row['type du probleme']))


# Valider et fermer
conn.commit()
conn.close()

print(" Données insérées avec succès dans qa_database.db")
