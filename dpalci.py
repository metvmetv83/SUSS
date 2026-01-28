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

# Dosya Yolları
KT_PATH = "DiziPal/src/main/kotlin/com/Pitipitii/DiziPal.kt"
GRADLE_PATH = "DiziPal/build.gradle.kts"
PROXY_BASE = "https://api.codetabs.com/v1/proxy/?quest="

def get_headers(base_url):
    return {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Origin': base_url,
        'Referer': f"{base_url}/",
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest'
    }

def fetch_from_api(base_url, type_val, tur_val=""):
    """DiziPal API'sini taklit ederek içerikleri çeker."""
    all_extracted = []
    current_last_id = "" # PHP'deki $last değişkeni
    api_url = f"{base_url}/api/load-series"
    
    print(f"\n>>> API Taraması Başladı: Type={type_val}, Tur={tur_val}")
    
    # 10 sayfa derinliğe kadar in (İhtiyaca göre artırılabilir)
    for p in range(1, 11):
        payload = {
            'date': current_last_id,
            'tur': tur_val,
            'durum': '',
            'kelime': '',
            'type': type_val,
            'siralama': ''
        }
        
        try:
            # Proxy üzerinden POST isteği at
            # Not: Bazı proxy'ler POST desteklemeyebilir, desteklemezse doğrudan requests.post kullanın
            print(f"Paket {p} çekiliyor (LastID: {current_last_id})...")
            res = requests.post(api_url, data=payload, headers=get_headers(base_url), timeout=30)
            
            if res.status_code != 200:
                print(f"API Hatası: {res.status_code}")
                break
            
            # API JSON içinde HTML döndürüyor (PHP'deki implode mantığı)
            data_json = res.json()
            html_content = "".join(data_json) if isinstance(data_json, list) else data_json
            
            if not html_content or len(html_content) < 100:
                print("Daha fazla içerik yok.")
                break
            
            soup = BeautifulSoup(html_content, 'html.parser')
            items = soup.find_all('a', href=True)
            
            last_item_id = ""
            found_count = 0
            
            for a in items:
                # PHP kodundaki 'data-date' veya 'id' kısmını last_id olarak yakala
                # Genelde <a> etiketinin id'si last_id olur
                if a.has_attr('id'):
                    last_item_id = a['id']
                
                title_tag = a.find(class_='title')
                img_tag = a.find('img')
                imdb_tag = a.find(class_='vote')
                
                if title_tag:
                    title = title_tag.get_text(strip=True)
                    url = a['href']
                    img = img_tag['src'] if img_tag else ""
                    imdb = imdb_tag.get_text(strip=True) if imdb_tag else "0"
                    
                    all_extracted.append({
                        "baslik": title,
                        "url": url if url.startswith('http') else f"{base_url.rstrip('/')}/{url.lstrip('/')}",
                        "imdb": imdb,
                        "resim": img
                    })
                    found_count += 1
            
            print(f"Paket {p} bitti. +{found_count} içerik bulundu.")
            
            # Bir sonraki istek için last_id güncelle
            if last_item_id:
                current_last_id = last_item_id
            else:
                break # Yeni ID yoksa dur
                
            time.sleep(1) # Ban koruması
            
        except Exception as e:
            print(f"API İstek Hatası: {e}")
            break
            
    return all_extracted

def main():
    target_url = "https://www.dizipal1226.com"
    
    # 1. Dosya Güncellemeleri
    if os.path.exists(KT_PATH):
        with open(KT_PATH, 'r', encoding='utf-8') as f: content = f.read()
        new_content = re.sub(r'override var mainUrl = ".*?"', f'override var mainUrl = "{target_url}"', content)
        with open(KT_PATH, 'w', encoding='utf-8') as f: f.write(new_content)

    if os.path.exists(GRADLE_PATH):
        with open(GRADLE_PATH, 'r', encoding='utf-8') as f: g_content = f.read()
        v_match = re.search(r'version\s*=\s*(\d+)', g_content)
        if v_match:
            new_v = int(v_match.group(1)) + 1
            new_g = re.sub(r'version\s*=\s*\d+', f'version = {new_v}', g_content)
            with open(GRADLE_PATH, 'w', encoding='utf-8') as f: f.write(new_g)

    # 2. Veri Çekme (Diziler=1, Filmler=2 - API tiplerine göre ayarla)
    final_results = []
    # PHP kodundaki 'typez' parametresine göre döngü
    final_results.extend(fetch_from_api(target_url, type_val='1')) # Diziler
    final_results.extend(fetch_from_api(target_url, type_val='2')) # Filmler

    # 3. Tekilleştirme ve Kaydet
    unique_data = []
    seen = set()
    for item in final_results:
        if item['url'] not in seen:
            unique_data.append(item)
            seen.add(item['url'])

    with open('diziler.json', 'w', encoding='utf-8') as f:
        json.dump(unique_data, f, ensure_ascii=False, indent=4)

    print(f"\nİşlem Başarıyla Tamamlandı! Toplam {len(unique_data)} içerik çekildi.")

if __name__ == "__main__":
    main()
