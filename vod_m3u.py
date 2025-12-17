
import requests
import time
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ================== AYARLAR ==================
BEARER_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbnYiOiJMSVZFIiwiaXBiIjoiMCIsImNnZCI6IjA5M2Q3MjBhLTUwMmMtNDFlZC1hODBmLTJiODE2OTg0ZmI5NSIsImNzaCI6IlRSS1NUIiwiZGN0IjoiM0VGNzUiLCJkaSI6IjMwYTM5YzllLWE4ZDYtNGEwMC05NDBmLTFjMTE4NDgzZDcxMiIsInNnZCI6ImJkNmUyNmY5LWJkMzYtNDE2ZC05YWQzLTYzNjhlNGZkYTMyMiIsInNwZ2QiOiJjYjZmZGMwMi1iOGJlLTQ3MTYtYTZjYi1iZTEyYTg4YjdmMDkiLCJpY2giOiIwIiwiaWRtIjoiMCIsImlhIjoiOjpmZmZmOjEwLjAuMC4yMDYiLCJhcHYiOiIxLjAuMCIsImFibiI6IjEwMDAiLCJuYmYiOjE3NTE3MDMxODQsImV4cCI6MTc1MTcwMzI0NCwiaWF0IjoxNzUxNzAzMTg0fQ.SGC_FfT7cU1RVM4E5rMYO2IsA4aYUoYq2SXl51-PZwM"
VOD_ID_FILE = "vod_ids.txt"
OUTPUT_M3U = "vodden.m3u"

BASE_URL = "https://core-api.kablowebtv.com/api/vod/detail"

# ================== SESSION ==================
session = requests.Session()

session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
    "Referer": "https://tvheryerde.com",
    "Origin": "https://tvheryerde.com",
    "Cache-Control": "max-age=0",
    "Authorization": BEARER_TOKEN
})

retry = Retry(
    total=3,
    backoff_factor=2,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"]
)

adapter = HTTPAdapter(max_retries=retry)
session.mount("https://", adapter)

# ================== FONKSİYONLAR ==================
def load_vod_ids(filename):
    if not os.path.exists(filename):
        print(f"[!] {filename} bulunamadı")
        return []
    with open(filename, "r", encoding="utf-8") as f:
        return [x.strip() for x in f if x.strip()]

def get_vod_detail(vod_id):
    try:
        r = session.get(
            BASE_URL,
            params={
                "VodUId": vod_id,
                "checkip": "false"
            },
            timeout=25
        )
        r.raise_for_status()
        js = r.json()
        if js.get("IsSucceeded") and js.get("Data"):
            return js["Data"][0]
    except requests.exceptions.Timeout:
        print(f"[⏱️ TIMEOUT] {vod_id}")
    except Exception as e:
        print(f"[!] HATA {vod_id}: {e}")
    return None

def write_m3u(items):
    with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")

        for item in items:
            title = item.get("Title", "Bilinmeyen")
            uid = item.get("UId", "")
            posters = item.get("Posters", [])
            stream = item.get("StreamData", {})

            logo = ""
            for p in posters:
                if p.get("Type", "").lower() == "listing":
                    logo = p.get("ImageUrl", "")
                    break

            mpd = stream.get("DashStreamUrl")
            drm = stream.get("IsDrmEnabled", True)

            if mpd and not drm:
                f.write(
                    f'#EXTINF:-1 tvg-id="{uid}" tvg-logo="{logo}" group-title="VOD",{title}\n{mpd}\n'
                )

    print(f"[✓] M3U oluşturuldu → {OUTPUT_M3U}")

# ================== MAIN ==================
def main():
    vod_ids = load_vod_ids(VOD_ID_FILE)
    if not vod_ids:
        return

    total = len(vod_ids)
    results = []

    print(f"[▶] {total} VOD işleniyor...")

    for i, vod_id in enumerate(vod_ids, 1):
        print(f"[{i}/{total}] {vod_id}")

        detail = get_vod_detail(vod_id)
        if detail:
            results.append(detail)

        time.sleep(1.2)

        if i % 40 == 0:
            print("⏸️ Kısa mola...")
            time.sleep(8)

    write_m3u(results)

    print("📂 Dosyalar:", os.listdir())

# ================== ÇALIŞTIR ==================
if __name__ == "__main__":
    main()
