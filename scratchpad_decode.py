import base64
import re
import urllib.parse

def local_decode(url):
    if '/articles/' in url:
        encoded = url.split('/articles/')[1].split('?')[0]
        padding = len(encoded) % 4
        if padding:
            encoded += '=' * (4 - padding)
        try:
            decoded_bytes = base64.urlsafe_b64decode(encoded)
            match_url = re.search(rb'https?://[^\x00-\x1f\x7f-\xff]+', decoded_bytes)
            if match_url:
                return match_url.group(0).decode('utf-8')
        except Exception as e:
            print("Error:", e)
    return url

print(local_decode("https://news.google.com/rss/articles/CBMiTkFVX3lxTFBtYml6MUUyZkdCRTZSTUM4eFZwb09zRlhnVEN0QkNRSkd6LVY2Wm1iTTVEVF9BYzFrbzZlVnk1cWM2cnlhQ19GTFZIMDZHZw?oc=5"))
