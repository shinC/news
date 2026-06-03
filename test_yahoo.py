from src.core.utils import get_article_text_playwright

url = 'https://finance.yahoo.com/economy/live/stock-market-today-dow-sp-500-nasdaq-futures-mixed-as-ai-fervor-meets-us-iran-uncertainty-224803638.html'
text = get_article_text_playwright(url)
print('TEXT LEN:', len(text))
print('PREVIEW:', text[:500])
