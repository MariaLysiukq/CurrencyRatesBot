import json
import logging
from pathlib import Path

import aiohttp

logger = logging.getLogger(__name__)
Rates = dict[str, float]


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


async def fetch_frankfurter_rates(base: str = "USD") -> Rates:
    """Fetches latest currency extange rates from frankfurter API"""
    url = f"https://api.frankfurter.app/latest?from={base}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    rates = data.get("rates", {})
                    rates[base] = 1.0
                    return rates
                else:
                    logger.error("Frankfurter API returned status %s", response.status)
                    return {}
    except Exception as error:
        logger.error("Error fetching rates: %s", error)
    return {}
