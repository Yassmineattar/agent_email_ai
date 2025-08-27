from retriever import SemanticSearcher
from generator import ResponseGenerator
import logging
import time
from typing import Dict, Any
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGChatbot:
    def __init__(self, config: Dict[str, Any] = None):
        """
        Orchestrateur principal du système RAG.
        
        Args:
            config: Configuration pour les chemins et modèles
        """
        self.config = config or self._default_config()
        self._initialize_components()
        logger.info(" Chatbot RAG initialisé avec succès")

    def _default_config(self) -> Dict[str, Any]:
        """Configuration par défaut"""
        return {
            "retriever": {
                "model_name": "all-MiniLM-L6-v2",
                "index_path": "db/faiss_index.index",
                "metadata_path": "db/metadata.pkl"
            },
            "generator": {
                "model_name": "meta-llama/Llama-3.2-1B-Instruct",
                "device": None  # Auto-détection
            }
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
            return {
                "question": question,
                "response": response,
                "sources": [
                    {
                        "uid": res.uid,
                        "logiciel": res.logiciel,
                        "probleme": res.probleme,
                        "distance": res.distance
                    } for res in results
                ],
                "metrics": {
                    "total_time": round(total_time, 2),
                    "retrieval_time": round(retrieval_time, 2),
                    "generation_time": round(generation_time, 2),
                    "results_count": len(results)
                },
                "success": True
            }
            
        except Exception as e:
            logger.error(f" Erreur lors de la génération: {e}")
            return {
                "question": question,
                "response": f"Erreur: {str(e)}",
                "sources": [],
                "metrics": {},
                "success": False
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
                
                # Affichage des sources si disponibles
                if result['sources']:
                    print(f"\n Sources:")
                    for source in result['sources']:
                        print(f"- {source['uid'], source['logiciel']} (confiance: {1-source['distance']:.2%})")
                
                # Métriques de performance
                print(f"\n  Temps total: {result['metrics']['total_time']}s")
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

if __name__ == "__main__":
    # Mode interactif complet
    chatbot = RAGChatbot()
    chatbot.interactive_chat()
    
    # Alternative: mode simple
    # simple_chat()