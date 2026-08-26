import requests
from bs4 import BeautifulSoup
import logging
from typing import Dict, Any, List
from src.core.kiwoom_api import KiwoomAPI
from src.core.scraper_kr import fetch_company_news_kr

logger = logging.getLogger(__name__)

ETF_KEYWORDS = ["KODEX", "TIGER", "HANARO", "ACE", "SOL", "RISE", "KOSEF", "ARIRANG", "KBSTAR", "PLUS", "WON", "KIWOOM", "HIT", "KINDEX", "ETN", "선물", "인버스", "레버리지"]

def is_etf(name: str) -> bool:
    n = name.upper().replace(" ", "")
    for kw in ETF_KEYWORDS:
        if kw in n: return True
    return False

def fetch_stock_reason_kr(stock_name: str) -> List[Dict[str, Any]]:
    try:
        news = fetch_company_news_kr([stock_name], days=3)
        res = []
        for a in news:
            if a.get("company") == stock_name:
                res.append({
                    "title": a.get("title"),
                    "url": a.get("url"),
                    "publish_date": a.get("publish_date")
                })
            if len(res) >= 5: break
        return res
    except: return []

def _fetch_naver_top_stocks() -> List[Dict[str, Any]]:
    stocks = []
    headers = {"User-Agent": "Mozilla/5.0"}
    for sosok in [0, 1]:
        url = f"https://finance.naver.com/sise/sise_quant.naver?sosok={sosok}"
        try:
            res = requests.get(url, headers=headers, timeout=10)
            res.encoding = "euc-kr"
            soup = BeautifulSoup(res.text, "lxml")
            table = soup.find("table", {"class": "type_2"})
            if not table: continue
            rows = table.find_all("tr")
            for r in rows:
                tds = r.find_all("td")
                if len(tds) >= 10:
                    try:
                        name = tds[1].text.strip()
                        if not name or is_etf(name): continue
                        price = float(tds[2].text.strip().replace(",", ""))
                        cp_str = tds[4].text.strip().replace("%", "").replace("+", "").replace("-", "")
                        cp = float(cp_str) if cp_str else 0.0
                        if "\u25bc" in tds[3].text or "-" in tds[3].text: cp *= -1
                        tv_val = float(tds[6].text.strip().replace(",", "")) * 1000000
                        stocks.append({"ticker": name, "name": name, "price": str(int(price)), "change_pct": cp, "trading_value": tv_val})
                    except: continue
        except: continue
    return stocks

