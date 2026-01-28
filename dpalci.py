import requests
import re
import os
import json
import time
from urllib.parse import quote

# Ayarlar
GRADLE_PATH = "DiziPal/build.gradle.kts"
BASE_URL = "https://www.dizipal1226.com"
PROXY_BASE = "https://api.codetabs.com/v1/proxy/?quest="

def get_headers():
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'Origin': BASE_URL,
        'Referer': f'{BASE_URL}/'
    }

def scrape_titan_deep(category):
    results = []
    session = requests.Session()
    last_id = "" 
    
    print(f"\n>>> {category.upper()} Koleksiyonu taranıyor...")

    # 1. Aşama: İlk Sayfayı Proxy ile çek (Engeli aşmak için)
    try:
        target = f"{BASE_URL}/koleksiyon/{category}"
        url = PROXY_BASE + quote(target)
        res = session.get(url, headers=get_headers(), timeout=30)
        html = res.text
        
        # Senin çalışan regex mantığın
        items = re.findall(r'<a[^>]+id="([^"]+)"[^>]+href="([^"]+)"[^>]*>.*?class="title">([^<]+)</span>', html, re.DOTALL)
        
        for item_id, href, title in items:
            full_link = href if href.startswith('http') else f"{BASE_URL}{href}"
            results.append({"baslik": title.strip().upper(), "url": full_link})
            last_id = item_id # Kaydırma için son ID'yi sakla

        print(f"  - İlk sayfa: {len(results)} içerik alındı.")

        # 2. Aşama: API ile "Daha Fazla" (Proxy'SİZ - Direkt POST)
        # API genellikle ana sayfa kadar sert korunmaz.
        for p in range(1, 15): # 15 sayfa derinliğe in (~450 içerik)
            if not last_id: break
            
            payload = {
                'date': last_id,
                'tur': category,
                'type': '', 'durum': '', 'kelime': '', 'siralama': ''
            }
            
            try:
                # Proxy'yi devreden çıkarıp direkt siteye soruyoruz
                api_res = requests.post(f"{BASE_URL}/api/load-series", data=payload, headers=get_headers(), timeout=15)
                
                if api_res.status_code == 200:
                    ajax_data = api_res.json()
                    ajax_html = "".join(ajax_data) if isinstance(ajax_data, list) else str(ajax_data)
                    
                    # Yeni gelenleri ayıkla
                    new_batch = re.findall(r'<a[^>]+id="([^"]+)"[^>]+href="([^"]+)"[^>]*>.*?class="title">([^<]+)</span>', ajax_html, re.DOTALL)
                    
                    if not new_batch: break
                    
                    for n_id, n_href, n_title in new_batch:
                        n_url = n_href if n_href.startswith('http') else f"{BASE_URL}{n_href}"
                        results.append({"baslik": n_title.strip().upper(), "url": n_url})
                        last_id = n_id 
                    
                    print(f"  - Kaydırma {p}: +{len(new_batch)} içerik.")
                    time.sleep(0.5)
                else:
                    break
            except:
                break

    except Exception as e:
        print(f"  - Hata: {e}")
        
    return results

def main():
    # Sürüm artır
    if os.path.exists(GRADLE_PATH):
        with open(GRADLE_PATH, 'r') as f: content = f.read()
        v = re.search(r'version\s*=\s*(\d+)', content)
        if v:
            new_v = int(v.group(1)) + 1
            with open(GRADLE_PATH, 'w') as f: f.write(re.sub(r'version\s*=\s*\d+', f'version = {new_v}', content))
            print(f"Yeni Sürüm: {new_v}")

    # Koleksiyonlar
    kats = ["exxen", "netflix", "gain", "disney", "beindizi", "blutv"]
    all_data = []
    for k in kats:
        all_data.extend(scrape_titan_deep(k))

    # Tekilleştirme
    unique = {x['url']: x for x in all_data}.values()
    
    with open('diziler.json', 'w', encoding='utf-8') as f:
        json.dump(list(unique), f, ensure_ascii=False, indent=4)

    print(f"\n--- BİTTİ ---")
    print(f"Toplam {len(unique)} içerik dev arşive eklendi!")

if __name__ == "__main__":
    main()
