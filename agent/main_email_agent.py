from email_reader import fetch_support_emails

if __name__ == "__main__":
    sent = fetch_support_emails(limit=5)

    # print(f"\n=== 📥 INBOX ({len(inbox)} messages) ===")
    # for i, mail in enumerate(inbox, 1):
    #     print(f"\n--- INBOX #{i} ---")
    #     print("Sujet :", mail["subject"])
    #     print("De :", mail["from"])
    #     print("À :", mail["to"])
    #     print("Date :", mail["date"])
    #     print("Contenu :\n", mail["content"])

    print(f"\n=== 📤 SENT ({len(sent)} messages) ===")
    for i, mail in enumerate(sent, 1):
        print(f"\n--- SENT #{i} ---")
        print("Sujet :", mail["subject"])
        print("De :", mail["from"])
        print("À :", mail["to"])
        print("Date :", mail["date"])
        print("Contenu :\n", mail["content"])
