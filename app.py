import os
from flask import Flask, jsonify
import ccxt
import pandas as pd
import pandas_ta as ta
import requests

# --- Configuration ---
app = Flask(__name__)
binance = ccxt.binance()

# Environment-aware port
PORT = int(os.environ.get("PORT", 8080))

# ID mapping (Rosetta Stone)
ID_MAPPING = {
    'BTC/USDT': 'bitcoin',
    'ETH/USDT': 'ethereum',
    # ... rest of mapping ...
    'RON/USDT': 'ronin'
}
CRYPTO_PAIRS = list(ID_MAPPING.keys())

# Helper: fetch PHP rate
def get_php_rate():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=tether&vs_currencies=php"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()['tether']['php']
    except Exception:
        return 58.0

# Health check endpoint
@app.route("/health")
def health():
    return "OK", 200

# Homepage
@app.route("/")
def home():
    return (
        "<h1>Crypto Data Fortress v3.0 (Precision Strike)</h1>"
        "<p>Endpoints: <a href=\"/full-analysis\">/full-analysis</a></p>"
    )

# Main analysis endpoint
@app.route('/full-analysis')
def get_full_analysis():
    php_rate = get_php_rate()
    report = {}

    for pair in CRYPTO_PAIRS:
        key = ID_MAPPING[pair]
        try:
            ohlcv = binance.fetch_ohlcv(pair, timeframe='1d', limit=100)
            df = pd.DataFrame(ohlcv, columns=['timestamp','open','high','low','close','volume'])
            df.ta.rsi(length=14, append=True)
            df.ta.macd(fast=12, slow=26, signal=9, append=True)
            df.ta.bbands(length=20, std=2, append=True)

            latest = df.iloc[-1]
            usd = latest['close']
            php = usd * php_rate
            rsi = latest['RSI_14']
            macd = latest['MACD_12_26_9']
            signal = latest['MACDs_12_26_9']
            bb_upper = latest['BBU_20_2.0']
            bb_lower = latest['BBL_20_2.0']

            report[key] = {
                "live_prices": {"usd": usd, "php": php},
                "analysis": {
                    "rsi_value": rsi,
                    "rsi_signal": 'SELL' if rsi>70 else 'BUY' if rsi<30 else 'NEUTRAL',
                    "macd_signal": 'BUY' if macd>signal else 'SELL',
                    "bb_signal": 'SELL' if usd>bb_upper else 'BUY' if usd<bb_lower else 'NEUTRAL'
                }
            }
        except Exception as e:
            report[key] = {"error": str(e)}

    return jsonify(report)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)
