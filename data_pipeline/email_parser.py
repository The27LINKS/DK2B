import re

def get_clean_body(raw_email_path: str) -> str:
    """Reads an Enron .txt file and extracts only the message content."""
    with open(raw_email_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        
    # Enron emails separate headers from body with a double newline
    parts = re.split(r'\n\s*\n', content, 1)
    
    if len(parts) > 1:
        body = parts[1].strip()
        # Remove common email junk like '-----Original Message-----'
        clean_body = re.split(r'-+Original Message-+', body, 1)[0]
        return clean_body.strip()
    
    return content.strip()
