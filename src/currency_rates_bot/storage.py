import json
import logging
import time
from collections.abc import Awaitable, Callable
from pathlib import Path

import aiohttp

logger = logging.getLogger(__name__)

# Exchange rates expressed as "UAH per one unit of currency" (UAH itself is 1.0).
Rates = dict[str, float]

NBU_RATES_URL = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json"
REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=10)


class RateStorage:
    def __init__(self, file_name: str = "rates.json"):
        self.base_dir = Path(__file__).resolve().parent.parent.parent
        self.data_dir = self.base_dir / "data"
        self.file_path = self.data_dir / file_name

    def load_rates(self) -> Rates:
        """Loads exchange rates from the local json"""
        if not self.file_path.exists():
            logger.warning("Rates file not found: %s", self.file_path)
            return {}
        with self.file_path.open(encoding='utf-8') as file:
            return json.load(file)

    def save_rates(self, rates: Rates) -> None:
        """Saves the provided exchange to the local json"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        with self.file_path.open('w', encoding='utf-8') as file:
            json.dump(rates, file, ensure_ascii=False, indent=2)
        logger.info("Rates saved successfully to %s", self.file_path.name)


async def fetch_nbu_rates() -> Rates:
    """Fetches the official National Bank of Ukraine rates (UAH per unit)."""
    try:
        async with aiohttp.ClientSession(timeout=REQUEST_TIMEOUT) as session:
            async with session.get(NBU_RATES_URL) as response:
                if response.status != 200:
                    logger.error("NBU API returned status %s", response.status)
                    return {}
                data = await response.json()
    except Exception as error:
        logger.error("Error fetching rates: %s", error)
        return {}

    rates: Rates = {"UAH": 1.0}
    for item in data:
        code, rate = item.get("cc"), item.get("rate")
        if code and rate:
            rates[code] = float(rate)
    return rates


class RateProvider:
    """Returns live rates, cached for `ttl_seconds`.

    If the API is unavailable, the last successfully fetched rates are used,
    and if there are none yet, the bundled `data/rates.json` file.
    """

    def __init__(
        self,
        storage: RateStorage,
        fetcher: Callable[[], Awaitable[Rates]] = fetch_nbu_rates,
        ttl_seconds: float = 3600,
        clock: Callable[[], float] = time.monotonic,
    ):
        self.storage = storage
        self.fetcher = fetcher
        self.ttl_seconds = ttl_seconds
        self.clock = clock
        self._rates: Rates = {}
        self._fetched_at: float | None = None

    async def get_rates(self) -> Rates:
        if self._fetched_at is not None and self.clock() - self._fetched_at < self.ttl_seconds:
            return self._rates

        rates = await self.fetcher()
        if rates:
            self._rates = rates
            self._fetched_at = self.clock()
            return rates

        if self._rates:
            logger.warning("Using previously fetched rates")
            return self._rates

        logger.warning("Using fallback rates from %s", self.storage.file_path.name)
        return self.storage.load_rates()


def convert(amount: float, from_curr: str, to_curr: str, rates: Rates) -> float:
    """Converts `amount` using rates expressed in UAH per unit."""
    return amount * rates[from_curr] / rates[to_curr]
