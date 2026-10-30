from os import getenv, path
from dotenv import load_dotenv

load_dotenv(path.join(path.dirname(__file__), ".env"))

# REQUIRED CONFIG
BOT_TOKEN = getenv("BOT_TOKEN", "")
OWNER_ID = int(getenv("OWNER_ID", "0"))
TELEGRAM_API = int(getenv("TELEGRAM_API", "0"))
TELEGRAM_HASH = getenv("TELEGRAM_HASH", "")
