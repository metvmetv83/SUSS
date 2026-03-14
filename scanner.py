import requests
import json
import re

def scan_channels():
    active_channels = []
    # Tarama aralığı (Örn: 700-950 arası en aktif yerdir)
    for ch_id in range(1, 1050):
        url = f"https://ginikoturkish.com/xml/secure/plist.php?ch={ch_id}"
        try:
            r = requests.get(url, timeout=5)
            if "HlsStreamURL" in r.text:
                # Kanal adını çek
                name_match = re.search(r"<key>name</key>\s*<string>(.*?)</string>", r.text)
                name = name_match.group(1) if name_match else f"Kanal {ch_id}"
                
                active_channels.append({
                    "id": ch_id,
                    "name": name,
                    "logo": f"https://www.giniko.com/logos/190x110/{ch_id}.jpg",
                    "xmlUrl": url
                })
                print(f"Bulundu: {name}")
        except:
            continue
    
    with open("channels.json", "w", encoding="utf-8") as f:
        json.dump(active_channels, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    scan_channels()
