import pandas as pd
import os
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# Load API key
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

# Init LLM via OpenRouter (modèle gratuit)
llm = ChatOpenAI(
    temperature=0,
    model="mistralai/mistral-7b-instruct",
    openai_api_base="https://openrouter.ai/api/v1",
    openai_api_key=api_key
)

# Prompt pour extraction Q/R
prompt_template = PromptTemplate(
    input_variables=["email_full"],
    template="""
Tu es un assistant support technique. Tu vas lire un message complet contenant :
- l'objet du mail (sujet)
- le contenu de l'échange entre un utilisateur et un technicien IT.

Tu dois analyser ce message et :
1. Identifier le **logiciel concerné** (exemples : SAP, AGIRH, Docubase, MariProject)
2. Résumer **le problème** mentionné par l’utilisateur
3. Extraire **la solution apportée par le support**

Retourne uniquement un JSON structuré :

{{
  "logiciel": "...",
  "probleme": "...",
  "solution": "..."
}}

== Message ==
{email_full}
"""
)

chain = LLMChain(llm=llm, prompt=prompt_template)

# Extraction
def extract_qr(input_csv="data/structured_input.csv", output_csv="data/structured_qr.csv"):
    df = pd.read_csv(input_csv)
    structured_results = []

    for idx, row in df.iterrows():
        email_text = row["email_full"]
        uid = row["uid"]

        if pd.isna(email_text) or len(email_text.strip()) < 30:
            continue

        try:
            print(f"🟡 Traitement email UID {uid}...")
            response = chain.run(email_full=email_text)

            # Nettoyage + parsing JSON
            response = response.strip().replace("“", "\"").replace("”", "\"")
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            json_str = response[json_start:json_end]

            data = json.loads(json_str)

            structured_results.append({
                "uid": uid,
                "logiciel": data.get("logiciel", row.get("logiciel_detecte", "")),
                "probleme": data.get("probleme", "").strip(),
                "solution": data.get("solution", "").strip(),
            })

        except Exception as e:
            print(f"❌ Erreur avec l’email UID {uid} : {e}")
            continue

    # Enregistrer dans un CSV final
    df_out = pd.DataFrame(structured_results)
    df_out.to_csv(output_csv, index=False)
    print(f"\n✅ Extraction terminée : {output_csv} généré avec {len(df_out)} lignes.")

# Lance l'exécution
if __name__ == "__main__":
    extract_qr()
