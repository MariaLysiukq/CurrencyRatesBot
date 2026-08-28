# CurrencyRatesBot
An asynchronous Python service designed to track global currency exchange rates and broadcast real-time automated market alerts.

## Data Source & API
This bot fetches real-time and historical exchange rates using the [Frankfurter API](https://api.frankfurter.app/).

# Quick Start (Recommended)
1. Clone the repository
Download the project to your local machine and navigate into the folder:

```bash
git clone git@github.com:MariaLysiukq/CurrencyRatesBot.git
cd Currency-rates-bot
```

2. Set up configuration
Create your environment variables file from the provided example:
```bash
cp .env.example .env
```
Note: Open the .env file and replace the placeholder with your actual BOT_TOKEN obtained from @BotFather.

3. Build and run the bot
Start the container in detached mode (background):

```bash
docker compose up --build -d
```
    --build: Ensures Docker packages your latest code and dependencies.

    -d: Runs the bot silently in the background, freeing up your terminal.

# Project Structure

```text
Currency-rates-bot/
├── src/
│   └── currency_rates_bot/
│       ├── main.py        # Entry point for the application
│       ├── handlers.py    # Telegram command handlers
│       ├── keyboards.py   # Reply and Inline keyboards
│       └── storage.py     # Data management logic
├── data/                  # Persistent data storage (rates.json)
├── Dockerfile             # Multi-stage build instructions
├── docker-compose.yml     # Container orchestration
├── requirements.txt       # Python dependencies
└── .pre-commit-config.yaml# Code quality hooks

Development Guidelines

This project uses pre-commit to maintain clean and consistent code. Before making your first commit, please initialize the hooks:

    Ensure the package is installed: pip install pre-commit

    Install the git hooks: pre-commit install

    Run checks manually on all files: pre-commit run --all-files
```
