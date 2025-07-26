from flask import Flask, jsonify
import ccxt
import pandas as pd
import pandas_ta as ta
import requests

# --- Configuration ---
app = Flask(__name__)
binance = ccxt.binance()

# *** ITO ANG PINAKA-MAHALAGANG BAHAGI: ANG ATING "ROSETTA STONE" ***
# Isinasalin nito ang Binance Pair sa tamang GSheet ID.
ID_MAPPING = {
    'BTC/USDT': 'bitcoin',
    'ETH/USDT': 'ethereum',
    'BNB/USDT': 'binancecoin',
    'SOL/USDT': 'solana',
    'XRP/USDT': 'ripple',
    'ADA/USDT': 'cardano',
    'DOGE/USDT': 'dogecoin',
    'AVAX/USDT': 'avalanche-2',
    'DOT/USDT': 'polkadot',
    'LINK/USDT': 'chainlink',
    'MATIC/USDT': 'matic-network',
    'UNI/USDT': 'uniswap',
    'LTC/USDT': 'litecoin',
    'XMR/USDT': 'monero',
    'XLM/USDT': 'stellar',
    'ATOM/USDT': 'cosmos',
    'AXS/USDT': 'axie-infinity',
    'SAND/USDT': 'the-sandbox',
    'MANA/USDT': 'decentraland',
    'SLP/USDT': 'smooth-love-potion',
    'GALA/USDT': 'gala',
    'RON/USDT': 'ronin'
}
# Ang listahan ng pairs ay awtomatikong kukunin mula sa ating mapping.
CRYPTO_PAIRS = list(ID_MAPPING.keys())

# --- Helper Function para sa PHP Conversion (Mula kay Sonnet, solid 'to) ---
def get_php_rate():
    try:
        print("Fetching USDT to PHP conversion rate...")
        url = "https://api.coingecko.com/api/v3/simple/price?ids=tether&vs_currencies=php"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        rate = data['tether']['php']
        print(f"Current rate: 1 USDT = {rate} PHP")
        return rate
    except Exception as e:
        print(f"!!! COULD NOT FETCH PHP RATE: {e}. Defaulting to 58.0")
        return 58.0

# --- Root Route (Homepage - galing din kay Sonnet, ganda nito) ---
@app.route('/')
def home():
    return """
    <h1>Crypto Data Fortress v3.0 (Precision Strike)</h1>
    <p>The fortress is operational. The data is flowing.</p>
    <p>Available endpoints:</p>
    <ul>
        <li><a href="/full-analysis">/full-analysis</a> - Get complete crypto analysis</li>
    </ul>
    """

# --- The Main Endpoint (Pinagsanib na lakas) ---
@app.route('/full-analysis')
def get_full_analysis():
    print("Request received. Starting full analysis...")
    php_conversion_rate = get_php_rate()
    final_report = {}

    for pair in CRYPTO_PAIRS:
        # Gamitin ang mapping para makuha ang tamang GSheet ID
        gsheet_id = ID_MAPPING[pair]
        try:
            print(f"Processing {pair} for GSheet ID: {gsheet_id}...")
            ohlcv = binance.fetch_ohlcv(pair, timeframe='1d', limit=100)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            if df.empty:
                raise ValueError("No data returned from exchange.")

            df.ta.rsi(length=14, append=True)
            df.ta.macd(fast=12, slow=26, signal=9, append=True)
            df.ta.bbands(length=20, std=2, append=True)

            latest = df.iloc[-1]
            price_in_usd = latest['close']
            price_in_php = price_in_usd * php_conversion_rate

            rsi_value = latest['RSI_14']
            rsi_signal = 'SELL' if rsi_value > 70 else 'BUY' if rsi_value < 30 else 'NEUTRAL'

            macd_line = latest['MACD_12_26_9']
            macd_signal_line = latest['MACDs_12_26_9']
            macd_signal = 'BUY' if macd_line > macd_signal_line else 'SELL'

            bb_upper = latest['BBU_20_2.0']
            bb_lower = latest['BBL_20_2.0']
            bb_signal = 'SELL' if price_in_usd > bb_upper else 'BUY' if price_in_usd < bb_lower else 'NEUTRAL'

            # *** ITO ANG PRECISION STRIKE: Gagamitin ang tamang GSheet ID bilang susi ***
            final_report[gsheet_id] = {
                "live_prices": {"usd": price_in_usd, "php": price_in_php},
                "analysis": {
                    "rsi_value": rsi_value, "rsi_signal": rsi_signal,
                    "macd_signal": macd_signal,
                    "bb_value": {"upper": bb_upper, "lower": bb_lower},
                    "bb_signal": bb_signal,
                }
            }
        except Exception as e:
            print(f"!!! FAILED to process {pair}: {e}")
            final_report[gsheet_id] = {
                "live_prices": {"usd": None, "php": None},
                "analysis": {"error": str(e)}
            }

    print("Analysis complete. Sending report.")
    return jsonify(final_report)

# --- Run The Server ---
if __name__ == "__main__":
    print("Starting Crypto Data Fortress v3.0 (The Precision Strike Edition)...")
    app.run(host='0.0.0.0', port=8080)
