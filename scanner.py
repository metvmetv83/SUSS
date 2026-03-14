#!/usr/bin/env python3
import requests
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

TOTAL = 5000
WORKERS = 40

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.ginikoturkish.com/"
}

def check_channel(ch):

    url = f"https://www.giniko.com/xml/secure/plist.php?ch={ch}"

    try:
        r = requests.get(url, headers=HEADERS, timeout=8)

        if r.status_code != 200:
            return None

        text = r.text

        # canlı yayın
        if "<string>false</string>" not in text:
            return None

        stream = re.search(r"<key>HlsStreamURL</key>\s*<string>(.*?)</string>", text)
        if not stream:
            return None

        stream = stream.group(1)

        # sadece bozzTV CDN
        if "tgn.bozztv.com" not in stream:
            return None

        name = re.search(r"<key>name</key>\s*<string>(.*?)</string>", text)
        logo = re.search(r"<key>logoUrlHD</key>\s*<string>(.*?)</string>", text)

        name = name.group(1).replace(" - Live","") if name else f"Kanal {ch}"
        logo = logo.group(1) if logo else f"https://www.giniko.com/logos/190x110/{ch}.jpg"

        print(f"✓ {ch} : {name}")

        return {
            "id": ch,
            "name": name,
            "logo": logo,
            "stream": stream,
            "plist": url
        }

    except:
        return None


def main():

    results = []

    with ThreadPoolExecutor(max_workers=WORKERS) as executor:

        futures = {executor.submit(check_channel, i): i for i in range(1, TOTAL+1)}

        for future in as_completed(futures):

            r = future.result()

            if r:
                results.append(r)

    results.sort(key=lambda x: x["id"])

    with open("channels3.json","w",encoding="utf-8") as f:
        json.dump(results,f,ensure_ascii=False,indent=2)

    print(f"\nToplam {len(results)} kanal bulundu")


if __name__ == "__main__":
    main()
