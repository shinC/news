import asyncio
from playwright.async_api import async_playwright
import newspaper

async def fetch_with_playwright(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            html = await page.content()
            return html
        except Exception as e:
            print(f"Playwright error: {e}")
            return None
        finally:
            await browser.close()

async def test():
    url = "https://www.investopedia.com/stock-market-today-dow-jones-s-and-p-500-06022026-11988714"
    html = await fetch_with_playwright(url)
    if html:
        print("HTML length:", len(html))
        article = newspaper.Article(url)
        article.download(input_html=html)
        article.parse()
        print("Article text length:", len(article.text))
        print("Snippet:", article.text[:200])
    else:
        print("Failed to get HTML")

if __name__ == "__main__":
    asyncio.run(test())
