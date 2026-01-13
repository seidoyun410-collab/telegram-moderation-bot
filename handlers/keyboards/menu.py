from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def main_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Предложить объявление")],
            [KeyboardButton(text="Платные услуги")]
        ]
    )