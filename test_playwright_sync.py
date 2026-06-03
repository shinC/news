from playwright.sync_api import sync_playwright
import newspaper

def fetch_with_playwright_sync(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
        page = context.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=15000)
            html = page.content()
            return html
        except Exception as e:
            print(f"Playwright error: {e}")
            return None
        finally:
            browser.close()

def test():
    url = "https://www.investopedia.com/stock-market-today-dow-jones-s-and-p-500-06022026-11988714"
    html = fetch_with_playwright_sync(url)
    if html:
        print("HTML length:", len(html))
        article = newspaper.Article(url)
        article.html = html
        article.download_state = 2  # Mark as downloaded
        article.parse()
        print("Article text length:", len(article.text))
        print("Snippet:", article.text[:200])
    else:
        print("Failed to get HTML")

if __name__ == "__main__":
    test()
