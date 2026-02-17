import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import re
import os
import html
import subprocess

# --- AYARLAR ---
BASE_URL = "https://dizipal.cx"
PLATFORM_SLUG = "hbomax"
OUTPUT_FILE = "hobi.json"

def get_chrome_main_version():
    try:
        output = subprocess.check_output(['google-chrome', '--version']).decode('utf-8')
        version = re.search(r'Google Chrome (\d+)', output).group(1)
        return int(version)
    except:
        return None

def get_options():
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    return options

def clean_key(text):
    text = html.unescape(text)
    text = re.sub(r'[\s\:\,\'’"”]+', '-', text)
    return text.strip('-')

def scrape():
    version = get_chrome_main_version()
    options = get_options()
    driver = uc.Chrome(options=options, version_main=version)
    
    results = {}
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                results = json.load(f)
        except: pass

    try:
        print("Ana sayfaya gidiliyor (Cloudflare Beklemesi)...")
        driver.get(BASE_URL)
        time.sleep(15) # Bekleme süresini artırdık

        for page_num in range(1, 3): # Test için 2 sayfa
            target_url = f"{BASE_URL}/platform/{PLATFORM_SLUG}/page/{page_num}/"
            print(f"Hedef: {target_url}")
            driver.get(target_url)
            time.sleep(5)

            # post-item yerine daha genel bir seçici deniyoruz (a etiketi içindeki yapılar)
            # Dizipal genellikle 'article' veya 'div.post-column' kullanır
            items = driver.find_elements(By.XPATH, "//div[contains(@class, 'post-item')] | //article")
            
            print(f"Bulunan element sayısı: {len(items)}")

            for item in items:
                try:
                    anchor = item.find_element(By.TAG_NAME, "a")
                    title = anchor.get_attribute("title") or anchor.text
                    if not title: continue
                    
                    key = clean_key(title)
                    if key in results: continue

                    url = anchor.get_attribute("href")
                    img_el = item.find_elements(By.TAG_NAME, "img")
                    img = img_el[0].get_attribute("src") if img_el else ""
                    
                    print(f"İçerik Bulundu: {title}")
                    
                    # Detay sayfasına geçiş
                    driver.execute_script(f"window.open('{url}', '_blank');")
                    driver.switch_to.window(driver.window_handles[1])
                    time.sleep(3)
                    
                    content_data = {"isim": title, "resim": img, "bolumler": []}
                    
                    # Bölüm linklerini bul (a tagları içinde 'bolum' geçenler)
                    source = driver.page_source
                    ep_links = list(set(re.findall(r'href="(https?://[^"]+bolum[^"]+)"', source)))
                    
                    if not ep_links:
                        iframe = driver.find_elements(By.TAG_NAME, "iframe")
                        if iframe:
                            content_data["bolumler"].append({"bolum_baslik": "Film/Tek Parça", "link": iframe[0].get_attribute("src")})
                    else:
                        for i, ep_url in enumerate(sorted(ep_links)[:10], 1): # Hız için ilk 10 bölüm
                            driver.get(ep_url)
                            time.sleep(1)
                            iframe_src = driver.execute_script("return document.querySelector('iframe')?.src")
                            if iframe_src:
                                content_data["bolumler"].append({"bolum_baslik": f"{i}. Bölüm", "link": iframe_src})

                    results[key] = content_data
                    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                        json.dump(results, f, ensure_ascii=False, indent=2)
                    
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                except Exception as e:
                    continue

    finally:
        driver.quit()
        print(f"Bitti. Toplam: {len(results)}")

if __name__ == "__main__":
    scrape()
