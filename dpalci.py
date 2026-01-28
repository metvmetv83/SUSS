import requests
import re
import os
import json
import sys

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("HATA: beautifulsoup4 kütüphanesi eksik.")
    sys.exit(1)

KT_PATH = "DiziPal/src/main/kotlin/com/Pitipitii/DiziPal.kt"
GRADLE_PATH = "DiziPal/build.gradle.kts"
PROXY_BASE = "https://api.codetabs.com/v1/proxy/?quest="

def get_headers():
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    }

def fetch_series(url):
    try:
        proxy_url = f"{PROXY_BASE}{url}"
        print(f"Proxy üzerinden veriler çekiliyor: {proxy_url}")
        
        res = requests.get(proxy_url, headers=get_headers(), timeout=30)
        
        if res.status_code != 200:
            print(f"Proxy Hatası: {res.status_code}")
            return

        soup = BeautifulSoup(res.text, 'html.parser')
        results = []

        # DiziPal'ın modern grid yapısında linkler genellikle 'a' içinde ama classları farklıdır.
        # Bu yüzden tüm linkleri alıp filtrelemeyi genişletiyoruz.
        for a in soup.find_all('a', href=True):
            href = a['href']
            # Başlık bazen <a> içinde değil, içindeki <h3> veya <span> içindedir
            title = a.get_text(strip=True)
            
            # Filtreleme kriterleri:
            # 1. Başlık çok kısa olmamalı (reklamları elemek için)
            # 2. Link ana domaini içermeli veya göreceli olmalı
            # 3. Kategori veya sayfalama linkleri olmamalı
            if len(title) > 4:
                bad_words = ['kategori', 'category', 'etiket', 'tag', 'page', 'wp-content', 'contact', 'iletisim']
                if not any(word in href.lower() for word in bad_words):
                    # Göreceli linkleri tam linke çevir
                    full_link = href if href.startswith('http') else f"{url.rstrip('/')}/{href.lstrip('/')}"
                    results.append({"baslik": title, "url": full_link})

        # Tekilleştirme (Aynı başlığı 1 kez al)
        unique_results = []
        seen = set()
        for item in results:
            if item['baslik'].lower() not in seen:
                unique_results.append(item)
                seen.add(item['baslik'].lower())
        
        # Sonuçları Kaydet
        with open('diziler.json', 'w', encoding='utf-8') as f:
            json.dump(unique_results, f, ensure_ascii=False, indent=4)
        
        print(f"İşlem başarılı: {len(unique_results)} içerik kaydedildi.")
        
        # Eğer hala 0 ise sayfanın yapısını anlamak için ilk 300 karakteri basalım
        if len(unique_results) == 0:
            print("Gelen veri örneği:", res.text[:300])

    except Exception as e:
        print(f"Scraping hatası: {e}")

def check_url(url):
    try:
        proxy_url = f"{PROXY_BASE}{url}"
        r = requests.get(proxy_url, headers=get_headers(), timeout=20)
        # Proxy başarılıysa site ayaktadır
        return url if r.status_code == 200 else None
    except:
        return None

def main():
    target_url = "https://www.dizipal1226.com"
    working_url = check_url(target_url)

    if working_url:
        print(f"Aktif URL: {working_url}")
        
        # Kotlin Güncelleme
        if os.path.exists(KT_PATH):
            with open(KT_PATH, 'r', encoding='utf-8') as f:
                content = f.read()
            new_content = re.sub(r'mainUrl\s*=\s*".*?"', f'mainUrl = "{working_url}"', content)
            with open(KT_PATH, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Güncellendi: {KT_PATH}")

        # Gradle Güncelleme
        if os.path.exists(GRADLE_PATH):
            with open(GRADLE_PATH, 'r', encoding='utf-8') as f:
                g_content = f.read()
            v_match = re.search(r'version\s*=\s*(\d+)', g_content)
            if v_match:
                new_v = int(v_match.group(1)) + 1
                new_g = re.sub(r'version\s*=\s*\d+', f'version = {new_v}', g_content)
                with open(GRADLE_PATH, 'w', encoding='utf-8') as f:
                    f.write(new_g)
                print(f"Sürüm yükseltildi: {new_v}")
        
        fetch_series(working_url)
    else:
        print("Siteye ulaşılamadı.")
        sys.exit(1)

if __name__ == "__main__":
    main()
