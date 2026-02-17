import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time
import json
import re
import subprocess
import os

# --- AYARLAR ---
BASE_URL = "https://dizipal.cx"
PLATFORM_SLUG = "hbomax"
OUTPUT_FILE = "hobi.json"

def get_chrome_version():
    try:
        output = subprocess.check_output(['google-chrome', '--version']).decode('utf-8')
        return int(re.search(r'Google Chrome (\d+)', output).group(1))
    except: return None

def scrape_hbomax():
    version = get_chrome_version()
    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--blink-settings=imagesEnabled=false') # Resimleri yükleme (HIZ)
    
    # Cloudflare'i geçmek için user-agent ekleyelim
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    driver = uc.Chrome(options=options, version_main=version)
    results = {}

    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            try: results = json.load(f)
            except: pass

    try:
        print("Cloudflare geciliyor...")
        driver.get(BASE_URL)
        time.sleep(15) # İlk geçiş kritik

        for page in range(1, 4): # İlk 3 sayfa
            url = f"{BASE_URL}/platform/{PLATFORM_SLUG}/page/{page}/"
            print(f"Sayfa {page} taranıyor...")
            driver.get(url)
            time.sleep(5) 

            # HTML Kaynağını al ve Regex ile tüm içerikleri saniyeler içinde bul
            html_source = driver.page_source
            # Dizipal'in güncel link yapısını yakalayan regex
            content_matches = re.findall(r'<div class="post-item">.*?href="(.*?)".*?title="(.*?)".*?src="(.*?)"', html_source, re.S)

            if not content_matches:
                print("⚠️ İçerik bulunamadı. Seçiciler güncelleniyor...")
                # Alternatif regex (Eğer class değiştiyse)
                content_matches = re.findall(r'<a href="(https://dizipal.cx/.*?/)".*?title="(.*?)"', html_source)

            print(f"Bulunan yeni içerik: {len(content_matches)}")

            for link, title, img in content_matches:
                slug = title.replace(" ", "-").lower()
                if slug in results: continue

                print(f"-> {title} işleniyor...")
                driver.get(link)
                time.sleep(2)
                
                # Sayfadaki tüm bölüm linklerini ve iframe'i tek seferde al
                inner_html = driver.page_source
                episodes = list(set(re.findall(r'href="(https://dizipal.cx/.*?bolum.*?/)"', inner_html)))
                
                res = {"isim": title, "resim": img, "bolumler": []}

                if not episodes: # Film
                    iframe = re.search(r'<iframe.*?src="(.*?)"', inner_html)
                    if iframe:
                        res["bolumler"].append({"bolum_baslik": "Film", "link": iframe.group(1)})
                else:
                    # Sadece ilk ve son bölüme bakarak veya sınırlayarak hızlandırabilirsin
                    for i, ep_url in enumerate(sorted(episodes)[:15], 1): # İlk 15 bölüm sınırı (HIZ İÇİN)
                        driver.get(ep_url)
                        if_src = driver.execute_script("return document.querySelector('iframe')?.src")
                        if if_src:
                            res["bolumler"].append({"bolum_baslik": f"{i}. Bölüm", "link": if_src})

                results[slug] = res
                # Her içerikte kaydet ki yarıda kalırsa veri gitmesin
                with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)

    finally:
        driver.quit()
        print(f"İşlem bitti. Toplam: {len(results)}")

if __name__ == "__main__":
    scrape_hbomax()
