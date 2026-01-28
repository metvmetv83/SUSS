import requests
import re
import os
import json
import sys
import time

try:
    from bs4 import BeautifulSoup
except ImportError:
    sys.exit(1)

KT_PATH = "DiziPal/src/main/kotlin/com/Pitipitii/DiziPal.kt"
GRADLE_PATH = "DiziPal/build.gradle.kts"
API_URL = "https://www.dizipal1226.com/api/load-series"

def get_headers():
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Referer': 'https://www.dizipal1226.com/'
    }

def fetch_deep_collection(category_name):
    """Koleksiyonun dibine kadar API üzerinden iner."""
    results = []
    last_id = "" # PHP'deki $last_id
    
    print(f"\n>>> {category_name.upper()} Arşivi Derin Taranıyor...")
    
    # 10 'Daha Fazla Göster' tıklaması simüle et (Her tık ~30 içerik)
    for p in range(1, 11):
        payload = {
            'date': last_id,
            'tur': category_name, # exxen, netflix vb.
            'durum': '',
            'kelime': '',
            'type': '', # Boş bırakılırsa tümünü getirir
            'siralama': ''
        }
        
        try:
            # Doğrudan POST isteği (Proxy bazen POST bozduğu için direkt deniyoruz)
            res = requests.post(API_URL, data=payload, headers=get_headers(), timeout=20)
            
            if res.status_code != 200: break
            
            data = res.json()
            # Gelen veri HTML listesi ise birleştir
            html = "".join(data) if isinstance(data, list) else data
            
            if not html or len(html) < 200:
                print(f"  - {p}. sayfada içerik bitti.")
                break
                
            soup = BeautifulSoup(html, 'html.parser')
            items = soup.find_all('a', href=True)
            
            found_count = 0
            for a in items:
                # Bir sonraki istek için ID'yi güncelle (PHP'deki id=id mantığı)
                if a.has_attr('id'):
                    last_id = a['id']
                
                title_tag = a.find(class_='title')
                if title_tag:
                    title = title_tag.get_text(strip=True).upper()
                    href = a['href']
                    full_link = href if href.startswith('http') else f"https://www.dizipal1226.com{href}"
                    
                    results.append({"baslik": title, "url": full_link})
                    found_count += 1
            
            print(f"  - Paket {p}: +{found_count} içerik çekildi. (Son ID: {last_id})")
            if found_count == 0: break
            time.sleep(0.5) # Sunucuyu kızdırmayalım
            
        except Exception as e:
            print(f"  - Hata: {e}")
            break
            
    return results

def main():
    # 1. Versiyon Güncelle
    if os.path.exists(GRADLE_PATH):
        with open(GRADLE_PATH, 'r') as f: content = f.read()
        v = re.search(r'version\s*=\s*(\d+)', content)
        if v:
            new_v = int(v.group(1)) + 1
            new_c = re.sub(r'version\s*=\s*\d+', f'version = {new_v}', content)
            with open(GRADLE_PATH, 'w') as f: f.write(new_c)

    # 2. Tüm Koleksiyonları API ile tara
    all_data = []
    # En büyük koleksiyonlar
    kategoriler = ["exxen", "netflix", "gain", "disney", "beindizi", "blutv"]
    
    for kat in kategoriler:
        all_data.extend(fetch_deep_collection(kat))

    # 3. Tekilleştirme ve Temizlik
    unique_data = []
    seen = set()
    for item in all_data:
        if item['url'] not in seen and len(item['baslik']) > 2:
            unique_data.append(item)
            seen.add(item['url'])

    with open('diziler.json', 'w', encoding='utf-8') as f:
        json.dump(unique_data, f, ensure_ascii=False, indent=4)

    print(f"\n--- İŞLEM TAMAMLANDI ---")
    print(f"Toplam {len(unique_data)} benzersiz içerik dev arşive eklendi!")

if __name__ == "__main__":
    main()
