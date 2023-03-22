import os
import logging
import requests
import prettytable as pt

from redis import Redis

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, JobQueue, MessageHandler, filters, \
    CallbackQueryHandler

from coingecko.cg import check_trending, check_coin_info
from binance.bn import remove_alert, set_alert, list_alerts, check_price, set_custom_check, check_custom_list, \
    refresh_prices_callback, check_alerts

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Initialize environment variables
TELEGRAM_API_KEY = os.environ.get("TELEGRAM_API_KEY")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to the crypto price alert bot!\n"
        "Use /set {coin1 coin2 ...} to set alerts for the cryptocurrencies you're interested in."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = (
        "🤖 I'm CryptoBot! Here are the commands you can use:\n\n"
        "/help - Display this help guide\n"
        "/start - Welcome message and a brief introduction about the bot\n"
        "/set <coin_id_1> <coin_id_2> ... - Set a price alert for a coin\n"
        "/remove <coin_id> - Remove a price alert for a coin\n"
        "/list - List all the current price alerts\n"
        "/p <coin_id_1> <coin_id_2> ... - Check the current price of one or multiple coins\n"
        "/px <name> <coin_id_1> <coin_id_2> ... - Set a custom list with a name to check multiple coin prices\n"
        "/pxc <name> - Check the prices of coins in the custom list by its name\n"
        "/ppp <coin_symbol> - Check information for a coin on CoinGecko (e.g., BTC, ETH)\n"
        "/trending - Check top 7 trending coins on CoinGecko\n"
    )

    await update.message.reply_text(help_text)


def main():
    job_queue = JobQueue()
    app = ApplicationBuilder().token(TELEGRAM_API_KEY).job_queue(job_queue).build()
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("remove", remove_alert))
    app.add_handler(CommandHandler("set", set_alert))
    app.add_handler(CommandHandler("list", list_alerts))
    app.add_handler(MessageHandler(filters.Regex(r'^(?:/|)[Pp](?:\s|$)'), check_price))

    app.add_handler(CommandHandler("px", set_custom_check))
    app.add_handler(CommandHandler("pxc", check_custom_list))

    # Add callback handler for the Refresh button
    app.add_handler(CallbackQueryHandler(refresh_prices_callback, pattern="^refresh"))
    # Coingecko Trending
    app.add_handler(CommandHandler("trending", check_trending))
    app.add_handler(CommandHandler("ppp", check_coin_info))

    job_queue.run_repeating(check_alerts, interval=180, first=0)
    job_queue.start()

    app.run_polling()


if __name__ == "__main__":
    main()
