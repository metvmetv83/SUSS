import requests
import re
import os
import json
import time
from urllib.parse import quote

# Dosya Yolları
KT_PATH = "DiziPal/src/main/kotlin/com/Pitipitii/DiziPal.kt"
GRADLE_PATH = "DiziPal/build.gradle.kts"
BASE_URL = "https://www.dizipal1226.com"
PROXY_BASE = "https://api.codetabs.com/v1/proxy/?quest="

def get_headers():
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest'
    }

def scrape_titan_ultra(category):
    results = []
    last_id = ""
    
    print(f"\n>>> {category.upper()} Arşivi Kazılıyor...")

    # 1. Aşama: İlk Sayfayı Çek
    try:
        target = f"{BASE_URL}/koleksiyon/{category}"
        url = PROXY_BASE + quote(target)
        res = requests.get(url, headers=get_headers(), timeout=30)
        html = res.text
        
        # İçerik ayıklama (Regex)
        items = re.findall(r'<a[^>]+id="([^"]+)"[^>]+href="([^"]+)"[^>]*>.*?class="title">([^<]+)</span>', html, re.DOTALL)
        
        for item_id, href, title in items:
            full_link = href if href.startswith('http') else f"{BASE_URL}{href}"
            results.append({"baslik": title.strip().upper(), "url": full_link})
            last_id = item_id # Son çekilenin ID'si

        print(f"  - Başlangıç: {len(results)} içerik.")

        # 2. Aşama: API'yi GET parametreleriyle zorla (Lazy Load Bypass)
        # Sitenin API'si ?date=... formatını destekliyor mu deniyoruz
        for p in range(1, 6):
            if not last_id: break
            
            # API URL'sini GET parametreleriyle oluşturuyoruz
            api_call = f"{BASE_URL}/api/load-series?date={last_id}&tur={category}&type=&durum=&kelime=&siralama="
            proxied_api = PROXY_BASE + quote(api_call)
            
            api_res = requests.get(proxied_api, headers=get_headers(), timeout=20)
            if api_res.status_code == 200:
                try:
                    ajax_data = api_res.json()
                    ajax_html = "".join(ajax_data) if isinstance(ajax_data, list) else str(ajax_data)
                    
                    new_items = re.findall(r'<a[^>]+id="([^"]+)"[^>]+href="([^"]+)"[^>]*>.*?class="title">([^<]+)</span>', ajax_html, re.DOTALL)
                    
                    if not new_items: break
                    
                    for n_id, n_href, n_title in new_items:
                        n_url = n_href if n_href.startswith('http') else f"{BASE_URL}{n_href}"
                        results.append({"baslik": n_title.strip().upper(), "url": n_url})
                        last_id = n_id
                    
                    print(f"  - Derinlik {p}: +{len(new_items)} yeni içerik eklendi.")
                    time.sleep(1)
                except: break
            else: break

    except Exception as e:
        print(f"  - Hata: {e}")
        
    return results

def main():
    # Versiyon Güncelle
    if os.path.exists(GRADLE_PATH):
        with open(GRADLE_PATH, 'r') as f: content = f.read()
        v = re.search(r'version\s*=\s*(\d+)', content)
        if v:
            new_v = int(v.group(1)) + 1
            with open(GRADLE_PATH, 'w') as f: f.write(re.sub(r'version\s*=\s*\d+', f'version = {new_v}', content))
            print(f"Yeni Sürüm Hazırlanıyor: {new_v}")

    # Koleksiyonlar
    kats = ["exxen", "netflix", "gain", "disney", "blutv"]
    all_data = []
    for k in kats:
        all_data.extend(scrape_titan_ultra(k))

    # Tekilleştirme
    unique = {x['url']: x for x in all_data}.values()
    
    with open('diziler.json', 'w', encoding='utf-8') as f:
        json.dump(list(unique), f, ensure_ascii=False, indent=4)

    print(f"\n--- İŞLEM TAMAMLANDI ---")
    print(f"Toplam {len(unique)} benzersiz içerik dev arşive eklendi.")

if __name__ == "__main__":
    main()
