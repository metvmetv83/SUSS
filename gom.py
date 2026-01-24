import requests
import re
import base64
import string
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Referer": "https://play.dizigom104.com/"
}

# -------------------------------------------------
# M3U8 link aktif mi kontrol
# -------------------------------------------------
def check_link_is_active(url):
    try:
        r = requests.head(url, headers=HEADERS, timeout=1.5, allow_redirects=True)
        return r.status_code == 200
    except:
        return False


# -------------------------------------------------
# Embed içinden m3u8 bul
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

        letters = string.ascii_lowercase
        for char in letters:
            for num in ["1", "2"]:
                prefix = f"{char}{num}"
                test_url = f"https://{prefix}.df856-54hilsnz.xyz/storage/media/{video_hash}-720.mp4/gomindex.m3u8"
                if check_link_is_active(test_url):
                    return test_url

        return None
    except:
        return None


# -------------------------------------------------
# Bölüm sayfasından embed al
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

        api_match = re.search(r'/(api/watch/.*?\.dizigom)', decoded_js)
        if not api_match:
            return None

        api_url = "https://dizigom104.com" + api_match.group(1)
        api_res = requests.get(api_url, headers=HEADERS)

        final_html = base64.b64decode(api_res.text).decode("utf-8")
        embed_match = re.search(r'src=["\'](https?://.*?)["\']', final_html)

        return embed_match.group(1) if embed_match else None

    except:
        return None


# -------------------------------------------------
# Tüm bölümleri çek (1 → 4521)
# -------------------------------------------------
def get_all_episode_links(max_page=4521):
    episodes = []

    for page in range(1, max_page + 1):
        if page == 1:
            url = "https://dizigom104.com/tum-bolumler/"
        else:
            url = f"https://dizigom104.com/tum-bolumler/page/{page}/"

        print(f"[SAYFA] {page}/{max_page}")

        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            links = re.findall(
                r'<a href="(https://dizigom104.com/.*?-izle/.*?)"',
                r.text
            )
            episodes.extend(links)
            time.sleep(0.1)

        except Exception as e:
            print(f"[HATA] Sayfa {page}: {e}")

    return list(set(episodes))


# -------------------------------------------------
# MAIN
# -------------------------------------------------
def main():
    m3u_filename = "dizigom-tum-bolumler.m3u"
    print(f"\nBOT BAŞLADI → {m3u_filename}\n")

    episode_links = get_all_episode_links(4521)
    print(f"\nTOPLAM BÖLÜM: {len(episode_links)}\n")

    with open(m3u_filename, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")

        for ep_url in episode_links:
            print(f"[BÖLÜM] {ep_url}")

            try:
                r = requests.get(ep_url, headers=HEADERS, timeout=10)

                title_match = re.search(r'<title>(.*?) (?:İzle|izle)', r.text)
                ep_name = title_match.group(1).strip() if title_match else "Bilinmeyen Bölüm"

                logo_match = re.search(r'"image":"(.*?)"', r.text)
                logo = logo_match.group(1).replace("\\/", "/") if logo_match else ""

                embed = get_embed_from_episode(ep_url)
                if not embed:
                    print("  ❌ PLAYER ERROR")
                    continue

                m3u8 = get_m3u8_link(embed)
                if not m3u8:
                    print("  ❌ M3U8 YOK")
                    continue

                f.write(
                    f'#EXTINF:-1 tvg-name="TR: {ep_name}" '
                    f'tvg-logo="{logo}" group-title="Dizigom",TR: {ep_name}\n'
                )
                f.write(m3u8 + "\n")
                f.flush()

                print("  ✅ EKLENDİ")
                time.sleep(0.1)

            except Exception as e:
                print(f"  ⚠ HATA: {e}")

    print("\nBİTTİ ✔ M3U DOSYASI HAZIR")


if __name__ == "__main__":
    main()