def fetch_extra_market_info() -> Dict[str, Any]:
    """18번 증시 정보 수집: 지수/거래대금, 글로벌 지수, 환율/원자재/국채, 투자자 동향"""
    extra = {
        "indices_detail": {},
        "global_indices": {},
        "exchanges_and_macro": {},
        "investor_trends": {}
    }
    headers = {"User-Agent": "Mozilla/5.0"}
    
    # 1. 지수 & 거래대금
    indices_list = [('KOSPI', '코스피'), ('KOSDAQ', '코스닥'), ('KPI200', '코스피 200')]
    for code, name in indices_list:
        try:
            url = f'https://finance.naver.com/sise/sise_index.naver?code={code}'
            res = requests.get(url, headers=headers, timeout=5)
            res.encoding = 'euc-kr'
            soup = BeautifulSoup(res.text, 'lxml')
            
            now = soup.select_one('#now_value').text.strip() if soup.select_one('#now_value') else ""
            change_elem = soup.select_one('#change_value_and_rate')
            change_text = change_elem.text.strip() if change_elem else ""
            
            cp_str = "+0.00%"
            if change_elem:
                parts = change_text.split()
                for p in parts:
                    if '%' in p:
                        clean_p = p.replace('상승', '').replace('하락', '').replace('보합', '')
                        if not clean_p.startswith('+') and not clean_p.startswith('-'):
                            sign = "-" if ("하락" in change_text or "-" in change_text) else "+"
                            cp_str = f"{sign}{clean_p}"
                        else:
                            cp_str = clean_p
                        break
                        
            amount_elem = soup.select_one('#amount')
            tv_str = ""
            if amount_elem and code != 'KPI200':
                try:
                    tv_val = float(amount_elem.text.strip().replace(',', '')) / 1000000
                    tv_str = f"{round(tv_val, 1)}조"
                except: pass
                
            extra["indices_detail"][name] = {
                "price": now,
                "change_pct_str": cp_str,
                "trading_value_str": tv_str
            }
        except: pass

    # 2. 투자자 매매동향
    def _format_inv_amt(amt_str):
        if not amt_str: return "0원"
        clean_str = amt_str.replace(',', '').replace('+', '')
        try:
            val_eok = int(clean_str)
        except: return "0원"
        sign_word = "순매수" if val_eok > 0 else "순매도"
        abs_eok = abs(val_eok)
        if abs_eok >= 10000:
            cho = abs_eok // 10000
            eok = abs_eok % 10000
            amt_formatted = f"{cho}조 {eok:,}억원" if eok > 0 else f"{cho}조원"
        else:
            amt_formatted = f"{abs_eok:,}억원"
        return f"{amt_formatted} {sign_word}"

    for code, name in [('KOSPI', '코스피 시장'), ('KOSDAQ', '코스닥 시장')]:
        try:
            url = f'https://m.stock.naver.com/api/index/{code}/trend'
            r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
            d = r.json()
            extra["investor_trends"][name] = {
                "외국인": _format_inv_amt(d.get('foreignValue', '0')),
                "기관": _format_inv_amt(d.get('institutionalValue', '0')),
                "개인": _format_inv_amt(d.get('personalValue', '0'))
            }
        except: pass

    # 3. 글로벌 지수 (yfinance)
    import yfinance as yf
    global_symbols = [
        ("🇺🇸 나스닥 선물", "NQ=F"),
        ("🇯🇵 일본지수", "^N225"),
        ("🇨🇳 상해종합", "000001.SS"),
        ("🇭🇰 항셍지수", "^HSI"),
        ("🇹🇼 대만가권", "^TWII")
    ]
    for g_name, ticker in global_symbols:
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="5d")
            if len(hist) >= 2:
                prev_close = hist['Close'].iloc[-2]
                curr_close = hist['Close'].iloc[-1]
                cp = ((curr_close - prev_close) / prev_close) * 100
            else: cp = 0.0
            sign = "+" if cp > 0 else ""
            extra["global_indices"][g_name] = f"{sign}{cp:.2f}%"
        except:
            extra["global_indices"][g_name] = "+0.00%"

    # 4. 환율 및 유가/국채
    try:
        url_mkt = 'https://finance.naver.com/marketindex/'
        res_m = requests.get(url_mkt, headers=headers, timeout=5)
        res_m.encoding = 'euc-kr'
        soup_m = BeautifulSoup(res_m.text, 'lxml')

        target_currencies = {
            "미국 USD": "달러환율",
            "일본 JPY(100엔)": "일본JPY(100엔)",
            "유럽연합 EUR": "유럽연합EUR",
            "중국 CNY": "중국CNY"
        }
        for a in soup_m.select('a.head'):
            h_text = a.select_one('.h_lst').text.strip() if a.select_one('.h_lst') else ""
            val_text = a.select_one('.value').text.strip() if a.select_one('.value') else ""
            change_text = a.select_one('.change').text.strip() if a.select_one('.change') else ""
            blind_text = a.select_one('.blind').text.strip() if a.select_one('.blind') else ""
            for key, label in target_currencies.items():
                if key in h_text:
                    sign = "-" if "하락" in blind_text else "+"
                    extra["exchanges_and_macro"][label] = f"{val_text}원({sign}{change_text}원)"
    except: pass

    try:
        wti_t = yf.Ticker("CL=F")
        wti_hist = wti_t.history(period="5d")
        if len(wti_hist) >= 2:
            w_prev = wti_hist['Close'].iloc[-2]
            w_curr = wti_hist['Close'].iloc[-1]
            w_diff = w_curr - w_prev
            w_sign = "+" if w_diff > 0 else "-"
            extra["exchanges_and_macro"]["유가(WTI)"] = f"{w_curr:.2f}({w_sign}{abs(w_diff):.2f}달러)"
    except: pass

    try:
        tnx_t = yf.Ticker("^TNX")
        tnx_hist = tnx_t.history(period="5d")
        if len(tnx_hist) >= 2:
            t_prev = tnx_hist['Close'].iloc[-2]
            t_curr = tnx_hist['Close'].iloc[-1]
            t_cp = ((t_curr - t_prev) / t_prev) * 100
            t_sign = "+" if t_cp > 0 else "-"
            extra["exchanges_and_macro"]["미국국채 10년"] = f"{t_curr:.4f}({t_sign}{abs(t_cp):.2f}%)"
    except: pass

    return extra

