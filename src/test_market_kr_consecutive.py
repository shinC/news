import os
import sys
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.market_kr import get_market_data
from src.core.formatter import save_to_markdown

logging.basicConfig(level=logging.INFO)

def test_kr_market_and_formatting():
    print("=== Testing KR Market Data Collection (ka10131 included) ===")
    market_data = get_market_data()
    
    summary_info = market_data.get("summary_info", {})
    consec_data = summary_info.get("consecutive_trading") or market_data.get("consecutive_trading")
    
    print("\n[Consecutive Trading Data Summary]")
    if consec_data:
        kospi = consec_data.get("KOSPI", [])
        kosdaq = consec_data.get("KOSDAQ", [])
        print(f"KOSPI Items: {len(kospi)}")
        if kospi:
            print("KOSPI Top 3 sample:", kospi[:3])
        print(f"KOSDAQ Items: {len(kosdaq)}")
        if kosdaq:
            print("KOSDAQ Top 3 sample:", kosdaq[:3])
    else:
        print("No consecutive trading data found!")

    # Test saving markdown
    test_news = []
    output_filename = "test_kr_economy_news.md"
    
    save_to_markdown(
        news_data=test_news,
        market_data=market_data,
        report_title="Korea Economy & Business News Report",
        index_title="한국 주요 3대 지수 (전일 대비)",
        output_filename=output_filename
    )
    
    output_path = os.path.join("data/output", output_filename)
    if os.path.exists(output_path):
        print(f"\nMarkdown successfully generated at: {output_path}")
        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()
            print("\n[Generated Markdown Tail - Last 1500 chars]")
            print(content[-1500:])

if __name__ == "__main__":
    test_kr_market_and_formatting()
