import requests
import re
import os
import json
import time
from urllib.parse import quote

GRADLE_PATH = "DiziPal/build.gradle.kts"
BASE_URL = "https://www.dizipal1226.com"
PROXY_BASE = "https://api.allorigins.win/get?url="

def get_headers():
    return {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'}

def fetch_data(url):
    try:
        proxied_url = PROXY_BASE + quote(url)
        res = requests.get(proxied_url, headers=get_headers(), timeout=25)
        if res.status_code == 200:
            return res.json().get('contents', '')
    except:
        return ""
    return ""

def scrape_path(path_name, is_full_url=False):
    results = []
    # Eğer path tam URL değilse BASE_URL ile birleştir
    clean_path = path_name if is_full_url else f"{BASE_URL}/{path_name}"
    print(f"\n>>> {path_name.upper()} taranıyor...")

    # Her kategori için 5 sayfa derinlik (Hız ve verimlilik dengesi)
    for p in range(1, 6):
        target = clean_path + (f"/page/{p}/" if p > 1 else "/")
        # Koleksiyonlar bazen ?paged= kullanır, diziler/filmler /page/ kullanır. 
        # İkisini de kapsamak için yedekli deneme yapıyoruz.
        
        html = fetch_data(target)
        if not html: break
            
        # Gelişmiş Regex: Başlık ve Linkleri yakalar
        items = re.findall(r'href="([^"]+)"[^>]*>.*?class="title">([^<]+)</span>', html, re.DOTALL)
        if not items:
            items = re.findall(r'class="title">.*?<a href="([^"]+)">([^<]+)</a>', html, re.DOTALL)

        if not items: break
        
        page_count = 0
        for href, title in items:
            # Filtre: Sadece içerik linklerini al
            if not any(x in href for x in ['/page/', '/kategori/', '?paged=']):
                full_link = href if href.startswith('http') else f"{BASE_URL}{href}"
                results.append({"baslik": title.strip().upper(), "url": full_link})
                page_count += 1
        
        print(f"  - Sayfa {p}: {page_count} içerik.")
        if page_count < 5: break
        time.sleep(0.3)
            
    return results

def main():
    # Versiyon artırımı
    if os.path.exists(GRADLE_PATH):
        with open(GRADLE_PATH, 'r') as f:
            content = f.read()
            v = re.search(r'version\s*=\s*(\d+)', content)
            if v:
                new_v = int(v.group(1)) + 1
                with open(GRADLE_PATH, 'w') as f:
                    f.write(re.sub(r'version\s*=\s*\d+', f'version = {new_v}', content))

    # Senin verdiğin listenin tam hali
    targets = [
        "koleksiyon/netflix", "koleksiyon/exxen", "koleksiyon/blutv", 
        "koleksiyon/disney", "koleksiyon/amazon-prime", "koleksiyon/tod-bein", 
        "koleksiyon/gain", "tur/mubi", "diziler", "filmler"
    ]
    
    final_list = []
    for t in targets:
        final_list.extend(scrape_path(t))

    # Tekilleştirme
    unique_data = {item['url']: item for item in final_list}.values()
    
    with open('diziler.json', 'w', encoding='utf-8') as f:
        json.dump(list(unique_data), f, ensure_ascii=False, indent=4)

    print(f"\n--- TARAMA TAMAMLANDI ---")
    print(f"Toplam {len(unique_data)} benzersiz içerik toplandı ve diziler.json güncellendi.")

if __name__ == "__main__":
    main()
