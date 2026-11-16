import asyncio
from types import SimpleNamespace

import pytest

from currency_rates_bot import handlers, storage
from currency_rates_bot.storage import RateStorage


class FakeMessage:
    def __init__(self, text: str = ""):
        self.text = text
        self.replies: list[str] = []

    async def reply_text(self, text, reply_markup=None):
        self.replies.append(text)


def make_update(text: str = ""):
    return SimpleNamespace(
        message=FakeMessage(text),
        effective_user=SimpleNamespace(first_name="Test"),
    )


def make_context(args=None):
    return SimpleNamespace(user_data={}, args=args or [])


@pytest.fixture
def tmp_storage(tmp_path, monkeypatch):
    rate_storage = RateStorage()
    rate_storage.data_dir = tmp_path
    rate_storage.file_path = tmp_path / "rates.json"
    monkeypatch.setattr(handlers, "storage", rate_storage)
    return rate_storage


# --- storage -----------------------------------------------------------------

def test_save_and_load_rates_round_trip(tmp_storage):
    tmp_storage.save_rates({"UAH": 1.0, "USD": 41.5})

    assert tmp_storage.load_rates() == {"UAH": 1.0, "USD": 41.5}


def test_load_rates_returns_empty_dict_when_file_missing(tmp_storage):
    assert tmp_storage.load_rates() == {}


class FakeResponse:
    def __init__(self, status, payload):
        self.status = status
        self._payload = payload

    async def json(self):
        return self._payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False


class FakeSession:
    def __init__(self, response):
        self._response = response

    def get(self, url):
        return self._response

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False


def test_fetch_rates_adds_base_currency(monkeypatch):
    response = FakeResponse(200, {"rates": {"EUR": 0.9}})
    monkeypatch.setattr(storage.aiohttp, "ClientSession", lambda: FakeSession(response))

    rates = asyncio.run(storage.fetch_frankfurter_rates("USD"))

    assert rates == {"EUR": 0.9, "USD": 1.0}


def test_fetch_rates_returns_empty_dict_on_api_error(monkeypatch):
    response = FakeResponse(500, {})
    monkeypatch.setattr(storage.aiohttp, "ClientSession", lambda: FakeSession(response))

    assert asyncio.run(storage.fetch_frankfurter_rates("USD")) == {}


# --- handlers ----------------------------------------------------------------

def test_convert_command_calculates_and_records_history(tmp_storage):
    tmp_storage.save_rates({"UAH": 1.0, "USD": 40.0})
    update, context = make_update(), make_context(["10", "usd", "uah"])

    asyncio.run(handlers.cmd_convert(update, context))

    assert update.message.replies == ["💱 10.0 USD = 400.00 UAH"]
    assert context.user_data["history"] == ["10.0 USD = 400.00 UAH"]


def test_convert_command_rejects_non_numeric_amount(tmp_storage):
    update, context = make_update(), make_context(["ten", "USD", "UAH"])

    asyncio.run(handlers.cmd_convert(update, context))

    assert update.message.replies == ["Amount should be a number!"]


def test_history_keeps_last_five_conversions(tmp_storage):
    tmp_storage.save_rates({"UAH": 1.0, "USD": 40.0})
    context = make_context()

    for amount in range(1, 8):
        context.args = [str(amount), "USD", "UAH"]
        asyncio.run(handlers.cmd_convert(make_update(), context))

    assert len(context.user_data["history"]) == 5
    assert context.user_data["history"][0].startswith("3.0 USD")


def test_unknown_text_without_pending_action_shows_menu_hint():
    update, context = make_update("hello"), make_context()

    asyncio.run(handlers.on_text_message(update, context))

    assert update.message.replies == ["Choose the button or write a command"]


def test_step_by_step_conversion_flow(tmp_storage):
    tmp_storage.save_rates({"UAH": 1.0, "EUR": 50.0})
    context = make_context()

    for text in ["convert", "EUR", "UAH", "2"]:
        update = make_update(text)
        asyncio.run(handlers.on_text_message(update, context))

    assert update.message.replies == ["💱 2.0 EUR = 100.00 UAH"]
