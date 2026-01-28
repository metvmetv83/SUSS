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
        'X-Requested-With': 'XMLHttpRequest'
    }

def clean_text(text):
    try:
        text = text.encode('latin-1').decode('utf-8')
    except: pass
    # Gereksiz kalabalığı ve "Daha fazla göster" metnini temizle
    if "daha fazla" in text.lower() or text == "#":
        return None
    clean = re.split(r'\d+\. Sezon|Henüz|Kişi|\d+ hafta|\d+ ay|imdb|IMDB', text, flags=re.IGNORECASE)[0]
    return clean.strip()

def scrape_deep_with_filter(base_url, section, type_id):
    results = []
    print(f"\n>>> {section.upper()} taranıyor...")
    
    # Sayfa yapısı üzerinden gitmek en kararlısı (Hatta URL'de # olsa bile)
    for p in range(1, 8): # 7 sayfa derinlik
        target = f"{base_url}/{section}/page/{p}/?type={type_id}"
        print(f"Sayfa {p} çekiliyor...")
        
        try:
            res = requests.get(f"{PROXY_BASE}{target}", headers=get_headers(), timeout=30)
            res.encoding = 'utf-8'
            
            if res.status_code != 200 or len(res.text) < 4000:
                break
                
            soup = BeautifulSoup(res.text, 'html.parser')
            links = soup.find_all('a', href=True)
            
            found_count = 0
            for a in links:
                href = a['href']
                raw_title = a.get_text(strip=True)
                title = clean_text(raw_title)
                
                # Sadece gerçek içerik linklerini al (Butonları ve kategorileri ele)
                if title and len(title) > 3 and href != "#" and base_url in href:
                    if not any(x in href.lower() for x in ['kategori', 'etiket', 'page/', 'iletisim']):
                        results.append({"baslik": title, "url": href})
                        found_count += 1
            
            print(f"Sayfa {p}: +{found_count} içerik.")
            if found_count == 0: break
            time.sleep(0.5)
            
        except:
            break
            
    return results

def main():
    target_url = "https://www.dizipal1226.com"
    
    # Versiyon Güncelle
    if os.path.exists(GRADLE_PATH):
        with open(GRADLE_PATH, 'r', encoding='utf-8') as f: content = f.read()
        v = re.search(r'version\s*=\s*(\d+)', content)
        if v:
            new_v = int(v.group(1)) + 1
            new_g = re.sub(r'version\s*=\s*\d+', f'version = {new_v}', content)
            with open(GRADLE_PATH, 'w', encoding='utf-8') as f: f.write(new_g)

    # Veri Topla
    all_content = []
    all_content.extend(scrape_deep_with_filter(target_url, "diziler", "1"))
    all_content.extend(scrape_deep_with_filter(target_url, "filmler", "2"))

    # Tekilleştirme
    unique_list = []
    seen = set()
    for item in all_content:
        if item['url'] not in seen:
            unique_list.append(item)
            seen.add(item['url'])

    with open('diziler.json', 'w', encoding='utf-8') as f:
        json.dump(unique_list, f, ensure_ascii=False, indent=4)

    print(f"\nTamamlandı! {len(unique_list)} temiz içerik kaydedildi.")

if __name__ == "__main__":
    main()
