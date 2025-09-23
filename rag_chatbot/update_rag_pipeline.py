#!/usr/bin/env python3
"""
SCRIPT DE MISE À JOUR RAG
1. Prend les données de knowledge_base.jsonl
2. Les stocke dans la base SQLite qa_database.db (en respectant le schéma existant)
3. Appelle la fonction d'indexation de embe_index.py
"""

import json
import sqlite3
import logging
import sys
from pathlib import Path
from datetime import datetime

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RAGPipelineUpdater:
    def __init__(self):
        self.knowledge_base_path = "knowledge_base.jsonl"
        # Utiliser la même base de données que l'ancienne structure
        self.database_path = "db/qa_database_updated.db"
        
    def load_knowledge_base(self):
        """Charge les données de knowledge_base.jsonl"""
        logger.info(f"Chargement de {self.knowledge_base_path}...")
        
        try:
            with open(self.knowledge_base_path, 'r', encoding='utf-8') as f:
                data = [json.loads(line.strip()) for line in f if line.strip()]
            
            logger.info(f"{len(data)} entrées chargées")
            return data
        except Exception as e:
            logger.error(f"Erreur lors du chargement: {e}")
            return None
    
    def init_database(self):
        """Initialise la base de données SQLite avec le schéma existant"""
        try:
            # Créer le dossier db s'il n'existe pas
            Path("db").mkdir(exist_ok=True)
            
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Créer la table avec le schéma existant (AUTOINCREMENT)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS qa_pairs (
                    uid INTEGER PRIMARY KEY AUTOINCREMENT,
                    logiciel TEXT,
                    probleme TEXT,
                    solution TEXT,
                    type_probleme TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Base de données initialisée avec le schéma AUTOINCREMENT")
            return True
            
        except Exception as e:
            logger.error(f"Erreur initialisation base de données: {e}")
            return False
    
    def get_max_existing_uid(self):
        """Récupère le UID maximum existant dans la base"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT MAX(uid) FROM qa_pairs")
            result = cursor.fetchone()
            max_uid = result[0] if result[0] is not None else 0
            
            conn.close()
            logger.info(f"UID maximum existant: {max_uid}")
            return max_uid
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du UID max: {e}")
            return 0
    
    def entry_exists(self, logiciel, probleme, solution):
        """Vérifie si une entrée existe déjà basée sur le contenu (pour éviter les doublons)"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT uid FROM qa_pairs 
                WHERE logiciel = ? AND probleme = ? AND solution = ?
            ''', (logiciel, probleme, solution))
            
            exists = cursor.fetchone()
            conn.close()
            return exists is not None
            
        except Exception as e:
            logger.error(f"Erreur vérification existence entrée: {e}")
            return False
    
    def validate_and_clean_data(self, data):
        """Valide et nettoie les données avant insertion"""
        cleaned_data = []
        
        for item in data:
            # Nettoyer les champs
            cleaned_item = {
                'logiciel': str(item.get('logiciel', '')).strip(),
                'probleme': str(item.get('probleme', '')).strip(),
                'solution': str(item.get('solution', '')).strip(),
                'type_probleme': str(item.get('type_probleme', 'Général')).strip()
            }
            
            # Vérifier que les champs obligatoires ne sont pas vides
            if not cleaned_item['logiciel'] or not cleaned_item['probleme'] or not cleaned_item['solution']:
                logger.warning(f"Entrée ignorée - champs obligatoires manquants: {cleaned_item}")
                continue
            
            # Vérifier si l'entrée existe déjà
            if self.entry_exists(cleaned_item['logiciel'], cleaned_item['probleme'], cleaned_item['solution']):
                logger.info(f"Entrée déjà existante ignorée: {cleaned_item['logiciel']} - {cleaned_item['probleme'][:50]}...")
                continue
            
            cleaned_data.append(cleaned_item)
        
        logger.info(f"Données validées: {len(cleaned_data)} nouvelles entrées après nettoyage")
        return cleaned_data
    
    def insert_into_database(self, data):
        """Insère les données dans la base SQLite en respectant AUTOINCREMENT"""
        logger.info("Insertion des données dans la base...")
        
        try:
            # Nettoyer et valider les données
            cleaned_data = self.validate_and_clean_data(data)
            if not cleaned_data:
                logger.warning("Aucune nouvelle donnée à insérer après validation")
                return 0
            
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            inserted_count = 0
            error_count = 0
            
            for item in cleaned_data:
                try:
                    # Insertion sans spécifier l'uid (géré par AUTOINCREMENT)
                    cursor.execute('''
                        INSERT INTO qa_pairs (logiciel, probleme, solution, type_probleme)
                        VALUES (?, ?, ?, ?)
                    ''', (
                        item['logiciel'], 
                        item['probleme'], 
                        item['solution'], 
                        item['type_probleme']
                    ))
                    inserted_count += 1
                    
                except Exception as e:
                    logger.error(f"Erreur insertion entrée: {e}")
                    error_count += 1
                    continue
            
            conn.commit()
            
            # Récupérer le nombre total d'entrées
            cursor.execute("SELECT COUNT(*) FROM qa_pairs")
            total_count = cursor.fetchone()[0]
            
            conn.close()
            
            logger.info(f"Insertion terminée: {inserted_count} nouvelles entrées, {error_count} erreurs")
            logger.info(f"Total d'entrées dans la base: {total_count}")
            
            return inserted_count
            
        except Exception as e:
            logger.error(f"Erreur insertion base de données: {e}")
            return 0
    
    def run_indexation(self):
        """Exécute la fonction d'indexation de embe_index.py"""
        logger.info("Lancement de l'indexation FAISS...")
        
        try:
            # Import dynamique pour éviter les problèmes de circular imports
            from embed_and_index import DocumentEmbedder
            
            embedder = DocumentEmbedder()
            embedder.create_and_save_index()
            
            logger.info("Indexation terminée avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'indexation: {e}")
            return False
    
    def run(self):
        """Exécute le pipeline complet"""
        logger.info("DÉBUT DU PIPELINE RAG")
        
        # 1. Charger les données
        data = self.load_knowledge_base()
        if not data:
            logger.error("Échec du chargement des données")
            return False
        
        # 2. Initialiser la base avec le bon schéma
        if not self.init_database():
            logger.error("Échec de l'initialisation de la base")
            return False
        
        # 3. Récupérer le UID max actuel (pour information)
        current_max_uid = self.get_max_existing_uid()
        
        # 4. Insérer les nouvelles données
        count = self.insert_into_database(data)
        if count == 0:
            logger.warning("Aucune nouvelle donnée insérée (peut-être que toutes existent déjà)")
            # Continuer quand même le processus
        
        # 5. Lancer l'indexation (décommenter si nécessaire)
        # if not self.run_indexation():
        #     logger.error("Échec de l'indexation")
        #     return False
        
        logger.info("PIPELINE TERMINÉ AVEC SUCCÈS")
        return True

def main():
    """Fonction principale"""
    updater = RAGPipelineUpdater()
    success = updater.run()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()