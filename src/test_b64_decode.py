import base64
import sys

def decode_gnews_b64():
    # URL parts after /articles/
    encoded = "CBMiVEFVX3lxTE9sRXlSUmY3UGhkbkFxMktjbXJ2ZVNUWWRVOW9lcHZsRXJ0YW5EWEsyN05ScVozeXpKdFdJU1VTNlZqS3NLQmxqdVlWaGZNRnVBT01OcA"
    
    # Pad if necessary
    padding = len(encoded) % 4
    if padding:
        encoded += '=' * (4 - padding)
        
    try:
        # Base64 URL decode
        decoded = base64.urlsafe_b64decode(encoded)
        print("Decoded bytes:", decoded)
        
        # Try to find http or https in the decoded bytes
        import re
        match = re.search(rb'https?://[^\x00-\x1f\x7f-\xff]+', decoded)
        if match:
            print("Found URL:", match.group(0).decode('utf-8'))
        else:
            print("No URL found in decoded bytes")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    decode_gnews_b64()
