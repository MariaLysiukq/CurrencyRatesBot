# Currency Rates Bot

An asynchronous Telegram bot for looking up and converting currency exchange rates. The project uses the Frankfurter API as its exchange-rate data source.

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

The bot uses the [Frankfurter API](https://api.frankfurter.app/). No Frankfurter API key is listed as required by the current project configuration.

## Project structure

```text
.
├── src/currency_rates_bot/
│   ├── main.py
│   ├── handlers.py
│   ├── keyboards.py
│   └── storage.py
├── data/
├── .env.example
├── Dockerfile
└── docker-compose.yml
```

## Development checks

Install and run the configured pre-commit hooks:

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```
