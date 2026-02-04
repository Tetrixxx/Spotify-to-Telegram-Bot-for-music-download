# Spotify to Telegram Bot

Automatikusan küldi a Spotify playlist zenéket egy Telegram bot-nak letöltésre.

## Két verzió:

### 1. `spotify_auto_sender.py` - Automatikus
- Selenium böngésző automatizációval
- Automatikusan gyűjti a linkeket a playlistről
- Teljesen automatikus, nincs szükség kézi műveletekre

### 2. `spotify_clipboard_sender.py` - Vágólap alapú
- Egyszerűbb és gyorsabb
- A vágólapról olvassa be a linkeket
- Kézi másolás szükséges a Spotify-ból

## Telepítés

### 1. Függőségek telepítése:
```bash
pip install -r requirements.txt
```

### 2. Környezeti változók beállítása:

Másold át a `.env.example` fájlt `.env` névre:
```bash
copy .env.example .env
```

Majd töltsd ki a `.env` fájlt a saját adataiddal:
```env
API_ID=your_telegram_api_id
API_HASH=your_telegram_api_hash
BOT_USERNAME=your_bot_username
PLAYLIST_URL=https://open.spotify.com/playlist/your_playlist_id
```

#### Telegram API kulcsok beszerzése:
1. Menj a https://my.telegram.org oldalra
2. Jelentkezz be a telefonszámoddal
3. Menj az "API development tools" menübe
4. Hozz létre egy új alkalmazást
5. Másold ki az `api_id`-t és `api_hash`-t

## Használat

### Auto Sender (automatikus):
```bash
python spotify_auto_sender.py
```

### Clipboard Sender (vágólap):
1. Nyisd meg a Spotify playlistet
2. Jelöld ki az összes zenét: **Ctrl+A**
3. Másold ki: **Ctrl+C**
4. Futtasd a szkriptet:
```bash
python spotify_clipboard_sender.py
```

## Megjegyzések

- Az első futtatásnál be kell jelentkezni Telegramba
- A már elküldött zenéket a `downloaded_tracks.txt` tárolja
- A szkript nem küldi el többször ugyanazt a zenét
