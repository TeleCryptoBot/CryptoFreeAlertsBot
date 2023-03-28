import os
import requests
import prettytable as pt
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, JobQueue, MessageHandler, filters, \
    CallbackQueryHandler

from .utils import get_current_price

from ..alert import redis_client


async def list_alerts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.chat_id
    user_key = f"user:{user_id}"

    coins = redis_client.hgetall(user_key)
    if not coins:
        await update.message.reply_text("You haven't set alerts for any cryptocurrencies.")
        return

    table = pt.PrettyTable(['Coin', 'Price'])
    table.border = False
    table.header = False
    table.padding_width = 1
    table.align['Coin'] = 'l'
    table.align['Price'] = 'l'

    for coin_id, old_price in coins.items():
        coin_id = coin_id.decode("utf-8")
        old_price = float(old_price)
        table.add_row([f"{coin_id.upper()}", f"{old_price:.2f} USDT"])

    await update.message.reply_text(f"Cryptocurrencies you've set alerts for:\n<pre>{table.get_string()}</pre>",
                                    parse_mode="HTML")


async def set_alert(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("Please specify at least one cryptocurrency (coin_id).")
        return

    coin_ids = [coin.lower() for coin in args]
    user_id = update.message.chat_id

    for coin_id in coin_ids:
        current_price = get_current_price(coin_id)
        if current_price is None:
            await update.message.reply_text(f"Could not find cryptocurrency {coin_id}, please check again.")
            continue

        redis_client.hset(f"user:{user_id}", coin_id, current_price)
        await update.message.reply_text(f"Price alert for {coin_id} has been set!")


async def remove_alert(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("Please specify at least one cryptocurrency (coin_id) to remove.")
        return

    coin_ids = [coin.lower() for coin in args]
    user_id = update.message.chat_id
    user_key = f"user:{user_id}"

    for coin_id in coin_ids:
        if redis_client.hexists(user_key, coin_id):
            redis_client.hdel(user_key, coin_id)
            await update.message.reply_text(f"Alert for {coin_id} has been removed!")
        else:
            await update.message.reply_text(f"No alert found for {coin_id}.")


async def get_price_change(coin_id: str, interval: str):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={coin_id.upper()}USDT&interval={interval}&limit=2"
        response = requests.get(url)
        response.raise_for_status()

        klines = response.json()
        if len(klines) != 2:
            return None

        old_price = float(klines[0][4])
        # Close price of the previous kline
        current_price = float(klines[1][4])  # Close price of the current kline

        percentage_change = ((current_price - old_price) / old_price) * 100
        return percentage_change
    except Exception as e:
        logging.error(f"Error fetching price change for {coin_id}: {e}")
        return None


async def check_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message_text = update.message.text.strip().lower()
    args = message_text.split()[1:]  # Split message into words and ignore the first word (command itself)

    if len(args) < 1:
        await update.message.reply_text("Please specify at least one cryptocurrency (coin_id).")
        return

    coin_ids = [coin.lower() for coin in args]

    table = pt.PrettyTable(['Symbol', 'Price', 'Change'])
    table.border = False
    table.header = True
    table.padding_width = 1
    table.align['Symbol'] = 'l'
    table.align['Price'] = 'l'
    table.align['Change'] = 'l'

    for coin_id in coin_ids:
        current_price = get_current_price(coin_id)
        price_change_percent = await get_price_change(coin_id, "1d")

        if current_price is None:
            price_formatted = "0"
            price_change_formatted = "--"
        else:
            price_formatted = f"${current_price:,.4f}"
            price_change_formatted = f"{price_change_percent:+.2f}% ✈️" if price_change_percent > 0 else f"{price_change_percent:.2f}% 🥶"

        table.add_row([coin_id.upper(), price_formatted, price_change_formatted])

    # Add Refresh button
    keyboard = [
        [
            InlineKeyboardButton("Refresh", callback_data=f"refresh {' '.join(coin_ids)}"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(f"<pre>{table.get_string()}</pre>", parse_mode="HTML", reply_markup=reply_markup,
                                    reply_to_message_id=update.message.message_id)


async def refresh_prices_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query: CallbackQuery = update.callback_query
    coin_ids = query.data.split()[1:]
    await query.answer()

    table = pt.PrettyTable(['Symbol', 'Price', 'Change'])
    table.border = False
    table.header = True
    table.padding_width = 1
    table.align['Symbol'] = 'l'
    table.align['Price'] = 'l'
    table.align['Change'] = 'l'

    for coin_id in coin_ids:
        current_price = get_current_price(coin_id)
        price_change_percent = await get_price_change(coin_id, "1d")

        if current_price is None:
            price_formatted = "0"
            price_change_formatted = "--"
        else:
            price_formatted = f"${current_price:,.2f}"
            price_change_formatted = f"{price_change_percent:+.2f}% ✈️" if price_change_percent > 0 else f"{price_change_percent:.2f}% 🥶"
            table.add_row([coin_id.upper(), price_formatted, price_change_formatted])

    # Add Refresh button
    keyboard = [
        [
            InlineKeyboardButton("Refresh", callback_data=f"refresh {' '.join(coin_ids)}"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(f"<pre>{table.get_string()}</pre>", parse_mode="HTML", reply_markup=reply_markup)


async def set_custom_check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Please specify a custom name followed by at least one coin symbol.")
        return

    custom_name = args[0].lower()
    user_id = update.message.chat_id
    custom_key = f"user:{user_id}:custom:{custom_name}"
    logging.info("custom_key %s " % custom_key)
    coin_ids = [coin.lower() for coin in args[1:]]
    redis_client.delete(custom_key)
    redis_client.sadd(custom_key, *coin_ids)

    await update.message.reply_text(f"Custom list '{custom_name}' set with the following coins: {', '.join(coin_ids)}")


async def check_custom_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("Please specify a custom name to check.")
        return

    custom_name = args[0].lower()
    user_id = update.message.chat_id
    custom_key = f"user:{user_id}:custom:{custom_name}"
    coin_ids = [coin.decode("utf-8") for coin in redis_client.smembers(custom_key)]

    if not coin_ids:
        await update.message.reply_text(f"No custom list found for '{custom_name}'.")
        return

    table = pt.PrettyTable(['Symbol', 'Price', 'Change'])
    table.border = False
    table.header = False
    table.padding_width = 1
    table.align['Symbol'] = 'l'
    table.align['Price'] = 'l'
    table.align['Change'] = 'l'

    for coin_id in coin_ids:
        current_price = get_current_price(coin_id)
        price_change_percent = await get_price_change(coin_id, "1d")

        if current_price is None:
            price_formatted = "0"
            price_change_formatted = "--"
        else:
            price_formatted = f"${current_price:,.2f}"
            price_change_formatted = f"{price_change_percent:+.2f}% ✈️" if price_change_percent > 0 else f"{price_change_percent:.2f}% 🥶"

        table.add_row([coin_id.upper(), price_formatted, price_change_formatted])

    await update.message.reply_text(f"<pre>{table.get_string()}</pre>", parse_mode="HTML")


async def check_alerts(context: ContextTypes.DEFAULT_TYPE):
    for key in redis_client.scan_iter("user:*"):
        key_type = redis_client.type(key).decode("utf-8")

        if key_type != "hash":
            continue

        user_id = int(key.decode("utf-8").split(":")[1])
        coins = redis_client.hgetall(key)

        for coin_id, old_price in coins.items():
            coin_id = coin_id.decode("utf-8")
            old_price = float(old_price)
            current_price = get_current_price(coin_id)

            if current_price is None:
                continue

            percentage_change = ((current_price - old_price) / old_price) * 100
            if percentage_change > 0:
                trend_icon = "📈"
            else:
                trend_icon = "📉"

            if abs(percentage_change) >= PERCENTAGE_CHANGE:
                price_change_15m = await get_price_change(coin_id, "15m")
                price_change_4h = await get_price_change(coin_id, "4h")
                price_change_1d = await get_price_change(coin_id, "1d")

                await context.bot.send_message(
                    chat_id=user_id,
                    text=(
                        f"{trend_icon}. <b>{coin_id.upper()}</b> has changed by {percentage_change:.2f}%!\n"
                        f"Current price: {current_price}\n"
                        f"Change in 15 minutes: {price_change_15m:.2f}%\n"
                        f"Change in 4 hours: {price_change_4h:.2f}%\n"
                        f"Change in 1 day: {price_change_1d:.2f}%"
                    ), parse_mode='HTML'
                )
                redis_client.hset(key, coin_id, current_price)


# Check Value 10 BTC

async def check_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message_text = update.message.text.strip().lower()
    args = message_text.split()[1:]  # Split message into words and ignore the first word (command itself)

    if len(args) < 2:
        await update.message.reply_text("Please specify at least one cryptocurrency (coin_id).")
        return

    amount = float(args[0])
    coin = args[1].lower()
    if coin == 'btc':
        btc_price = get_current_price(coin_id=coin)
        usdt_value = amount * btc_price
        output = (
            f"{amount} {coin.upper()} = \n\n"
            f"💰 {usdt_value:,.2f} USDT"
        )

    else:
        usdt_price = get_current_price(coin_id=coin)
        btc_price = get_current_price(coin_id='btc')
        usdt_value = amount * usdt_price
        btc_value = usdt_value / btc_price
        output = (
            f"{amount} {coin.upper()} = \n\n"
            f"💰 {usdt_value:,.2f} USDT\n"
            f"💰 {btc_value:,.6f} BTC"
        )

    await update.message.reply_text(f"<pre>{output}</pre>", parse_mode='HTML',
                                    reply_to_message_id=update.message.message_id)
