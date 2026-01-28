import requests
import re
import os
import json
import sys

# Dosya Yolları
KT_PATH = "DiziPal/src/main/kotlin/com/Pitipitii/DiziPal.kt"
GRADLE_PATH = "DiziPal/build.gradle.kts"
PROXY_BASE = "https://api.codetabs.com/v1/proxy/?quest="

def get_headers():
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
    }

def main():
    target_url = "https://www.dizipal1226.com"
    print(f"Hedef: {target_url} taranıyor...")

    # Versiyon artırma işlemi
    if os.path.exists(GRADLE_PATH):
        with open(GRADLE_PATH, 'r') as f: content = f.read()
        v = re.search(r'version\s*=\s*(\d+)', content)
        if v:
            new_v = int(v.group(1)) + 1
            new_c = re.sub(r'version\s*=\s*\d+', f'version = {new_v}', content)
            with open(GRADLE_PATH, 'w') as f: f.write(new_c)

    results = []
    # Ana sayfa, diziler ve filmler sayfalarını tara
    endpoints = ["", "/diziler", "/filmler"]
    
    for ep in endpoints:
        full_url = f"{PROXY_BASE}{target_url}{ep}"
        try:
            print(f"İstek gönderiliyor: {target_url}{ep}")
            res = requests.get(full_url, headers=get_headers(), timeout=30)
            res.encoding = 'utf-8'
            
            # HTML içindeki tüm link yapılarını regex ile yakala
            # Örn: <a ... href="https://site.com/dizi-adi">...</a>
            pattern = r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>'
            matches = re.findall(pattern, res.text, re.DOTALL)
            
            for href, text in matches:
                # Temizlik
                clean_t = re.sub('<[^<]+?>', '', text).strip() # HTML taglarını sil
                
                # Filtre: Gereksiz linkleri ele
                bad = ['kategori', 'etiket', 'page', 'iletisim', 'yorum', 'uye', 'kayit', 'daha fazla', 'dmca']
                if len(clean_t) > 3 and not any(x in href.lower() for x in bad) and target_url in href:
                    if href != f"{target_url}/" and href != target_url:
                        results.append({"baslik": clean_t, "url": href})
            
        except Exception as e:
            print(f"Hata ({ep}): {e}")

    # Tekilleştirme
    unique_data = []
    seen = set()
    for item in results:
        if item['url'] not in seen:
            unique_data.append(item)
            seen.add(item['url'])

    # Kaydet
    with open('diziler.json', 'w', encoding='utf-8') as f:
        json.dump(unique_list := list(unique_data), f, ensure_ascii=False, indent=4)

    print(f"\nSonuç: {len(unique_list)} içerik bulundu ve kaydedildi.")

if __name__ == "__main__":
    main()
