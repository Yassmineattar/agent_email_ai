import pandas as pd
import os
import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# Charger la clé API
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

# Initialiser Gemini (remplace OpenRouter)
llm = ChatGoogleGenerativeAI(
    model="gemini-pro",
    google_api_key=api_key,
    temperature=0  # ou ajuste si tu veux plus de variété
)

# Prompt pour extraction Q/R
prompt_template = PromptTemplate(
    input_variables=["email_full"],
    template="""
Tu es un assistant IT. Tu vas lire un message contenant un échange entre un utilisateur et un technicien support. Le message peut ou non contenir un problème logiciel réel.

Ta tâche est de :
1. Identifier le **logiciel concerné** (SAP, AGIRH, Docubase, MariProject, etc.)
2. Extraire le **problème rencontré** par l'utilisateur
3. Expliquer la **solution donnée** par le support

⚠️ Si le message n’a rien à voir avec un problème logiciel, réponds uniquement :

`{"skip": true}`

Sinon, retourne ce JSON structuré :

{{
  "logiciel": "...",
  "probleme": "...",
  "solution": "..."
}}

== Message ==
{email_full}
"""
)

# Chaîne avec LLM
chain = LLMChain(llm=llm, prompt=prompt_template)

# Fonction d'extraction
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

            if data.get("skip"):
                continue

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

# Exécution
if __name__ == "__main__":
    extract_qr()
