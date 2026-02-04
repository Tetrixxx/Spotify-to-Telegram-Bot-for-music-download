from telethon.sync import TelegramClient
from telethon.sessions import StringSession
import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv('API_ID', '0'))
API_HASH = os.getenv('API_HASH', '')

def generate_session():
    print("--- Telegram StringSession Generátor ---")
    
    if API_ID == 0 or not API_HASH:
        print("HIBA: API_ID vagy API_HASH hiányzik a .env fájlból!")
        return

    with TelegramClient(StringSession(), API_ID, API_HASH) as client:
        print("\nSikeres bejelentkezés!")
        print("\nMASOLD EZT A SOROKAT A GITHUB SECRET-BE (TELEGRAM_SESSION):")
        print("----------------------------------------------------------")
        print(client.session.save())
        print("----------------------------------------------------------")
        print("FIGYELEM: Ne oszd meg ezt a szöveget senkivel!")

if __name__ == '__main__':
    generate_session()
