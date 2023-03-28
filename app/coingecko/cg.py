from datetime import datetime

import requests
from telegram import Update
from telegram.ext import CallbackContext, ContextTypes
import prettytable as pt
from cachetools import cached, TTLCache
from pycoingecko import CoinGeckoAPI
from .utils import format_number
cg = CoinGeckoAPI()


@cached(cache=TTLCache(maxsize=100000, ttl=60))
def get_trending_coins():
    url = "https://api.coingecko.com/api/v3/search/trending"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()["coins"]
    else:
        return None


async def check_trending(update: Update, context: CallbackContext) -> None:
    trending_coins = get_trending_coins()

    if trending_coins is None:
        await update.message.reply_text("Failed to get trending coins. Please try again later.")
        return

    table = pt.PrettyTable(['No', 'Rank', 'Symbol', 'Name'])
    table.border = False
    table.header = True
    table.padding_width = 1
    table.align['No'] = 'l'
    table.align['Rank'] = 'l'
    table.align['Symbol'] = 'l'
    table.align['Name'] = 'l'
    counter = 1

    for coin in trending_coins:
        rank = coin["item"]["market_cap_rank"]
        if not rank:
            rank = "--"
        symbol = coin["item"]["symbol"].upper()
        name = coin["item"]["name"]
        num = f"#{counter}"
        table.add_row([num, rank, symbol, name])
        counter += 1
    message = '''Coingecko Trending Search \n
    '''
    message += f"<pre>{table.get_string()}</pre>"

    await update.message.reply_text(message, parse_mode="HTML")


@cached(cache=TTLCache(maxsize=1000000, ttl=60 * 3600))
def get_coin_list():
    response = requests.get(f'https://api.coingecko.com/api/v3/coins/list')
    response.raise_for_status()
    coins = response.json()
    return coins


def get_coin_info(coin_symbol):
    try:

        coins = get_coin_list()

        coin_id = None
        for coin in coins:
            if coin['symbol'].lower() == coin_symbol.lower():
                coin_id = coin['id']
                break
        if coin_id is None:
            print(f'Error: Coin not found with symbol {coin_symbol}')
            return None

        coin_data = cg.get_coin_by_id(id=coin_id, localization=False, tickers=False, market_data=True,
                                      community_data=False, developer_data=False)
        return coin_data
    except Exception as e:
        print(f"Error getting coin info for '{coin_symbol}': {e}")
        return None


async def check_coin_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message_text = update.message.text.strip()
    args = message_text.split()[1:]

    if len(args) < 1:
        await update.message.reply_text("Please specify at least one cryptocurrency symbol.")
        return

    coin_symbol = args[0]

    coin_info = get_coin_info(coin_symbol)
    if coin_info is None:
        await update.message.reply_text(f"Coin not found with symbol {coin_symbol}.")
        return

    coin_name = coin_info['name']
    coin_rank = coin_info['market_cap_rank']
    current_price = coin_info['market_data']['current_price']['usd']
    market_cap = coin_info['market_data']['market_cap']['usd']
    low_24h = coin_info['market_data']['low_24h']['usd']
    high_24h = coin_info['market_data']['high_24h']['usd']
    volume_24h = coin_info['market_data']['total_volume']['usd']
    price_change_24h = coin_info['market_data']['price_change_percentage_24h']
    price_change_7d = coin_info['market_data']['price_change_percentage_7d']
    price_change_30d = coin_info['market_data']['price_change_percentage_30d']
    ath = coin_info['market_data']['ath']['usd']
    atl = coin_info['market_data']['atl']['usd']

    atl_date_str = coin_info['market_data']['atl_date']['usd']
    atl_date = datetime.strptime(atl_date_str, '%Y-%m-%dT%H:%M:%S.%fZ')
    ath_date_str = coin_info['market_data']['ath_date']['usd']
    ath_date = datetime.strptime(ath_date_str, '%Y-%m-%dT%H:%M:%S.%fZ')

    ath_change = coin_info['market_data']['ath_change_percentage']['usd']
    atl_change = coin_info['market_data']['atl_change_percentage']['usd']
    circulating_supply = coin_info['market_data']['circulating_supply']
    max_supply = coin_info['market_data']['max_supply']

    output = (
        f"<p>💰 {coin_name} 💰 #{coin_rank}</p>"
        f"<ul>"
        f"<li>Price: {current_price:,.2f} $</li>"
        f"<li>Mkt Cap: {format_number(market_cap)} $</li>"
        f"<li>24h: ↑{high_24h:,.2f} $, ↓{low_24h:,.2f} $</li>"
        f"<li>24h Vol: {format_number(volume_24h)} $</li>"
        f"<li>24h Chg: {price_change_24h:+.2f}%</li>"
        f"<li>7d/30d Chg: {price_change_7d:+.2f}% / {price_change_30d:+.2f}%</li>"
        f"<li>ATH: {ath:,.2f} $ ({ath_date.strftime('%Y-%m-%d')})</li>"
        f"<li>ATL: {atl:,.6f} $ ({atl_date.strftime('%Y-%m-%d')})</li>"
        f"<li>ATH/ATL %: ➗{ath_change:.1f} / ❎{atl_change:.1f}</li>"
        f"<li>Supply: {circulating_supply:,.2f} M / {max_supply:,.2f} M</li>"
        f"</ul>"
    )

    await update.message.reply_text(f"<pre>{output}</pre>", parse_mode="HTML")
