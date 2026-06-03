import asyncio
from playwright.async_api import async_playwright

async def test():
    url = "https://www.investopedia.com/stock-market-today-dow-jones-s-and-p-500-06022026-11988714"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36")
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            
            # Use same selectors as our code
            content = await page.evaluate("""() => {
                const selectors = ['article', '.article-body', '.story-body', '.main-content', 'main', '#content'];
                let result = '';
                for (let sel of selectors) {
                    let el = document.querySelector(sel);
                    if (el && el.innerText.length > 300) {
                        result = el.innerText;
                        break;
                    }
                }
                if (!result) result = document.body.innerText;
                return result;
            }""")
            print("--- innerText ---")
            print(content[:1500])
        except Exception as e:
            print(e)
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test())
