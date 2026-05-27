import pandas as pd
import requests

try:
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    html_sp500 = requests.get('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies', headers=headers).text
    sp500 = pd.read_html(html_sp500)[0]['Symbol'].tolist()
    print(f"S&P 500 count: {len(sp500)}")
    
    html_ndx = requests.get('https://en.wikipedia.org/wiki/Nasdaq-100', headers=headers).text
    tables = pd.read_html(html_ndx)
    nasdaq100 = []
    for i, t in enumerate(tables):
        if 'Ticker' in t.columns:
            nasdaq100 = t['Ticker'].tolist()
            print(f"Nasdaq 100 count: {len(nasdaq100)}")
            break
            
    combined = list(set(sp500 + nasdaq100))
    print(f"Combined count: {len(combined)}")
except Exception as e:
    print(f"Error: {e}")
