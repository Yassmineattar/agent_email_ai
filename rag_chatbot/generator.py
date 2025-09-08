from typing import List
from retriever import SearchResult #add rag_chatbot.retriever when use app
import logging
import os
from openai import OpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResponseGenerator:
    def __init__(self, model_name: str, device: str = None):
        """
        Initialise le générateur de réponses via OpenRouter.
        
        Args:
            model_name: identifiant du modèle OpenRouter (ex: meta-llama/llama-3.2-1b-instruct)
            device: ignoré ici (géré côté API)
        """
        self.model_name = model_name
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("Veuillez définir la variable d'environnement OPENROUTER_API_KEY")

        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        )
        logger.info(f" Générateur initialisé avec {model_name} (OpenRouter)")

    def _build_prompt(self, query: str, context_results: List[SearchResult]) -> str:
        """Construit le prompt contextuel"""
        context_text = ""
        for i, res in enumerate(context_results, 1):
            context_text += (
                f"### Source {i}:\n"
                f"Logiciel: {res.logiciel}\n"
                f"Problème: {res.probleme}\n"
                f"Solution: {res.solution}\n\n"
            )

        return f"""
Vous êtes un assistant technique expert. Répondez à la question en utilisant exclusivement le contexte fourni.

CONTEXTE:
{context_text}

INSTRUCTIONS:
- Répondez de manière concise et précise
- Mentionnez le logiciel concerné
- Citez les sources lorsque pertinent
- Si le contexte ne contient pas la réponse, dites-le clairement
- Répondez en français

QUESTION UTILISATEUR:
{query}
"""

    def generate_response(self, query: str, context_results: List[SearchResult]) -> str:
        """Génère une réponse contextuelle avec OpenRouter"""
        if not context_results:
            return "Je n'ai pas trouvé d'informations pertinentes dans ma base de connaissances."
        
        prompt = self._build_prompt(query, context_results)

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "Tu es un assistant technique utile."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )
            content = response.choices[0].message.content.strip()
            logger.info(f" Réponse générée ({len(content)} caractères)")
            return content

        except Exception as e:
            logger.error(f"Erreur pendant la génération: {e}")
            return f"Erreur: {str(e)}"


# Exemple d’utilisation rapide
if __name__ == "__main__":
    try:
        from retriever import SemanticSearcher

        searcher = SemanticSearcher(
            model_name="all-MiniLM-L6-v2",
            index_path="db/faiss_index.index",
            metadata_path="db/metadata.pkl"
        )

        query = "Comment générer un rapport dans docubase?"
        results = searcher.search(query, k=3)

        generator = ResponseGenerator(
            model_name="meta-llama/llama-3.2-1b-instruct"
        )

        response = generator.generate_response(query, results)
        print("\nRéponse générée :")
        print(response)

    except Exception as e:
        logger.error(f"Erreur dans le main: {e}")
