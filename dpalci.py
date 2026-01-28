import requests
import re
import os
import json
import time

KT_PATH = "DiziPal/src/main/kotlin/com/Pitipitii/DiziPal.kt"
GRADLE_PATH = "DiziPal/build.gradle.kts"
BASE_URL = "https://www.dizipal1226.com"

def get_headers():
    return {
        'authority': 'www.dizipal1226.com',
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': BASE_URL,
        'referer': f'{BASE_URL}/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest'
    }

def scrape_collection(category):
    session = requests.Session()
    results = []
    print(f"\n>>> {category.upper()} Koleksiyonu taranıyor...")

    try:
        # 1. Aşama: İlk sayfayı çekip başlangıç verisini al
        init_res = session.get(f"{BASE_URL}/koleksiyon/{category}", headers=get_headers(), timeout=20)
        
        # Regex ile hem ID (Date) hem Link hem Başlık çekiyoruz
        # Kalıp: <a id="[DATE]" href="[LINK]">...<span class="title">[TITLE]</span>
        pattern = r'<a[^>]+id="([^"]+)"[^>]+href="([^"]+)"[^>]*>.*?class="title">([^<]+)</span>'
        initial_items = re.findall(pattern, init_res.text, re.DOTALL)
        
        for item_id, href, title in initial_items:
            full_url = href if href.startswith('http') else f"{BASE_URL}{href}"
            results.append({"id": item_id, "baslik": title.strip().upper(), "url": full_url})
        
        if not results:
            print("  - İlk sayfa boş döndü. Manuel regex denemesi yapılıyor...")
            return []

        print(f"  - Başlangıç: {len(results)} içerik bulundu.")
        
        # 2. Aşama: Infinite Scroll (Sonsuz Kaydırma) Simülasyonu
        # PHP kodundaki $last = $_GET['last_id'] mantığı burada 'date' olarak gider.
        last_id = results[-1]['id']
        
        for p in range(1, 8): # 7 sayfa derinliğe in (~200+ içerik)
            payload = {
                'date': last_id,
                'tur': category,
                'durum': '',
                'kelime': '',
                'type': '',
                'siralama': ''
            }
            
            # API'den yeni partiyi iste
            api_res = session.post(f"{BASE_URL}/api/load-series", data=payload, headers=get_headers(), timeout=20)
            
            if api_res.status_code == 200:
                data = api_res.json()
                html_chunk = "".join(data) if isinstance(data, list) else str(data)
                
                new_items = re.findall(pattern, html_chunk, re.DOTALL)
                
                if not new_items:
                    break
                
                batch_count = 0
                for n_id, n_href, n_title in new_items:
                    n_url = n_href if n_href.startswith('http') else f"{BASE_URL}{n_href}"
                    results.append({"id": n_id, "baslik": n_title.strip().upper(), "url": n_url})
                    last_id = n_id # Bir sonraki istek için en güncel ID
                    batch_count += 1
                
                print(f"  - Kaydırma {p}: +{batch_count} yeni içerik.")
                time.sleep(1)
            else:
                break

    except Exception as e:
        print(f"  - Hata oluştu: {e}")
        
    return results

def main():
    # Versiyonu otomatik artır
    if os.path.exists(GRADLE_PATH):
        with open(GRADLE_PATH, 'r') as f: content = f.read()
        v = re.search(r'version\s*=\s*(\d+)', content)
        if v:
            new_v = int(v.group(1)) + 1
            with open(GRADLE_PATH, 'w') as f: 
                f.write(re.sub(r'version\s*=\s*\d+', f'version = {new_v}', content))
            print(f"Versiyon Yükseltildi: {new_v}")

    final_results = []
    # En popüler koleksiyonlar
    categories = ["exxen", "netflix", "gain", "disney", "blutv", "beindizi"]
    
    for cat in categories:
        final_results.extend(scrape_collection(cat))

    # Tekilleştirme
    unique_data = {item['url']: item for item in final_results}.values()
    
    # JSON Kaydet
    with open('diziler.json', 'w', encoding='utf-8') as f:
        json.dump(list(unique_data), f, ensure_ascii=False, indent=4)

    print(f"\nİşlem Tamamlandı! Toplam {len(unique_data)} içerik dev arşive eklendi.")

if __name__ == "__main__":
    main()
