import newspaper
from newspaper import Article

url = "https://n.news.naver.com/mnews/article/001/0014021234"
print("Testing default Article...")
try:
    article = Article(url, language='ko')
    article.download()
    print("Downloaded!")
except Exception as e:
    print("Error:", e)

print("Testing configured Article...")
try:
    config = newspaper.Config()
    config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
    config.request_timeout = 10
    article = Article(url, language='ko', config=config)
    article.download()
    print("Configured downloaded!")
except Exception as e:
    print("Error:", e)
