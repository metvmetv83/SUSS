import requests
import re
import os
import json
import time
from urllib.parse import quote

# Ayarlar
GRADLE_PATH = "DiziPal/build.gradle.kts"
BASE_URL = "https://www.dizipal1226.com"
# Codetabs yerine AllOrigins kullanıyoruz (Daha stabil)
PROXY_BASE = "https://api.allorigins.win/get?url="

def get_headers():
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

def scrape_titan_deep(category):
    results = []
    last_id = "" 
    
    print(f"\n>>> {category.upper()} Koleksiyonu taranıyor...")

    try:
        # 1. Aşama: İlk Sayfayı AllOrigins ile çek
        target = f"{BASE_URL}/koleksiyon/{category}"
        url = PROXY_BASE + quote(target)
        res = requests.get(url, headers=get_headers(), timeout=30)
        
        if res.status_code == 200:
            # AllOrigins veriyi 'contents' anahtarı içinde string olarak döner
            data = res.json()
            html = data.get('contents', '')
            
            # Daha geniş kapsamlı regex: ID, Link ve Başlığı aynı anda yakala
            # Site yapısı değişse bile 'id', 'href' ve 'title' üçlüsünü arar
            items = re.findall(r'id="([^"]+)"[^>]+href="([^"]+)"[^>]*>.*?class="title">([^<]+)</span>', html, re.DOTALL)
            
            if not items:
                # Yedek Regex: Eğer id yoksa sadece link ve başlık al
                items = re.findall(r'href="([^"]+)"[^>]*>.*?class="title">([^<]+)</span>', html, re.DOTALL)

            for match in items:
                # Regex sonucuna göre eşleştirme (id varsa 3, yoksa 2 grup döner)
                if len(match) == 3:
                    item_id, href, title = match
                    last_id = item_id
                else:
                    href, title = match
                
                full_link = href if href.startswith('http') else f"{BASE_URL}{href}"
                results.append({"baslik": title.strip().upper(), "url": full_link})

            print(f"  - İlk sayfa: {len(results)} içerik alındı.")
            
            # 2. Aşama: Derin Tarama (Kaydırma)
            # Proxy üzerinden GET parametresiyle API'yi zorluyoruz
            if last_id:
                for p in range(1, 10):
                    api_target = f"{BASE_URL}/api/load-series?date={last_id}&tur={category}"
                    api_url = PROXY_BASE + quote(api_target)
                    
                    api_res = requests.get(api_url, headers=get_headers(), timeout=20)
                    if api_res.status_code == 200:
                        ajax_html = api_res.json().get('contents', '')
                        new_batch = re.findall(r'id="([^"]+)"[^>]+href="([^"]+)"[^>]*>.*?class="title">([^<]+)</span>', ajax_html, re.DOTALL)
                        
                        if not new_batch: break
                        
                        for n_id, n_href, n_title in new_batch:
                            n_url = n_href if n_href.startswith('http') else f"{BASE_URL}{n_href}"
                            results.append({"baslik": n_title.strip().upper(), "url": n_url})
                            last_id = n_id
                        
                        print(f"  - Kaydırma {p}: +{len(new_batch)} içerik.")
                        time.sleep(1)
                    else: break

    except Exception as e:
        print(f"  - Hata oluştu: {e}")
        
    return results

def main():
    if os.path.exists(GRADLE_PATH):
        with open(GRADLE_PATH, 'r') as f: content = f.read()
        v = re.search(r'version\s*=\s*(\d+)', content)
        if v:
            new_v = int(v.group(1)) + 1
            with open(GRADLE_PATH, 'w') as f: f.write(re.sub(r'version\s*=\s*\d+', f'version = {new_v}', content))
            print(f"Yeni Sürüm: {new_v}")

    kats = ["exxen", "netflix", "gain", "disney", "blutv"]
    all_data = []
    for k in kats:
        all_data.extend(scrape_titan_deep(k))

    unique = {x['url']: x for x in all_data}.values()
    
    with open('diziler.json', 'w', encoding='utf-8') as f:
        json.dump(list(unique), f, ensure_ascii=False, indent=4)

    print(f"\n--- BİTTİ ---")
    print(f"Toplam {len(unique)} içerik kaydedildi.")

if __name__ == "__main__":
    main()
