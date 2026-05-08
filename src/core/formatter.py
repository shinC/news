import os
import logging
from typing import List, Dict, Any
from config.settings import settings

logger = logging.getLogger(__name__)

def save_to_markdown(news_data: List[Dict[str, Any]], market_data: Dict[str, Any] = None) -> None:
    """
    수집된 시황 정보와 정렬된 뉴스 데이터를 마크다운 포맷으로 변환하여 파일로 저장합니다.
    """
    if not os.path.exists(settings.output_dir):
        os.makedirs(settings.output_dir)
        
    file_path = os.path.join(settings.output_dir, settings.output_filename)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("# US Economy & Business News Report\n\n")
        
        # 시황 정보 기록 (market_data가 있을 경우)
        if market_data:
            f.write("## 📈 간편 시황 요약\n")
            f.write(f"> **데이터 출처**: {market_data.get('source', 'Yahoo Finance (yfinance)')}\n\n")
            
            indices = market_data.get("indices", {})
            if indices:
                f.write("### 주요 3대 지수 (전일 대비)\n")
                for name, info in indices.items():
                    sign = "+" if info['change_pct'] > 0 else ""
                    f.write(f"- **{name}**: {info['price']} ({sign}{info['change_pct']}%)\n")
                f.write("\n")
                
            top_sector = market_data.get("top_sector")
            bottom_sector = market_data.get("bottom_sector")
            if top_sector and bottom_sector:
                f.write("### 섹터 동향 (장 마감 기준)\n")
                f.write(f"- 🚀 **가장 많이 상승한 섹터**: {top_sector['name']} (+{round(top_sector['change_pct'], 2)}%)\n")
                f.write(f"- 📉 **가장 많이 하락한 섹터**: {bottom_sector['name']} ({round(bottom_sector['change_pct'], 2)}%)\n")
                f.write("\n")
        
        f.write("---\n\n")
        f.write("## 📰 주요 헤드라인 (시간순 & 중복도순)\n\n")
        
        if not news_data:
            f.write("수집된 뉴스가 없습니다.\n")
            return
            
        # 클러스터 ID별로 이미 출력한 대표 기사를 추적 (옵션: 중복 기사는 접거나 묶어서 표시 가능)
        printed_clusters = set()
        
        for item in news_data:
            cluster_id = item.get('cluster_id')
            cluster_size = item.get('cluster_size', 1)
            
            # 클러스터 내 대표 기사만 메인으로 출력하고, 
            # 나머지는 생략하거나 하위 목록으로 처리할 수 있지만, 요구사항인 헤드라인 나열을 위해 모두 출력
            
            pub_date = item.get('publish_date')
            date_str = pub_date.strftime('%Y-%m-%d %H:%M') if pd.notnull(pub_date) else "Unknown Date"
            
            title = item.get('title', 'No Title')
            url = item.get('url', '#')
            
            f.write(f"### [{title}]({url})\n")
            f.write(f"- **발행일시**: {date_str} | **중복도(Cluster Size)**: {cluster_size}\n")
            
            summary = item.get('summary', '')
            if summary:
                # 긴 요약은 2~3줄로 자르거나 그대로 표출
                f.write(f"- **요약**: {summary[:300]}...\n")
                
            keywords = item.get('keywords', [])
            if keywords:
                f.write(f"- **키워드**: {', '.join(keywords)}\n")
            
            f.write("\n---\n")
            
    logger.info(f"결과물이 {file_path} 에 저장되었습니다.")
    
# pandas is used in date_str check
import pandas as pd
