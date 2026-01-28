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

def clean_text(text):
    """Bozuk karakterleri düzeltir ve gereksiz boşlukları siler."""
    try:
        # Encoding hatasını düzelt (latin-1 -> utf-8)
        text = text.encode('latin-1').decode('utf-8')
    except:
        pass
    # '6. Sezon 15. Bölüm3 hafta önce' gibi birleşik metinleri temizle
    text = re.split(r'\d+\s+hafta|\d+\s+ay|Henüz|Kişi', text)[0]
    return text.strip()

def fetch_series(url):
    try:
        proxy_url = f"{PROXY_BASE}{url}"
        res = requests.get(proxy_url, timeout=30)
        res.encoding = 'utf-8' # Doğrudan encoding set et
        
        soup = BeautifulSoup(res.text, 'html.parser')
        results = []

        # Sadece dizi ve film olabilecek linkleri seç
        for a in soup.find_all('a', href=True):
            href = a['href']
            raw_title = a.get_text(strip=True)
            
            # Filtreleme: Gereksiz sayfaları ve kısa başlıkları ele
            bad_paths = ['javascript', 'koleksiyon', 'forum', 'trendler', 'email-protection', 'filmler', 'diziler', 'iletisim']
            if any(x in href.lower() for x in bad_paths) or len(raw_title) < 3:
                continue
            
            # Sadece dizi veya film sayfası gibi duran linkleri al
            # Genellikle ana dizinde olurlar: /dizi-adi veya /dizi/dizi-adi
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
        
        print(f"Temizlik Tamamlandı: {len(unique_results)} gerçek içerik kaydedildi.")

    except Exception as e:
        print(f"Hata: {e}")

# ... (main ve check_url fonksiyonları aynı kalacak)

if __name__ == "__main__":
    # main() çağrısı burada
    import main as m # veya mevcut main fonksiyonunu buraya ekle
    from __main__ import main
    main()
