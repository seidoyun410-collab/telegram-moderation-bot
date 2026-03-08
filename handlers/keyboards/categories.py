from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

categories_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="📱 Электроника", callback_data="cat_electronics"),
            InlineKeyboardButton(text="👕 Одежда", callback_data="cat_clothes")
        ],
        [
            InlineKeyboardButton(text="🪑 Мебель", callback_data="cat_furniture"),
            InlineKeyboardButton(text="🚗 Авто", callback_data="cat_auto")
        ],
        [
            InlineKeyboardButton(text="🏠 Недвижимость", callback_data="cat_realty"),
            InlineKeyboardButton(text="💼 Работа", callback_data="cat_job")
        ],
        [
            InlineKeyboardButton(text="🛠 Услуги", callback_data="cat_services"),
            InlineKeyboardButton(text="🎮 Хобби", callback_data="cat_hobby")
        ],
        [
            InlineKeyboardButton(text="📦 Разное", callback_data="cat_other")
        ]
    ]
)