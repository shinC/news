import requests
import xml.etree.ElementTree as ET

topics = {
    "Business": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtcGhHZ0pLVWlnQVAB",
    "World": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx1YlY4U0FtcGhHZ0pLVWlnQVAB",
    "Nation": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRFZxYUdjU0FtcGhHZ0pLVWlnQVAB",
    "Tech": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtcGhHZ0pLVWlnQVAB",
    "Science": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp0Y1RjU0FtcGhHZ0pLVWlnQVAB",
    "Health": "CAAqJggKIiBDQkFTRWdvSUwyMHZNR3QwTlRFU0FtcGhHZ0pLVWlnQVAB"
}

for name, tid in topics.items():
    res = requests.get(f'https://news.google.com/rss/topics/{tid}?hl=ko&gl=KR&ceid=KR%3Ako')
    try:
        title = ET.fromstring(res.text).find('.//title').text
        print(f"{name}: {title}")
    except:
        print(f"{name}: ERROR")
