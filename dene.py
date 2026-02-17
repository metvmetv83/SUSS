import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time
import json
import re
import os
import html

# --- AYARLAR ---
BASE_URL = "https://dizipal.cx"
PLATFORM_SLUG = "hbomax"
OUTPUT_FILE = "hobii.json"

def get_options():
    options = uc.ChromeOptions()
    options.add_argument('--headless') # GitHub Actions için şart
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    # HIZLANDIRICI AYARLAR
    options.page_load_strategy = 'eager' 
    options.add_argument('--blink-settings=imagesEnabled=false') # Resim yok
    return options

def clean_key(text):
    text = html.unescape(text)
    text = re.sub(r'[\s\:\,\'’"”]+', '-', text)
    return text.strip('-')

def scrape():
    options = get_options()
    driver = uc.Chrome(options=options)
    
    results = {}
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            results = json.load(f)

    try:
        print("Giriş yapılıyor...")
        driver.get(BASE_URL)
        time.sleep(10) # CF için ilk bekleyiş

        page_num = 1
        while page_num <= 5: # Örnek: İlk 5 sayfayı tara
            print(f"Sayfa {page_num} taranıyor...")
            driver.get(f"{BASE_URL}/platform/{PLATFORM_SLUG}/page/{page_num}/")
            
            items = driver.find_elements(By.CLASS_NAME, "post-item")
            if not items: break

            content_links = []
            for item in items:
                try:
                    a = item.find_element(By.TAG_NAME, "a")
                    title = a.get_attribute("title")
                    key = clean_key(title)
                    if key not in results:
                        content_links.append({
                            "url": a.get_attribute("href"),
                            "title": title,
                            "key": key,
                            "img": item.find_element(By.TAG_NAME, "img").get_attribute("src")
                        })
                except: continue

            # İçerik Detayları (Daha hızlı döngü)
            for content in content_links:
                print(f"İşleniyor: {content['title']}")
                driver.get(content['url'])
                
                results[content['key']] = {
                    "isim": content['title'],
                    "resim": content['img'],
                    "bolumler": []
                }

                # Sayfadaki tüm bölüm linklerini tek seferde Regex ile topla (HIZLI)
                source = driver.page_source
                ep_links = list(set(re.findall(r'href="(https?://[^"]+bolum[^"]+)"', source)))
                
                if not ep_links: # Film ise
                    iframe_src = driver.execute_script("return document.querySelector('iframe')?.src")
                    if iframe_src:
                        results[content['key']]["bolumler"].append({"bolum_baslik": "Film", "link": iframe_src})
                else:
                    # Bölümleri gez
                    for i, ep_url in enumerate(sorted(ep_links), 1):
                        driver.get(ep_url)
                        # JS ile direkt src çek (WebDriverWait'ten daha hızlıdır)
                        src = driver.execute_script("return document.querySelector('iframe')?.src")
                        if src:
                            results[content['key']]["bolumler"].append({
                                "bolum_baslik": f"{i}. Bölüm",
                                "link": src
                            })
                
                # Her içerikten sonra kaydet (Veri kaybını önler)
                with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)

            page_num += 1

    finally:
        driver.quit()
        print("İşlem tamam.")

if __name__ == "__main__":
    scrape()
