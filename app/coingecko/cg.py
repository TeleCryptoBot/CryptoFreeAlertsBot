import requests
from telegram import Update
from telegram.ext import CallbackContext, ContextTypes
import prettytable as pt
from cachetools import cached, TTLCache


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

        response = requests.get(f'https://api.coingecko.com/api/v3/coins/{coin_id}')
        response.raise_for_status()
        data = response.json()
        coin_info = {
            'symbol': data['symbol'].upper(),
            'name': data['name'],
            'price_usd': data['market_data']['current_price']['usd'],
            'price_btc': data['market_data']['current_price']['btc'],
            'market_cap_rank': data['market_data']['market_cap_rank'],
            'price_change_24h': data['market_data']['price_change_percentage_24h'],
        }
        return coin_info
    except Exception as e:
        print(f'Error getting coin info: {e}')
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

    response_text = (
        f"<b>{coin_info['name']} ({coin_info['symbol']})</b>\n"
        f"Price: ${coin_info['price_usd']:.2f} | {coin_info['price_btc']:.8f} BTC\n"
        f"Market Cap Rank: {coin_info['market_cap_rank']}\n"
        f"Price Change (24h): {coin_info['price_change_24h']:+.2f}%"
    )

    await update.message.reply_text(response_text, parse_mode="HTML")
