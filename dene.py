import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time
import json
import re
import os
import html
import subprocess

# --- AYARLAR ---
BASE_URL = "https://dizipal.cx"
PLATFORM_SLUG = "hbomax"
OUTPUT_FILE = "hobii.json"

def get_chrome_main_version():
    """GitHub Actions üzerindeki Chrome sürümünü tespit eder"""
    try:
        output = subprocess.check_output(['google-chrome', '--version']).decode('utf-8')
        version = re.search(r'Google Chrome (\d+)', output).group(1)
        print(f"Sistemde bulunan Chrome versiyonu: {version}")
        return int(version)
    except Exception as e:
        print(f"Versiyon tespit edilemedi: {e}")
        return None

def get_options():
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.page_load_strategy = 'eager' # Sayfa iskeleti yüklenince devam et
    options.add_argument('--blink-settings=imagesEnabled=false') # Resimleri yükleme (HIZ)
    return options

def clean_key(text):
    text = html.unescape(text)
    text = re.sub(r'[\s\:\,\'’"”]+', '-', text)
    return text.strip('-')

def scrape():
    version = get_chrome_main_version()
    options = get_options()
    
    # version_main hatayı çözen kritik parametre
    driver = uc.Chrome(options=options, version_main=version)
    
    results = {}
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                results = json.load(f)
        except: pass

    try:
        print("Ana sayfaya gidiliyor...")
        driver.get(BASE_URL)
        time.sleep(10) # Cloudflare geçişi için bekleyiş

        for page_num in range(1, 6): # İlk 5 sayfayı tarar
            print(f"Sayfa {page_num} taranıyor...")
            driver.get(f"{BASE_URL}/platform/{PLATFORM_SLUG}/page/{page_num}/")
            
            items = driver.find_elements(By.CLASS_NAME, "post-item")
            if not items: break

            for item in items:
                try:
                    anchor = item.find_element(By.TAG_NAME, "a")
                    title = anchor.get_attribute("title")
                    key = clean_key(title)
                    
                    if key in results: continue

                    url = anchor.get_attribute("href")
                    img = item.find_element(By.TAG_NAME, "img").get_attribute("src")
                    
                    # İçerik detayına git
                    driver.execute_script(f"window.open('{url}', '_blank');")
                    driver.switch_to.window(driver.window_handles[1])
                    
                    time.sleep(2)
                    source = driver.page_source
                    ep_links = list(set(re.findall(r'href="(https?://[^"]+bolum[^"]+)"', source)))
                    
                    content_data = {"isim": title, "resim": img, "bolumler": []}

                    if not ep_links: # Film
                        src = driver.execute_script("return document.querySelector('iframe')?.src")
                        if src: content_data["bolumler"].append({"bolum_baslik": "Film", "link": src})
                    else: # Dizi
                        for i, ep_url in enumerate(sorted(ep_links), 1):
                            driver.get(ep_url)
                            src = driver.execute_script("return document.querySelector('iframe')?.src")
                            if src:
                                content_data["bolumler"].append({"bolum_baslik": f"{i}. Bölüm", "link": src})
                    
                    results[key] = content_data
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])

                    # Her içerik sonrası kaydet
                    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                        json.dump(results, f, ensure_ascii=False, indent=2)
                        
                except Exception as e:
                    print(f"Hata: {e}")
                    continue

    finally:
        driver.quit()
        print(f"İşlem bitti. Toplam {len(results)} içerik.")

if __name__ == "__main__":
    scrape()
