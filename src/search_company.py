import argparse
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.scraper import fetch_company_news_us
from core.scraper_kr import fetch_company_news_kr
from core.formatter import save_company_news_to_markdown

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def main():
    setup_logging()
    logger = logging.getLogger("search_company")
    
    parser = argparse.ArgumentParser(description="특정 기업들에 대한 최신 뉴스를 스크래핑합니다.")
    parser.add_argument("--market", choices=["us", "kr"], required=True, help="뉴스 검색을 수행할 대상 마켓 (us 또는 kr)")
    parser.add_argument("--companies", nargs="+", required=True, help="검색할 기업명 목록 (공백으로 구분)")
    parser.add_argument("--days", type=int, default=3, help="최근 며칠간의 뉴스를 검색할지 지정 (기본값: 3)")
    
    args = parser.parse_args()
    
    logger.info(f"=== 기업 뉴스 스크래핑 시작 ({args.market.upper()}) ===")
    logger.info(f"대상 기업: {args.companies}")
    logger.info(f"검색 기간: 최근 {args.days}일")
    
    if args.market == "us":
        news_data = fetch_company_news_us(args.companies, args.days)
    else:
        news_data = fetch_company_news_kr(args.companies, args.days)
        
    if news_data:
        logger.info(f"총 {len(news_data)} 건의 기사를 수집/파싱했습니다.")
        save_company_news_to_markdown(news_data, market_type=args.market)
    else:
        logger.warning("수집된 기사가 없습니다.")
        
    logger.info(f"=== 기업 뉴스 스크래핑 완료 ===")

if __name__ == "__main__":
    main()
