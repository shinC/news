import os
import sys
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.market_kr import get_market_data
from src.core.formatter import save_to_markdown

logging.basicConfig(level=logging.INFO)

def test_today():
    print("=== Testing KR Market Data Collection for Today (Strict Today Date) ===")
    market_data = get_market_data()
    
    summary_info = market_data.get("summary_info", {})
    eql_data = summary_info.get("equal_net_trading") or market_data.get("equal_net_trading")
    
    print("\n[Equal Net Trading Data Summary]")
    if eql_data:
        all_items = eql_data.get("ALL", [])
        print(f"ALL Items Count: {len(all_items)}")
        if all_items:
            print("ALL Sample Item:", all_items[0])
    
    output_filename = "test_today_result.md"
    save_to_markdown(
        news_data=[],
        market_data=market_data,
        report_title="Korea Economy & Business News Report",
        index_title="한국 주요 3대 지수 (전일 대비)",
        output_filename=output_filename
    )
    
    output_path = os.path.join("data/output", output_filename)
    if os.path.exists(output_path):
        print(f"\nGenerated Markdown Path: {output_path}")
        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()
            print("\n[Tail Output - Last 1000 chars]")
            print(content[-1000:])

if __name__ == "__main__":
    test_today()
