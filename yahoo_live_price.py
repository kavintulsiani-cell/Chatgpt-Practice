import requests
import json



def normalize_ticker(ticker):
        # Remove spaces and uppercase
    sym = ticker.strip().upper()

        # If it already contains .NS or .BO → return as is
    if sym.endswith(".NS") or sym.endswith(".BO"):
        return sym

        # Else assume NSE and add .NS

    return sym + ".NS"





def get_live_price(user_ticker):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{user_ticker}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=5)

        if response.status_code == 429:
            print("⛔ Yahoo is rate-limiting you (Too Many Requests). Try again in a few seconds.")
            return None

        if response.status_code != 200:
            print("Error fetching price:", response.status_code)
            return None

        data = response.json()
        print (data)
        # Safety checks (Yahoo sometimes returns null)
        if data.get("chart", {}).get("result") is None:
            print("⚠️ No data available for this ticker.")
            return None

        result = data["chart"]["result"][0]
        print ("result : ", result)
        meta = result["meta"]
        live_price = meta.get("regularMarketPrice")

        return live_price

    except requests.exceptions.RequestException as e:
        print("⚠️ Network error:", e)
        return None
if __name__ == "__main__":
    ticker = input ("Enter stock symbol: ")
    user_ticker = normalize_ticker (ticker)
    print (user_ticker)
    live_price = get_live_price(user_ticker)
    print(live_price)