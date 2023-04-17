import requests
import logging


def get_current_price(coin_id: str):
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={coin_id.upper()}USDT"
        response = requests.get(url)
        response.raise_for_status()

        ticker = response.json()
        return float(ticker["price"])
    except Exception as e:
        logging.error(f"Error fetching price for {coin_id}: {e}")
        return None
