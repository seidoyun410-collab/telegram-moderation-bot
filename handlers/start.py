import json
import os
from uuid import uuid4
from datetime import datetime, timedelta
from html import escape

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputMediaPhoto
)

from .keyboards.menu import main_menu_kb  # твой существующий файл с главным меню

router = Router()

# -------------------------
# FSM состояния
# -------------------------
class OfferAdStates(StatesGroup):
    waiting_for_category = State()
    waiting_for_text = State()
    waiting_for_photos = State()
    waiting_for_reply = State()  # для модератора ответа пользователю

# -------------------------
# Кнопки
# -------------------------
cancel_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Отмена")]],
    resize_keyboard=True,
    one_time_keyboard=True
)

photo_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Готово")], [KeyboardButton(text="Отмена")]],
    resize_keyboard=True,
    one_time_keyboard=True
)

# -------------------------
# Категории
# -------------------------
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

# -------------------------
# ID группы модерации и канала
# -------------------------
MODERATION_GROUP_ID = -1001986951886  # числовой ID группы модерации
MAIN_CHANNEL_ID = -1001642154296   # числовой ID канала, бот должен быть админом

# -------------------------
# Блокировка пользователей
# -------------------------
blocked_users = set()

# -------------------------
# JSON хранилище объявлений
# -------------------------
ADS_JSON_FILE = "pending_ads.json"
AD_EXPIRATION_DAYS = 7  # старые объявления удаляются через 7 дней

def cleanup_old_ads(json_ads: dict) -> dict:
    """Удаляет объявления старше AD_EXPIRATION_DAYS"""
    now = datetime.now()
    new_ads = {}
    for ad_id, ad in json_ads.items():
        ad_time = datetime.fromisoformat(ad.get("timestamp"))
        if now - ad_time <= timedelta(days=AD_EXPIRATION_DAYS):
            new_ads[ad_id] = ad
    return new_ads

