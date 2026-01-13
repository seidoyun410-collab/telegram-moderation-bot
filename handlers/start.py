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
from html import escape

from .keyboards.menu import main_menu_kb

router = Router()

# FSM состояния
class OfferAdStates(StatesGroup):
    waiting_for_text = State()
    waiting_for_photos = State()
    waiting_for_reply = State()  # для модератора ответа пользователю

# Кнопки
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

# ID группы модерации и канала
MODERATION_GROUP_ID = -1001986951886  # числовой ID группы модерации
MAIN_CHANNEL_ID = -1001642154296      # числовой ID канала, бот должен быть админом

# Простая база заблокированных пользователей
blocked_users = set()

# Хранилище объявлений на модерации
pending_ads = {}


# /start
@router.message(Command("start"))
async def start_bot(message: types.Message):
    user_name = escape(message.from_user.full_name)
    text = f"""
Здравствуйте, {user_name}❕

В данном боте вы можете предложить свое объявление для публикации в <a href="https://t.me/vape_irk38">Вейп Барахолка | Иркутск</a>

Коммерческие посты публикуются только на платной основе, к ним относится:

<pre>
▫️ оптовая продажа  
▫️ продажа нового товара  
▫️ продажа одноразок и жидкостей  
▫️ реклама магазина / вейпшопа
</pre>

Если вы хотите приобрести рекламу, жмите на кнопку "Платные услуги"❗
"""
    await message.answer(text, reply_markup=main_menu_kb(), parse_mode="HTML")


# "Предложить объявление"
@router.message(F.text == "Предложить объявление")
async def offer_ad(message: types.Message, state: FSMContext):
    if message.from_user.id in blocked_users:
        await message.answer("Вы заблокированы и не можете отправлять объявления ❌")
        return
    await message.answer("Круто! Пришли мне текст своего объявления!", reply_markup=cancel_kb)
    await state.set_state(OfferAdStates.waiting_for_text)


# Отмена (из любого состояния)
@router.message(F.text == "Отмена")
async def cancel_process(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Процесс отменён. Возвращаемся в главное меню.", reply_markup=main_menu_kb())


# Получение текста объявления
@router.message(OfferAdStates.waiting_for_text)
async def receive_ad_text(message: types.Message, state: FSMContext):
    ad_text = f"{message.text}\n\nСвязаться с продавцом @{message.from_user.username or 'username'}"
    await state.update_data(ad_text=ad_text, photos=[], user_id=message.from_user.id)
    await message.answer(
        f"Отлично! Вот текст твоего объявления с контактом:\n\n{ad_text}\n\nТеперь пришли фото объявления. "
        "Можно прислать несколько фото. Когда закончишь — нажми 'Готово'.",
        reply_markup=photo_kb
    )
    await state.set_state(OfferAdStates.waiting_for_photos)


# Получение фото
@router.message(OfferAdStates.waiting_for_photos, F.photo)
async def receive_ad_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])
    photos.append(message.photo[-1].file_id)  # добавляем последнее фото (большой размер)
    await state.update_data(photos=photos)
    await message.answer(f"Фото добавлено! Всего фото: {len(photos)}", reply_markup=photo_kb)


# Завершение отправки объявления
@router.message(F.text == "Готово")
async def finish_ad(message: types.Message, state: FSMContext):
    data = await state.get_data()
    ad_text = data.get("ad_text")
    photos = data.get("photos", [])
    user_id = data.get("user_id")

    # Определяем, заблокирован пользователь или нет, чтобы кнопка корректно отображалась
    block_button_text = "Разблокировать" if user_id in blocked_users else "Заблокировать"
    block_callback = "unblock" if user_id in blocked_users else "block"

    # Кнопки модерации
    moderation_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Опубликовать", callback_data=f"publish:{user_id}"),
                InlineKeyboardButton(text="Ответить", callback_data=f"reply:{user_id}"),
                InlineKeyboardButton(text=block_button_text, callback_data=f"{block_callback}:{user_id}")
            ]
        ]
    )

    # Сохраняем объявление для модератора
    pending_ads[user_id] = {"text": ad_text, "photos": photos}

    # Отправка на модерацию
    if photos:
        media = [InputMediaPhoto(media=photo_id) for photo_id in photos]
        media[0].caption = ad_text
        await message.bot.send_media_group(chat_id=MODERATION_GROUP_ID, media=media)
        await message.bot.send_message(chat_id=MODERATION_GROUP_ID, text="Действия для модерации:", reply_markup=moderation_kb)
    else:
        await message.bot.send_message(chat_id=MODERATION_GROUP_ID, text=ad_text, reply_markup=moderation_kb)

    await message.answer("Твое объявление отправлено на модерацию ✅", reply_markup=main_menu_kb())
    await state.clear()


# Публикация в канал
@router.callback_query(F.data.startswith("publish:"))
async def publish_ad(callback: types.CallbackQuery):
    user_id = int(callback.data.split(":")[1])

    ad = pending_ads.get(user_id)
    if not ad:
        await callback.answer("Ошибка: нет данных для публикации!", show_alert=True)
        return

    ad_text = ad.get("text")
    photos = ad.get("photos", [])

    try:
        if not photos:
            await callback.bot.send_message(chat_id=MAIN_CHANNEL_ID, text=ad_text)
        elif len(photos) == 1:
            await callback.bot.send_photo(chat_id=MAIN_CHANNEL_ID, photo=photos[0], caption=ad_text)
        else:
            media = [InputMediaPhoto(media=photo, caption=ad_text if i == 0 else None) for i, photo in enumerate(photos)]
            await callback.bot.send_media_group(chat_id=MAIN_CHANNEL_ID, media=media)

        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.bot.send_message(chat_id=MODERATION_GROUP_ID, text="Объявление опубликовано ✅")
        await callback.answer("Объявление опубликовано в канал!")

        pending_ads.pop(user_id, None)

    except Exception as e:
        await callback.answer(f"Ошибка при публикации: {e}", show_alert=True)


# Ответ модератора пользователю
@router.callback_query(F.data.startswith("reply:"))
async def reply_user(callback: types.CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split(":")[1])
    await state.update_data(reply_user_id=user_id)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Напиши сообщение пользователю, оно будет отправлено напрямую.")
    await state.set_state(OfferAdStates.waiting_for_reply)
    await callback.answer()


@router.message(OfferAdStates.waiting_for_reply)
async def send_reply_to_user(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("reply_user_id")
    await message.bot.send_message(chat_id=user_id, text=f"Модератор: {message.text}")
    await message.answer("Сообщение отправлено пользователю ✅", reply_markup=main_menu_kb())
    await state.clear()


# Блокировка / Разблокировка пользователя
@router.callback_query(F.data.startswith("block:") | F.data.startswith("unblock:"))
async def toggle_block_user(callback: types.CallbackQuery):
    action, user_id_str = callback.data.split(":")
    user_id = int(user_id_str)

    if action == "block":
        blocked_users.add(user_id)
        new_text = "Разблокировать"
        new_action = "unblock"
        result_text = "Пользователь заблокирован 🚫"
    else:  # unblock
        blocked_users.discard(user_id)
        new_text = "Заблокировать"
        new_action = "block"
        result_text = "Пользователь разблокирован ✅"

    # Обновляем кнопки в сообщении модерации
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Опубликовать", callback_data=f"publish:{user_id}"),
                InlineKeyboardButton(text="Ответить", callback_data=f"reply:{user_id}"),
                InlineKeyboardButton(text=new_text, callback_data=f"{new_action}:{user_id}")
            ]
        ]
    )

    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer(result_text)
