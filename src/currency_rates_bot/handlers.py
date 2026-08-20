from telegram import ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes

from .keyboards import MENU_CONVERT, MENU_HELP, MENU_HISTORY, MENU_RATES, currency_keyboard, main_menu_keyboard
from .storage import RateStorage, fetch_frankfurter_rates

_HELP_TEXT = (
    "Available commands:\n\n"
    "Show current exchange rates - /rates\n"
    "Converting - /convert <amount> <from> <to>\n"
    "Show last 5 operations - /history\n"
)

_PENDING_ACTION_KEY = "pending_menu_action"
storage = RateStorage()


def _clear_pending_action(context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.pop(_PENDING_ACTION_KEY, None)


async def _reply_with_menu(update: Update, text: str) -> None:
    await update.message.reply_text(text, reply_markup=main_menu_keyboard())


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _clear_pending_action(context)
    user_name = update.effective_user.first_name
    context.user_data[_PENDING_ACTION_KEY] = "set_base_currency"

    await update.message.reply_text(
        f"Hi, {user_name}!\n\n"
        "Welcome to the Currency Cat Bot. Before we start, choose your base currency:",
        reply_markup=currency_keyboard()
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _clear_pending_action(context)
    await _reply_with_menu(update, _HELP_TEXT)


async def cmd_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _clear_pending_action(context)
    history = context.user_data.get("history", [])
    if not history:
        await _reply_with_menu(update, "Your history is empty. Try converting some currencies first!")
        return
    history_lines = [f" {i + 1}. {item} " for i, item in enumerate(history)]
    history_text = "Your last 5 conversions:\n\n" + "\n".join(history_lines)
    await _reply_with_menu(update, history_text)


async def cmd_rates(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _clear_pending_action(context)
    base_currency = context.user_data.get("base_currency", "EUR")
    rates = await fetch_frankfurter_rates(base=base_currency)
    if not rates:
        await _reply_with_menu(update, "Currency rates not available at the moment.")
        return
    rates_lines = []
    for currency, rate in rates.items():
        if currency != base_currency:
            rates_lines.append(f"{currency}: {rate}")
    await _reply_with_menu(update, f"Current rates (Base: {base_currency}):\n\n" + "\n".join(rates_lines))


async def cmd_convert(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _clear_pending_action(context)
    if len(context.args) != 3:
        await _reply_with_menu(update, "Enter in this format: /convert <amount> <from> <to>\n")
        return
    amount_str, from_curr, to_curr = context.args
    from_curr, to_curr = from_curr.upper(), to_curr.upper()
    try:
        amount = float(amount_str)
    except ValueError:
        await _reply_with_menu(update, "Amount should be a number!")
        return

    rates = storage.load_rates()
    if from_curr not in rates or to_curr not in rates:
        await _reply_with_menu(update, "Rates not available for the given currencies.")
        return
    result = (amount * rates[from_curr]) / rates[to_curr]
    result_text = f"{amount} {from_curr} = {result:.2f} {to_curr}"

    if "history" not in context.user_data:
        context.user_data["history"] = []
    context.user_data["history"].append(result_text)
    context.user_data["history"] = context.user_data["history"][-5:]
    await _reply_with_menu(update, f"💱 {result_text}")


async def _handle_convert_amount(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    """Helper: Processes the final math and history saving for currency conversion."""
    if not text.replace('.', '', 1).isdigit():
        await update.message.reply_text("Amount should be a number! Try again:")
        return

    amount = float(text)
    from_curr = context.user_data.get("convert_from_curr")
    to_curr = context.user_data.get("convert_to_curr")

    rates = storage.load_rates()
    if from_curr not in rates or to_curr not in rates:
        await _reply_with_menu(update, "Rates not available for the given currencies.")
        _clear_pending_action(context)
        return
    result = (amount * rates[from_curr]) / rates[to_curr]
    result_text = f"{amount} {from_curr} = {result:.2f} {to_curr}"
    history = context.user_data.setdefault("history", [])
    history.append(result_text)
    context.user_data["history"] = history[-5:]
    await _reply_with_menu(update, f"💱 {result_text}")
    _clear_pending_action(context)


async def _process_pending_action(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str, text: str) -> bool:
    """Routes the user through the step-by-step conversation"""
    if action == "set_base_currency":
        chosen_currency = text.upper()
        context.user_data["base_currency"] = chosen_currency
        _clear_pending_action(context)
        await _reply_with_menu(
            update,
            f"Great! Your base currency is set to {chosen_currency}.\n\n" + _HELP_TEXT
        )
        return True
    if action == "convert_from":
        context.user_data["convert_from_curr"] = text.upper()
        context.user_data[_PENDING_ACTION_KEY] = "convert_to"
        await update.message.reply_text("To which currency:", reply_markup=currency_keyboard())
        return True
    if action == "convert_to":
        context.user_data["convert_to_curr"] = text.upper()
        context.user_data[_PENDING_ACTION_KEY] = "convert_amount"
        await update.message.reply_text("Enter the amount:", reply_markup=ReplyKeyboardRemove())
        return True
    if action == "convert_amount":
        await _handle_convert_amount(update, context, text)
        return True
    return False


async def on_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Hendlers incoming message from user"""
    text = update.message.text.strip()
    pending_action = context.user_data.get(_PENDING_ACTION_KEY)
    _clear_pending_action(context)

    if text == MENU_HELP:
        await cmd_help(update, context)
        return
    elif text == MENU_HISTORY:
        await cmd_history(update, context)
        return
    elif text == MENU_RATES:
        await cmd_rates(update, context)
        return
    elif text == MENU_CONVERT:
        context.user_data[_PENDING_ACTION_KEY] = "convert_from"
        await update.message.reply_text("From which currency:", reply_markup=currency_keyboard())
        return
    if pending_action == "set_base_currency":
        chosen_currency = text.upper()
        context.user_data["base_currency"] = chosen_currency
        _clear_pending_action(context)
        await _reply_with_menu(
            update,
            f"Great! Your base currency is set to {chosen_currency}.\n\n" + _HELP_TEXT
        )
        return
    if pending_action == "convert_from":
        context.user_data["convert_from_curr"] = text.upper()
        context.user_data[_PENDING_ACTION_KEY] = "convert_to"
        await update.message.reply_text("To which currency:", reply_markup=currency_keyboard())
        return
    if pending_action == "convert_to":
        context.user_data["convert_to_curr"] = text.upper()
        context.user_data[_PENDING_ACTION_KEY] = "convert_amount"
        await update.message.reply_text("Enter the amount:", reply_markup=ReplyKeyboardRemove())
        return
    if pending_action:
        handled = await _process_pending_action(update, context, pending_action, text)
    if handled:
        return

    _clear_pending_action(context)
    await _reply_with_menu(update, "Choose the button or write a command")
