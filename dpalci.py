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

def get_headers():
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    }

def clean_text(text):
    try:
        text = text.encode('latin-1').decode('utf-8')
    except: pass
    clean = re.split(r'\d+\. Sezon|Henüz|Kişi|\d+ hafta|\d+ ay|imdb|IMDB', text, flags=re.IGNORECASE)[0]
    return clean.strip()

def scrape_section(base_url, section_path, type_id):
    """Hem ana bölümü hem de API parametreli versiyonunu tarar."""
    results = []
    # 1. Normal sayfa tarama
    # 2. API benzeri filtre parametreli tarama (?type=1)
    targets = [
        f"{base_url}/{section_path}",
        f"{base_url}/diziler?type={type_id}",
        f"{base_url}/filmler?type={type_id}"
    ]

    for target in targets:
        try:
            print(f"Hedef taranıyor: {target}")
            res = requests.get(f"{PROXY_BASE}{target}", headers=get_headers(), timeout=30)
            res.encoding = 'utf-8'
            
            soup = BeautifulSoup(res.text, 'html.parser')
            links = soup.find_all('a', href=True)
            
            found = 0
            for a in links:
                href = a['href']
                title = clean_text(a.get_text(strip=True))
                
                bad_keywords = ['kategori', 'koleksiyon', 'forum', 'iletisim', 'giris', 'uye', 'dmca', 'filmler', 'diziler', 'page/']
                
                if len(title) > 4 and not any(x in href.lower() for x in bad_keywords):
                    full_link = href if href.startswith('http') else f"{base_url.rstrip('/')}/{href.lstrip('/')}"
                    results.append({"baslik": title, "url": full_link})
                    found += 1
            print(f"Bulunan: {found}")
        except Exception as e:
            print(f"Hata: {e}")
            
    return results

def main():
    target_url = "https://www.dizipal1226.com"
    
    # Versiyonu artır
    if os.path.exists(GRADLE_PATH):
        with open(GRADLE_PATH, 'r', encoding='utf-8') as f: content = f.read()
        v = re.search(r'version\s*=\s*(\d+)', content)
        if v:
            new_v = int(v.group(1)) + 1
            new_g = re.sub(r'version\s*=\s*\d+', f'version = {new_v}', content)
            with open(GRADLE_PATH, 'w', encoding='utf-8') as f: f.write(new_g)
            print(f"Sürüm Yükseltildi: {new_v}")

    # Kotlin URL güncelle
    if os.path.exists(KT_PATH):
        with open(KT_PATH, 'r', encoding='utf-8') as f: kt = f.read()
        new_kt = re.sub(r'override var mainUrl = ".*?"', f'override var mainUrl = "{target_url}"', kt)
        with open(KT_PATH, 'w', encoding='utf-8') as f: f.write(new_kt)

    # Verileri topla
    all_data = []
    all_data.extend(scrape_section(target_url, "diziler", "1"))
    all_data.extend(scrape_section(target_url, "filmler", "2"))

    # Tekilleştirme
    unique_list = []
    seen = set()
    for item in all_data:
        if item['url'] not in seen:
            unique_list.append(item)
            seen.add(item['url'])

    with open('diziler.json', 'w', encoding='utf-8') as f:
        json.dump(unique_list, f, ensure_ascii=False, indent=4)

    print(f"\nSonuç: {len(unique_list)} içerik kaydedildi.")

if __name__ == "__main__":
    main()
