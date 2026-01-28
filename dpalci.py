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
PAGE_LIMIT = 10  # Her kategori için taranacak sayfa sayısı

def get_headers():
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept-Language': 'tr-TR,tr;q=0.9',
    }

def clean_text(text):
    try:
        text = text.encode('latin-1').decode('utf-8')
    except:
        pass
    # Sezon, Bölüm, puan gibi ekleri temizle
    clean = re.split(r'\d+\. Sezon|Henüz|Kişi|\d+ hafta|\d+ ay|imdb|IMDB', text, flags=re.IGNORECASE)[0]
    return clean.strip()

def scrape_category(base_url, category_name):
    """Belirli bir kategorideki tüm sayfaları gezer."""
    category_results = []
    print(f"--- {category_name.upper()} Kategorisi Başlatılıyor ---")
    
    for page in range(1, PAGE_LIMIT + 1):
        # Sayfa URL'sini oluştur (Örn: /diziler?page=2)
        page_url = f"{base_url}/{category_name}?page={page}"
        print(f"Sayfa {page} taranıyor...")
        
        try:
            res = requests.get(f"{PROXY_BASE}{page_url}", headers=get_headers(), timeout=30)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # İçerik kartlarını bul (DiziPal genellikle article veya div.post-column kullanır)
            found_in_page = 0
            for a in soup.find_all('a', href=True):
                href = a['href']
                title = clean_text(a.get_text(strip=True))
                
                # Sadece dizi/film linki olabilecekleri seç (kısa ve anlamsızları ele)
                if len(title) > 3 and not any(x in href.lower() for x in ['kategori', 'forum', 'iletisim', 'page=']):
                    full_link = href if href.startswith('http') else f"{base_url.rstrip('/')}/{href.lstrip('/')}"
                    category_results.append({"baslik": title, "url": full_link, "tip": category_name})
                    found_in_page += 1
            
            if found_in_page == 0:
                print("Daha fazla içerik bulunamadı, bu kategori bitiriliyor.")
                break
                
            time.sleep(1) # Sunucuyu yormamak için kısa bekleme
        except Exception as e:
            print(f"Sayfa {page} hatası: {e}")
            break
            
    return category_results

def main():
    target_url = "https://www.dizipal1226.com"
    # Proxy ile sitenin ayakta olduğunu kontrol et
    try:
        r = requests.get(f"{PROXY_BASE}{target_url}", timeout=20)
        if r.status_code != 200:
            print("Siteye ulaşılamadı.")
            sys.exit(1)
    except:
        sys.exit(1)

    print(f"Aktif URL: {target_url}")

    # 1. Dosyaları Güncelle (Önceki mantıkla aynı)
    if os.path.exists(KT_PATH):
        with open(KT_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
        new_content = re.sub(r'mainUrl\s*=\s*".*?"', f'mainUrl = "{target_url}"', content)
        with open(KT_PATH, 'w', encoding='utf-8') as f: f.write(new_content)

    if os.path.exists(GRADLE_PATH):
        with open(GRADLE_PATH, 'r', encoding='utf-8') as f:
            g_content = f.read()
        v_match = re.search(r'version\s*=\s*(\d+)', g_content)
        if v_match:
            new_v = int(v_match.group(1)) + 1
            new_g = re.sub(r'version\s*=\s*\d+', f'version = {new_v}', g_content)
            with open(GRADLE_PATH, 'w', encoding='utf-8') as f: f.write(new_g)

    # 2. Tüm Arşivi Çek (Diziler ve Filmler)
    all_content = []
    all_content.extend(scrape_category(target_url, "diziler"))
    all_content.extend(scrape_category(target_url, "filmler"))

    # Tekilleştirme
    unique_data = []
    seen = set()
    for item in all_content:
        if item['baslik'].lower() not in seen:
            unique_data.append(item)
            seen.add(item['baslik'].lower())

    with open('diziler.json', 'w', encoding='utf-8') as f:
        json.dump(unique_data, f, ensure_ascii=False, indent=4)

    print(f"Toplam {len(unique_data)} içerik dev arşive kaydedildi!")

if __name__ == "__main__":
    main()
