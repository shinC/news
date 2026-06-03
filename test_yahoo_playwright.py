from playwright.sync_api import sync_playwright

url = 'https://finance.yahoo.com/economy/live/stock-market-today-dow-sp-500-nasdaq-futures-mixed-as-ai-fervor-meets-us-iran-uncertainty-224803638.html'

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--disable-dev-shm-usage', '--no-sandbox'])
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
        )
        page = context.new_page()
        try:
            print("Navigating...")
            response = page.goto(url, timeout=30000, wait_until='domcontentloaded')
            print("Status:", response.status if response else "None")
            page.wait_for_timeout(5000)
            
            html = page.content()
            with open('yahoo_test.html', 'w', encoding='utf-8') as f:
                f.write(html)
            print("HTML length:", len(html))
            
            # Print available class names
            classes = page.evaluate("""() => {
                let els = document.querySelectorAll('div[class]');
                let cls = new Set();
                els.forEach(e => {
                    e.className.split(' ').forEach(c => cls.add(c));
                });
                return Array.from(cls).filter(c => c.includes('body') || c.includes('live') || c.includes('update') || c.includes('article') || c.includes('content'));
            }""")
            print("Found classes:", classes)
        except Exception as e:
            print("Error:", e)
        finally:
            browser.close()

if __name__ == "__main__":
    run()
