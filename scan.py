#!/usr/bin/env python3
"""
Giniko 1-1000 kanal tarayıcı
Çalışan kanalları channels.json olarak kaydeder
"""
import asyncio
import aiohttp
import json
import re
import sys

TOTAL = 1000
BATCH = 50
TIMEOUT = 8
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.ginikoturkish.com/"
}

def parse_channel(text, ch_id):
    if "HlsStreamURL" not in text:
        return None

    lines = [l.strip() for l in text.split("\n") if l.strip()]
    
    # isVOD=false olan bloğun stream URL'sini bul
    stream_url = None
    name = None
    logo = None
    last_isvod = None

    for i, line in enumerate(lines):
        if line == "isVOD" and i+1 < len(lines):
            last_isvod = lines[i+1]
        if line == "HlsStreamURL" and i+1 < len(lines):
            url = lines[i+1]
            if url.startswith("http") and last_isvod == "false":
                stream_url = url
                break
        if line == "name" and i+1 < len(lines) and not lines[i+1].startswith("http") and name is None:
            name = lines[i+1].replace(" - Live", "").strip()
        if line == "logoUrlHD" and i+1 < len(lines) and lines[i+1].startswith("http") and logo is None:
            logo = lines[i+1]

    # Fallback: ilk HlsStreamURL
    if not stream_url:
        m = re.search(r'HlsStreamURL\s+(https?://\S+)', text)
        if m:
            stream_url = m.group(1)

    if not stream_url or not name:
        return None

    return {
        "id": ch_id,
        "name": name,
        "logo": logo or f"https://www.giniko.com/logos/190x110/{ch_id}.jpg",
        "xmlUrl": f"https://ginikoturkish.com/xml/secure/plist.php?ch={ch_id}"
    }

async def check_channel(session, ch_id):
    url = f"https://ginikoturkish.com/xml/secure/plist.php?ch={ch_id}"
    try:
        async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=TIMEOUT)) as r:
            if r.status != 200:
                return None
            text = await r.text()
            return parse_channel(text, ch_id)
    except Exception:
        return None

async def main():
    results = []
    connector = aiohttp.TCPConnector(limit=50)
    async with aiohttp.ClientSession(connector=connector) as session:
        for start in range(1, TOTAL+1, BATCH):
            end = min(start + BATCH - 1, TOTAL)
            ids = list(range(start, end+1))
            tasks = [check_channel(session, i) for i in ids]
            batch_results = await asyncio.gather(*tasks)
            found = [r for r in batch_results if r]
            results.extend(found)
            print(f"[{start:4d}-{end:4d}] {len(found):2d} kanal | Toplam: {len(results)}", flush=True)

    # Sırala
    results.sort(key=lambda x: x["id"])

    with open("channels.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Toplam {len(results)} kanal bulundu → channels.json")
    return len(results)

if __name__ == "__main__":
    count = asyncio.run(main())
    sys.exit(0 if count > 0 else 1)
