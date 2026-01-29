import requests
import re
import json
from urllib.parse import quote

# AYARLAR
BASE_URL = "https://www.dizipal1226.com"

def fetch_data_python(url):
    """Python tarafında siteleri taramak için kullanılan proxy"""
    python_proxy = "https://api.allorigins.win/get?url="
    try:
        res = requests.get(python_proxy + quote(url), timeout=20)
        if res.status_code == 200:
            return res.json().get('contents', '')
    except:
        return ""
    return ""

def get_content():
    targets = [
        "koleksiyon/netflix", "koleksiyon/exxen", "koleksiyon/blutv", 
        "koleksiyon/disney", "koleksiyon/gain", "diziler", "filmler"
    ]
    
    all_items = []
    for t in targets:
        print(f"Tarama yapılıyor: {t}...")
        html = fetch_data_python(f"{BASE_URL}/{t}")
        if not html: continue

        # Regex ile li elementlerini yakalıyoruz
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
                    "imdb": m_imdb.group(1) if m_imdb else "0.0",
                    "link": full_link
                })
    
    # Tekilleştirme
    unique = {x['link']: x for x in all_items}.values()
    return list(unique)

def create_html(data):
    # Veriyi JSON formatına çevir
    json_data = json.dumps(data, ensure_ascii=False)
    
    html_template = """<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ME TV PORTAL</title>
    <style>
        :root { --main-bg: #0b0c10; --card-bg: #1f2833; --accent: #66fcf1; }
        body { background: var(--main-bg); color: #fff; font-family: sans-serif; margin: 0; padding-bottom: 50px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 15px; padding: 15px; }
        .card { background: var(--card-bg); border-radius: 8px; overflow: hidden; cursor: pointer; border: 1px solid #45a29e33; transition: 0.3s; position: relative; }
        .card:hover { transform: scale(1.05); border-color: var(--accent); }
        .card img { width: 100%; height: 210px; object-fit: cover; }
        .card-title { padding: 8px; font-size: 11px; text-align: center; color: var(--accent); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .badge-imdb { position: absolute; top: 5px; right: 5px; background: rgba(0,0,0,0.8); color: orange; padding: 2px 5px; border-radius: 4px; font-size: 10px; }
        #loading { display:none; position:fixed; top:50%; left:50%; transform:translate(-50%, -50%); background:rgba(0,0,0,0.9); padding:20px; border-radius:10px; z-index:10000; border:1px solid var(--accent); }
        .hidden { display: none !important; }
        .episode-item { background: #1f2833; margin: 8px; padding: 12px; border-radius: 8px; cursor: pointer; border: 1px solid #45a29e33; }
        .episode-item:hover { border-color: var(--accent); }
        #player-screen { display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:#000; z-index:1000; }
        iframe { width:100%; height:100%; border:none; }
    </style>
</head>
<body>

    <div id="loading">İşlem yapılıyor, lütfen bekleyin...</div>

    <div id="main-view">
        <h1 style="text-align:center; color:var(--accent);">ME TV PORTAL</h1>
        <div class="grid" id="movie-grid"></div>
    </div>

    <div id="episode-view" class="hidden" style="padding:20px;">
        <button onclick="showMain()" style="background:var(--accent); padding:10px; border:none; cursor:pointer; font-weight:bold;">← ANA SAYFA</button>
        <div id="episode-list"></div>
    </div>

    <div id="player-screen">
        <button onclick="closePlayer()" style="position:fixed; top:10px; right:10px; background:red; color:#fff; border:none; padding:10px; z-index:1100; cursor:pointer;">KAPAT</button>
        <div id="video-container" style="width:100%; height:100%;"></div>
    </div>

    <script>
        // Python'dan gelen JSON verisi
        const diziData = [JSON_DATA][0]; 
        const BASE_URL = "[BASE_URL]";

        const proxyList = [
            "https://api.codetabs.com/v1/proxy/?quest=",
            "https://corsproxy.io/?",
            "https://api.allorigins.win/get?url="
        ];

        const grid = document.getElementById('movie-grid');
        
        diziData.forEach((item, index) => {
            grid.innerHTML += `
                <div class="card" onclick="loadEpisodes(${index})">
                    <div class="badge-imdb">⭐ ${item.imdb}</div>
                    <img src="${item.img}" onerror="this.src='https://via.placeholder.com/140x210'">
                    <div class="card-title">${item.title}</div>
                </div>`;
        });

        async function smartFetch(url) {
            for(let p of proxyList) {
                try {
                    const finalUrl = p + encodeURIComponent(url);
                    const res = await fetch(finalUrl);
                    if(!res.ok) continue;
                    
                    if(p.includes("allorigins")) {
                        const data = await res.json();
                        if(data.contents) return data.contents;
                    } else {
                        const data = await res.text();
                        if(data && data.length > 500) return data; 
                    }
                } catch(e) { console.error("Proxy hatası:", p); continue; }
            }
            return null;
        }

        async function loadEpisodes(index) {
            const item = diziData[index];
            const loader = document.getElementById('loading');
            loader.style.display = 'block';
            
            const html = await smartFetch(item.link);
            if(!html) { 
                alert("Bölümler çekilemedi. Lütfen bir süre sonra tekrar deneyin veya farklı bir içerik seçin."); 
                loader.style.display = 'none'; 
                return; 
            }

            const doc = new DOMParser().parseFromString(html, 'text/html');
            const links = doc.querySelectorAll('a[href*="/bolum/"], .episode-item a, .episodes li a');
            
            let listHtml = '<h2 style="color:var(--accent)">' + item.title + '</h2>';
            let found = false;

            links.forEach(a => {
                const href = a.getAttribute('href');
                const title = a.innerText.trim() || "Bölüm";
                if(href && !href.includes('#') && href.includes('bolum')) {
                    const fullHref = href.startsWith('http') ? href : BASE_URL + (href.startsWith('/') ? '' : '/') + href;
                    listHtml += `<div class="episode-item" onclick="playVideo('${fullHref}')">${title}</div>`;
                    found = true;
                }
            });

            if(!found) listHtml += "<p>Üzgünüz, bu içerik için aktif bölüm linki bulunamadı.</p>";

            document.getElementById('episode-list').innerHTML = listHtml;
            document.getElementById('main-view').classList.add('hidden');
            document.getElementById('episode-view').classList.remove('hidden');
            loader.style.display = 'none';
            window.scrollTo(0,0);
        }

        async function playVideo(url) {
            document.getElementById('loading').style.display = 'block';
            const html = await smartFetch(url);
            if(!html) { alert("Video sayfası yüklenemedi."); document.getElementById('loading').style.display = 'none'; return; }

            const doc = new DOMParser().parseFromString(html, 'text/html');
            const iframe = doc.querySelector('#vast_new iframe, .series-player-container iframe, iframe[src*="embed"], iframe[src*="m3u8"]');
            
            if(iframe) {
                let src = iframe.getAttribute('src');
                if(src.startsWith('//')) src = 'https:' + src;
                document.getElementById('player-screen').style.display = 'block';
                document.getElementById('video-container').innerHTML = `<iframe src="${src}" allowfullscreen allow="autoplay"></iframe>`;
            } else { 
                alert("Video kaynağı (iframe) bu sayfada bulunamadı."); 
            }
            document.getElementById('loading').style.display = 'none';
        }

        function showMain() {
            document.getElementById('main-view').classList.remove('hidden');
            document.getElementById('episode-view').classList.add('hidden');
        }

        function closePlayer() {
            document.getElementById('player-screen').style.display = 'none';
            document.getElementById('video-container').innerHTML = '';
        }
    </script>
</body>
</html>"""

    # Veriyi enjekte et
    final_html = html_template.replace("[JSON_DATA]", json_data).replace("[BASE_URL]", BASE_URL)
    
    with open("dpalci.html", "w", encoding="utf-8") as f:
        f.write(final_html)

    # HATA DÜZELTİLDİ: json_data olduğu gibi (köşeli parantezlerle) gönderiliyor
    final_html = html_template.replace("[JSON_DATA]", json_data).replace("[BASE_URL]", BASE_URL)
    
    with open("dpalci.html", "w", encoding="utf-8") as f:
        f.write(final_html)

if __name__ == "__main__":
    print("Veriler Python tarafından çekiliyor...")
    data = get_content()
    if data:
        create_html(data)
        print(f"Tamamlandı! {len(data)} içerik dpalci.html dosyasına işlendi.")
    else:
        print("Hata: Ana sayfadan veri çekilemedi. Bağlantınızı kontrol edin.")
