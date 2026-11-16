# Currency Rates Bot

[![Tests](https://github.com/MariaLysiukq/CurrencyRatesBot/actions/workflows/tests.yml/badge.svg)](https://github.com/MariaLysiukq/CurrencyRatesBot/actions/workflows/tests.yml)

An asynchronous Telegram bot for looking up and converting currency exchange rates. It uses the official National Bank of Ukraine (NBU) exchange rates, so UAH and 40+ other currencies are supported.

## Requirements

- Python 3.10+
- Docker and Docker Compose
- A Telegram bot token from [@BotFather](https://t.me/BotFather)

## Run with Docker Compose

```bash
git clone https://github.com/MariaLysiukq/CurrencyRatesBot.git
cd CurrencyRatesBot
cp .env.example .env
```

Edit `.env` and set your Telegram bot token:

```env
BOT_TOKEN=replace-with-your-telegram-bot-token
```

Keep `.env` private; do not commit real credentials.

Build and start the bot:

```bash
docker compose up --build -d
```

View its logs:

```bash
docker compose logs -f bot
```

Stop it:

```bash
docker compose down
```

## Exchange-rate source

The bot uses the official [National Bank of Ukraine API](https://bank.gov.ua/ua/open-data/api-dev) (no API key needed). Rates are expressed in UAH per unit, so any pair can be converted, for example USD → PLN.

- Live rates are cached in memory for 1 hour to avoid unnecessary requests.
- If the API is unavailable, the bot keeps using the last fetched rates.
- If no rates have been fetched yet, it falls back to `data/rates.json`.

`/rates` shows the value of 1 unit of your base currency in USD, EUR, PLN, GBP and UAH.

## Project structure

```text
.
├── src/currency_rates_bot/
│   ├── main.py
│   ├── handlers.py
│   ├── keyboards.py
│   └── storage.py
├── data/
├── tests/
├── .env.example
├── Dockerfile
└── docker-compose.yml
```

## Running tests

```bash
pip install -r requirements.txt pytest
pytest
```

The tests use fake Telegram and HTTP objects, so no bot token or network access is needed.

## Development checks

Install and run the configured pre-commit hooks:

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

## License

[MIT](LICENSE)
