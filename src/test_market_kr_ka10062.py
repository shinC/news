import os
import sys
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.market_kr import get_market_data
from src.core.formatter import save_to_markdown

logging.basicConfig(level=logging.INFO)

def test_kr_market_ka10062():
    print("=== Testing KR Market Data Collection (ka10062 included) ===")
    market_data = get_market_data()
    
    summary_info = market_data.get("summary_info", {})
    eql_data = summary_info.get("equal_net_trading") or market_data.get("equal_net_trading")
    
    print("\n[Equal Net Trading Data Summary (ka10062)]")
    if eql_data:
        all_items = eql_data.get("ALL", [])
        kospi_items = eql_data.get("KOSPI", [])
        kosdaq_items = eql_data.get("KOSDAQ", [])
        print(f"ALL Items Count: {len(all_items)}")
        if all_items:
            print("ALL Top 3 Sample:", all_items[:3])
        print(f"KOSPI Items Count: {len(kospi_items)}")
        print(f"KOSDAQ Items Count: {len(kosdaq_items)}")
    else:
        print("No ka10062 equal net trading data found!")

    # Test saving markdown
    test_news = []
    output_filename = "test_kr_economy_news_ka10062.md"
    
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
    test_kr_market_ka10062()
