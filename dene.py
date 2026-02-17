import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time
import json
import os
import subprocess
import re

# --- KRİTİK AYAR ---
# Eğer bu adres tarayıcıda açılmıyorsa güncel dizipal adresini buraya yazmalısın!
BASE_URL = "https://dizipal.cx" 
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
    options.add_argument('--window-size=1920,1080')
    # Cloudflare için gerçekçi bir user-agent
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    driver = uc.Chrome(options=options, version_main=version)
    results = {}

    try:
        print(f"Giris yapiliyor: {BASE_URL}")
        driver.get(BASE_URL)
        time.sleep(20) # Cloudflare geçişi için uzun süre (Gerekirse artır)

        for page in range(1, 3):
            target = f"{BASE_URL}/platform/{PLATFORM_SLUG}/page/{page}/"
            print(f"Sayfa taranıyor: {target}")
            driver.get(target)
            time.sleep(10) # Sayfanın render edilmesi için bekleme

            # EN GARANTİ SEÇİCİ: İçinde 'dizipal.cx/dizi' veya 'bolum' geçen tüm linkleri bul
            links = driver.find_elements(By.XPATH, "//a[contains(@href, '/dizi/') or contains(@href, '/film/')]")
            
            # Tekrar eden linkleri temizle ve listeye al
            content_list = []
            seen_urls = set()
            for l in links:
                url = l.get_attribute("href")
                title = l.get_attribute("title") or l.text
                if url and title and url not in seen_urls:
                    content_list.append({"url": url, "title": title})
                    seen_urls.add(url)

            print(f"Bulunan potansiyel icerik: {len(content_list)}")

            for content in content_list:
                slug = content['title'].replace(" ", "-").lower()
                if slug in results: continue

                print(f"-> Detay: {content['title']}")
                driver.get(content['url'])
                time.sleep(5)

                res = {"isim": content['title'], "bolumler": []}
                
                # Iframe yakala (Dizi bölümleri veya film player)
                iframes = driver.find_elements(By.TAG_NAME, "iframe")
                if iframes:
                    res["bolumler"].append({"bolum_baslik": "Video", "link": iframes[0].get_attribute("src")})

                # Bölüm linkleri varsa (Dizi ise)
                eps = driver.find_elements(By.CSS_SELECTOR, "a[href*='bolum']")
                for ep in eps[:5]: # HIZ İÇİN: Şimdilik her içerikten sadece 5 bölüm
                    res["bolumler"].append({
                        "bolum_baslik": ep.text,
                        "link": ep.get_attribute("href")
                    })

                results[slug] = res
                # Her icerikte dosyayı fiziksel olarak diske yaz
                with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)

    finally:
        driver.quit()
        print(f"Bitti. Toplam: {len(results)}")

if __name__ == "__main__":
    scrape()
