from setuptools import find_packages, setup

setup(
    name="currency-rates-bot",
    version="0.1.0",
    description="Telegram bot for currency exchange rates and conversion",
    author="Maria Lysiuk",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.10",
    install_requires=[
        "python-telegram-bot>=20.0",
        "python-dotenv",
        "aiohttp",
    ],
)
