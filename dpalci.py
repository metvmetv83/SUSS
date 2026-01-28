import requests
import re
import os
import json
import sys

# BeautifulSoup kontrolü
try:
    from bs4 import BeautifulSoup
except ImportError:
    print("HATA: beautifulsoup4 eksik. YAML dosyanıza ekleyin.")
    sys.exit(1)

# YOLLAR
KT_PATH = "DiziPal/src/main/kotlin/com/Pitipitii/DiziPal.kt"
GRADLE_PATH = "DiziPal/build.gradle.kts"
PROXY_BASE = "https://api.codetabs.com/v1/proxy/?quest="

def get_headers():
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept-Language': 'tr-TR,tr;q=0.9',
    }

def clean_text(text):
    """Bozuk Türkçe karakterleri düzeltir ve tarih/puan bilgilerini ayıklar."""
    try:
        # Bazı proxy servisleri latin-1 döner, bunu utf-8'e zorla
        text = text.encode('latin-1').decode('utf-8')
    except:
        pass
    
    # "Konuşanlar6. Sezon... 3 hafta önce" gibi metinleri sadece isim kalacak şekilde böler
    clean = re.split(r'\d+\. Sezon|Henüz|Kişi|\d+ hafta|\d+ ay', text)[0]
    return clean.strip()

def fetch_series(url):
    """Proxy üzerinden temiz dizi listesi çeker."""
    try:
        proxy_url = f"{PROXY_BASE}{url}"
        print(f"Veriler çekiliyor: {proxy_url}")
        res = requests.get(proxy_url, headers=get_headers(), timeout=30)
        res.encoding = 'utf-8' 
        
        soup = BeautifulSoup(res.text, 'html.parser')
        results = []

        # Gereksiz linkleri elemek için anahtar kelimeler
        bad_words = ['kategori', 'koleksiyon', 'forum', 'trendler', 'iletisim', 'email-protection', 'javascript', 'giris']

        for a in soup.find_all('a', href=True):
            href = a['href']
            raw_title = a.get_text(strip=True)
            
            # Filtrele: Link ve başlık uygun mu?
            if any(x in href.lower() for x in bad_words) or len(raw_title) < 4:
                continue
            
            title = clean_text(raw_title)
            if title and len(title) > 2:
                full_link = href if href.startswith('http') else f"{url.rstrip('/')}/{href.lstrip('/')}"
                results.append({"baslik": title, "url": full_link})

        # Tekilleştirme
        unique_results = []
        seen = set()
        for item in results:
            if item['baslik'].lower() not in seen:
                unique_results.append(item)
                seen.add(item['baslik'].lower())
        
        with open('diziler.json', 'w', encoding='utf-8') as f:
            json.dump(unique_results, f, ensure_ascii=False, indent=4)
        
        print(f"İşlem başarılı: {len(unique_results)} içerik kaydedildi.")

    except Exception as e:
        print(f"Scraping hatası: {e}")

def check_url(url):
    try:
        r = requests.get(f"{PROXY_BASE}{url}", headers=get_headers(), timeout=20)
        return url if r.status_code == 200 else None
    except:
        return None

def main():
    target_url = "https://www.dizipal1226.com"
    working_url = check_url(target_url)

    if working_url:
        print(f"Aktif URL: {working_url}")
        
        # 1. Kotlin Dosyasını Güncelle
        if os.path.exists(KT_PATH):
            with open(KT_PATH, 'r', encoding='utf-8') as f:
                content = f.read()
            new_content = re.sub(r'mainUrl\s*=\s*".*?"', f'mainUrl = "{working_url}"', content)
            with open(KT_PATH, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Güncellendi: {KT_PATH}")

        # 2. Gradle Sürüm Artır
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
        
        # 3. Dizileri Çek
        fetch_series(working_url)
    else:
        print("Siteye ulaşılamadı.")
        sys.exit(1)

if __name__ == "__main__":
    main()
