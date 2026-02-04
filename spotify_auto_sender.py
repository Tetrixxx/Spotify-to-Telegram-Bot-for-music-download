import time
import os
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from telethon import TelegramClient, sync
from telethon.sessions import StringSession
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- KONFIGURÁCIÓ ---

# A Spotify Playlist linkje
PLAYLIST_URL = os.getenv('PLAYLIST_URL', '')

# Telegram Adatok
API_ID = int(os.getenv('API_ID', '0'))
API_HASH = os.getenv('API_HASH', '')
BOT_USERNAME = os.getenv('BOT_USERNAME', '')

# Fájl a már letöltött zenék tárolására
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

def get_spotify_links():
    print("--- Böngésző indítása (REGEX MÓD)... ---")
    
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("window-size=1280,720")

    if os.getenv('HEADLESS') == 'true':
        chrome_options.add_argument("--headless=new")


    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    found_track_ids = set()

    try:
        driver.get(PLAYLIST_URL)
        
        print("--- Várakozás az oldal betöltésére... ---")
        time.sleep(5)  # Várunk, hogy betöltődjön az oldal bejelentkezés nélkül
        
        print("--- Keresés a forráskódban... ---")
        
        # Megkeressük a Spotify belső görgetési konténerét
        scroll_script = """
            // A Spotify fő görgethető konténere
            var container = document.querySelector('[data-testid="playlist-tracklist"]');
            if (!container) {
                container = document.querySelector('.main-view-container__scroll-node-child');
            }
            if (!container) {
                container = document.querySelector('[data-overlayscrollbars-viewport]');
            }
            if (!container) {
                // Fallback: keressük a scrollable elemet
                var elements = document.querySelectorAll('*');
                for (var el of elements) {
                    if (el.scrollHeight > el.clientHeight && el.clientHeight > 400) {
                        container = el;
                        break;
                    }
                }
            }
            return container ? true : false;
        """
        
        has_container = driver.execute_script(scroll_script)
        print(f"Görgetési konténer találva: {has_container}")
        
        # Görgetési szkript - lépésenként görgetünk a konténerben
        def scroll_and_collect():
            nonlocal found_track_ids
            
            # Scroll script ami a megfelelő konténert használja
            driver.execute_script("""
                var container = document.querySelector('[data-testid="playlist-tracklist"]');
                if (!container) container = document.querySelector('.main-view-container__scroll-node-child');
                if (!container) container = document.querySelector('[data-overlayscrollbars-viewport]');
                if (!container) container = document.body;
                container.scrollTop = 0;
            """)
            time.sleep(1)
            
            last_count = 0
            attempts = 0
            scroll_position = 0
            scroll_step = 800  # Kisebb lépésekben görgetünk
            
            while attempts < 10:  # Max 10 sikertelen próba
                # HTML kinyerése
                page_source = driver.page_source
                
                # Track ID-k keresése
                ids_in_view = re.findall(r'/track/([a-zA-Z0-9]{22})', page_source)
                for track_id in ids_in_view:
                    found_track_ids.add(track_id)
                
                current_count = len(found_track_ids)
                print(f"Megtalált egyedi azonosítók: {current_count} (görgetés: {scroll_position}px)    ", end='\r')
                
                # Görgetés lefelé
                scroll_position += scroll_step
                driver.execute_script(f"""
                    var container = document.querySelector('[data-testid="playlist-tracklist"]');
                    if (!container) container = document.querySelector('.main-view-container__scroll-node-child');
                    if (!container) container = document.querySelector('[data-overlayscrollbars-viewport]');
                    if (!container) container = document.body;
                    container.scrollTop = {scroll_position};
                """)
                time.sleep(0.8)  # Várakozás betöltésre
                
                # Ellenőrzés: találtunk-e újat?
                if current_count == last_count:
                    attempts += 1
                else:
                    attempts = 0
                
                last_count = current_count
        
        # 3 teljes végigfuttatás a biztonság kedvéért
        for run in range(3):
            print(f"\n--- {run+1}. Teljes görgetés ---")
            scroll_and_collect()
            time.sleep(1)

        print(f"\nKész! Összesen {len(found_track_ids)} dalt találtam.")
        
        # Szabványos Spotify linkek generálása
        full_links = [f"https://open.spotify.com/track/{t_id}" for t_id in found_track_ids]
        return full_links

    except Exception as e:
        print(f"Hiba: {e}")
        full_links = [f"https://open.spotify.com/track/{t_id}" for t_id in found_track_ids]
        return full_links
    finally:
        driver.quit()

def main():
    history = load_history()
    current_tracks = get_spotify_links()

    if not current_tracks:
        print("Nem találtam zenéket, vagy hiba történt a beolvasáskor.")
        return

    print(f"\n--- Telegram küldés indítása ({len(current_tracks)} db zene van a listán) ---")

    new_tracks_found = False

    session_string = os.getenv('TELEGRAM_SESSION')
    if session_string:
        print("--- Környezeti változóban talált munkamenet használata ---")
        session = StringSession(session_string)
    else:
        print("--- Helyi fájl munkamenet használata ---")
        session = 'my_session'

    with TelegramClient(session, API_ID, API_HASH) as client:
        
        # Először küldünk egy /start üzenetet a botnak
        print("--- /start üzenet küldése a botnak... ---")
        client.send_message(BOT_USERNAME, '/start')
        time.sleep(2)  # Várunk egy kicsit, hogy a bot válaszoljon
        print("--- Bot inicializálva, zenék küldése indul... ---")
        
        for track_url in current_tracks:
            if track_url not in history:
                print(f"\nFeldolgozás: {track_url}")
                
                try:
                    # A. Utolsó üzenet ID lekérése
                    last_msgs = client.get_messages(BOT_USERNAME, limit=1)
                    last_msg_id = last_msgs[0].id if last_msgs else 0
                    
                    # B. Link küldése
                    client.send_message(BOT_USERNAME, track_url)
                    print(f" -> Link elküldve. Várakozás a bot 2 válaszára...", end="", flush=True)
                    
                    # C. Várakozás
                    start_time = time.time()
                    while True:
                        time.sleep(2)
                        print(".", end="", flush=True)
                        
                        recent_messages = client.get_messages(BOT_USERNAME, min_id=last_msg_id, limit=10)
                        incoming_msgs = [msg for msg in recent_messages if not msg.out]
                        
                        if len(incoming_msgs) >= 2:
                            print(" KÉSZ! (Megérkezett a 2 válasz)")
                            break
                        
                        if time.time() - start_time > 60:
                            print(" IDŐTÚLLÉPÉS! (Továbbmegyek)")
                            break
                    
                    # D. Mentés
                    save_history(track_url)
                    new_tracks_found = True
                    time.sleep(1) 
                    
                except Exception as e:
                    print(f"\n -> Hiba történt: {e}")

    if not new_tracks_found:
        print("\nNincs új letölthető zene.")
    else:
        print("\nFolyamat befejezve.")

if __name__ == '__main__':
    main()