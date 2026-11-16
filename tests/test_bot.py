import asyncio
from types import SimpleNamespace

import pytest

from currency_rates_bot import handlers, storage
from currency_rates_bot.storage import RateProvider, RateStorage, convert


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


def make_context(args=None, user_data=None):
    return SimpleNamespace(user_data=user_data or {}, args=args or [])


@pytest.fixture
def tmp_storage(tmp_path):
    rate_storage = RateStorage()
    rate_storage.data_dir = tmp_path
    rate_storage.file_path = tmp_path / "rates.json"
    return rate_storage


@pytest.fixture
def live_rates(monkeypatch, tmp_storage):
    """Make the handlers use fixed "live" rates instead of calling the NBU API."""
    rates = {"UAH": 1.0, "USD": 40.0, "EUR": 50.0}

    async def fetcher():
        return rates

    monkeypatch.setattr(handlers, "rate_provider", RateProvider(tmp_storage, fetcher=fetcher))
    return rates


# --- storage -----------------------------------------------------------------

def test_save_and_load_rates_round_trip(tmp_storage):
    tmp_storage.save_rates({"UAH": 1.0, "USD": 41.5})

    assert tmp_storage.load_rates() == {"UAH": 1.0, "USD": 41.5}


def test_load_rates_returns_empty_dict_when_file_missing(tmp_storage):
    assert tmp_storage.load_rates() == {}


def test_convert_uses_uah_per_unit_rates():
    rates = {"UAH": 1.0, "USD": 40.0, "EUR": 50.0}

    assert convert(10, "USD", "UAH", rates) == 400
    assert convert(400, "UAH", "USD", rates) == 10
    assert convert(4, "EUR", "USD", rates) == 5


# --- NBU API -----------------------------------------------------------------

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


def patch_session(monkeypatch, response):
    monkeypatch.setattr(storage.aiohttp, "ClientSession", lambda **kwargs: FakeSession(response))


def test_fetch_nbu_rates_parses_response_and_adds_uah(monkeypatch):
    payload = [
        {"cc": "USD", "rate": 41.5, "txt": "Долар США"},
        {"cc": "EUR", "rate": 45.25, "txt": "Євро"},
    ]
    patch_session(monkeypatch, FakeResponse(200, payload))

    rates = asyncio.run(storage.fetch_nbu_rates())

    assert rates == {"UAH": 1.0, "USD": 41.5, "EUR": 45.25}


def test_fetch_nbu_rates_returns_empty_dict_on_api_error(monkeypatch):
    patch_session(monkeypatch, FakeResponse(500, []))

    assert asyncio.run(storage.fetch_nbu_rates()) == {}


# --- RateProvider ------------------------------------------------------------

def test_provider_caches_rates_until_ttl_expires(tmp_storage):
    calls = []
    now = [0.0]

    async def fetcher():
        calls.append(1)
        return {"UAH": 1.0, "USD": 40.0 + len(calls)}

    provider = RateProvider(tmp_storage, fetcher=fetcher, ttl_seconds=60, clock=lambda: now[0])

    first = asyncio.run(provider.get_rates())
    now[0] = 30
    cached = asyncio.run(provider.get_rates())
    now[0] = 61
    refreshed = asyncio.run(provider.get_rates())

    assert first == cached == {"UAH": 1.0, "USD": 41.0}
    assert refreshed == {"UAH": 1.0, "USD": 42.0}
    assert len(calls) == 2


def test_provider_keeps_last_rates_when_api_fails(tmp_storage):
    responses = [{"UAH": 1.0, "USD": 40.0}, {}]
    now = [0.0]

    async def fetcher():
        return responses.pop(0)

    provider = RateProvider(tmp_storage, fetcher=fetcher, ttl_seconds=60, clock=lambda: now[0])
    asyncio.run(provider.get_rates())
    now[0] = 120

    assert asyncio.run(provider.get_rates()) == {"UAH": 1.0, "USD": 40.0}


def test_provider_falls_back_to_rates_file(tmp_storage):
    tmp_storage.save_rates({"UAH": 1.0, "PLN": 11.0})

    async def fetcher():
        return {}

    provider = RateProvider(tmp_storage, fetcher=fetcher)

    assert asyncio.run(provider.get_rates()) == {"UAH": 1.0, "PLN": 11.0}


# --- handlers ----------------------------------------------------------------

def test_convert_command_uses_live_rates_and_records_history(live_rates):
    update, context = make_update(), make_context(["10", "usd", "uah"])

    asyncio.run(handlers.cmd_convert(update, context))

    assert update.message.replies == ["💱 10.0 USD = 400.00 UAH"]
    assert context.user_data["history"] == ["10.0 USD = 400.00 UAH"]


def test_convert_command_rejects_non_numeric_amount(live_rates):
    update, context = make_update(), make_context(["ten", "USD", "UAH"])

    asyncio.run(handlers.cmd_convert(update, context))

    assert update.message.replies == ["Amount should be a number!"]


def test_convert_command_rejects_unknown_currency(live_rates):
    update, context = make_update(), make_context(["1", "USD", "XYZ"])

    asyncio.run(handlers.cmd_convert(update, context))

    assert update.message.replies == ["Rates not available for the given currencies."]


def test_history_keeps_last_five_conversions(live_rates):
    context = make_context()

    for amount in range(1, 8):
        context.args = [str(amount), "USD", "UAH"]
        asyncio.run(handlers.cmd_convert(make_update(), context))

    assert len(context.user_data["history"]) == 5
    assert context.user_data["history"][0].startswith("3.0 USD")


def test_rates_command_works_with_uah_base(live_rates):
    update, context = make_update(), make_context(user_data={"base_currency": "UAH"})

    asyncio.run(handlers.cmd_rates(update, context))

    reply = update.message.replies[0]
    assert "Base: UAH" in reply
    assert "USD: 0.0250" in reply
    assert "EUR: 0.0200" in reply


def test_rates_command_with_usd_base(live_rates):
    update, context = make_update(), make_context(user_data={"base_currency": "USD"})

    asyncio.run(handlers.cmd_rates(update, context))

    reply = update.message.replies[0]
    assert "UAH: 40.0000" in reply
    assert "EUR: 0.8000" in reply
    assert "USD:" not in reply


def test_rates_command_rejects_unknown_base(live_rates):
    update, context = make_update(), make_context(user_data={"base_currency": "XYZ"})

    asyncio.run(handlers.cmd_rates(update, context))

    assert update.message.replies == ["Rates are not available for XYZ. Choose another base currency."]


def test_unknown_text_without_pending_action_shows_menu_hint():
    update, context = make_update("hello"), make_context()

    asyncio.run(handlers.on_text_message(update, context))

    assert update.message.replies == ["Choose the button or write a command"]


def test_step_by_step_conversion_flow(live_rates):
    context = make_context()

    for text in ["convert", "EUR", "UAH", "2"]:
        update = make_update(text)
        asyncio.run(handlers.on_text_message(update, context))

    assert update.message.replies == ["💱 2.0 EUR = 100.00 UAH"]
