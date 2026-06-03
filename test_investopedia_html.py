import asyncio
from playwright.async_api import async_playwright

async def test():
    url = "https://www.investopedia.com/stock-market-today-dow-jones-s-and-p-500-06022026-11988714"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            
            content = await page.evaluate("""() => {
                let el = document.querySelector('.article-content') || document.querySelector('article');
                if (!el) return 'No article tag found';
                
                let result = '';
                let blocks = el.querySelectorAll('p, h2, h3');
                for (let child of blocks) {
                    result += child.tagName + ': ' + child.innerText.substring(0, 50).replace(/\\n/g, ' ') + '\\n';
                }
                return result;
            }""")
            print("--- HTML Structure ---")
            print(content)
        except Exception as e:
            print(e)
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test())
