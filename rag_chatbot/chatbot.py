from retriever import SemanticSearcher #add rag_chatbot.retriever when use app if not no need to
from generator import ResponseGenerator #add rag_chatbot.generator when use app
import logging
import time
from typing import Dict, Any, List
import json
import hashlib
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CacheManager:
    """Gestionnaire de cache simple avec fichiers JSON"""
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True, parents=True) # creer le dossier dans Streamlit Cloud automatiquement
        logger.info(f"- Cache initialisé dans {cache_dir}")

    def _get_cache_key(self, question: str) -> str:
        """Génère une clé de cache unique"""
        return hashlib.md5(question.strip().lower().encode()).hexdigest()

    def _get_cache_path(self, question: str) -> Path:
        """Retourne le chemin du fichier cache"""
        key = self._get_cache_key(question)
        return self.cache_dir / f"{key}.json"

    def get(self, question: str) -> Dict[str, Any]:
        """Récupère une réponse du cache"""
        cache_file = self._get_cache_path(question)
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                logger.info(f"- Cache hit pour: {question[:50]}...")
                return cached_data
            except Exception as e:
                logger.error(f"- Erreur lecture cache: {e}")
        logger.info(f"- Cache miss pour: {question[:50]}...")
        return None

    def set(self, question: str, data: Dict[str, Any]):
        """Stocke une réponse dans le cache"""
        try:
            cache_file = self._get_cache_path(question)
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"- Cache stored pour: {question[:50]}...")
        except Exception as e:
            logger.error(f"- Erreur écriture cache: {e}")

    def clear(self):
        """Vide le cache"""
        # S'assurer que le dossier existe
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
                logger.info(f"- Fichier cache supprimé: {cache_file.name}")
            except Exception as e:
                logger.error(f"- Erreur suppression cache: {e}")
        logger.info("- Cache vidé")

class RAGChatbot:
    def __init__(self, config: Dict[str, Any] = None):
        """
        Orchestrateur principal du système RAG - Mode ligne de commande seulement.
        """
        self.config = config or self._default_config()
        self.cache = CacheManager()
        self._initialize_components()
        logger.info("🤖 Chatbot RAG initialisé (mode CLI)")

    def _default_config(self) -> Dict[str, Any]:
        """Configuration par défaut"""
        return {
            "retriever": {
                "model_name": "all-MiniLM-L6-v2",
                "index_path": "db/faiss_index.index",
                "metadata_path": "db/metadata.pkl"
            },
            "generator": {
                "model_name": "meta-llama/llama-3.3-70b-instruct:free",
                "device": None
            },
            "cache_enabled": True
        }

    def _initialize_components(self):
        """Initialise les composants du système RAG"""
        try:
            # Initialisation du retriever
            retriever_config = self.config["retriever"]
            self.searcher = SemanticSearcher(
                model_name=retriever_config["model_name"],
                index_path=retriever_config["index_path"],
                metadata_path=retriever_config["metadata_path"]
            )
            
            # Initialisation du generator
            generator_config = self.config["generator"]
            self.generator = ResponseGenerator(
                model_name=generator_config["model_name"],
                device=generator_config["device"]
            )
            
            logger.info(" Composants RAG initialisés")
            
        except Exception as e:
            logger.error(f" Erreur d'initialisation: {e}")
            raise

    def ask(self, question: str, k: int = 3) -> Dict[str, Any]:
        """
        Pose une question au chatbot et retourne une réponse complète.
        
        Args:
            question: Question de l'utilisateur
            k: Nombre de résultats à récupérer
            
        Returns:
            Dictionnaire avec réponse, métriques et sources
        """
        # Vérifier le cache d'abord
        if self.config["cache_enabled"]:
            cached_response = self.cache.get(question)
            if cached_response:
                return {**cached_response, "cached": True}
        
        try:
            start_time = time.time()
            
            # Étape 1: Recherche sémantique
            retrieval_start = time.time()
            results = self.searcher.search(question, k=k)
            retrieval_time = time.time() - retrieval_start
            
            # Étape 2: Génération de réponse
            generation_start = time.time()
            response = self.generator.generate_response(question, results)
            generation_time = time.time() - generation_start
            
            total_time = time.time() - start_time
            
            # Formatage de la réponse
            result = {
                "question": question,
                "response": response,
                "sources": [
                    {
                        "uid": res.uid,
                        "logiciel": res.logiciel,
                        "probleme": res.probleme,
                        "solution": res.solution,
                        "distance": res.distance,
                        "confidence": (1 - res.distance) * 100
                    } for res in results
                ],
                "metrics": {
                    "total_time": round(total_time, 2),
                    "retrieval_time": round(retrieval_time, 2),
                    "generation_time": round(generation_time, 2),
                    "results_count": len(results)
                },
                "success": True,
                "cached": False
            }
            
            # Stocker dans le cache
            if self.config["cache_enabled"]:
                self.cache.set(question, result)
            
            return result
            
        except Exception as e:
            logger.error(f"- Erreur lors de la génération: {e}")
            return {
                "question": question,
                "response": f"Erreur: {str(e)}",
                "sources": [],
                "metrics": {},
                "success": False,
                "cached": False
            }

    def interactive_chat(self):
        """Mode interactif en ligne de commande"""
        print(" Chatbot RAG - Tapez 'quit' pour quitter\n")
        
        while True:
            try:
                question = input(" Vous: ").strip()
                
                if question.lower() in ['quit', 'exit', 'q']:
                    print(" À bientôt!")
                    break
                
                if not question:
                    continue
                
                # Obtention de la réponse
                result = self.ask(question)
                
                # Affichage de la réponse
                print(f"\n Assistant: {result['response']}")
                
                if result.get('cached', False):
                    print(" (Réponse depuis le cache)")
                
                # Affichage des sources si disponibles
                if result['sources']:
                    print(f"\n Sources:")
                    for source in result['sources']:
                        print(f"  - {source['logiciel']} (confiance: {source['confidence']:.1f}%)")
                
                # Métriques de performance
                print(f"\n⏱  Temps total: {result['metrics']['total_time']}s")
                if result['metrics']['retrieval_time'] > 0:
                    print(f" Recherche: {result['metrics']['retrieval_time']}s")
                if result['metrics']['generation_time'] > 0:
                    print(f" Génération: {result['metrics']['generation_time']}s")
                
                print("─" * 50)
                
            except KeyboardInterrupt:
                print("\n Interruption utilisateur")
                break
            except Exception as e:
                print(f" Erreur: {e}")

# Interface simplifiée pour tests rapides
def simple_chat():
    """Version simplifiée pour tests"""
    chatbot = RAGChatbot()
    
    while True:
        question = input("\n Posez votre question: ").strip()
        if question.lower() in ['quit', 'exit']:
            break
        
        result = chatbot.ask(question)
        print(f"\n Réponse: {result['response']}")
        if result.get('cached', False):
            print(" (Depuis le cache)")

if __name__ == "__main__":
    # Mode interactif complet
    chatbot = RAGChatbot()
    chatbot.interactive_chat()