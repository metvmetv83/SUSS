import requests
from bs4 import BeautifulSoup
import re
import concurrent.futures
import time

BASE_URL = "https://www.hdfilmizle.life"
OUTPUT_FILE = "dizipal33.m3u"

DIZI_BASLANGIC = 1
DIZI_BITIS = 50

FILM_BASLANGIC = 1
FILM_BITIS = 975

WORKERS = 10

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": BASE_URL
}

def get_soup(url):
    for _ in range(3):
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code == 200:
                return BeautifulSoup(r.text, "lxml")
        except:
            time.sleep(2)
    return None

def extract_vidrame(page_url):
    soup = get_soup(page_url)
    if not soup:
        return None

    iframe = soup.find("iframe", src=re.compile("vidrame"))
    if iframe:
        src = iframe.get("src") or iframe.get("data-src")
        if src:
            m = re.search(r"/vr/([a-zA-Z0-9]+)", src)
            if m:
                return f"https://vidrame.pro/vr/get/{m.group(1)}/master.m3u8"
    return None

def process_movie(card):
    try:
        title = card.find("h2").text.strip()
        link = BASE_URL + card.get("href")
        img = card.find("img")
        poster = img.get("data-src") if img else ""

        m3u8 = extract_vidrame(link)
        if m3u8:
            return (
                f'#EXTINF:-1 tvg-name="TR:{title}" tvg-logo="{poster}" group-title="Filmler",{title}\n'
                f'{m3u8}\n'
            )
    except:
        pass
    return None

def get_movies(page):
    url = f"{BASE_URL}/page/{page}/"
    soup = get_soup(url)
    if not soup:
        return []

    container = soup.find("div", id="moviesListResult")
    if not container:
        return []

    results = []
    cards = container.find_all("a", class_="poster")
    for card in cards:
        item = process_movie(card)
        if item:
            results.append(item)
    return results

def process_episode(dizi, poster, url, bolum):
    full = BASE_URL + url
    m3u8 = extract_vidrame(full)
    if m3u8:
        return (
            f'#EXTINF:-1 tvg-name="TR:{dizi} {bolum}" tvg-logo="{poster}" group-title="Diziler",{dizi} {bolum}\n'
            f'{m3u8}\n'
        )
    return None

def get_series(page):
    url = f"{BASE_URL}/yabanci-dizi-izle-2/page/{page}/"
    soup = get_soup(url)
    if not soup:
        return []

    container = soup.find("div", id="moviesListResult")
    if not container:
        return []

    results = []

    for card in container.find_all("a", class_="poster"):
        dizi = card.find("h2").text.strip()
        dizi_url = BASE_URL + card.get("href")
        img = card.find("img")
        poster = img.get("data-src") if img else ""

        detail = get_soup(dizi_url)
        if not detail:
            continue

        eps = detail.find_all("a", href=re.compile("/sezon-"))
        seen = set()

        for ep in eps:
            href = ep.get("href")
            if href in seen:
                continue
            seen.add(href)

            bolum = ep.text.strip()
            item = process_episode(dizi, poster, href, bolum)
            if item:
                results.append(item)

    return results

def main():
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")

    print("🎬 Filmler çekiliyor...")
    with concurrent.futures.ThreadPoolExecutor(WORKERS) as ex:
        for future in concurrent.futures.as_completed(
            [ex.submit(get_movies, i) for i in range(FILM_BASLANGIC, FILM_BITIS + 1)]
        ):
            for item in future.result():
                with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                    f.write(item)

    print("📺 Diziler çekiliyor...")
    with concurrent.futures.ThreadPoolExecutor(WORKERS) as ex:
        for future in concurrent.futures.as_completed(
            [ex.submit(get_series, i) for i in range(DIZI_BASLANGIC, DIZI_BITIS + 1)]
        ):
            for item in future.result():
                with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                    f.write(item)

    print("✅ İşlem tamamlandı:", OUTPUT_FILE)

if __name__ == "__main__":
    main()
