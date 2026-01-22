import json
import subprocess

JSON_FILE = "com.json"
OUTPUT_M3U8 = "output.m3u8"

def get_m3u8_from_url(url):
    """
    yt-dlp ile gerçek m3u8 linkini alır
    """
    cmd = [
        "yt-dlp",
        "-g",
        "-f",
        "best",
        url
    ]

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True
    )

    return result.stdout.strip()


def main():
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        channels = json.load(f)

    lines = ["#EXTM3U"]

    for ch in channels:
        name = ch.get("name")
        url = ch.get("url")

        if not name or not url:
            continue

        print(f"[+] {name} alınıyor...")

        try:
            m3u8 = get_m3u8_from_url(url)
            if not m3u8:
                print(f"[-] {name} m3u8 bulunamadı")
                continue

            lines.append(f"#EXTINF:-1,{name}")
            lines.append(m3u8)

        except Exception as e:
            print(f"[!] Hata ({name}): {e}")

    with open(OUTPUT_M3U8, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n✅ output.m3u8 oluşturuldu")


if __name__ == "__main__":
    main()
