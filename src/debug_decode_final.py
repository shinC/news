import requests
import re
from bs4 import BeautifulSoup

def debug_decode(url):
    print(f"Testing URL: {url}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
    }
    try:
        session = requests.Session()
        res = session.get(url, headers=headers, timeout=10, allow_redirects=True)
        print(f"Final URL after redirects: {res.url}")
        
        if "news.google.com" not in res.url:
            return res.url
            
        print(f"HTML Length: {len(res.text)}")
        
        patterns = [
            r'data-url="([^"]+)"',
            r'data-n-au="([^"]+)"',
            r'window\.location\.replace\("([^"]+)"\)',
            r'url=(https?://[^&"]+)',
            r'content="0;url=(https?://[^"]+)"',
            r'\["https://[^"]+"\]'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, res.text, re.I)
            if match:
                found = match.group(1 if "(" in pattern else 0).strip('[]" ')
                print(f"Found pattern {pattern}: {found}")
                if "google.com" not in found:
                    return found
        
        # Try to find any link in the body
        soup = BeautifulSoup(res.text, 'lxml')
        for a in soup.find_all('a', href=True):
            if "google.com" not in a['href'] and a['href'].startswith('http'):
                print(f"Found fallback link in <a>: {a['href']}")
                return a['href']

    except Exception as e:
        print(f"Error: {e}")
    return url

if __name__ == "__main__":
    # Test a typical Google News article URL
    u = "https://news.google.com/rss/articles/CBMidEFVX3lxTE9ma19pXzJBdVBNR0tBUnN2bnpGOHJUNENodVA1UlNaWkdONzJrUkRZcl9PUFU5UE1STFduWndpT1R4eWxFQVpyWmVuWU5qVjFVREx1RGxESDNZUHVpeFFMS0oxZmR6SUtfaGxkLVR4X2d4Q3Vq?oc=5"
    print(f"Decoded: {debug_decode(u)}")
