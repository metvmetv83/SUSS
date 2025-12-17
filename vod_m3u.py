import requests
import time
import os

# ================== AYARLAR ==================

BEARER_TOKEN = "Bearer eyJhbGciOiJIUzI1NiJ9.eyJjZ2QiOiIwOTNkNzIwYS01MDJjLTQxZWQtYTgwZi0yYjgxNjk4NGZiOTUiLCJkaSI6IjBmYTAzNTlkLWExOWItNDFiMi05ZTczLTI5ZWNiNjk2OTY0MCIsImFwdiI6IjEuMC4wIiwiZW52IjoiTElWRSIsImFibiI6IjEwMDAiLCJzcGdkIjoiYTA5MDg3ODQtZDEyOC00NjFmLWI3NmItYTU3ZGViMWI4MGNjIiwiaWNoIjoiMCIsInNnZCI6ImViODc3NDRjLTk4NDItNDUwNy05YjBhLTQ0N2RmYjg2NjJhZCIsImlkbSI6IjAiLCJkY3QiOiIzRUY3NSIsImlhIjoiOjpmZmZmOjEwLjAuMC41IiwiY3NoIjoiVFJLU1QiLCJpcGIiOiIwIn0.bT8PK2SvGy2CdmbcCnwlr8RatdDiBe_08k7YlnuQqJE"

HEADERS = {
    "Authorization": BEARER_TOKEN,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://tvheryerde.com",
    "Origin": "https://tvheryerde.com",
    "Accept": "application/json"
}

VOD_ID_FILE = "vod_ids.txt"
OUTPUT_M3U = "vod_final.m3u"

DETAIL_URL = "https://core-api.kablowebtv.com/api/vod/detail"

# =================================================


def load_vod_ids():
    if not os.path.exists(VOD_ID_FILE):
        print("❌ vod_ids.txt bulunamadı")
        return []

    with open(VOD_ID_FILE, "r", encoding="utf-8") as f:
        ids = [x.strip() for x in f if x.strip()]

    print(f"📋 {len(ids)} adet VOD ID bulundu")
    return ids


def get_vod_detail(vod_id):
    try:
        r = requests.get(
            DETAIL_URL,
            headers=HEADERS,
            params={"VodUId": vod_id},
            timeout=8
        )
        if r.status_code != 200:
            return None

        data = r.json()
        if data.get("IsSucceeded") and data.get("Data"):
            return data["Data"][0]

    except Exception:
        return None

    return None


def extract_stream(film):
    """
    Güvenli stream çıkarma
    """
    sd = film.get("StreamData")

    if not sd or not isinstance(sd, dict):
        return None, None

    if sd.get("IsDrmEnabled") is True:
        return None, None

    return sd.get("HlsStreamUrl") or sd.get("DashStreamUrl"), sd


def extract_logo(film):
    for p in film.get("Posters", []):
        if p.get("Type", "").lower() == "listing":
            return p.get("ImageUrl", "")
    return ""


def main():
    vod_ids = load_vod_ids()
    if not vod_ids:
        return

    written = 0

    with open(OUTPUT_M3U, "w", encoding="utf-8") as m3u:
        m3u.write("#EXTM3U\n")

        for i, vod_id in enumerate(vod_ids, 1):
            print(f"[{i}] {vod_id}")

            film = get_vod_detail(vod_id)
            if not film:
                print("  ⏭ API boş")
                continue

            title = film.get("Title", "Bilinmeyen")
            uid = film.get("UId", vod_id)
            logo = extract_logo(film)

            stream_url, sd = extract_stream(film)
            if not stream_url:
                print(f"  ⏭ {title} (DRM / Stream yok)")
                continue

            m3u.write(
                f'#EXTINF:-1 tvg-id="{uid}" tvg-logo="{logo}" group-title="VOD",{title}\n'
            )
            m3u.write(stream_url + "\n")

            written += 1
            print(f"  ✅ Yazıldı: {title}")

            # hız / ban yememek için
            time.sleep(0.15)

    print("\n==============================")
    print(f"✅ M3U OLUŞTU: {OUTPUT_M3U}")
    print(f"🎬 Yazılan film: {written}")
    print("==============================")
    print(f"📂 Konum: {os.path.abspath(OUTPUT_M3U)}")


if __name__ == "__main__":
    main()
