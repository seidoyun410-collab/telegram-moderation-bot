import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties
from aiohttp import ClientConnectorError, ServerDisconnectedError
from handlers import register_routes
from config import TEST_BOT_TOKEN

TOKEN = "8672189204:AAGrnnuODcgFbni7TV_LmdGagRN1sowyEVI"

async def main():
    #bot = Bot(token=TEST_BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    bot = Bot(
        token=TOKEN,
        default=DefaultBotProperties(parse_mode="HTML")  # Для HTML разметки
    )
    dp = Dispatcher()

    register_routes(dp)

    print("Бот запущен! Ожидание обновлений...")

    try:
        while True:
            try:
                await dp.start_polling(bot)
            except (ServerDisconnectedError, ClientConnectorError) as e:
                print(f"[!] Ошибка соединения: {e}. Переподключение через 1 секунду...")
                await asyncio.sleep(1)
            except Exception as e:
                print(f"[!] Неожиданная ошибка: {e}. Перезапуск через 1 секунду...")
                await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Бот остановлен пользователем!")
    finally:
        # Всегда закрываем сессию бота
        await bot.session.close()
        print("Сессия бота закрыта. Выход...")

if __name__ == "__main__":
    asyncio.run(main())
