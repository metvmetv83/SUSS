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
PAGE_LIMIT = 20  # Her bölüm için taranacak sayfa derinliği

def get_headers():
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    }

def clean_text(text):
    try:
        text = text.encode('latin-1').decode('utf-8')
    except:
        pass
    # Gereksiz ekleri temizle (Sezon, Bölüm, imdb puanı gibi)
    clean = re.split(r'\d+\. Sezon|Henüz|Kişi|\d+ hafta|\d+ ay|imdb|IMDB', text, flags=re.IGNORECASE)[0]
    return clean.strip()

def scrape_full_archive(base_url, category):
    """Belirli bir kategorideki tüm sayfaları Proxy üzerinden gezer."""
    results = []
    print(f"\n>>> {category.upper()} arşivi taranıyor...")
    
    for page in range(1, PAGE_LIMIT + 1):
        # Sayfa URL yapısı: /diziler/page/1 veya /filmler/page/1
        page_url = f"{base_url}/{category}/page/{page}/"
        print(f"Sayfa {page} kontrol ediliyor...")
        
        try:
            full_proxy_url = f"{PROXY_BASE}{page_url}"
            res = requests.get(full_proxy_url, headers=get_headers(), timeout=30)
            res.encoding = 'utf-8'
            
            if res.status_code != 200:
                print(f"Sayfa {page} bulunamadı veya Proxy hatası. Kategori sonlandırıldı.")
                break
                
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # İçerik linklerini bul (Genellikle h2 veya h3 içindeki <a> etiketleri)
            page_items = 0
            for a in soup.find_all('a', href=True):
                title = clean_text(a.get_text(strip=True))
                href = a['href']
                
                # Sadece dizi/film linki olabilecek, anlamsız olmayan linkleri filtrele
                if len(title) > 3 and not any(x in href.lower() for x in ['kategori', 'page/', 'iletisim', 'koleksiyon', 'forum']):
                    full_link = href if href.startswith('http') else f"{base_url.rstrip('/')}/{href.lstrip('/')}"
                    results.append({"baslik": title, "url": full_link, "tip": category})
                    page_items += 1
            
            if page_items == 0:
                print("Sayfada içerik bulunamadı, durduruluyor.")
                break
            
            print(f"Sayfa {page} tamamlandı. (+{page_items} içerik)")
            time.sleep(0.5) # Proxy'yi ve siteyi yormamak için kısa mola
            
        except Exception as e:
            print(f"Hata oluştu (Sayfa {page}): {e}")
            break
            
    return results

def main():
    target_url = "https://www.dizipal1226.com"
    
    # URL'nin canlı olup olmadığını kontrol et
    try:
        check = requests.get(f"{PROXY_BASE}{target_url}", timeout=20)
        if check.status_code != 200:
            print("Ana siteye ulaşılamıyor, işlem iptal.")
            sys.exit(1)
    except:
        sys.exit(1)

    print(f"Aktif URL Onaylandı: {target_url}")

    # 1. Dosyaları Güncelle
    if os.path.exists(KT_PATH):
        with open(KT_PATH, 'r', encoding='utf-8') as f: content = f.read()
        new_content = re.sub(r'mainUrl\s*=\s*".*?"', f'mainUrl = "{target_url}"', content)
        with open(KT_PATH, 'w', encoding='utf-8') as f: f.write(new_content)
        print("Kotlin dosyası güncellendi.")

    if os.path.exists(GRADLE_PATH):
        with open(GRADLE_PATH, 'r', encoding='utf-8') as f: g_content = f.read()
        v_match = re.search(r'version\s*=\s*(\d+)', g_content)
        if v_match:
            new_v = int(v_match.group(1)) + 1
            new_g = re.sub(r'version\s*=\s*\d+', f'version = {new_v}', g_content)
            with open(GRADLE_PATH, 'w', encoding='utf-8') as f: f.write(new_g)
            print(f"Build versiyonu {new_v} yapıldı.")

    # 2. Tüm Arşivi Derinlemesine Tara
    full_db = []
    full_db.extend(scrape_full_archive(target_url, "diziler"))
    full_db.extend(scrape_full_archive(target_url, "filmler"))

    # Tekrar eden verileri temizle
    unique_db = []
    seen = set()
    for item in full_db:
        if item['baslik'].lower() not in seen:
            unique_db.append(item)
            seen.add(item['baslik'].lower())

    # 3. JSON Olarak Kaydet
    with open('diziler.json', 'w', encoding='utf-8') as f:
        json.dump(unique_db, f, ensure_ascii=False, indent=4)

    print(f"\nİşlem Tamamlandı! Toplam {len(unique_db)} içerik dev arşive eklendi.")

if __name__ == "__main__":
    main()
