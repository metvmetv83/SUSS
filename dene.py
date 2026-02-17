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
OUTPUT_FILE = "hobii.json"

def get_chrome_version():
    try:
        output = subprocess.check_output(['google-chrome', '--version']).decode('utf-8')
        version = re.search(r'Google Chrome (\d+)', output).group(1)
        return int(version)
    except:
        return None

def scrape_hbomax():
    version = get_chrome_version()
    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    # HIZ İÇİN: Resimleri ve gereksiz render işlemlerini kapat
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
            print(f"\n--- Sayfa {page_num} Taranıyor ---")
            driver.get(platform_url)
            time.sleep(2)

            items = driver.find_elements(By.CLASS_NAME, "post-item")
            if not items: break

            page_contents = []
            for item in items:
                try:
                    anchor = item.find_element(By.TAG_NAME, "a")
                    title = anchor.get_attribute("title")
                    key = title.replace(" ", "-").lower() # Basit key temizliği
                    
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
                    print(f"> {content['title']} inceleniyor...")
                    driver.get(content['url'])
                    
                    # Sayfa kaynağındaki tüm bölüm linklerini REGEX ile anında bul
                    # Selenium ile tek tek arama yapmaktan çok daha hızlıdır
                    source = driver.page_source
                    ep_links = sorted(list(set(re.findall(r'href="(https?://[^"]+bolum[^"]+)"', source))))

                    results[content['key']] = {
                        "isim": content['title'],
                        "resim": content['img'],
                        "bolumler": []
                    }

                    if not ep_links:
                        # Film Senaryosu: JS ile direkt iframe src'yi al
                        iframe_src = driver.execute_script("return document.querySelector('iframe')?.src")
                        if iframe_src:
                            results[content['key']]["bolumler"].append({"bolum_baslik": "Film", "link": iframe_src})
                    else:
                        # Dizi Senaryosu: Sadece ilk ve son sayfaya bakarak hızlanabiliriz
                        # Şimdilik hepsini gezer ama hızlı modda
                        for i, ep_url in enumerate(ep_links, 1):
                            driver.get(ep_url)
                            # Beklemeden JS ile iframe sorgula
                            iframe_src = driver.execute_script("return document.querySelector('iframe')?.src")
                            if iframe_src:
                                results[content['key']]["bolumler"].append({
                                    "bolum_baslik": f"{i}. Bolum",
                                    "link": iframe_src
                                })
                            if i >= 20: break # Hız için bölüm sınırlaması (isteğe bağlı)

                    # Her içerik bittiğinde kaydet (Yarıda kalırsa veri gitmez)
                    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                        json.dump(results, f, ensure_ascii=False, indent=2)

                except Exception as e:
                    print(f"Hata: {content['title']} -> {e}")

            page_num += 1
            if page_num > 10: break # Çok fazla sayfa varsa sınırla

    finally:
        driver.quit()
        print(f"İşlem tamamlandı. Toplam {len(results)} içerik.")

if __name__ == "__main__":
    scrape_hbomax()