def get_market_data() -> Dict[str, Any]:
    market_info = {"indices": {}, "top_sector": None, "bottom_sector": None, "top_themes_detailed": [], "top_stocks": [], "source": "Naver Finance & Kiwoom API"}
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        market_info["summary_info"] = fetch_extra_market_info()
    except Exception as e:
        logger.error(f"fetch_extra_market_info error: {e}")

    try:
        url_sise = "https://finance.naver.com/sise/"
        res = requests.get(url_sise, headers=headers)
        res.encoding = "euc-kr"
        soup = BeautifulSoup(res.text, "lxml")
        time_elem = soup.select_one("#time")
        if time_elem:
            try:
                import pandas as pd
                market_info["market_date"] = pd.to_datetime(time_elem.text.split()[0]).to_pydatetime()
            except: pass
        indices_map = {"KOSPI": ("KOSPI_now", "KOSPI_change"), "KOSDAQ": ("KOSDAQ_now", "KOSDAQ_change"), "KOSPI200": ("KPI200_now", "KPI200_change")}
        for name, (id_now, id_change) in indices_map.items():
            now_elem = soup.select_one(f"#{id_now}")
            change_elem = soup.select_one(f"#{id_change}")
            if now_elem and change_elem:
                price = now_elem.text.strip()
                change_texts = change_elem.text.split()
                cp = "0.00"
                for t in change_texts:
                    if "%" in t:
                        cp = t.replace("%", "").replace("\uc0c1\uc2b9", "").replace("\ud558\ub77d", "").replace("\ubcf4\ud569", "")
                        break
                sign = -1 if "\ud558\ub77d" in change_elem.text or "-" in change_elem.text else 1
                try: cp_f = float(cp.replace("+", "").replace("-", "")) * sign
                except: cp_f = 0.0
                market_info["indices"][name] = {"price": price, "change_pct": cp_f}
    except: pass
    
    # 2. 섹터/테마 정보 수집 (Naver Finance 기준)
    try:
        # 사용자 요청에 따라 인포스탁과 유사한 네이버 테마 랭킹 사용
        url_theme = "https://finance.naver.com/sise/theme.naver"
        res = requests.get(url_theme, headers=headers)
        res.encoding = 'euc-kr'
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'lxml')
        
        table = soup.find('table', {'class': 'type_1 theme'})
        themes = []
        if table:
            rows = table.find_all('tr')
            for r in rows:
                tds = r.find_all('td')
                if len(tds) >= 3:
                    name_td = tds[0]
                    a_tag = name_td.find('a')
                    if not a_tag: continue
                    
                    theme_name = a_tag.text.strip()
                    theme_href = a_tag.get('href', '')
                    theme_id = ""
                    if "no=" in theme_href:
                        theme_id = theme_href.split("no=")[1].split("&")[0]
                    
                    change_pct_str = tds[1].text.strip().replace("%", "").replace("+", "").replace("-", "")
                    if not change_pct_str: continue
                    sign = -1 if "-" in tds[1].text else 1
                    try:
                        change_pct = float(change_pct_str) * sign
                        themes.append({
                            "name": theme_name, 
                            "id": theme_id, 
                            "change_pct": change_pct
                        })
                    except ValueError: continue
        
        if themes:
            themes.sort(key=lambda x: x["change_pct"], reverse=True)
            market_info["top_sector"] = themes[0]
            market_info["bottom_sector"] = themes[-1]
            logger.info(f"네이버 테마 {len(themes)}개 수집 완료. 상위 테마: {themes[0]['name']}")
            
            # 상위 6개 테마 상세 수집
            top_themes_detailed = []
            for theme in themes[:6]:
                theme_info = {
                    "name": theme["name"],
                    "change_pct": theme["change_pct"],
                    "stocks": []
                }
                
                if theme["id"]:
                    # 테마 상세 페이지에서 종목 리스트 수집
                    detail_url = f"https://finance.naver.com/sise/sise_group_detail.naver?type=theme&no={theme['id']}"
                    try:
                        d_res = requests.get(detail_url, headers=headers)
                        d_res.encoding = "euc-kr"
                        d_soup = BeautifulSoup(d_res.text, "lxml")
                        d_table = d_soup.find("table", {"class": "type_5"})
                        if d_table:
                            d_rows = d_table.find_all("tr")
                            valid_comps = []
                            for dr in d_rows:
                                dtds = dr.find_all("td")
                                if len(dtds) >= 6:
                                    s_name = dtds[0].text.strip()
                                    if is_etf(s_name): continue
                                    s_pr_str = dtds[2].text.strip().replace(",", "")
                                    s_cp_str = dtds[4].text.strip().replace("%", "").replace("+", "").replace("-", "")
                                    s_vol_str = dtds[8].text.strip().replace(",", "")
                                    if not s_pr_str or not s_cp_str: continue
                                    s_sign = -1 if "\u25bc" in dtds[3].text or "-" in dtds[3].text else 1
                                    try:
                                        s_pr = int(s_pr_str)
                                        s_cp = float(s_cp_str) * s_sign
                                        s_vol = int(s_vol_str) if s_vol_str else 0
                                        s_tv = s_pr * s_vol
                                        if s_cp >= 10 or s_tv >= 100000000000:
                                            valid_comps.append({"name": s_name, "change_pct": s_cp, "trading_value": s_tv})
                                    except: continue
                            if valid_comps: theme_info["stocks"] = sorted(valid_comps, key=lambda x: x["change_pct"], reverse=True)[:6]
                    except: pass
                top_themes_detailed.append(theme_info)
            market_info["top_themes_detailed"] = top_themes_detailed
    except: pass
    try:
        kiwoom = KiwoomAPI()
        # 사용자의 지적대로, 코스피/코스닥을 따로 가져와 합치면 실제 전체 시장 기준 랭킹이 왜곡되므로 다시 전체(000)로 롤백합니다.
        all_st = kiwoom.get_top_trading_value("000")
        
        if not all_st: all_st = _fetch_naver_top_stocks()
        if all_st:
            unique_st = []
            seen = set()
            for s in all_st:
                t = s.get("ticker")
                n = s.get("name", t)
                if t and t not in seen and not is_etf(n):
                    unique_st.append(s)
                    seen.add(t)
            unique_st.sort(key=lambda x: x.get("trading_value", 0), reverse=True)
            top_100 = unique_st[:100]
            top_gn = sorted(top_100, key=lambda x: x.get("change_pct", 0), reverse=True)[:20]
            top_vol = top_100[:20]
            gn_tk = list(set([s["ticker"] for s in top_gn] + [s["ticker"] for s in top_vol]))
            
            for s in top_100:
                if s["ticker"] in gn_tk: s["reason"] = fetch_stock_reason_kr(s["ticker"])
                else: s["reason"] = []
            market_info["top_stocks"] = top_100
    except: pass
    return market_info
