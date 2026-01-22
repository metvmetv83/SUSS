import json
import os
from common import get_m3u8_from_url

INPUT_JSON = "com.json"
OUTPUT_M3U8 = "output.m3u8"


def main():
    if not os.path.exists(INPUT_JSON):
        print("com.json bulunamadı")
        return

    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        channels = json.load(f)

    lines = ["#EXTM3U\n"]

    for ch in channels:
        name = ch.get("name")
        url = ch.get("url")

        if not name or not url:
            continue

        print("Çözülüyor:", name)

        m3u8 = get_m3u8_from_url(url)

        if not m3u8:
            print("  ❌ m3u8 alınamadı")
            continue

        lines.append(f"#EXTINF:-1,{name}\n")
        lines.append(f"{m3u8}\n")

        print("  ✅ eklendi")

    with open(OUTPUT_M3U8, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print("\n✔ output.m3u8 hazır")


if __name__ == "__main__":
    main()
