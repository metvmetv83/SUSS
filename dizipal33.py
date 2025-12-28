import requests, re, time
from bs4 import BeautifulSoup
import concurrent.futures

# === AYARLAR ===
BASE_URL = "https://dizipal1224.com"
OUTPUT_FILE = "dizipal33.m3u"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Referer": BASE_URL
}

FILM_BASLANGIC_SAYFASI = 1
FILM_BITIS_SAYFASI = 150    # kaç sayfa istiyorsan ayarla
WORKER_COUNT = 8


# === BASİT İSTEK FUNK. ===
def get_soup(url):
    for _ in range(3):
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code == 200:
                return BeautifulSoup(r.text, "html.parser")
        except Exception:
            time.sleep(2)
    return None


# === FİLM SAYFASINDAN M3U8 ÇIKAR ===
def extract_m3u8_from_detail(detail_url):
    s = get_soup(detail_url)
    if not s:
        return None

    iframe = s.find("iframe")
    if not iframe:
        return None

    src = iframe.get("data-src") or iframe.get("src")
    if not src:
        return None

    # iframe içindeki .m3u8
    if "vidrame" in src:
        # vidrame id yakala
        match = re.search(r"vidrame\.pro/vr/([a-zA-Z0-9]+)", src)
        if match:
            vid = match.group(1)
            return f"https://vidrame.pro/vr/get/{vid}/master.m3u8"

    # sayfa içinde .m3u8 geçiyorsa direkt yakala
    inner = requests.get(src, headers=HEADERS, timeout=15).text
    m = re.search(r'(https?://[^"\' ]+\.m3u8)', inner)
    if m:
        return m.group(1)

    return None


# === TEK FİLMİ İŞLE ===
def process_movie(card):
    try:
        href = card.get("href")
        full_url = href if href.startswith("http") else BASE_URL + href

        title_tag = card.find("h2", class_="title") or card.find("div", class_="title")
        title = title_tag.text.strip() if title_tag else "Bilinmeyen Film"

        img = card.find("img")
        poster_path = ""
        if img:
            poster_path = img.get("data-src") or img.get("src")
        poster_url = (
            poster_path if poster_path.startswith("http") else BASE_URL + poster_path
        )

        m3u8 = extract_m3u8_from_detail(full_url)
        if not m3u8:
            return None

        tvg_name = f"TR:{title}"
        entry = (
            f'#EXTINF:-1 tvg-id="" tvg-name="{tvg_name}" '
            f'tvg-logo="{poster_url}" group-title="Dizipal33-Film",{tvg_name}\n'
            f'{m3u8}\n'
        )
        return entry
    except Exception:
        return None


# === FİLM SAYFASINI TARA ===
def get_movies_from_page(page):
    url = f"{BASE_URL}/filmler?page={page}"
    soup = get_soup(url)
    if not soup:
        return []

    container = soup.find("div", id="moviesListResult")
    if not container:
        return []

    cards = container.find_all("a", class_="poster")
    results = []
    for card in cards:
        entry = process_movie(card)
        if entry:
            results.append(entry)
    return results


# === ANA FONK. ===
def main():
    print(f"🎬 Dizipal33 Full Film Çekici başlatılıyor ({FILM_BITIS_SAYFASI} sayfa)")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")

    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKER_COUNT) as ex:
        futures = {
            ex.submit(get_movies_from_page, i): i
            for i in range(FILM_BASLANGIC_SAYFASI, FILM_BITIS_SAYFASI + 1)
        }

        for fut in concurrent.futures.as_completed(futures):
            sayfa = futures[fut]
            try:
                data = fut.result()
                if data:
                    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                        for d in data:
                            f.write(d)
                    print(f"[OK] Film Sayfa {sayfa} tamamlandı. ({len(data)} film)")
                else:
                    print(f"[!] Film Sayfa {sayfa} boş döndü.")
            except Exception as e:
                print(f"[HATA] {sayfa}: {e}")

    print(f"\n✅ İşlem tamamlandı. Sonuç dosyası: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
