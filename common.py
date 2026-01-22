import json
import subprocess
import time
import os

JSON_FILE = "com.json"
YT_DLP = "yt-dlp"

def get_hls(video_id):
    url = f"https://www.youtube.com/watch?v={video_id}"

    cmd = [
        YT_DLP,
        "--print", "manifest_url",
        "--no-warnings",
        "--force-ipv4",
        "--user-agent", "Mozilla/5.0",
        url
    ]

    p = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True
    )

    out = p.stdout.strip()
    if out and "m3u8" in out:
        return out.splitlines()[0]

    return None


def is_enabled(v):
    return v is True or v == 1 or v == "1"


def main():
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    for key, ch in data.items():

        if not is_enabled(ch.get("enabled")):
            continue

        name = ch.get("name", key)
        video_id = ch.get("video_id")
        file = ch.get("file", key) + ".m3u8"

        print(f"[+] {name} alınıyor...")

        hls = get_hls(video_id)

        if not hls:
            print(f"[-] {name} HLS bulunamadı")
            continue

        with open(file, "w", encoding="utf-8") as f:
            f.write(
                "#EXTM3U\n"
                "#EXT-X-VERSION:3\n"
                "#EXT-X-STREAM-INF:BANDWIDTH=800000\n"
                f"{hls}\n"
            )

        print(f"[✓] {name} OK -> {file}")
        time.sleep(2)

    print("Bitti")


if __name__ == "__main__":
    main()
