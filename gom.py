import requests
import re
import base64
import string
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Referer": "https://play.dizigom104.com/"
}

BASE_URL = "https://dizigom104.com"
MAX_PAGE = 4521


# -------------------------------------------------
# LINK AKTİF Mİ (AYNI)
# -------------------------------------------------
def check_link_is_active(url):
    try:
        r = requests.head(url, headers=HEADERS, timeout=2, allow_redirects=True)
        return r.status_code == 200
    except:
        return False


# -------------------------------------------------
# EMBED → M3U8 (AYNI)
# -------------------------------------------------
def get_m3u8_link(embed_url):
    try:
        r = requests.get(embed_url, headers=HEADERS, timeout=10)

        m2 = re.search(
            r"eval\(function\(p,a,c,k,e,d\).*?\('(.+?)'\.split\('\|'\)",
            r.text,
            re.S
        )
        if not m2:
            return None

        parts = m2.group(1).split("|")
        video_hash = next((p for p in parts if re.fullmatch(r"[a-f0-9]{32}", p)), None)
        if not video_hash:
            return None

        for c in string.ascii_lowercase:
            for n in ("1", "2"):
                test_url = f"https://{c}{n}.df856-54hilsnz.xyz/storage/media/{video_hash}-720.mp4/gomindex.m3u8"
                if check_link_is_active(test_url):
                    return test_url
        return None
    except:
        return None


# -------------------------------------------------
# BÖLÜM → EMBED (AYNI)
# -------------------------------------------------
def get_embed_from_episode(episode_url):
    try:
        r = requests.get(episode_url, headers=HEADERS, timeout=10)

        pattern = r'eval\(function\(h,u,n,t,e,r\).*?\("(.*?)",(\d+),"(.*?)",(\d+),(\d+),(\d+)\)'
        match = re.search(pattern, r.text)
        if not match:
            return None

        h_data, u_val, n_data, t_val, e_val, r_val = match.groups()
        u_val, t_val, e_val, r_val = map(int, (u_val, t_val, e_val, r_val))

        def _0xe2c(d, e, f):
            g = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ+/"
            h, i = g[0:e], g[0:f]
            j = 0
            for idx, char in enumerate(d[::-1]):
                if char in h:
                    j += h.find(char) * (e ** idx)
            k = ""
            while j > 0:
                k = i[j % f] + k
                j = (j - (j % f)) // f
            return k or "0"

        decoded_js = ""
        idx_i = 0
        while idx_i < len(h_data):
            s = ""
            while idx_i < len(h_data) and h_data[idx_i] != n_data[e_val]:
                s += h_data[idx_i]
                idx_i += 1
            for j in range(len(n_data)):
                s = s.replace(n_data[j], str(j))
            if s:
                decoded_js += chr(int(_0xe2c(s, e_val, 10)) - t_val)
            idx_i += 1

        api_path_match = re.search(r'/(api/watch/.*?\.dizigom)', decoded_js)
        if not api_path_match:
            return None

        api_res = requests.get(BASE_URL + api_path_match.group(1), headers=HEADERS)
        final_html = base64.b64decode(api_res.text).decode("utf-8")

        embed_match = re.search(r'src=["\'](https?://.*?)["\']', final_html)
        return embed_match.group(1) if embed_match else None
    except:
        return None


# -------------------------------------------------
# TUM-BOLUMLER → GERÇEK HTML’DEN BÖLÜM LİNKLERİ
# (TEK DÜZELTİLEN YER)
# -------------------------------------------------
def get_all_episode_links():
    episodes = set()

    for page in range(1, MAX_PAGE + 1):
        url = f"{BASE_URL}/tum-bolumler/" if page == 1 else f"{BASE_URL}/tum-bolumler/page/{page}/"
        print(f"[SAYFA] {page}/{MAX_PAGE}")

        r = requests.get(url, headers=HEADERS, timeout=15)

        # GERÇEK YAPI: episode-box içindeki -bolum-hd linkleri
        links = re.findall(
            r'<div class="episode-box">.*?<a href="(https://dizigom104\.com/[^"]+-bolum-hd\d+/)"',
            r.text,
            re.S
        )

        for l in links:
            episodes.add(l)

        time.sleep(0.05)

    return list(episodes)


# -------------------------------------------------
# MAIN (AYNI AKIŞ)
# -------------------------------------------------
def main():
    out = "dizigom-full.m3u"
    print("\n--- DIZIGOM FULL ARSIV BOTU BAŞLATILDI ---\n")

    episodes = get_all_episode_links()
    print(f"\nTOPLAM BÖLÜM: {len(episodes)}\n")

    if not episodes:
        print("❌ HİÇ BÖLÜM BULUNAMADI")
        return

    with open(out, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")

        for ep in episodes:
            print(f"[BÖLÜM] {ep}")

            r = requests.get(ep, headers=HEADERS, timeout=10)

            title_match = re.search(r'<title>(.*?) (?:İzle|izle)', r.text)
            d_isim = title_match.group(1).strip() if title_match else "Bilinmeyen"

            logo_match = re.search(r'"image":"(.*?)"', r.text)
            d_logo = logo_match.group(1).replace("\\/", "/") if logo_match else ""

            embed = get_embed_from_episode(ep)
            if not embed:
                print("  ❌ EMBED YOK")
                continue

            m3u8 = get_m3u8_link(embed)
            if not m3u8:
                print("  ❌ M3U8 YOK")
                continue

            f.write(
                f'#EXTINF:-1 tvg-name="TR: {d_isim}" tvg-logo="{d_logo}" group-title="Dizigom",TR: {d_isim}\n'
            )
            f.write(m3u8 + "\n")
            f.flush()

            print("  ✅ EKLENDİ")
            time.sleep(0.1)

    print("\n✔ BİTTİ – M3U HAZIR")


if __name__ == "__main__":
    main()
