import requests
import time
import os

# ==============================
# 🔐 BEARER TOKEN (AYNEN KOYDUĞUN)
# ==============================
BEARER_TOKEN = "Bearer eyJhbGciOiJIUzI1NiJ9.eyJjZ2QiOiIwOTNkNzIwYS01MDJjLTQxZWQtYTgwZi0yYjgxNjk4NGZiOTUiLCJkaSI6IjBmYTAzNTlkLWExOWItNDFiMi05ZTczLTI5ZWNiNjk2OTY0MCIsImFwdiI6IjEuMC4wIiwiZW52IjoiTElWRSIsImFibiI6IjEwMDAiLCJzcGdkIjoiYTA5MDg3ODQtZDEyOC00NjFmLWI3NmItYTU3ZGViMWI4MGNjIiwiaWNoIjoiMCIsInNnZCI6ImViODc3NDRjLTk4NDItNDUwNy05YjBhLTQ0N2RmYjg2NjJhZCIsImlkbSI6IjAiLCJkY3QiOiIzRUY3NSIsImlhIjoiOjpmZmZmOjEwLjAuMC41IiwiY3NoIjoiVFJLU1QiLCJpcGIiOiIwIn0.bT8PK2SvGy2CdmbcCnwlr8RatdDiBe_08k7YlnuQqJE"

# ==============================
# 📡 HEADERLAR
# ==============================
HEADERS = {
    "Authorization": BEARER_TOKEN,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://tvheryerde.com",
    "Origin": "https://tvheryerde.com",
    "Accept": "application/json"
}

VOD_IDS_FILE = "vod_ids.txt"
OUTPUT_M3U = "vod_final.m3u"

# ==============================
# 🎬 ANA İŞLEV
# ==============================
def main():
    if not os.path.exists(VOD_IDS_FILE):
        print("❌ vod_ids.txt bulunamadı")
        return

    with open(VOD_IDS_FILE, "r", encoding="utf-8") as f:
        vod_ids = [i.strip() for i in f if i.strip()]

    print(f"📋 {len(vod_ids)} adet VOD ID bulundu")

    yazilan = 0

    with open(OUTPUT_M3U, "w", encoding="utf-8") as m3u:
        m3u.write("#EXTM3U\n")

        for i, vod_id in enumerate(vod_ids, 1):
            print(f"[{i}] {vod_id}")

            try:
                r = requests.get(
                    "https://core-api.kablowebtv.com/api/vod/detail",
                    headers=HEADERS,
                    params={"VodUId": vod_id},
                    timeout=10
                )
            except Exception as e:
                print("  ❌ Bağlantı hatası")
                continue

            if r.status_code != 200:
                print(f"  ❌ HTTP {r.status_code}")
                continue

            js = r.json()
            if not js.get("IsSucceeded") or not js.get("Data"):
                print("  ❌ API başarısız")
                continue

            film = js["Data"][0]

            title = film.get("Title") or film.get("Name") or "VOD"

            sd = film.get("StreamData", {})
            stream_url = sd.get("HlsStreamUrl") or sd.get("DashStreamUrl")

            if not stream_url:
                print("  ❌ Stream yok")
                continue

            m3u.write(f"#EXTINF:-1,{title}\n")
            m3u.write(stream_url + "\n")

            yazilan += 1
            print("  ✅ Yazıldı")

            time.sleep(0.1)  # API'yi boğmamak için

    print("\n==============================")
    print(f"✅ M3U OLUŞTURULDU: {OUTPUT_M3U}")
    print(f"🎬 Toplam yazılan: {yazilan}")
    print("==============================")

# ==============================
if __name__ == "__main__":
    main()
