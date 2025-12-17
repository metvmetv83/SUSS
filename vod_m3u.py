
import requests
import time
import os
import json
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ================== AYARLAR ==================
BEARER_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbnYiOiJMSVZFIiwiaXBiIjoiMCIsImNnZCI6IjA5M2Q3MjBhLTUwMmMtNDFlZC1hODBmLTJiODE2OTg0ZmI5NSIsImNzaCI6IlRSS1NUIiwiZGN0IjoiM0VGNzUiLCJkaSI6IjMwYTM5YzllLWE4ZDYtNGEwMC05NDBmLTFjMTE4NDgzZDcxMiIsInNnZCI6ImJkNmUyNmY5LWJkMzYtNDE2ZC05YWQzLTYzNjhlNGZkYTMyMiIsInNwZ2QiOiJjYjZmZGMwMi1iOGJlLTQ3MTYtYTZjYi1iZTEyYTg4YjdmMDkiLCJpY2giOiIwIiwiaWRtIjoiMCIsImlhIjoiOjpmZmZmOjEwLjAuMC4yMDYiLCJhcHYiOiIxLjAuMCIsImFibiI6IjEwMDAiLCJuYmYiOjE3NTE3MDMxODQsImV4cCI6MTc1MTcwMzI0NCwiaWF0IjoxNzUxNzAzMTg0fQ.SGC_FfT7cU1RVM4E5rMYO2IsA4aYUoYq2SXl51-PZwM"
OUTPUT_M3U = "vodden.m3u"
OUTPUT_M3U = "vodden.m3u"
VOD_ID_FILE = "vod_ids.txt"
LOG_FILE = "vod_log.json"

HEADERS = {
    "Authorization": BEARER_TOKEN,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://tvheryerde.com",
    "Origin": "https://tvheryerde.com",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7"
}

# ================== SESSION ==================
session = requests.Session()
session.headers.update(HEADERS)

retry = Retry(
    total=3,
    backoff_factor=2,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"]
)

adapter = HTTPAdapter(max_retries=retry)
session.mount("https://", adapter)

# ================== TOKEN KONTROL ==================
def check_token_expiry():
    try:
        try:
            import jwt
        except ImportError:
            print("[!] jwt modülü yok, token süresi kontrolü atlandı")
            return True

        token = BEARER_TOKEN.replace("Bearer ", "")
        decoded = jwt.decode(token, options={"verify_signature": False})
        exp = decoded.get("exp")

        if not exp:
            return True

        exp_date = datetime.fromtimestamp(exp)
        if exp_date < datetime.now():
            print(f"[!] TOKEN SÜRESİ DOLMUŞ: {exp_date}")
            return False

        print(f"[✓] Token geçerli (bitiş: {exp_date})")
        return True

    except Exception as e:
        print(f"[!] Token kontrol hatası: {e}")
        return True

# ================== VOD ID OKUMA ==================
def load_vod_ids(filename):
    if not os.path.exists(filename):
        print(f"[!] {filename} bulunamadı")
        return []

    ids = []
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if "vod/" in line:
                ids.append(line.split("/")[-1])
            else:
                ids.append(line)

    print(f"[✓] {len(ids)} VOD ID yüklendi")
    return ids

# ================== API ÇAĞRISI ==================
def get_film_detail(vod_id):
    url = "https://core-api.kablowebtv.com/api/vod/detail"
    params = {
        "VodUId": vod_id,
        "checkip": "false"
    }

    try:
        r = session.get(url, params=params, timeout=25)
        r.raise_for_status()

        js = r.json()
        if js.get("IsSucceeded") and js.get("Data"):
            return js["Data"][0]

    except requests.exceptions.Timeout:
        print(f"[⏱️ TIMEOUT] {vod_id}")
    except Exception as e:
        print(f"[!] Hata {vod_id}: {e}")

    return None

# ================== STREAM AYIKLAMA ==================
def extract_stream_info(film):
    title = film.get("Title", "Bilinmeyen")
    uid = film.get("UId", "")
    logo = ""

    for p in film.get("Posters", []):
        if p.get("Type", "").lower() == "listing":
            logo = p.get("ImageUrl", "")
            break

    stream = film.get("StreamData", {})
    mpd = stream.get("DashStreamUrl")
    hls = stream.get("HlsStreamUrl")
    drm = stream.get("IsDrmEnabled", True)

    genre = "VOD"
    cats = film.get("Categories", [])
    if cats and isinstance(cats[0], dict):
        genre = cats[0].get("Name", "VOD")

    return title, uid, logo, mpd, hls, drm, genre

# ================== M3U YAZ ==================
def write_m3u(films):
    if not films:
        print("[!] Yazılacak içerik yok")
        return 0

    count = 0
    with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")

        for film in films:
            title, uid, logo, mpd, hls, drm, genre = extract_stream_info(film)

            url = None
            if mpd and not drm:
                url = mpd
            elif hls and not drm:
                url = hls

            if url:
                f.write(
                    f'#EXTINF:-1 tvg-id="{uid}" tvg-logo="{logo}" group-title="{genre}",{title}\n{url}\n'
                )
                count += 1

    print(f"[✓] {count}/{len(films)} içerik yazıldı → {OUTPUT_M3U}")
    return count

# ================== LOG ==================
def save_log(films):
    data = {
        "timestamp": datetime.now().isoformat(),
        "total": len(films),
        "films": []
    }

    for film in films:
        title, uid, logo, mpd, hls, drm, genre = extract_stream_info(film)
        data["films"].append({
            "title": title,
            "id": uid,
            "drm": drm,
            "mpd": mpd,
            "hls": hls,
            "genre": genre
        })

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"[✓] Log yazıldı → {LOG_FILE}")

# ================== MAIN ==================
def main():
    print("=" * 50)
    print("VOD M3U OLUŞTURUCU")
    print("=" * 50)

    if not check_token_expiry():
        return

    vod_ids = load_vod_ids(VOD_ID_FILE)
    if not vod_ids:
        return

    films = []
    total = len(vod_ids)

    for i, vid in enumerate(vod_ids, 1):
        print(f"[{i}/{total}] {vid}")
        detail = get_film_detail(vid)
        if detail:
            films.append(detail)

        time.sleep(1.0)
        if i % 40 == 0:
            print("⏸️ Kısa mola...")
            time.sleep(8)

    write_m3u(films)
    save_log(films)

    print("\n📂 Dosyalar:", os.listdir())

# ================== RUN ==================
if __name__ == "__main__":
    main()
