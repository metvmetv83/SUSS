import json
import subprocess
import os

INPUT_JSON = "com.json"
OUTPUT_M3U8 = "output.m3u8"

SUBPROCESS_FLAGS = 0
if os.name == "nt":
    try:
        SUBPROCESS_FLAGS = subprocess.CREATE_NO_WINDOW
    except:
        pass


def get_m3u8(url):
    try:
        result = subprocess.run(
            [
                "yt-dlp",
                "--no-warnings",
                "--print",
                "manifest_url",
                url
            ],
            capture_output=True,
            text=True,
            creationflags=SUBPROCESS_FLAGS,
            timeout=20
        )

        if result.returncode != 0:
            return None

        out = result.stdout.strip()
        if out.startswith("http"):
            return out

    except Exception as e:
        print("yt-dlp hata:", e)

    return None


def main():
    if not os.path.exists(INPUT_JSON):
        print("com.json bulunamadı")
        return

    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        channels = json.load(f)

    lines = ["#EXTM3U\n"]

    for ch in channels:
        if not ch.get("enabled", True):
            continue

        name = ch.get("name", "Bilinmeyen")
        url = ch.get("url")

        if not url:
            continue

        print("Çözülüyor:", name)
        m3u8 = get_m3u8(url)

        if not m3u8:
            print("  ❌ m3u8 alınamadı")
            continue

        lines.append(f'#EXTINF:-1,{name}\n')
        lines.append(f'{m3u8}\n')

        print("  ✅ eklendi")

    with open(OUTPUT_M3U8, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print("\n✔ output.m3u8 oluşturuldu")


if __name__ == "__main__":
    main()
