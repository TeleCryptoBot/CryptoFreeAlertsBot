# 🤖 Crypto Telegram Bot

Crypto Telegram Bot is a smart bot that helps you monitor the prices of various cryptocurrencies, set alerts, and check the trending coins on CoinGecko.

Demo: @CryptoFreeAlertsBot
## 🚀 Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### 📋 Prerequisites

- Docker
- Docker Compose

### 🛠️ Installation

1. Clone the repository
```shell
git clone https://github.com/TeleCryptoBot/CryptoFreeAlertsBot.git crypto-telegram-bot
cd crypto-telegram-bot
```
2. Create a .env file in the project root and add your Telegram API key:
```shell
echo "TELEGRAM_API_KEY=YOUR_TELEGRAM_API_KEY" > .env
echo "PERCENTAGE_CHANGE=3" >> .env
```
Replace YOUR_TELEGRAM_API_KEY with your actual Telegram API key.

3. Build and run the project using Docker Compose:
```shell
docker-compose up --build -d
```
Now the Crypto Telegram Bot should be running and connected to your Telegram account.

## 📚 Available Commands

- `/start`: Start the bot
- `/help`: Show help information
- `/set`: Set a price alert for a cryptocurrency
- `/remove`: Remove a price alert for a cryptocurrency
- `/list`: List all price alerts
- `/p`, `p`, or `/P`: Check the price of one or multiple cryptocurrencies
- `/px`: Set a custom list of cryptocurrencies to check
- `/pxc`: Check the price of a custom list of cryptocurrencies
- `/trending`: Check the top-7 trending coins on CoinGecko
- `/ppp`: Check detailed information about a cryptocurrency by its symbol
- `/value`: Get price in usdt with amount

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.
