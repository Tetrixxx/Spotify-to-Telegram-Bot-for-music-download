import time
import os
try:
    import pyperclip
except ImportError:
    print("HIBA: Telepítsd a modult: pip install pyperclip")
    exit()
from telethon import TelegramClient, sync
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- KONFIGURÁCIÓ ---
API_ID = int(os.getenv('API_ID', '0'))
API_HASH = os.getenv('API_HASH', '')
BOT_USERNAME = os.getenv('BOT_USERNAME', '')
HISTORY_FILE = 'downloaded_tracks.txt'
# --------------------

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, 'r') as f:
        return [line.strip() for line in f.readlines()]

def save_history(track_link):
    with open(HISTORY_FILE, 'a') as f:
        f.write(f"{track_link}\n")

def main():
    print("--- Vágólap beolvasása... ---")
    content = pyperclip.paste()
    
    # Sorokra bontás és szűrés
    lines = content.split('\n')
    spotify_links = []
    
    for line in lines:
        line = line.strip()
        # Ha tartalmazza a spotify track linket
        if "open.spotify.com/track" in line or "spotify:track:" in line:
            spotify_links.append(line)
            
    print(f"Találtam {len(spotify_links)} db Spotify linket a vágólapon!")
    
    if len(spotify_links) == 0:
        print("Hiba: Üres a vágólap, vagy nem Spotify zenék voltak rajta.")
        print("Tipp: Nyisd meg a Spotify appot -> Ctrl+A -> Ctrl+C -> Futtasd újra ezt.")
        return

    history = load_history()
    
    with TelegramClient('my_session', API_ID, API_HASH) as client:
        count = 0
        for link in spotify_links:
            clean_link = link.split('?')[0] # Szemét levágása a végéről
            
            if clean_link not in history:
                count += 1
                print(f"[{count}/{len(spotify_links)}] Feldolgozás: {clean_link}")
                
                try:
                    # 1. Utolsó üzenet ID
                    last_msgs = client.get_messages(BOT_USERNAME, limit=1)
                    last_msg_id = last_msgs[0].id if last_msgs else 0
                    
                    # 2. Küldés
                    client.send_message(BOT_USERNAME, clean_link)
                    print(f" -> Elküldve. Várakozás a botra...", end="", flush=True)

                    # 3. Várakozás (Smart Wait)
                    start_time = time.time()
                    while True:
                        time.sleep(2)
                        print(".", end="", flush=True)
                        
                        recent = client.get_messages(BOT_USERNAME, min_id=last_msg_id, limit=10)
                        incoming = [msg for msg in recent if not msg.out]
                        
                        if len(incoming) >= 2:
                            print(" KÉSZ!")
                            break
                        
                        if time.time() - start_time > 60:
                            print(" IDŐTÚLLÉPÉS!")
                            break
                    
                    save_history(clean_link)
                    
                except Exception as e:
                    print(f"Hiba: {e}")
                    time.sleep(10) # Hiba esetén pici szünet
            else:
                print(f"Már letöltve: {clean_link}")

    print("Kész!")

if __name__ == '__main__':
    main()