import os
import sys
import argparse
import datetime
import logging
from typing import Dict, Any, List

# src 디렉토리를 파이썬 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.kiwoom_api import KiwoomAPI
from config.settings import settings_kr

logger = logging.getLogger("run_equal_trading")

def _format_eql_amt(amt_str: Any) -> str:
    if not amt_str: return "0원"
    s = str(amt_str).replace('+', '').strip()
    try:
        val = int(s)
    except:
        return "0원"
    if val == 0:
        return "0원"
    
    sign = "-" if val < 0 else "+"
    abs_val = abs(val)
    
    if abs_val >= 100000: # 1,000억원 이상
        eok = abs_val // 100
        rem_eok = eok % 10000
        if eok >= 10000:
            cho = eok // 10000
            amt_formatted = f"{cho}조 {rem_eok:,}억원" if rem_eok > 0 else f"{cho}조원"
        else:
            amt_formatted = f"{eok:,}억원"
    elif abs_val >= 100: # 1억원 이상 (예: 6870 -> 68억 7,000만원)
        eok = abs_val // 100
        man = (abs_val % 100) * 100
        if man > 0:
            amt_formatted = f"{eok:,}억 {man:,}만원"
        else:
            amt_formatted = f"{eok:,}억원"
    else: # 1억원 미만 (예: 27 -> 2,700만원)
        man = abs_val * 100
        amt_formatted = f"{man:,}만원"
        
    return f"{sign}{amt_formatted}"

