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
        'X-Requested-With': 'XMLHttpRequest'
    }

def clean_text(text):
    try:
        text = text.encode('latin-1').decode('utf-8')
    except: pass
    clean = re.split(r'\d+\. Sezon|Henüz|Kişi|\d+ hafta|\d+ ay|imdb|IMDB', text, flags=re.IGNORECASE)[0]
    return clean.strip()

def scrape_full(base_url, endpoint):
    """Hem ana sayfayı hem de 'Daha Fazla' butonundan gelen verileri çeker."""
    results = []
    # 1. Aşama: Sayfanın kendisini tara (Senin çalışan kodun)
    target = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    print(f"\n>>> {endpoint.upper()} taranıyor: {target}")
    
    try:
        res = requests.get(f"{PROXY_BASE}{target}", headers=get_headers(), timeout=30)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Sayfadaki tüm linkleri topla
        for a in soup.find_all('a', href=True):
            href = a['href']
            title = clean_text(a.get_text(strip=True))
            bad_keywords = ['kategori', 'koleksiyon', 'forum', 'iletisim', 'giris', 'uye', 'dmca', 'filmler', 'diziler', 'page/']
            
            if len(title) > 3 and not any(x in href.lower() for x in bad_keywords):
                full_link = href if href.startswith('http') else f"{base_url.rstrip('/')}/{href.lstrip('/')}"
                results.append({"baslik": title, "url": full_link, "tip": endpoint})

        # 2. Aşama: 'Daha Fazla' Butonunu Simüle Et (AJAX)
        # DiziPal'da bu genellikle /wp-admin/admin-ajax.php üzerinden döner 
        # veya basitçe /page/X/ üzerinden HTML parçası olarak gelir.
        # Senin için en sağlamı 5 sayfalık bir 'gizli' tarama eklemek:
        for p in range(2, 6): # Sayfa 2'den 5'e kadar zorla
            ajax_target = f"{target}/page/{p}/"
            print(f"Ek içerikler aranıyor (Sayfa {p})...")
            ajax_res = requests.get(f"{PROXY_BASE}{ajax_target}", headers=get_headers(), timeout=20)
            
            if ajax_res.status_code == 200 and len(ajax_res.text) > 5000:
                ajax_soup = BeautifulSoup(ajax_res.text, 'html.parser')
                found = 0
                for a in ajax_soup.find_all('a', href=True):
                    h = a['href']
                    t = clean_text(a.get_text(strip=True))
                    if len(t) > 3 and not any(x in h.lower() for x in bad_keywords):
                        results.append({"baslik": t, "url": h if h.startswith('http') else f"{base_url.rstrip('/')}/{h.lstrip('/')}"})
                        found += 1
                if found == 0: break
            else:
                break

    except Exception as e:
        print(f"Hata: {e}")
    return results

def main():
    target_url = "https://www.dizipal1226.com"
    
    # Kotlin & Gradle Güncelleme
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

    # Veri Toplama
    full_list = []
    full_list.extend(scrape_full(target_url, "diziler"))
    full_list.extend(scrape_full(target_url, "filmler"))

    # Tekilleştirme
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
