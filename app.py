import os
from flask import Flask, jsonify
import ccxt
import pandas as pd
import pandas_ta as ta
import requests
import logging

# --- Basic Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration ---
app = Flask(__name__)
PORT = int(os.environ.get("PORT", 8080))

# --- CCXT Exchange Instance (THE GRANDMASTER PIVOT!) ---
# Pinalitan natin si Binance ng isang mas "friendly" na exchange na walang location restrictions.
exchange = ccxt.kucoin()

# --- ID Mapping (The Rosetta Stone) ---
ID_MAPPING = {
    'BTC/USDT': 'bitcoin', 'ETH/USDT': 'ethereum', 'BNB/USDT': 'binancecoin',
    'SOL/USDT': 'solana', 'XRP/USDT': 'ripple', 'ADA/USDT': 'cardano',
    'DOGE/USDT': 'dogecoin', 'AVAX/USDT': 'avalanche-2', 'DOT/USDT': 'polkadot',
    'LINK/USDT': 'chainlink', 'MATIC/USDT': 'matic-network', 'UNI/USDT': 'uniswap',
    'LTC/USDT': 'litecoin', 'XMR/USDT': 'monero', 'XLM/USDT': 'stellar',
    'ATOM/USDT': 'cosmos', 'AXS/USDT': 'axie-infinity', 'SAND/USDT': 'the-sandbox',
    'MANA/USDT': 'decentraland', 'SLP/USDT': 'smooth-love-potion',
    'GALA/USDT': 'gala', 'RON/USDT': 'ronin'
}
CRYPTO_PAIRS = list(ID_MAPPING.keys())

# --- Helper Function: Fetch PHP Rate ---
def get_php_rate():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=tether&vs_currencies=php"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        rate = response.json()['tether']['php']
        logging.info(f"Successfully fetched PHP rate: {rate}")
        return rate
    except Exception as e:
        logging.error(f"Could not fetch PHP rate: {e}. Defaulting to 58.5")
        return 58.5

# --- Health Check and Homepage Routes ---
@app.route("/health")
def health():
    return "OK", 200

@app.route("/")
def home():
    return "<h1>Crypto Data Fortress is Online</h1><p>Data source: KuCoin. Use /full-analysis to get data.</p>"

# --- Main Analysis Endpoint ---
@app.route('/full-analysis')
def get_full_analysis():
    logging.info("'/full-analysis' request received. Starting job.")
    php_rate = get_php_rate()
    final_report = {}

    for pair in CRYPTO_PAIRS:
        key = ID_MAPPING[pair]
        try:
            logging.info(f"Processing pair: {pair} from KuCoin")
            ohlcv = exchange.fetch_ohlcv(pair, timeframe='1d', limit=100)
            if not ohlcv:
                raise ValueError(f"No OHLCV data returned for {pair}")

            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df.ta.rsi(length=14, append=True)
            df.ta.macd(fast=12, slow=26, signal=9, append=True)
            df.ta.bbands(length=20, std=2, append=True)

            latest = df.iloc[-1]
            usd_price = latest['close']
            
            if pd.isna(usd_price) or pd.isna(latest['RSI_14']):
                 raise ValueError(f"TA calculation resulted in NaN for {pair}")

            final_report[key] = {
                "live_prices": {"usd": usd_price, "php": usd_price * php_rate},
                "analysis": {
                    "rsi_value": latest['RSI_14'],
                    "rsi_signal": 'SELL' if latest['RSI_14'] > 70 else 'BUY' if latest['RSI_14'] < 30 else 'NEUTRAL',
                    "macd_signal": 'BUY' if latest['MACD_12_26_9'] > latest['MACDs_12_26_9'] else 'SELL',
                    "bb_value": {"upper": latest['BBU_20_2.0'], "lower": latest['BBL_20_2.0']},
                    "bb_signal": 'SELL' if usd_price > latest['BBU_20_2.0'] else 'BUY' if usd_price < latest['BBL_20_2.0'] else 'NEUTRAL'
                }
            }
        except Exception as e:
            logging.error(f"FAILED to process {pair}: {e}")
            final_report[key] = {"live_prices": None, "analysis": {"error": str(e)}}

    logging.info("Analysis complete. Sending report.")
    return jsonify(final_report)

# --- Run The Server ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)