def update_equal_trading_in_markdown(eql_data: Dict[str, List[Dict[str, Any]]],
                                     output_filepath: str,
                                     date_label: str = "") -> None:
    """
    기관 및 외국인 동시(동일) 순매수 상위 결과를 지정된 마크다운 파일에 업데이트합니다.
    기존 마크다운 파일에 동일 순매수 상위 섹션이 존재하면 해당 섹션을 제거한 후 새로 갱신하며,
    기존의 다른 마크다운 본문(뉴스 브리핑 등)은 그대로 보존합니다.
    """
    output_dir = os.path.dirname(output_filepath)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    base_content = ""
    marker = "📊 기관 및 외국인 동시(동일) 순매수 상위"
    
    if os.path.exists(output_filepath):
        with open(output_filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if marker in content:
            idx = content.find(marker)
            prefix = content[:idx]
            prefix_lines = prefix.rstrip().splitlines()
            if prefix_lines and prefix_lines[-1].strip() == "---":
                prefix_lines.pop()
            base_content = "\n".join(prefix_lines).rstrip()
        else:
            base_content = content.rstrip()

    new_section_lines = []
    if base_content:
        new_section_lines.append("\n\n---\n\n")
    else:
        new_section_lines.append("")

    date_str = f" ({date_label})" if date_label else ""
    new_section_lines.append(f"📊 기관 및 외국인 동시(동일) 순매수 상위{date_str}\n")
    new_section_lines.append("> 출처: 키움증권 API (ka10062) | 거래소 통합 | 금액 기준 동시 순매수 상위\n\n")
    
    sections = [
        ("전체 시장 (KOSPI + KOSDAQ)", "ALL"),
        ("코스피 (KOSPI)", "KOSPI"),
        ("코스닥 (KOSDAQ)", "KOSDAQ")
    ]
    
    has_content = False
    for mkt_name, mkt_key in sections:
        items = eql_data.get(mkt_key, [])
        if items:
            has_content = True
            new_section_lines.append(f"### 📌 {mkt_name} 동시 순매수 Top {len(items)}\n\n")
            new_section_lines.append("| 순위 | 종목명 | 현재가 | 등락률 | 기관 순매수액 | 외국인 순매수액 | 합계 순매수액 |\n")
            new_section_lines.append("|---|---|---|---|---|---|---|\n")
            for item in items:
                rank = item.get("rank", "")
                name = item.get("name", "")
                code = item.get("ticker_cd", "")
                
                prc = item.get("price", "0")
                try:
                    prc_int = int(prc.replace("+", "").replace("-", ""))
                    prc_str = f"{prc_int:,}원"
                except:
                    prc_str = f"{prc}원"
                    
                cp = item.get("change_pct", "0.00")
                cp_str = f"{cp}%" if not cp.endswith("%") else cp
                if not cp_str.startswith("+") and not cp_str.startswith("-") and cp_str != "0.00%":
                    cp_str = f"+{cp_str}"
                    
                o_amt = _format_eql_amt(item.get("organ_amt"))
                f_amt = _format_eql_amt(item.get("foreign_amt"))
                t_amt = _format_eql_amt(item.get("total_amt"))
                
                new_section_lines.append(f"| {rank} | {name} | {prc_str} | {cp_str} | {o_amt} | {f_amt} | {t_amt} |\n")
            new_section_lines.append("\n")

    if not has_content:
        new_section_lines.append("해당 일자의 동시 순매수 수집 결과가 없거나 장 마감 전/정산 이전 상태입니다.\n\n")

    final_content = base_content + "".join(new_section_lines)

    with open(output_filepath, 'w', encoding='utf-8') as f:
        f.write(final_content)

    logger.info(f"동일 순매수 상위 결과가 {output_filepath} 에 성공적으로 갱신(기존 섹션 대체)되었습니다.")

# 하위 호환용 alias
append_equal_trading_to_markdown = update_equal_trading_in_markdown

def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    today_default = datetime.datetime.now().strftime("%Y%m%d")

    parser = argparse.ArgumentParser(description="키움증권 API (ka10062) 동일 순매수 상위 별도 수집 스크립트")
    parser.add_argument("--date", "-d", type=str, default=today_default,
                        help=f"조회 대상 일자 (YYYYMMDD 형식, 기본값: 오늘 날짜 {today_default})")
    parser.add_argument("--sort", "-s", type=str, default="3",
                        help="정렬 조건 (1: 기관 순매수순, 2: 외국인 순매수순, 3: 합계 순매수순 - HTS 0798 기본값, 기본값: 3)")
    parser.add_argument("--limit", "-l", type=int, default=10,
                        help="시장별 수집 종목 수 (기본값: 10)")
    parser.add_argument("--output", "-o", type=str, default=None,
                        help="결과를 갱신할 마크다운 파일 경로 (기본값: data/output/kr_economy_news.md)")

    args = parser.parse_args()

    target_date = args.date.replace("-", "").strip()
    sort_cnd = args.sort.strip()
    limit = args.limit
    
    if args.output:
        output_filepath = args.output
    else:
        output_filepath = os.path.join(settings_kr.output_dir, settings_kr.output_filename)

    logger.info(f"=== 키움증권 동일순매매순위(ka10062) 별도 수집 시작 ===")
    logger.info(f"조회 기준일: {target_date}, 정렬조건(sort_cnd): {sort_cnd}, 시장별 limit: {limit}")
    logger.info(f"저장 마크다운 대상: {output_filepath}")

    kiwoom = KiwoomAPI()
    
    # 1. 수집 수행 (전체 000, 코스피 001, 코스닥 101)
    eq_all = kiwoom.get_equal_net_trading_rank("000", limit=limit, target_date=target_date, sort_cnd=sort_cnd)
    eq_kospi = kiwoom.get_equal_net_trading_rank("001", limit=limit, target_date=target_date, sort_cnd=sort_cnd)
    eq_kosdaq = kiwoom.get_equal_net_trading_rank("101", limit=limit, target_date=target_date, sort_cnd=sort_cnd)

    eql_data = {
        "ALL": eq_all,
        "KOSPI": eq_kospi,
        "KOSDAQ": eq_kosdaq
    }

    # 2. 마크다운 파일 갱신 (기존 동일 순매수 섹션 제거 후 새로 대체)
    formatted_date_label = f"{target_date[:4]}-{target_date[4:6]}-{target_date[6:]}" if len(target_date) == 8 else target_date
    update_equal_trading_in_markdown(eql_data, output_filepath, date_label=formatted_date_label)

    logger.info("=== 키움증권 동일순매매순위(ka10062) 별도 수집 완료 ===")

if __name__ == "__main__":
    main()

