#!/usr/bin/env python3
import requests
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# Tüm aralığı tara
TOTAL = 5000 
WORKERS = 40

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.ginikoturkish.com/"
}

# Türk kanallarını en başa almak için kullanılacak filtre
TURKISH_KEYWORDS = [
    'TRT', 'ATV', 'TV8', 'SHOW', 'KANAL', 'STAR', 'NOW', 'FOX', 'KANAL 7', 
    'BEYAZ', 'FLASH', 'TGRT', 'TELE1', 'KRT', 'HALK', 'SZC', 'EKOL',
    'HABER', 'NTV', 'CNN', '24 TV', 'ULUSAL', 'BLOOMBERG',
    'SPOR', 'SPORT', 'BEIN', 'TJK', 'BELGESEL', 'DMAX', 'TLC', 
    'SINEMA', 'YESILCAM', 'DIZI', 'FILM', 'COCUK', 'MINIKA'
]

def check_channel(ch):
    url = f"https://www.giniko.com/xml/secure/plist.php?ch={ch}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=8)
        if r.status_code != 200: return None
        
        text = r.text
        if "<string>false</string>" not in text: return None

        stream = re.search(r"<key>HlsStreamURL</key>\s*<string>(.*?)</string>", text)
        if not stream or "tgn.bozztv.com" not in stream.group(1): return None

        name_match = re.search(r"<key>name</key>\s*<string>(.*?)</string>", text)
        logo_match = re.search(r"<key>logoUrlHD</key>\s*<string>(.*?)</string>", text)

        name = name_match.group(1).replace(" - Live","") if name_match else f"Kanal {ch}"
        logo = logo_match.group(1) if logo_match else f"https://www.giniko.com/logos/190x110/{ch}.jpg"

        print(f"✓ {ch} : {name}")
        return {"id": ch, "name": name, "logo": logo, "stream": stream.group(1), "plist": url}
    except:
        return None

def is_turkish(name):
    """Kanal ismine ve Türkçeye özgü karakterlere bakarak tespit eder."""
    name_upper = name.upper()
    # Türkçe karakter kontrolü
    if any(c in name_upper for c in "ĞÜŞİÖÇI"): return True
    # Anahtar kelime kontrolü
    return any(k in name_upper for k in TURKISH_KEYWORDS)

def main():
    results = []
    print(f"{TOTAL} kanal taranıyor, lütfen bekleyin...\n")

    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        # 1'den 5000'e kadar tüm kanalları taramaya gönderiyoruz
        futures = {executor.submit(check_channel, i): i for i in range(1, TOTAL + 1)}
        
        for future in as_completed(futures):
            r = future.result()
            if r:
                results.append(r)

    # --- KRİTİK SIRALAMA MANTIĞI ---
    # 1. Türk kanalı olanları (True) en başa al (not is_turkish yaparak False (0) olanları başa getiriyoruz)
    # 2. Sonra kendi içlerinde ID'ye göre sırala
    results.sort(key=lambda x: (not is_turkish(x["name"]), x["id"]))

    with open("channels7.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\nİşlem bitti! Toplam {len(results)} kanal bulundu.")
    print("Türk kanalları en başa taşındı, ardından diğer yabancı kanallar eklendi.")

if __name__ == "__main__":
    main()
