import requests
import re
import os
import json
import sys

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
    except:
        pass
    # Gereksiz kalabalığı temizle
    clean = re.split(r'\d+\. Sezon|Henüz|Kişi|\d+ hafta|\d+ ay|imdb|IMDB', text, flags=re.IGNORECASE)[0]
    return clean.strip()

def scrape_endpoint(base_url, endpoint):
    """Belirli bir endpoint altındaki (diziler/filmler) tüm linkleri toplar."""
    results = []
    target = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    print(f"\n>>> {endpoint.upper()} taranıyor: {target}")
    
    try:
        res = requests.get(f"{PROXY_BASE}{target}", headers=get_headers(), timeout=30)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Sitenin içindeki tüm linkleri bul
        links = soup.find_all('a', href=True)
        print(f"Toplam {len(links)} ham link bulundu. Filtreleniyor...")

        for a in links:
            href = a['href']
            title = clean_text(a.get_text(strip=True))
            
            # Filtreleme:
            # 1. Başlık en az 3 karakter olmalı
            # 2. Link, ana sayfaya veya yönetimsel sayfalara gitmemeli
            bad_keywords = ['kategori', 'koleksiyon', 'forum', 'iletisim', 'giris', 'uye', 'dmca', 'filmler', 'diziler']
            
            if len(title) > 3 and not any(x in href.lower() for x in bad_keywords):
                # Sadece dizi veya film detayı olabilecek linkleri seç (Genelde /dizi-adi veya /izle/ gibi)
                full_link = href if href.startswith('http') else f"{base_url.rstrip('/')}/{href.lstrip('/')}"
                results.append({"baslik": title, "url": full_link, "tip": endpoint})
                
    except Exception as e:
        print(f"Hata: {e}")
        
    return results

def main():
    target_url = "https://www.dizipal1226.com"
    
    # 1. Dosya Güncellemeleri
    if os.path.exists(KT_PATH):
        with open(KT_PATH, 'r', encoding='utf-8') as f: content = f.read()
        new_content = re.sub(r'override var mainUrl = ".*?"', f'override var mainUrl = "{target_url}"', content)
        with open(KT_PATH, 'w', encoding='utf-8') as f: f.write(new_content)
        print("Kotlin güncellendi.")

    if os.path.exists(GRADLE_PATH):
        with open(GRADLE_PATH, 'r', encoding='utf-8') as f: g_content = f.read()
        v_match = re.search(r'version\s*=\s*(\d+)', g_content)
        if v_match:
            new_v = int(v_match.group(1)) + 1
            new_g = re.sub(r'version\s*=\s*\d+', f'version = {new_v}', g_content)
            with open(GRADLE_PATH, 'w', encoding='utf-8') as f: f.write(new_g)
            print(f"Versiyon: {new_v}")

    # 2. Geniş Kapsamlı Tarama
    # DiziPal tüm arşivi genellikle tek bir büyük listede veya /diziler - /filmler altında sunar.
    full_list = []
    full_list.extend(scrape_endpoint(target_url, "diziler"))
    full_list.extend(scrape_endpoint(target_url, "filmler"))

    # Tekrar edenleri temizle
    unique_data = []
    seen = set()
    for item in full_list:
        if item['baslik'].lower() not in seen:
            unique_data.append(item)
            seen.add(item['baslik'].lower())

    with open('diziler.json', 'w', encoding='utf-8') as f:
        json.dump(unique_data, f, ensure_ascii=False, indent=4)

    print(f"\nİşlem Tamamlandı: {len(unique_data)} içerik çekildi.")

if __name__ == "__main__":
    main()
