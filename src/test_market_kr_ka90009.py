import os
import sys
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.market_kr import get_market_data
from src.core.formatter import save_to_markdown

logging.basicConfig(level=logging.INFO)

def test_kr_market_ka90009():
    print("=== Testing KR Market Data Collection (ka90009 included) ===")
    market_data = get_market_data()
    
    summary_info = market_data.get("summary_info", {})
    top_data = summary_info.get("top_trading") or market_data.get("top_trading")
    
    print("\n[Top Trading Data Summary (ka90009)]")
    if top_data:
        kospi = top_data.get("KOSPI", {})
        kosdaq = top_data.get("KOSDAQ", {})
        print(f"KOSPI Foreign Buy Count: {len(kospi.get('foreign_buy', []))}, Organ Buy Count: {len(kospi.get('organ_buy', []))}")
        print("KOSPI Foreign Buy Sample:", kospi.get('foreign_buy', [])[:3])
        print(f"KOSDAQ Foreign Buy Count: {len(kosdaq.get('foreign_buy', []))}, Organ Buy Count: {len(kosdaq.get('organ_buy', []))}")
        print("KOSDAQ Foreign Buy Sample:", kosdaq.get('foreign_buy', [])[:3])
    else:
        print("No ka90009 top trading data found!")

    # Test saving markdown
    test_news = []
    output_filename = "test_kr_economy_news_ka90009.md"
    
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
    test_kr_market_ka90009()
