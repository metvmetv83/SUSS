import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time
import json
import os
import subprocess
import re

# --- GÜNCEL AYARLAR ---
# NOT: .cx çalışmıyorsa .click, .xyz veya güncel rakamlı domaini (dizipal840.com vb.) deneyin.
BASE_URL = "https://dizipal.cx" 
PLATFORM_SLUG = "hbomax"
OUTPUT_FILE = "hobii.json"

def get_chrome_version():
    try:
        output = subprocess.check_output(['google-chrome', '--version']).decode('utf-8')
        return int(re.search(r'Google Chrome (\d+)', output).group(1))
    except: return None

def scrape():
    version = get_chrome_version()
    options = uc.ChromeOptions()
    options.add_argument('--headless') # GitHub için şart
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    # Resimleri engellemek hızı %300 artırır
    options.add_argument('--blink-settings=imagesEnabled=false')

    driver = uc.Chrome(options=options, version_main=version)
    results = {}

    try:
        print(f"Hedef Adres: {BASE_URL}")
        driver.get(BASE_URL)
        time.sleep(15) # Cloudflare geçişi için kritik bekleme

        for page in range(1, 3):
            url = f"{BASE_URL}/platform/{PLATFORM_SLUG}/page/{page}/"
            print(f"Tarama: {url}")
            driver.get(url)
            time.sleep(8) # İçeriğin yüklenmesi için süre

            # Linkleri en geniş kapsamda topla
            elements = driver.find_elements(By.TAG_NAME, "a")
            content_links = []
            for el in elements:
                try:
                    href = el.get_attribute("href")
                    title = el.get_attribute("title") or el.text
                    # Sadece dizi veya film içeren linkleri ayıkla
                    if href and ("/dizi/" in href or "/film/" in href):
                        if href not in [c['url'] for c in content_links]:
                            content_links.append({"url": href, "title": title.strip()})
                except: continue

            print(f"Saptanan Link Sayısı: {len(content_links)}")

            for item in content_links:
                slug = item['url'].split('/')[-2]
                if slug in results: continue

                print(f"  > Veri Çekiliyor: {item['title']}")
                driver.get(item['url'])
                time.sleep(4)

                # Sayfa kaynağında iframe ara
                try:
                    iframe = driver.find_element(By.TAG_NAME, "iframe")
                    video_link = iframe.get_attribute("src")
                except:
                    video_link = "Bulunamadı"

                results[slug] = {
                    "isim": item['title'],
                    "link": item['url'],
                    "video": video_link
                }

                # Her adımda diske yaz (Güvenli yöntem)
                with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)

    finally:
        driver.quit()
        print(f"İşlem Tamamlandı. Toplam: {len(results)}")

if __name__ == "__main__":
    scrape()
