import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID")
ADMIN_ID = [int(id) for id in os.getenv("ADMIN_ID").split(",")]