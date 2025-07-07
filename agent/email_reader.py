from imap_tools import MailBox
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

EMAIL = os.getenv("EMAIL")
EMAIL_PASS = os.getenv("EMAIL_PASS")

def fetch_support_emails(limit=50):
    """
    Se connecte à la boîte Gmail du support et lit :
    - les messages envoyés ([Gmail]/Sent Mail)

    Retourne une liste: sent_emails
    """
    sent_emails = []

    sent_dir = Path("data")
    sent_dir.mkdir(parents=True, exist_ok=True)

    print("📡 Connexion à Gmail (support)...")

    with MailBox("imap.gmail.com").login(EMAIL, EMAIL_PASS) as mailbox:

        # # === INBOX ===
        # print(" Lecture des messages reçus (INBOX)...")
        # mailbox.folder.set("INBOX")
        # for msg in mailbox.fetch(limit=limit, reverse=True):
        #     image_paths = []

        #     for att in msg.attachments:
        #         if "image" in att.content_type:
        #             img_path = inbox_dir / f"{msg.uid}_{att.filename}"
        #             with open(img_path, "wb") as f:
        #                 f.write(att.payload)
        #             image_paths.append(str(img_path))

        #     inbox_emails.append({
        #         "uid": msg.uid,
        #         "subject": msg.subject,
        #         "from": msg.from_,
        #         "to": msg.to,
        #         "date": msg.date.strftime("%Y-%m-%d %H:%M:%S"),
        #         "content": msg.text or msg.html or "",
        #         "image_paths": ", ".join(image_paths),
        #         "folder": "INBOX"
        #     })

        # === SENT ===
        # Les emails SENT contiennent deja les messages envoyés par le support
        print(" Lecture des messages envoyés ([Gmail]/Sent Mail)...")
        mailbox.folder.set("[Gmail]/Messages envoyés")
        for msg in mailbox.fetch(limit=limit, reverse=True):
            image_paths = []

            for att in msg.attachments:
                if "image" in att.content_type:
                    img_path = sent_dir / f"{msg.uid}_{att.filename}"
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

    return sent_emails
