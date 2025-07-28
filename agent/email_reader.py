from imap_tools import MailBox
from pathlib import Path
import os
from dotenv import load_dotenv
import csv

load_dotenv()

EMAIL = os.getenv("EMAIL")
EMAIL_PASS = os.getenv("EMAIL_PASS")

def fetch_support_emails(limit=150):
    """
    Se connecte à la boîte Gmail du support et lit :
    - les messages envoyés ([Gmail]/Sent Mail)
    Enregistre les résultats(données brutes) dans sent_emails.csv + pièces jointes image
    """
    sent_emails = []

    sent_dir = Path("data")
    img_dir = Path("data")
    sent_dir.mkdir(parents=True, exist_ok=True)

    print("- Connexion à Gmail (support)...")

    with MailBox("imap.gmail.com").login(EMAIL, EMAIL_PASS) as mailbox:
        print(" Lecture des messages envoyés ([Gmail]/Messages envoyés)...")
        mailbox.folder.set("problème SAP")

        for msg in mailbox.fetch(limit=limit, reverse=True):
            image_paths = []

            for att in msg.attachments:
                if "image" in att.content_type  and "LOGO CERTIF" not in att.filename.upper() :
                    img_path = img_dir / f"{msg.uid}_{att.filename}"
                    with open(img_path, "wb") as f:
                        f.write(att.payload)
                    image_paths.append(str(img_path))

            sent_emails.append({
                "uid": msg.uid,
                "subject": msg.subject,
                "from": msg.from_,
                "to": msg.to,
                "date": msg.date.strftime("%Y-%m-%d %H:%M:%S"),
                "content": msg.text or msg.html or "",
                "image_paths": ", ".join(image_paths),
                "folder": "SENT"
            })

        # === Sauvegarde CSV ===
        csv_path = sent_dir / "sent_emails.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = ["uid", "subject", "from", "to", "date", "content", "image_paths", "folder"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            writer.writeheader()
            writer.writerows(sent_emails)


    print(f" {len(sent_emails)} e-mails envoyés sauvegardés dans : {csv_path}")
    return sent_emails
