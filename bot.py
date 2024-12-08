import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
from config import BOT_TOKEN
from db import create_tables
from handlers import admin, user

# Set up logging
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())

# Create tables on start
create_tables()

# Register handlers
admin.register_admin_handlers(dp)
user.register_user_handlers(dp)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
