from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from typing import List
from retriever import SearchResult
import torch
import logging
import os
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResponseGenerator:
    def __init__(self, model_name: str, device: str = None):
        """
        Initialise le générateur de réponses avec LLaMA.
        
        Args:
            model_name: nom du modèle HF ou chemin local
            device: "cuda", "cpu" ou None pour auto-détection
        """
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model_name = model_name
        hf_token = os.getenv("HF_TOKEN")
        
        logger.info(f"Chargement du modèle {model_name} sur {self.device}...")
        
        # Chargement avec gestion d'erreurs
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_name, 
                token=hf_token,
                padding_side="left"  # Important pour la génération
            )
            
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                token=hf_token,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto" if self.device == "cuda" else None,
                low_cpu_mem_usage=True
            )
            
            logger.info("Modèle chargé avec succès")
            
        except Exception as e:
            logger.error(f"Erreur de chargement: {e}")
            raise

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

        return f"""<|system|>
Vous êtes un assistant technique expert. Répondez à la question en utilisant exclusivement le contexte fourni.

CONTEXTE:
{context_text}

INSTRUCTIONS:
- Répondez de manière concise et précise
- Mentionnez le logiciel concerné
- Citez les sources lorsque pertinent
- Si le contexte ne contient pas la réponse, dites-le clairement
- Répondez en français</s>

<|user|>
{query}</s>

<|assistant|>
"""

    def generate_response(self, query: str, context_results: List[SearchResult]) -> str:
        """Génère une réponse contextuelle"""
        if not context_results:
            return "Je n'ai pas trouvé d'informations pertinentes dans ma base de connaissances."
        
        # Construction du prompt
        prompt = self._build_prompt(query, context_results)
        
        try:
            # Tokenization avec gestion de la longueur
            inputs = self.tokenizer(
                prompt, 
                return_tensors="pt", 
                truncation=True, 
                max_length=3000
            ).to(self.device)

            # Génération avec paramètres optimisés
            with torch.inference_mode():
                output_ids = self.model.generate(
                    **inputs,
                    max_new_tokens=256,
                    do_sample=True,
                    temperature=0.7,
                    top_p=0.9,
                    top_k=50,
                    repetition_penalty=1.1,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )

            # Décodage de la réponse
            response = self.tokenizer.decode(
                output_ids[0][inputs.input_ids.shape[1]:], 
                skip_special_tokens=True
            )
            
            logger.info(f" Réponse générée ({(len(response))} caractères)")
            return response.strip()
            
        except RuntimeError as e:
            if "out of memory" in str(e).lower():
                logger.error("Out of Memory - Réduction de la longueur du contexte")
                return "Erreur de mémoire. Veuillez reformuler votre question."
            raise

# Exemple d'utilisation avec gestion d'erreurs
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
            model_name="meta-llama/Llama-3.2-1B-Instruct"
        )

        response = generator.generate_response(query, results)
        print("\nRéponse générée :")
        print(response)

    except Exception as e:
        logger.error(f"Erreur dans le main: {e}")