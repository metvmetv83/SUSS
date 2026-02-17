import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import re
import subprocess
import os
import html

# --- AYARLAR ---
BASE_URL = "https://dizipal.cx"
PLATFORM_SLUG = "hbomax"
OUTPUT_FILE = "hobi.json"

def get_chrome_version():
    try:
        output = subprocess.check_output(['google-chrome', '--version']).decode('utf-8')
        version = re.search(r'Google Chrome (\d+)', output).group(1)
        return int(version)
    except:
        return None

def clean_key(text):
    text = html.unescape(text)
    text = re.sub(r'[\s\:\,\'’"”]+', '-', text)
    return text.strip('-')

def scrape_hbomax():
    version = get_chrome_version()
    print(f"Sistem Chrome Versiyonu: {version}")

    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    # HIZLANDIRICI AYARLAR: Resimleri ve gereksiz render işlemlerini engelle
    options.add_argument('--blink-settings=imagesEnabled=false')
    options.page_load_strategy = 'eager' 

    results = {}
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                results = json.load(f)
        except: pass

    driver = uc.Chrome(options=options, version_main=version)

    try:
        print("Cloudflare gecisi bekleniyor...")
        driver.get(BASE_URL)
        time.sleep(12) 

        page_num = 1
        while True:
            platform_url = f"{BASE_URL}/platform/{PLATFORM_SLUG}/page/{page_num}/"
            print(f"\n--- Sayfa {page_num} ---")
            driver.get(platform_url)
            
            # Sayfa yuklenene kadar kısa bekleme
            time.sleep(2)

            items = driver.find_elements(By.CLASS_NAME, "post-item")
            if not items:
                print("Icerik bulunamadi veya bitti.")
                break

            page_contents = []
            for item in items:
                try:
                    anchor = item.find_element(By.TAG_NAME, "a")
                    title = anchor.get_attribute("title")
                    key = clean_key(title)
                    if key in results: continue

                    page_contents.append({
                        "title": title,
                        "url": anchor.get_attribute("href"),
                        "img": item.find_element(By.TAG_NAME, "img").get_attribute("src"),
                        "key": key
                    })
                except: continue

            for content in page_contents:
                try:
                    print(f" Taraniyor: {content['title']}")
                    driver.get(content['url'])
                    
                    results[content['key']] = {
                        "isim": content['title'],
                        "resim": content['img'],
                        "bolumler": []
                    }

                    # Sayfa kaynagını tek seferde al ve Regex ile tum bolum linklerini ayıkla
                    # Bu islem driver.find_elements'den cok daha hızlıdır
                    source = driver.page_source
                    all_ep_links = sorted(list(set(re.findall(r'href="(https?://[^"]+bolum[^"]+)"', source))))

                    if not all_ep_links:
                        # Film senaryosu: Direkt iframe src al
                        iframe_src = driver.execute_script("return document.querySelector('iframe')?.src")
                        if iframe_src:
                            results[content['key']]["bolumler"].append({"bolum_baslik": "Film", "link": iframe_src})
                    else:
                        # Dizi senaryosu
                        for i, ep_url in enumerate(all_ep_links, 1):
                            driver.get(ep_url)
                            # Bekleme yapmadan JS ile iframe sorgula
                            iframe_src = driver.execute_script("return document.querySelector('iframe')?.src")
                            if iframe_src:
                                results[content['key']]["bolumler"].append({
                                    "bolum_baslik": f"{i}. Bolum",
                                    "link": iframe_src
                                })

                    # Anlık kaydet
                    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                        json.dump(results, f, ensure_ascii=False, indent=2)

                except Exception as e:
                    print(f"Hata: {content['title']} -> {e}")

            page_num += 1
            if page_num > 5: break # Sonsuz donguye girmemesi icin limit

    finally:
        driver.quit()
        print(f"Tamamlandi. {len(results)} icerik.")

if __name__ == "__main__":
    scrape_hbomax()
