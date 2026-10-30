import sys
from pathlib import Path
print(Path(__file__).parent.parent)
sys.path.append(str(Path(__file__).parent.parent.absolute()))
try:
    from pyrogram import Client
except Exception as e:
    print(e)
    print("\nInstall pyrogram: pip3 install pyrogram")
    exit(1)

print("Required pyrogram V2 or greater.")
from config import TELEGRAM_API, TELEGRAM_HASH
API_KEY, API_HASH = TELEGRAM_API, TELEGRAM_HASH
if not API_KEY:
    API_KEY = int(input("Enter API KEY: "))
if not API_HASH:
    API_HASH = input("Enter API HASH: ")
with Client(name="USS", api_id=API_KEY, api_hash=API_HASH, in_memory=True) as app:
    print(app.export_session_string())
