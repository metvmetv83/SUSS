import os
import re
import json
import socket
import subprocess
from flask import Flask, jsonify, abort, request

# -------------------------------
# ORTAM KONTROLLERİ
# -------------------------------
IS_GITHUB = os.getenv("GITHUB_ACTIONS") == "true"

SUBPROCESS_FLAGS = 0
if os.name == "nt":
    try:
        SUBPROCESS_FLAGS = subprocess.CREATE_NO_WINDOW
    except AttributeError:
        SUBPROCESS_FLAGS = 0

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
CHANNELS_JSON = os.path.join(DATA_DIR, "channels.json")

app = Flask(__name__)

# -------------------------------
# YARDIMCI FONKSİYONLAR
# -------------------------------
def get_ipv4_address():
    if IS_GITHUB:
        return "127.0.0.1"

    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        if ip and not ip.startswith("127."):
            return ip
    except:
        pass

    if os.name == "nt":
        try:
            result = subprocess.run(
                ["ipconfig"],
                capture_output=True,
                text=True,
                creationflags=SUBPROCESS_FLAGS
            )
            matches = re.findall(
                r"(?:IPv4.*?:\s*)(\d+\.\d+\.\d+\.\d+)",
                result.stdout
            )
            if matches:
                return matches[0]
        except:
            pass

    return "127.0.0.1"


def run_yt_dlp(url):
    try:
        cmd = [
            "yt-dlp",
            "--no-warnings",
            "--print",
            "manifest_url",
            url
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            creationflags=SUBPROCESS_FLAGS
        )

        if result.returncode != 0:
            return None

        out = result.stdout.strip()
        if out.startswith("http"):
            return out

    except Exception as e:
        print("yt-dlp hata:", e)

    return None


def load_channels():
    if not os.path.exists(CHANNELS_JSON):
        return []

    try:
        with open(CHANNELS_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

# -------------------------------
# ROUTES
# -------------------------------
@app.route("/")
def index():
    ip = get_ipv4_address()
    return jsonify({
        "status": "ok",
        "ip": ip,
        "github_actions": IS_GITHUB
    })


@app.route("/channels")
def channels():
    return jsonify(load_channels())


@app.route("/resolve")
def resolve():
    url = request.args.get("url")
    if not url:
        abort(400, "url parametresi yok")

    manifest = run_yt_dlp(url)
    if not manifest:
        abort(500, "m3u8 alinamadi")

    return jsonify({
        "source": url,
        "m3u8": manifest
    })

# -------------------------------
# MAIN
# -------------------------------
if __name__ == "__main__":
    if IS_GITHUB:
        print("GitHub Actions ortamı → Flask başlatılmadı")
        print("Script başarıyla tamamlandı")
    else:
        app.run(
            host="0.0.0.0",
            port=5000,
            debug=False
        )
