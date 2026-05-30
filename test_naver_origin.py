import requests
from bs4 import BeautifulSoup
import sys

url = "https://n.news.naver.com/article/001/0016105365?sid=101"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'}
res = requests.get(url, headers=headers)
soup = BeautifulSoup(res.text, 'lxml')

# 보통 네이버 뉴스에서 원본 기사 링크는 a 태그의 class 'media_end_head_origin_link' 나 다른 형태일 수 있음
origin_link = soup.select_one('a.media_end_head_origin_link')
if origin_link:
    print("Found origin link:", origin_link.get('href'))
else:
    print("Not found")

