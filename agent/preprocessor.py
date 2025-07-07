import re

def split_reply_and_quote(email_text: str):
    """
    Splits an email into reply (support message) and quoted message (user problem).
    """
    # Pattern to detect start of quoted message
    quote_pattern = r"(Le .* a écrit :)"
    
    parts = re.split(quote_pattern, email_text, maxsplit=1)
    
    if len(parts) > 1:
        reply_part = parts[0].strip()
        quoted_block = parts[2].strip() if len(parts) >= 3 else ""
    else:
        reply_part = email_text.strip()
        quoted_block = ""

    # Remove > characters from quoted block
    quoted_block = "\n".join(
        line.lstrip("> ").strip() for line in quoted_block.splitlines()
    )

    return {
        "reply": reply_part,
        "quoted": quoted_block
    }

