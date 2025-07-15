from email_reader import fetch_support_emails
# from preprocessor import split_reply_and_quote 

if __name__ == "__main__":
    sent = fetch_support_emails(limit=10)

    print(f"\n=== 📤 SENT ({len(sent)} messages) ===")
    for i, mail in enumerate(sent, 1):
        print(f"\n--- SENT #{i} ---")
        print("Sujet :", mail["subject"])
        print("De :", mail["from"])
        print("À :", mail["to"])
        print("Date :", mail["date"])

        # # Preprocess content to extract reply & quoted question
        # result = split_reply_and_quote(mail["content"])
        
        # print("\n--- Support Reply ---\n", result["reply"])
        # print("\n--- User Question (Quoted) ---\n", result["quoted"])
