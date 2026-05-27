import yfinance as yf

try:
    s = yf.Screener()
    s.set_predefined_body('most_actives')
    # Can we set count?
    s.patch_body({'size': 100})
    res = s.fetch()
    print("Screener quotes count:", len(s.quotes))
    if len(s.quotes) > 0:
        print("First 5:", [q['symbol'] for q in s.quotes[:5]])
        print("SNDK present?", any(q['symbol'] == 'SNDK' for q in s.quotes))
except Exception as e:
    print(f"Screener Error: {e}")

try:
    import requests
    # There is also a direct Yahoo Finance API for screeners
    url = "https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved"
    params = {"scrIds": "most_actives", "count": 100}
    headers = {'User-Agent': 'Mozilla/5.0'}
    resp = requests.get(url, params=params, headers=headers)
    data = resp.json()
    quotes = data['finance']['result'][0]['quotes']
    print("\nDirect API quotes count:", len(quotes))
    if len(quotes) > 0:
        print("First 5:", [q['symbol'] for q in quotes[:5]])
        print("SNDK present?", any(q['symbol'] == 'SNDK' for q in quotes))
except Exception as e:
    print(f"Direct API Error: {e}")
