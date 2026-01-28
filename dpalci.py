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
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': f'{BASE_URL}/',
        'Accept': 'application/json, text/javascript, */*; q=0.01'
    }

def scrape_collection(session, category):
    results = []
    print(f"\n>>> {category.upper()} koleksiyonu derin taranıyor...")
    
    # 1. Aşama: Sayfanın ilk halini al (İlk 20 içerik)
    try:
        main_page = session.get(f"{BASE_URL}/koleksiyon/{category}", headers=get_headers(), timeout=20)
        html = main_page.text
    except:
        return []

    # İçerik ayıklama fonksiyonu (Regex ile daha hızlı)
    def extract_items(source):
        found = []
        # Link ve Başlık Yakala
        items = re.findall(r'<a[^>]+id="([^"]+)"[^>]+href="([^"]+)"[^>]*>.*?class="title">([^<]+)</span>', source, re.S)
        for item_id, href, title in items:
            full_url = href if href.startswith('http') else f"{BASE_URL}{href}"
            found.append({"id": item_id, "baslik": title.strip().upper(), "url": full_url})
        return found

    # İlk sayfa verilerini ekle
    first_batch = extract_items(html)
    results.extend(first_batch)
    print(f"  - İlk sayfa: {len(first_batch)} içerik bulundu.")

    # 2. Aşama: Kaydırdıkça yüklenen (AJAX) kısımları çek
    if results:
        last_id = results[-1]['id'] # En son dizinin ID'si (tarih/date değeri)
        
        for p in range(1, 10): # 10 kez "aşağı kaydır"
            payload = {
                'date': last_id,
                'tur': category,
                'type': '',
                'durum': '',
                'kelime': '',
                'siralama': ''
            }
            
            try:
                # API'ye POST atıyoruz
                response = session.post(f"{BASE_URL}/api/load-series", data=payload, headers=get_headers(), timeout=20)
                
                if response.status_code == 200:
                    data = response.json()
                    # Gelen JSON bir liste içindeki HTML bloklarıdır
                    ajax_html = "".join(data) if isinstance(data, list) else str(data)
                    
                    new_items = extract_items(ajax_html)
                    if not new_items:
                        break
                        
                    results.extend(new_items)
                    last_id = new_items[-1]['id'] # ID güncelle
                    print(f"  - Kaydırma {p}: +{len(new_items)} içerik eklendi. (Yeni ID: {last_id})")
                    time.sleep(1) # Ban yememek için
                else:
                    break
            except Exception as e:
                print(f"  - Kaydırma hatası: {e}")
                break
                
    return results

def main():
    session = requests.Session()
    # Çerezleri kabul etmek için ana sayfaya bir kez git
    session.get(BASE_URL, headers=get_headers())

    # Versiyon güncelleme
    if os.path.exists(GRADLE_PATH):
        with open(GRADLE_PATH, 'r') as f: content = f.read()
        v = re.search(r'version\s*=\s*(\d+)', content)
        if v:
            new_v = int(v.group(1)) + 1
            with open(GRADLE_PATH, 'w') as f: 
                f.write(re.sub(r'version\s*=\s*\d+', f'version = {new_v}', content))

    # Tarama
    final_data = []
    cats = ["exxen", "netflix", "gain", "disney", "blutv"]
    
    for c in cats:
        final_data.extend(scrape_collection(session, c))

    # Tekilleştirme
    unique = {x['url']: x for x in final_data}.values()
    
    with open('diziler.json', 'w', encoding='utf-8') as f:
        json.dump(list(unique), f, ensure_ascii=False, indent=4)

    print(f"\nİşlem bitti! Toplam {len(unique)} içerik kaydedildi.")

if __name__ == "__main__":
    main()
