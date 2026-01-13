from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from html import escape

from .keyboards.menu import main_menu_kb

router = Router()

# Кнопки тарифов
paid_services_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="1 публикация — 500 ₽")],
        [KeyboardButton(text="3 публикации — 1000 ₽")],
        [KeyboardButton(text="Отмена")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

# Простое хранилище для выбора тарифов (для примера)
pending_paid = {}

# Кнопка "Платные услуги"
@router.message(F.text == "Платные услуги")
async def paid_services(message: types.Message):
    await message.answer(
        "Выберите тариф для платного размещения объявления:",
        reply_markup=paid_services_kb
    )

# Обработка выбора тарифа
@router.message(F.text.in_({"1 публикация — 500 ₽", "3 публикации — 1000 ₽"}))
async def handle_paid_choice(message: types.Message, state: FSMContext):
    username = message.from_user.username or message.from_user.full_name
    selected_tariff = message.text

    # Сохраняем выбор в хранилище
    pending_paid[username] = selected_tariff

    # Отправка в модерацию
    moderation_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Связаться с пользователем", callback_data=f"paid_contact:{username}"),
                InlineKeyboardButton(text="Одобрить", callback_data=f"paid_approve:{username}")
            ]
        ]
    )

    MODERATION_GROUP_ID = -1001986951886  # ID группы модерации

    await message.bot.send_message(
        chat_id=MODERATION_GROUP_ID,
        text=f"Пользователь @{username} выбрал тариф: {selected_tariff}",
        reply_markup=moderation_kb
    )

    # Ответ пользователю
    await message.answer(
        f"Вы выбрали: {selected_tariff}\n\nАдминистратор скоро с вами свяжется ✅",
        reply_markup=main_menu_kb()
    )

# Кнопка "Отмена"
@router.message(F.text == "Отмена")
async def cancel_paid_services(message: types.Message):
    await message.answer(
        "Вы вернулись в главное меню.",
        reply_markup=main_menu_kb()
    )


# --- Обработчики кнопок модератора ---

# Связаться с пользователем
@router.callback_query(F.data.startswith("paid_contact:"))
async def paid_contact(callback: types.CallbackQuery):
    username = callback.data.split(":")[1]
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(f"Свяжитесь с пользователем @{username} напрямую ✅")
    await callback.answer("Информация отправлена модератору")

# Одобрить тариф
@router.callback_query(F.data.startswith("paid_approve:"))
async def paid_approve(callback: types.CallbackQuery):
    username = callback.data.split(":")[1]
    tariff = pending_paid.pop(username, "неизвестный тариф")
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(f"Тариф @{username} ({tariff}) одобрен ✅")
    await callback.answer("Тариф одобрен")
