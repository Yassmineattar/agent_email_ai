import pandas as pd
import re

def clean_content(text):
    if pd.isna(text):
        return ""
    
    # 1. Supprimer les réponses en citation
    text = re.split(r"\nLe .*? a écrit :", text)[0]
    text = re.split(r"On .*? a écrit :", text)[0]

    # 2. Supprimer les signatures
    text = re.sub(r"(--|Cordialement|Bien à vous|Sincèrement)[\s\S]*", "", text, flags=re.IGNORECASE)

    # 3. Nettoyage général
    text = text.replace(">", "")
    text = text.replace("\r", " ").replace("\n", " ").strip()
    text = re.sub(r"\s+", " ", text)

    return text

def detect_logiciel(text):
    logiciels = ["SAP", "AGIRH", "MariProject", "Docubase"]
    for l in logiciels:
        if l.lower() in text.lower():
            return l
    return ""

def preprocess_sent_emails(input_csv="data/sent_emails.csv", output_csv="data/structured_input.csv"):
    df = pd.read_csv(input_csv)

    # Nettoyage du contenu
    df["content_clean"] = df["content"].apply(clean_content)

    # Détection image
    df["has_image"] = df["image_paths"].apply(lambda x: False if pd.isna(x) or x.strip() == "" else True)

    # Détection logiciel depuis subject + content
    df["logiciel_detecte"] = df.apply(
        lambda row: detect_logiciel(str(row["subject"]) + " " + str(row["content_clean"])),
        axis=1
    )

    # Champ combiné subject + content_clean
    df["email_full"] = df["subject"].fillna("") + "\n" + df["content_clean"]

    # Sélection des colonnes utiles
    df_structured = df[["uid", "subject", "email_full", "has_image", "logiciel_detecte"]]
    df_structured.to_csv(output_csv, index=False)
    print(f" Données nettoyées sauvegardées dans : {output_csv}")

# Pour exécution directe si besoin
if __name__ == "__main__":
    preprocess_sent_emails()
