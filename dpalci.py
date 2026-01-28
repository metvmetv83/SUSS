import requests
import re
import json
from urllib.parse import quote

# AYARLAR
BASE_URL = "https://www.dizipal1226.com"
PROXY = "https://api.allorigins.win/get?url="

def fetch_data(url):
    try:
        # User-agent eklemek sitelerin engellemesini önlemeye yardımcı olur
        res = requests.get(PROXY + quote(url), timeout=25)
        if res.status_code == 200:
            return res.json().get('contents', '')
    except Exception as e:
        print(f"Hata: {url} çekilemedi. -> {e}")
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
        print(f"Tarama yapılıyor: {t}")
        html = fetch_data(f"{BASE_URL}/{t}")
        if not html: continue

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
    
    unique = {x['link']: x for x in all_items}.values()
    return list(unique)

def create_html(data):
    # Veriyi JSON string'ine çeviriyoruz (ensure_ascii=False Türkçe karakterler için önemli)
    json_data = json.dumps(data, ensure_ascii=False)
    
    # HTML İçeriği - Python f-string çakışmalarını önlemek için JS kısımlarını {{ }} yaptık
    html_content = f"""<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TITAN TV | Oto Portal</title>
    <style>
        :root {{ --main-bg: #0b0c10; --card-bg: #1f2833; --accent: #66fcf1; }}
        body {{ background: var(--main-bg); color: #fff; font-family: sans-serif; margin: 0; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 15px; padding: 15px; }}
        .card {{ background: var(--card-bg); border-radius: 8px; overflow: hidden; cursor: pointer; border: 1px solid #45a29e33; position: relative; transition: 0.3s; }}
        .card:hover {{ transform: scale(1.05); border-color: var(--accent); }}
        .card img {{ width: 100%; height: 210px; object-fit: cover; }}
        .card-title {{ padding: 8px; font-size: 11px; text-align: center; color: var(--accent); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .badge-imdb {{ position: absolute; top: 5px; right: 5px; background: rgba(0,0,0,0.8); color: orange; padding: 2px 5px; border-radius: 4px; font-size: 10px; }}
        .hidden {{ display: none !important; }}
        #player-screen {{ display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:#000; z-index:10000; }}
        iframe {{ width:100%; height:100%; border:none; }}
        .episode-item {{ background: #1f2833; margin: 8px 0; padding: 12px; border-radius: 8px; cursor: pointer; display: flex; align-items: center; border: 1px solid transparent; }}
        .episode-item:hover {{ border-color: var(--accent); background: #2a3542; }}
        .episode-item img {{ width: 80px; height: 50px; margin-right: 15px; border-radius: 5px; object-fit: cover; }}
        .back-btn {{ background: var(--accent); color: #000; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <div id="main-screen">
        <h1 style="text-align:center; color:var(--accent); letter-spacing: 2px;">TITAN TV PORTAL</h1>
        <div class="grid" id="movie-grid"></div>
    </div>

    <div id="episodes-screen" class="hidden" style="padding:20px;">
        <button class="back-btn" onclick="location.reload()">← ANA SAYFAYA DÖN</button>
        <div id="episode-content"></div>
    </div>

    <div id="player-screen">
        <button onclick="closePlayer()" style="position:fixed; top:20px; right:20px; z-index:10001; background:red; color:white; border:none; padding:12px 20px; border-radius:5px; font-weight:bold; cursor:pointer;">KAPAT</button>
        <div id="video-container" style="width:100%; height:100%;"></div>
    </div>

    <script>
        const diziData = {json_data};
        const mainProxy = "https://api.allorigins.win/get?url=";
        const grid = document.getElementById('movie-grid');

        // Kartları oluştur
        diziData.forEach((item, index) => {{
            grid.innerHTML += `
                <div class="card" onclick="showEpisodes(${{index}})">
                    <div class="badge-imdb">⭐ ${{item.imdb}}</div>
                    <img src="${{item.img}}" onerror="this.src='https://via.placeholder.com/140x210?text=Resim+Yok'">
                    <div class="card-title">${{item.title}}</div>
                </div>`;
        }});

        async function showEpisodes(index) {{
            const item = diziData[index];
            document.getElementById('main-screen').classList.add('hidden');
            document.getElementById('episodes-screen').classList.remove('hidden');
            document.getElementById('episode-content').innerHTML = "<h3>" + item.title + " - Bölümler Yükleniyor...</h3>";

            try {{
                const res = await fetch(mainProxy + encodeURIComponent(item.link));
                const result = await res.json();
                const doc = new DOMParser().parseFromString(result.contents, 'text/html');
                const links = doc.querySelectorAll('.episode-item, .episodes li, a[href*="/bolum/"]');
                
                let html = '<div style="margin-top:20px;">';
                links.forEach(el => {{
                    const a = el.tagName === 'A' ? el : el.querySelector('a');
                    if(a) {{
                        const href = a.getAttribute('href');
                        const title = a.innerText.trim() || "Bölüm";
                        const fullHref = href.startsWith('http') ? href : "{BASE_URL}" + href;
                        html += `
                            <div class="episode-item" onclick="playVideo('${{fullHref}}')">
                                <img src="${{item.img}}">
                                <div>
                                    <div style="font-weight:bold; color:white;">${{title}}</div>
                                    <div style="font-size:10px; color:var(--accent);">İzlemek için tıklayın</div>
                                </div>
                            </div>`;
                    }}
                }});
                document.getElementById('episode-content').innerHTML = "<h2>" + item.title + "</h2>" + (html || '<p>Bölüm bulunamadı.</p>') + "</div>";
            }} catch(e) {{ 
                document.getElementById('episode-content').innerHTML = "<h3>Hata: Bölümler çekilemedi.</h3>";
            }}
        }}

        async function playVideo(url) {{
            document.getElementById('player-screen').style.display = 'block';
            document.getElementById('video-container').innerHTML = "<div style='color:white; text-align:center; margin-top:20%'><h2>Video Hazırlanıyor...</h2></div>";
            
            try {{
                const res = await fetch(mainProxy + encodeURIComponent(url));
                const result = await res.json();
                const doc = new DOMParser().parseFromString(result.contents, 'text/html');
                const iframe = doc.querySelector('#vast_new iframe, .series-player-container iframe, iframe');
                
                if(iframe) {{
                    let src = iframe.getAttribute('src');
                    if(src.startsWith('//')) src = 'https:' + src;
                    document.getElementById('video-container').innerHTML = `<iframe src="${{src}}" allowfullscreen allow="autoplay"></iframe>`;
                }} else {{ 
                    alert("Video oynatıcı bulunamadı!"); 
                    closePlayer(); 
                }}
            } catch(e) {{ 
                alert("Yükleme hatası!"); 
                closePlayer(); 
            }}
        }}

        function closePlayer() {{
            document.getElementById('player-screen').style.display = 'none';
            document.getElementById('video-container').innerHTML = '';
        }}
    </script>
</body>
</html>"""
    
    with open("dpalci.html", "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    diziler = get_content()
    if diziler:
        create_html(diziler)
        print(f"Bitti! {len(diziler)} içerik dpalci.html dosyasına işlendi.")
    else:
        print("İçerik çekilemedi, lütfen internetinizi veya BASE_URL'yi kontrol edin.")
