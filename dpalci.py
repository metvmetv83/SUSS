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
PROXY_BASE = "https://api.codetabs.com/v1/proxy/?quest="

def get_session_and_headers(base_url):
    """Siteden güncel çerezleri ve header bilgilerini toplar."""
    session = requests.Session()
    # Önce ana sayfaya gidip çerezleri alalım
    try:
        session.get(f"{PROXY_BASE}{base_url}", timeout=20)
    except:
        pass
    
    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Requested-With': 'XMLHttpRequest',
        'Origin': base_url,
        'Referer': f"{base_url}/",
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }
    return session, headers

def fetch_from_api(session, headers, base_url, type_val):
    all_extracted = []
    current_last_id = ""
    api_url = f"{base_url}/api/load-series"
    
    # CodeTabs proxy POST isteklerinde sorun çıkarabildiği için 
    # API isteğini doğrudan ama sağlam headerlarla deniyoruz.
    print(f"\n>>> API Taraması Başladı: Type={type_val}")
    
    for p in range(1, 6): # Test amaçlı 5 paket
        payload = {
            'date': current_last_id,
            'tur': '',
            'durum': '',
            'kelime': '',
            'type': type_val,
            'siralama': ''
        }
        
        try:
            print(f"Paket {p} isteniyor... (ID: {current_last_id})")
            # POST isteği
            res = session.post(api_url, data=payload, headers=headers, timeout=30)
            
            if res.status_code != 200:
                print(f"Hata Kodu: {res.status_code}")
                break
                
            # JSON yanıtını işle
            try:
                data_json = res.json()
                # PHP kodundaki implode mantığı: gelen veri bir liste ise birleştir
                html_content = "".join(data_json) if isinstance(data_json, list) else str(data_json)
            except:
                html_content = res.text

            if len(html_content) < 200:
                print("İçerik boş döndü.")
                break
            
            soup = BeautifulSoup(html_content, 'html.parser')
            items = soup.find_all('a', href=True)
            
            found_count = 0
            for a in items:
                # last_id güncellemesi için linkin id'sini al
                if a.has_attr('id'):
                    current_last_id = a['id']
                
                title_tag = a.find(class_='title') or a.find('h2')
                if title_tag:
                    title = title_tag.get_text(strip=True)
                    href = a['href']
                    full_link = href if href.startswith('http') else f"{base_url.rstrip('/')}/{href.lstrip('/')}"
                    all_extracted.append({"baslik": title, "url": full_link})
                    found_count += 1
            
            print(f"Başarılı: {found_count} içerik eklendi.")
            if found_count == 0: break
            time.sleep(1)

        except Exception as e:
            print(f"İstek sırasında hata: {e}")
            break
            
    return all_extracted

def main():
    target_url = "https://www.dizipal1226.com"
    session, headers = get_session_and_headers(target_url)

    # 1. Versiyon Güncelle
    if os.path.exists(GRADLE_PATH):
        with open(GRADLE_PATH, 'r') as f: content = f.read()
        v = re.search(r'version\s*=\s*(\d+)', content)
        if v:
            new_v = int(v.group(1)) + 1
            new_c = re.sub(r'version\s*=\s*\d+', f'version = {new_v}', content)
            with open(GRADLE_PATH, 'w') as f: f.write(new_c)
            print(f"Sürüm: {new_v}")

    # 2. API Çekimi
    results = []
    results.extend(fetch_from_api(session, headers, target_url, '1')) # Diziler
    results.extend(fetch_from_api(session, headers, target_url, '2')) # Filmler

    # 3. Kaydet
    unique_data = {item['url']: item for item in results}.values()
    with open('diziler.json', 'w', encoding='utf-8') as f:
        json.dump(list(unique_data), f, ensure_ascii=False, indent=4)
    
    print(f"\nSonuç: {len(unique_data)} içerik kaydedildi.")

if __name__ == "__main__":
    main()
