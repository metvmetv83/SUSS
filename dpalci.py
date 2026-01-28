import requests
import re
import os
import json
from urllib.parse import quote

# Ayarlar
BASE_URL = "https://www.dizipal1226.com"
PROXY = "https://api.allorigins.win/get?url="

def fetch_data(url):
    try:
        res = requests.get(PROXY + quote(url), timeout=20)
        if res.status_code == 200:
            return res.json().get('contents', '')
    except:
        return ""
    return ""

def get_content():
    targets = [
        "koleksiyon/netflix", "koleksiyon/exxen", "koleksiyon/blutv", 
        "koleksiyon/disney", "koleksiyon/amazon-prime", "koleksiyon/tod-bein", 
        "koleksiyon/gain", "tur/mubi", "diziler", "filmler"
    ]
    
    all_items = []
    for t in targets:
        print(f">>> {t.upper()} taranıyor...")
        html = fetch_data(f"{BASE_URL}/{t}")
        if not html: continue

        # PHP kodundaki regex mantığının Python hali
        items = re.findall(r'<li[^>]*>(.*?)</li>', html, re.DOTALL | re.IGNORECASE)
        for item in items:
            m_link = re.search(r'href="([^"]+)"', item)
            m_title = re.search(r'class="title">([^<]+)</span>', item)
            m_img = re.search(r'src="([^"]+)"', item)
            m_imdb = re.search(r'class="imdb[^>]*>([^<]+)</span>', item)

            if m_link and m_title:
                link = m_link.group(1)
                full_link = link if link.startswith('http') else f"{BASE_URL}{link}"
                all_items.append({
                    "title": m_title.group(1).strip().upper(),
                    "img": m_img.group(1) if m_img else "",
                    "imdb": m_imdb.group(1) if m_imdb else "-",
                    "link": full_link
                })
    
    # Tekilleştirme
    unique = {x['link']: x for x in all_items}.values()
    return list(unique)

def create_html(data):
    html_template = f"""
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>TITAN TV | Oto Portal</title>
        <script type="module" src="https://cdn.jsdelivr.net/npm/@ionic/core/dist/ionic/ionic.esm.js"></script>
        <style>
            :root {{ --main-bg: #0b0c10; --card-bg: #1f2833; --accent: #66fcf1; }}
            body {{ background: var(--main-bg); color: #fff; font-family: sans-serif; margin: 0; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 15px; padding: 15px; }}
            .card {{ background: var(--card-bg); border-radius: 8px; overflow: hidden; cursor: pointer; border: 1px solid #45a29e33; position: relative; }}
            .card img {{ width: 100%; height: 210px; object-fit: cover; }}
            .card-title {{ padding: 8px; font-size: 11px; text-align: center; color: var(--accent); }}
            .badge-imdb {{ position: absolute; top: 5px; right: 5px; background: rgba(0,0,0,0.8); color: orange; padding: 2px 5px; border-radius: 4px; font-size: 10px; }}
            .hidden {{ display: none !important; }}
            #player-screen {{ display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:#000; z-index:10000; }}
            iframe {{ width:100%; height:100%; border:none; }}
            .episode-item {{ background: #1f2833; margin: 5px; padding: 10px; border-radius: 5px; cursor: pointer; display: flex; align-items: center; }}
            .episode-item img {{ width: 60px; height: 40px; margin-right: 10px; border-radius: 3px; }}
        </style>
    </head>
    <body>
        <div id="main-screen">
            <h2 style="text-align:center; color:var(--accent);">TITAN TV PORTAL</h2>
            <div class="grid" id="movie-grid"></div>
        </div>

        <div id="episodes-screen" class="hidden" style="padding:20px;">
            <button onclick="location.reload()" style="background:var(--accent); padding:10px; border:none; border-radius:5px; cursor:pointer;">← ANA SAYFA</button>
            <div id="episode-content"></div>
        </div>

        <div id="player-screen">
            <button onclick="closePlayer()" style="position:fixed; top:10px; right:10px; z-index:10001; background:red; color:white; border:none; padding:10px; border-radius:5px;">KAPAT</button>
            <div id="video-container" style="width:100%; height:100%;"></div>
        </div>

        <script>
            const data = {json.dumps(data)};
            const proxy = "https://api.allorigins.win/get?url=";

            const grid = document.getElementById('movie-grid');
            data.forEach((item, index) => {{
                grid.innerHTML += `
                    <div class="card" onclick="showEpisodes(${{index}})">
                        <div class="badge-imdb">⭐ ${{item.imdb}}</div>
                        <img src="${{item.img}}">
                        <div class="card-title">${{item.title}}</div>
                    </div>`;
            }});

            async function showEpisodes(index) {{
                const item = data[index];
                document.getElementById('main-screen').classList.add('hidden');
                document.getElementById('episodes-screen').classList.remove('hidden');
                document.getElementById('episode-content').innerHTML = "<h3>" + item.title + " - Bölümler Yükleniyor...</h3>";

                try {{
                    const res = await fetch(proxy + encodeURIComponent(item.link));
                    const json = await res.json();
                    const doc = new DOMParser().parseFromString(json.contents, 'text/html');
                    const links = doc.querySelectorAll('.episode-item, .episodes li');
                    
                    let html = '<div style="margin-top:20px;">';
                    links.forEach(el => {{
                        const a = el.querySelector('a');
                        if(a) {{
                            const href = a.getAttribute('href');
                            const title = el.innerText.trim() || "Bölüm";
                            const fullHref = href.startsWith('http') ? href : "{BASE_URL}" + href;
                            html += `<div class="episode-item" onclick="playVideo('${{fullHref}}')">
                                        <img src="${{item.img}}">
                                        <span>${{title}}</span>
                                     </div>`;
                        }}
                    }});
                    document.getElementById('episode-content').innerHTML = "<h2>" + item.title + "</h2>" + html + "</div>";
                }} catch(e) {{ alert("Bölümler yüklenemedi!"); }}
            }}

            async function playVideo(url) {{
                document.getElementById('player-screen').style.display = 'block';
                document.getElementById('video-container').innerHTML = "<h2 style='color:white; text-align:center; margin-top:20%'>Video Hazırlanıyor...</h2>";
                
                try {{
                    const res = await fetch(proxy + encodeURIComponent(url));
                    const json = await res.json();
                    const doc = new DOMParser().parseFromString(json.contents, 'text/html');
                    const iframe = doc.querySelector('#vast_new iframe, .series-player-container iframe');
                    if(iframe) {{
                        let src = iframe.getAttribute('src');
                        if(src.startswith('//')) src = 'https:' + src;
                        document.getElementById('video-container').innerHTML = `<iframe src="${{src}}" allowfullscreen></iframe>`;
                    }} else {{ alert("Video bulunamadı!"); }}
                {{ catch(e) {{ alert("Hata!"); }}
            }}

            function closePlayer() {{
                document.getElementById('player-screen').style.display = 'none';
                document.getElementById('video-container').innerHTML = '';
            }}
        </script>
    </body>
    </html>
    """
    with open("dpalci.html", "w", encoding="utf-8") as f:
        f.write(html_template)

if __name__ == "__main__":
    dizi_listesi = get_content()
    create_html(dizi_listesi)
    print(f"Bitti! {len(dizi_listesi)} içerikli dpalci.html oluşturuldu.")
