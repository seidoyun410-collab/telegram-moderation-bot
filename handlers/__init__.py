from aiogram import Dispatcher

from handlers.start import router as start_router
from handlers.paid_services import router as paid_services_router  # подключаем новый роутер

def register_routes(dp: Dispatcher):
    dp.include_router(start_router)
    dp.include_router(paid_services_router)  # подключаем платные услуги

    