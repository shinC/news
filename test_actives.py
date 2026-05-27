import requests

try:
    url = "https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved"
    params = {"scrIds": "most_actives", "count": 250}
    headers = {'User-Agent': 'Mozilla/5.0'}
    resp = requests.get(url, params=params, headers=headers)
    data = resp.json()
    quotes = data['finance']['result'][0]['quotes']
    symbols = [q['symbol'] for q in quotes]
    print(f"Got {len(symbols)} symbols from most_actives")
    # Check for some known popular tickers
    for t in ['SNDK', 'NVDA', 'SMCI', 'PLTR', 'ARM', 'TSLA']:
        print(f"{t} in most_actives? {t in symbols}")
except Exception as e:
    print(f"Error: {e}")
