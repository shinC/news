import asyncio
from src.core.utils import get_article_text_playwright

url = "https://www.investopedia.com/stock-market-today-dow-jones-s-and-p-500-06022026-11988714"
text = get_article_text_playwright(url)
print("--- Extracted text ---")
print(text)
print("----------------------")
