#!/usr/bin/env python3
import requests
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- HEDEF ID LİSTESİ (En Aktif Türk Kanalları) ---
# Bu ID'ler Giniko/BozzTV altyapısında sık kullanılan Türk kanallarıdır.
ID_LIST = [
    1422, 1428, 1420, 1421, 1427, 1431, 1135, 1215, 1217, 1125, 
    1126, 1138, 1121, 1122, 1123, 1124, 1127, 1128, 1129, 1130,
    1131, 1132, 1133, 1134, 1136, 1137, 1139, 1140, 1141, 1142,
    1419, 1423, 1424, 1425, 1426, 1429, 1430, 1432, 1433, 1434
]

WORKERS = 10 # ID sayısı az olduğu için worker'ı düşürebilirsin

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.ginikoturkish.com/"
}

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
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200: return None
        
        text = r.text
        if "<string>false</string>" not in text: return None

        stream = re.search(r"<key>HlsStreamURL</key>\s*<string>(.*?)</string>", text)
        if not stream or "tgn.bozztv.com" not in stream.group(1): return None

        name_match = re.search(r"<key>name</key>\s*<string>(.*?)</string>", text)
        logo_match = re.search(r"<key>logoUrlHD</key>\s*<string>(.*?)</string>", text)

        name = name_match.group(1).replace(" - Live","") if name_match else f"Kanal {ch}"
        logo = logo_match.group(1) if logo_match else f"https://www.giniko.com/logos/190x110/{ch}.jpg"

        print(f"✓ {ch} Bulundu: {name}")
        return {"id": ch, "name": name, "logo": logo, "stream": stream.group(1), "plist": url}
    except:
        return None

def is_turkish(name):
    name_upper = name.upper()
    return any(k in name_upper for k in TURKISH_KEYWORDS) or any(c in name_upper for c in "ĞÜŞİÖÇI")

def main():
    results = []
    print(f"{len(ID_LIST)} özel ID taranıyor...\n")

    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = {executor.submit(check_channel, i): i for i in ID_LIST}
        for future in as_completed(futures):
            r = future.result()
            if r: results.append(r)

    # Önce Türk kanalları, sonra ID sırası
    results.sort(key=lambda x: (not is_turkish(x["name"]), x["id"]))

    with open("channels3.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\nBitti! {len(results)} kanal listelendi.")

if __name__ == "__main__":
    main()
