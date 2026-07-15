from telegram import KeyboardButton, ReplyKeyboardMarkup

MENU_HELP = "help"
MENU_RATES = "rates"
MENU_CONVERT = "convert"
MENU_HISTORY = "history"


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Creates and returns the main menu keyboard layout."""
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton(MENU_RATES), KeyboardButton(MENU_CONVERT)],
            [KeyboardButton(MENU_HELP), KeyboardButton(MENU_HISTORY)],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def currency_keyboard() -> ReplyKeyboardMarkup:
    """Show the buttons to the user"""
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("USD"), KeyboardButton("EUR")],
            [KeyboardButton("PLN"), KeyboardButton("GBP")],
            [KeyboardButton("UAH")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )
