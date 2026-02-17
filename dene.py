import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import time
import json
import os
import subprocess
import re

# --- AYARLAR ---
BASE_URL = "https://dizipal.cx" # Domain değişirse burayı güncelle
PLATFORM_SLUG = "hbomax"
OUTPUT_FILE = "hobi.json"

def get_chrome_version():
    try:
        output = subprocess.check_output(['google-chrome', '--version']).decode('utf-8')
        return int(re.search(r'Google Chrome (\d+)', output).group(1))
    except: return None

def scrape():
    version = get_chrome_version()
    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    # HIZ İÇİN KRİTİK AYARLAR
    options.add_argument('--disable-gpu')
    options.add_argument('--blink-settings=imagesEnabled=false') # Resimleri yükleme
    options.page_load_strategy = 'eager' # DOM hazır olduğunda bekleme yapma

    driver = uc.Chrome(options=options, version_main=version)
    results = {}

    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            try: results = json.load(f)
            except: pass

    try:
        print(f"Giriş yapılıyor: {BASE_URL}")
        driver.get(BASE_URL)
        time.sleep(15) # Cloudflare geçişi

        for page in range(1, 3): # Test için 2 sayfa
            target = f"{BASE_URL}/platform/{PLATFORM_SLUG}/page/{page}/"
            print(f"Taranan Sayfa: {target}")
            driver.get(target)
            time.sleep(5)

            # İçerikleri bul (Class bağımsız, link yapısından yakala)
            items = driver.find_elements(By.CSS_SELECTOR, "div.post-item, article, .post-column")
            print(f"Saptanan öğe: {len(items)}")

            content_list = []
            for item in items:
                try:
                    a = item.find_element(By.TAG_NAME, "a")
                    link = a.get_attribute("href")
                    title = a.get_attribute("title") or a.text
                    if link and title:
                        content_list.append({"url": link, "title": title.strip()})
                except: continue

            for content in content_list:
                slug = content['title'].replace(" ", "-").lower()
                if slug in results: continue

                print(f"-> Detay Alınıyor: {content['title']}")
                driver.get(content['url'])
                time.sleep(2)

                res = {"isim": content['title'], "resim": "", "bolumler": []}
                
                # Resim bul (Opsiyonel)
                try: res["resim"] = driver.find_element(By.TAG_NAME, "img").get_attribute("src")
                except: pass

                # Bölümleri bul
                eps = driver.find_elements(By.CSS_SELECTOR, "a[href*='bolum']")
                ep_links = [e.get_attribute("href") for e in eps]
                ep_links = list(dict.fromkeys(ep_links)) # Duplicate temizle

                if not ep_links:
                    # Film ise iframe al
                    iframe_src = driver.execute_script("return document.querySelector('iframe')?.src")
                    if iframe_src:
                        res["bolumler"].append({"bolum_baslik": "Film", "link": iframe_src})
                else:
                    # Dizi ise bölümlere hızlıca gir (İlk 5 bölüm test)
                    for i, url in enumerate(ep_links[:15], 1):
                        driver.get(url)
                        src = driver.execute_script("return document.querySelector('iframe')?.src")
                        if src:
                            res["bolumler"].append({"bolum_baslik": f"{i}. Bölüm", "link": src})

                results[slug] = res
                # Her döngüde dosyayı güncelle
                with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)

    finally:
        driver.quit()
        print(f"Bitti. Toplam: {len(results)} içerik.")

if __name__ == "__main__":
    scrape()
