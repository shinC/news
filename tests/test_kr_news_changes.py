import logging
import sys
import os
import unittest

# Add project root and src to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'src'))

from core.scraper_kr import fetch_news, fetch_company_news_kr, decode_google_news_url
from config.settings import settings_kr

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestKRNewsChanges(unittest.TestCase):
    
    def test_decode_google_news_url(self):
        logger.info("--- Testing decode_google_news_url ---")
        google_url = "https://news.google.com/rss/articles/CBMiTkFVX3lxTFBtYml6MUUyZkdCRTZSTUM4eFZwb09zRlhnVEN0QkNRSkd6LVY2Wm1iTTVEVF9BYzFrbzZlVnk1cWM2cnlhQ19GTFZIMDZHZw?oc=5"
        real_url = decode_google_news_url(google_url)
        logger.info(f"Google URL: {google_url}")
        logger.info(f"Decoded Real URL: {real_url}")
        self.assertNotEqual(real_url, google_url, "Google URL should be decoded to another URL")
        self.assertTrue(real_url.startswith("http"), "Real URL must start with http")

    def test_einfomax_rss_macro_news(self):
        logger.info("--- Testing Yeonhap Infomax RSS Macro News ---")
        news = fetch_news()
        macro_news = [n for n in news if n.get("category") == "Macro & Market"]
        logger.info(f"Total news fetched: {len(news)}")
        logger.info(f"Total Macro & Market news fetched: {len(macro_news)}")
        
        # Log parsed macro news
        for i, item in enumerate(macro_news[:3]):
            logger.info(f"Macro {i+1}: {item['title']} (URL: {item['url']})")
            self.assertIsNotNone(item.get("text"), "Macro news should have text body")
            
        # We don't assert len > 0 strictly in case there are no "증시-마감" articles in the last 3 days
        # but if there are, we verify they have the correct structure
        for item in macro_news:
            self.assertEqual(item["category"], "Macro & Market")
            self.assertTrue(item["url"].startswith("http"))
            self.assertIsNotNone(item["publish_date"])

    def test_fetch_company_news_kr(self):
        logger.info("--- Testing fetch_company_news_kr ---")
        companies = ["삼성전자", "SK하이닉스"]
        news = fetch_company_news_kr(companies)
        logger.info(f"Total company news fetched: {len(news)}")
        
        # Verify 5 articles per company
        samsung_news = [n for n in news if n.get("company") == "삼성전자"]
        hynix_news = [n for n in news if n.get("company") == "SK하이닉스"]
        
        logger.info(f"Samsung News count: {len(samsung_news)}")
        logger.info(f"Hynix News count: {len(hynix_news)}")
        
        self.assertTrue(len(samsung_news) <= 5, "Should collect at most 5 articles for Samsung")
        self.assertTrue(len(hynix_news) <= 5, "Should collect at most 5 articles for SK Hynix")
        
        for i, item in enumerate(news[:5]):
            logger.info(f"Company {item['company']} News {i+1}: {item['title']} (URL: {item['url']})")
            self.assertTrue(item["url"].startswith("http"), "Original URL must start with http")
            self.assertIn("특징주", item["title"], "Title should contain query keywords in Naver news")

if __name__ == "__main__":
    unittest.main()
