import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties
from aiohttp import ClientConnectorError, ServerDisconnectedError
from handlers import register_routes

TOKEN = "8517916697:AAEqL4pQIMXVw04S07qJZrWgq3riABajTVI"

async def main():
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
