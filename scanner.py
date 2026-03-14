#!/usr/bin/env python3
import requests
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

TOTAL = 1900
WORKERS = 30

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.ginikoturkish.com/"
}

def parse_channel(text, ch_id):

    blocks = re.findall(r"<dict>(.*?)</dict>", text, re.DOTALL)

    for block in blocks:

        isvod = re.search(r"<key>isVOD</key>\s*<string>(.*?)</string>", block)
        if not isvod:
            continue

        if isvod.group(1) != "false":
            continue

        name = re.search(r"<key>name</key>\s*<string>(.*?)</string>", block)
        logo = re.search(r"<key>logoUrlHD</key>\s*<string>(.*?)</string>", block)
        url = re.search(r"<key>HlsStreamURL</key>\s*<string>(.*?)</string>", block)

        if url:
            return {
                "id": ch_id,
                "name": name.group(1).replace(" - Live","") if name else f"Kanal {ch_id}",
                "logo": logo.group(1) if logo else f"https://www.giniko.com/logos/190x110/{ch_id}.jpg",
                "stream": url.group(1)
            }

    return None


def check_channel(ch_id):

    url = f"https://www.giniko.com/xml/secure/plist.php?ch={ch_id}"

    try:
        r = requests.get(url, headers=HEADERS, timeout=10)

        if r.status_code != 200:
            return None

        result = parse_channel(r.text, ch_id)

        if result:
            print(f"✓ {ch_id} : {result['name']}", flush=True)

        return result

    except:
        return None


def main():

    print(f"Taranıyor 1-{TOTAL}")

    results = []

    with ThreadPoolExecutor(max_workers=WORKERS) as executor:

        futures = {executor.submit(check_channel, i): i for i in range(1, TOTAL+1)}

        done = 0

        for future in as_completed(futures):

            done += 1

            r = future.result()

            if r:
                results.append(r)

            if done % 50 == 0:
                print(f"[{done}/{TOTAL}] bulunan: {len(results)}")

    results.sort(key=lambda x: x["id"])

    with open("channels3.json","w",encoding="utf-8") as f:
        json.dump(results,f,ensure_ascii=False,indent=2)

    print(f"\nToplam {len(results)} kanal bulundu")


if __name__ == "__main__":
    main()
