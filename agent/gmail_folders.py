from imap_tools import MailBox
import os
from dotenv import load_dotenv

load_dotenv()

EMAIL = os.getenv("EMAIL")
EMAIL_PASS = os.getenv("EMAIL_PASS")

with MailBox("imap.gmail.com").login(EMAIL, EMAIL_PASS) as mailbox:
    print("\n📂 Liste des dossiers IMAP disponibles :")
    for f in mailbox.folder.list():
        print("-", f.name)
