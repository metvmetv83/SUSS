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
DEPTH_LIMIT = 5  # Her kategori için 5 sayfa derinliğe in (toplam ~500 içerik)

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

def scrape_deep(base_url, section, type_id):
    results = []
    print(f"\n>>> {section.upper()} (Type {type_id}) derin tarama başlatıldı...")
    
    for p in range(1, DEPTH_LIMIT + 1):
        # Hem WordPress klasik hem de query parametreli sayfalama deneniyor
        # Örn: /diziler/page/2/?type=1
        target = f"{base_url}/{section}/page/{p}/?type={type_id}"
        print(f"Sayfa {p} taranıyor: {target}")
        
        try:
            res = requests.get(f"{PROXY_BASE}{target}", headers=get_headers(), timeout=30)
            res.encoding = 'utf-8'
            
            if res.status_code != 200 or len(res.text) < 5000:
                print(f"Sayfa {p} boş veya hatalı, bu kolu bitir.")
                break
                
            soup = BeautifulSoup(res.text, 'html.parser')
            links = soup.find_all('a', href=True)
            
            found_in_page = 0
            for a in links:
                href = a['href']
                title = clean_text(a.get_text(strip=True))
                
                bad_keywords = ['kategori', 'koleksiyon', 'forum', 'iletisim', 'giris', 'uye', 'dmca', 'filmler', 'diziler', 'page/']
                
                if len(title) > 4 and not any(x in href.lower() for x in bad_keywords):
                    full_link = href if href.startswith('http') else f"{base_url.rstrip('/')}/{href.lstrip('/')}"
                    results.append({"baslik": title, "url": full_link})
                    found_in_page += 1
            
            print(f"Sayfa {p} tamamlandı: +{found_in_page} içerik.")
            if found_in_page == 0: break
            time.sleep(1) # Siteyi yormayalım
            
        except Exception as e:
            print(f"Hata: {e}")
            break
            
    return results

def main():
    target_url = "https://www.dizipal1226.com"
    
    # 1. Versiyon & URL Güncelle
    if os.path.exists(GRADLE_PATH):
        with open(GRADLE_PATH, 'r', encoding='utf-8') as f: content = f.read()
        v = re.search(r'version\s*=\s*(\d+)', content)
        if v:
            new_v = int(v.group(1)) + 1
            new_g = re.sub(r'version\s*=\s*\d+', f'version = {new_v}', content)
            with open(GRADLE_PATH, 'w', encoding='utf-8') as f: f.write(new_g)
            print(f"Sürüm Yükseltildi: {new_v}")

    # 2. Derin Veri Toplama
    all_data = []
    all_data.extend(scrape_deep(target_url, "diziler", "1"))
    all_data.extend(scrape_deep(target_url, "filmler", "2"))

    # 3. Tekilleştirme
    unique_list = []
    seen = set()
    for item in all_data:
        if item['url'] not in seen:
            unique_list.append(item)
            seen.add(item['url'])

    with open('diziler.json', 'w', encoding='utf-8') as f:
        json.dump(unique_list, f, ensure_ascii=False, indent=4)

    print(f"\n--- İŞLEM TAMAMLANDI ---")
    print(f"Toplam {len(unique_list)} benzersiz içerik dev arşive eklendi.")

if __name__ == "__main__":
    main()
