import json
import subprocess
import time
import re
import os

# DOSYALAR
JSON_FILE = "com.json"
YT_DLP = "yt-dlp"          # Windows: yt-dlp.exe

# REGEX (PHP ile birebir)
HLS_REGEX = re.compile(
    r"https://manifest\.googlevideo\.com/[^\s\"']+\.m3u8[^\s\"']*"
)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"


def get_hls(video_id):
    url = f"https://www.youtube.com/watch?v={video_id}"

    cmd = [
        YT_DLP,
        "-f", "best[protocol^=m3u8]",
        "--no-warnings",
        "--user-agent", USER_AGENT,
        "--get-url",
        url
    ]

    p = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    # debug istersen aç
    # print(p.stdout)

    m = HLS_REGEX.search(p.stdout)
    if m:
        return m.group(0)

    return None


def main():
    if not os.path.exists(JSON_FILE):
        print("com.json bulunamadı")
        return

    with open(JSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    for i, ch in enumerate(data):

        if ch.get("enabled") is False:
            print(ch.get("name"), "kapalı")
            continue

        video_id = ch.get("video_id")
        if not video_id:
            print(i, "video_id yok")
            continue

        name = ch.get("name", f"ch{i}")
        file = ch.get("file", name)

        if not file.endswith(".m3u8"):
            file += ".m3u8"

        print(f"[+] {name} alınıyor...")

        hls = get_hls(video_id)

        if not hls:
            print(f"[-] {name} HLS bulunamadı")
            continue

        content = (
            "#EXTM3U\n"
            "#EXT-X-VERSION:3\n"
            "#EXT-X-STREAM-INF:BANDWIDTH=800000\n"
            f"{hls}\n"
        )

        with open(file, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"[✓] {name} OK -> {file}")

        time.sleep(2)  # PHP'deki sleep(2) ile aynı

    print("Bitti")


if __name__ == "__main__":
    main()