def load_pending_ads():
    if not os.path.exists(ADS_JSON_FILE):
        return {}
    with open(ADS_JSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    data = cleanup_old_ads(data)
    save_pending_ads(data)
    return data

def save_pending_ads(data):
    data = cleanup_old_ads(data)
    with open(ADS_JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# -------------------------
# /start
# -------------------------
@router.message(Command("start"))
async def start_bot(message: types.Message):
    user_name = escape(message.from_user.full_name)
    text = f"""
Здравствуйте, {user_name}! 👋

Добро пожаловать в бот предложки канала 
<a href="https://t.me/baraholka_irk38">Барахолка | Иркутск</a>

Здесь вы можете предложить своё объявление для публикации в канале.

<pre>
📦 Продажа вещей
🔄 Обмен и отдам даром
🛒 Покупка
</pre>

Чтобы предложить объявление — нажмите кнопку 
<b>"Предложить объявление"</b> в меню ниже.

После отправки объявление отправится на модерацию.
Если всё в порядке — оно будет опубликовано в канале.

❗ Пожалуйста, указывайте:
• понятное описание товара  
• стоимость  
• реальные фотографии
"""
    await message.answer(text, reply_markup=main_menu_kb(), parse_mode="HTML")

# -------------------------
# Предложить объявление → выбор категории
# -------------------------
@router.message(F.text == "Предложить объявление")
async def offer_ad(message: types.Message, state: FSMContext):
    if message.from_user.id in blocked_users:
        await message.answer("Вы заблокированы и не можете отправлять объявления ❌")
        return
    await message.answer("Сначала выбери категорию своего объявления:", reply_markup=categories_keyboard)
    await state.set_state(OfferAdStates.waiting_for_category)

# -------------------------
# Выбор категории
# -------------------------
@router.callback_query(F.data.startswith("cat_"))
async def choose_category(callback: types.CallbackQuery, state: FSMContext):
    category_map = {
        "cat_electronics": ("📱 Электроника", "электроника"),
        "cat_clothes": ("👕 Одежда", "одежда"),
        "cat_furniture": ("🪑 Мебель", "мебель"),
        "cat_auto": ("🚗 Авто", "авто"),
        "cat_realty": ("🏠 Недвижимость", "недвижимость"),
        "cat_job": ("💼 Работа", "работа"),
        "cat_services": ("🛠 Услуги", "услуги"),
        "cat_hobby": ("🎮 Хобби", "хобби"),
        "cat_other": ("📦 Разное", "разное")
    }
    category_name, category_tag = category_map.get(callback.data, ("", "other"))
    await state.update_data(category_name=category_name, category_tag=category_tag)
    await callback.message.edit_reply_markup()
    await callback.message.answer(f"Отлично! Ты выбрал категорию: {category_name}\nТеперь пришли текст своего объявления.", reply_markup=cancel_kb)
    await state.set_state(OfferAdStates.waiting_for_text)
    await callback.answer()

# -------------------------
# Отмена
# -------------------------
@router.message(F.text == "Отмена")
async def cancel_process(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Процесс отменён. Возвращаемся в главное меню.", reply_markup=main_menu_kb())

# -------------------------
# Ввод текста объявления
# -------------------------
@router.message(OfferAdStates.waiting_for_text)
async def receive_ad_text(message: types.Message, state: FSMContext):
    data = await state.get_data()
    category_name = data.get("category_name", "")
    category_tag = data.get("category_tag", "other")
    user_contact = f"@{message.from_user.username}" if message.from_user.username else "Написать через Telegram"

    ad_text = (
        f"{category_name}\n\n"
        f"📝 <b>Описание</b>:\n{message.text}\n\n"
        f"👤 <b>Продавец</b>: {user_contact}\n\n"
        f"#{category_tag} #барахолка_иркутск"
    )

    await state.update_data(ad_text=ad_text, photos=[], user_id=message.from_user.id)
    await message.answer(f"Отлично! Вот текст твоего объявления:\n\n{ad_text}\n\nТеперь пришли фото объявления (до 10). Когда закончишь — нажми 'Готово'.", reply_markup=photo_kb)
    await state.set_state(OfferAdStates.waiting_for_photos)

# -------------------------
# Получение фото (до 10)
# -------------------------
@router.message(OfferAdStates.waiting_for_photos, F.photo)
async def receive_ad_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])
    if len(photos) >= 10:
        await message.answer("❌ Максимальное количество фото — 10.")
        return
    photos.append(message.photo[-1].file_id)
    await state.update_data(photos=photos)
    await message.answer(f"Фото добавлено! Всего фото: {len(photos)}", reply_markup=photo_kb)

# -------------------------
# Завершение и сохранение в JSON
# -------------------------
@router.message(F.text == "Готово")
async def finish_ad(message: types.Message, state: FSMContext):
    data = await state.get_data()
    ad_text = data.get("ad_text")
    photos = data.get("photos", [])
    user_id = data.get("user_id")

    ad_id = str(uuid4())
    timestamp = datetime.now().isoformat()
    json_ads = load_pending_ads()
    json_ads[ad_id] = {
        "user_id": user_id,
        "ad_text": ad_text,
        "photos": photos,
        "timestamp": timestamp
    }
    save_pending_ads(json_ads)

    block_button_text = "Разблокировать" if user_id in blocked_users else "Заблокировать"
    block_callback = "unblock" if user_id in blocked_users else "block"

    moderation_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Опубликовать", callback_data=f"publish:{ad_id}"),
                InlineKeyboardButton(text="Ответить", callback_data=f"reply:{user_id}"),
                InlineKeyboardButton(text=block_button_text, callback_data=f"{block_callback}:{user_id}")
            ]
        ]
    )

    if photos:
        media = [InputMediaPhoto(media=photo_id) for photo_id in photos]
        media[0].caption = ad_text
        await message.bot.send_media_group(chat_id=MODERATION_GROUP_ID, media=media)
        await message.bot.send_message(chat_id=MODERATION_GROUP_ID, text="Действия для модерации:", reply_markup=moderation_kb)
    else:
        await message.bot.send_message(chat_id=MODERATION_GROUP_ID, text=ad_text, reply_markup=moderation_kb)

    await message.answer("Твое объявление отправлено на модерацию ✅", reply_markup=main_menu_kb())
    await state.clear()

# -------------------------
# Публикация объявления и удаление из JSON
# -------------------------
@router.callback_query(F.data.startswith("publish:"))
async def publish_ad(callback: types.CallbackQuery):
    ad_id = callback.data.split(":")[1]
    json_ads = load_pending_ads()
    ad = json_ads.get(ad_id)
    if not ad:
        await callback.answer("Ошибка: объявление не найдено!", show_alert=True)
        return

    ad_text = ad.get("ad_text")
    photos = ad.get("photos", [])
    user_id = ad.get("user_id")

    try:
        if not photos:
            await callback.bot.send_message(chat_id=MAIN_CHANNEL_ID, text=ad_text)
        elif len(photos) == 1:
            await callback.bot.send_photo(chat_id=MAIN_CHANNEL_ID, photo=photos[0], caption=ad_text)
        else:
            media = [InputMediaPhoto(media=photo, caption=ad_text if i == 0 else None)
                     for i, photo in enumerate(photos)]
            await callback.bot.send_media_group(chat_id=MAIN_CHANNEL_ID, media=media)

        # удаляем объявление из JSON
        json_ads.pop(ad_id)
        save_pending_ads(json_ads)

        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.bot.send_message(chat_id=MODERATION_GROUP_ID, text="Объявление опубликовано ✅")
        await callback.answer("Объявление опубликовано в канал!")

    except Exception as e:
        await callback.answer(f"Ошибка при публикации: {e}", show_alert=True)