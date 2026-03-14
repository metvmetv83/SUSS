import requests
import re
import json
import time

# Ayarlar
START_ID = 1
END_ID = 1500
OUTPUT_FILE = "metv_list_full.json"
BASE_XML_URL = "https://ginikoturkish.com/xml/secure/plist.php?ch="

def scan_channels():
    found_channels = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.ginikoturkish.com/"
    }

    print(f"Tarama başlatılıyor: {START_ID} - {END_ID}")

    for ch_id in range(START_ID, END_ID + 1):
        url = f"{BASE_XML_URL}{ch_id}"
        try:
            # Sunucuyu yormamak için çok kısa bekleme
            if ch_id % 50 == 0:
                print(f"Şu anki ID: {ch_id}...")
                time.sleep(1)

            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                xml_content = response.text
                
                # İsim kontrolü
                name_match = re.search(r"<key>name</key>\s*<string>(.*?)</string>", xml_content)
                
                if name_match:
                    raw_name = name_match.group(1).strip()
                    
                    # Filtre: Sadece "- Live" yazanları veya boş olanları geç
                    if not raw_name or raw_name.lower() == "- live":
                        continue
                    
                    # İsmi temizle
                    clean_name = re.sub(r"\s*-\s*Live", "", raw_name, flags=re.IGNORECASE).strip()
                    
                    found_channels.append({
                        "id": ch_id,
                        "name": clean_name,
                        "logo": f"https://www.giniko.com/logos/190x110/{ch_id}.jpg",
                        "xmlUrl": url
                    })
        except Exception as e:
            continue

    # Sonucu kaydet
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(found_channels, f, ensure_ascii=False, indent=2)
    
    print(f"Tarama bitti! Toplam {len(found_channels)} aktif kanal bulundu.")

if __name__ == "__main__":
    scan_channels()
