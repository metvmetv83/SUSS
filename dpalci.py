import requests
import re
import json
from urllib.parse import quote

# AYARLAR
BASE_URL = "https://www.dizipal1226.com"
# Codetabs proxy genelde daha kararlı sonuç verir
PROXY_JS = "https://api.codetabs.com/v1/proxy/?quest="

def fetch_data_python(url):
    """Python tarafında ana sayfa verilerini çekmek için kullanılan proxy servisi"""
    python_proxy = "https://api.allorigins.win/get?url="
    try:
        res = requests.get(python_proxy + quote(url), timeout=25)
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
        print(f"Tarama yapılıyor: {t}...")
        html = fetch_data_python(f"{BASE_URL}/{t}")
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
    json_data = json.dumps(data, ensure_ascii=False)
    
    # HTML şablonu (Replace yöntemi ile en güvenli yol)
    html_template = """<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>METV | VOD PORTAL</title>
    <script type="module" src="https://cdn.jsdelivr.net/npm/@ionic/core/dist/ionic/ionic.esm.js"></script>
    <style>
        :root { --main-bg: #0b0c10; --card-bg: #1f2833; --accent: #66fcf1; --text: #c5c6c7; }
        body { background: var(--main-bg); color: #fff; font-family: 'Segoe UI', sans-serif; margin: 0; overflow-x: hidden; }
        .aramapanel { display: flex; justify-content: space-between; align-items: center; padding: 15px 20px; background: #161b22; border-bottom: 2px solid var(--accent); }
        .logo img { width: 45px; height: 45px; object-fit: contain; }
        .logoisim { font-size: 22px; font-weight: 800; color: #fff; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 15px; padding: 15px; }
        .card { position: relative; background: var(--card-bg); border-radius: 8px; overflow: hidden; cursor: pointer; transition: 0.3s; border: 1px solid #45a29e33; }
        .card:hover { transform: scale(1.03); border-color: var(--accent); }
        .card img { width: 100%; height: 210px; object-fit: cover; }
        .badge-imdb { position: absolute; top: 8px; right: 8px; background: rgba(0,0,0,0.85); color: #EEBF16; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: bold; }
        .card-info { padding: 8px; text-align: center; }
        .card-title { font-size: 11px; font-weight: bold; color: var(--accent); overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
        .bolum-header { padding: 25px; display: flex; align-items: center; gap: 20px; background: #161b22; }
        .bolum-header img { width: 80px; height: 110px; border-radius: 6px; object-fit: cover; }
        .last-episodes { display: flex; flex-wrap: wrap; gap: 12px; padding: 15px; }
        .episode-item { width: calc(50% - 6px); }
        .episode-item a { display: flex; align-items: center; background: rgba(255,255,255,0.05); padding: 10px; border-radius: 8px; text-decoration: none; border: 1px solid transparent; }
        .episode-item a:hover { border-color: var(--accent); background: rgba(255,255,255,0.1); }
        .episode-item img { width: 90px; height: 55px; border-radius: 4px; margin-right: 12px; object-fit: cover; }
        .ep-title { display: block; color: #fff; font-size: 13px; font-weight: 500; }
        #player-screen { display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:#000; z-index:10000; }
        iframe { width: 100%; height: 100%; border: none; }
        .hidden { display: none !important; }
        #loading-overlay { display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.9); z-index:20000; flex-direction:column; align-items:center; justify-content:center; color:var(--accent); }
        @media (max-width: 700px) { .episode-item { width: 100%; } }
    </style>
</head>
<body>

<div id="loading-overlay">
    <ion-spinner name="crescent"></ion-spinner>
    <p id="loading-text">Yükleniyor...</p>
</div>

<div class="aramapanel">
    <div class="logoisim">ME TV PORTAL</div>
    <input type="text" id="seriesSearch" placeholder="Ara..." style="padding:8px; border-radius:20px; border:1px solid var(--accent); background:#000; color:#fff;" oninput="searchSeries()">
</div>

<div id="main-screen">
    <div class="grid" id="movie-grid"></div>
</div>

<div id="episodes-screen" class="hidden">
    <ion-button fill="clear" style="--color:var(--accent)" onclick="showMain()">← GERİ DÖN</ion-button>
    <div id="episode-content"></div>
</div>

<div id="player-screen">
    <ion-button style="position:absolute; top:10px; right:10px; z-index:11" color="danger" onclick="closePlayer()">KAPAT</ion-button>
    <div id="video-container" style="width:100%; height:100%;"></div>
</div>

<script>
const diziler = [JSON_DATA];
const proxy = "https://api.codetabs.com/v1/proxy/?quest=";

function toggleLoading(show, text = "Yükleniyor...") {
    const loader = document.getElementById('loading-overlay');
    document.getElementById('loading-text').innerText = text;
    loader.style.display = show ? 'flex' : 'none';
}

function renderMain(filter = "") {
    const grid = document.getElementById('movie-grid');
    grid.innerHTML = "";
    diziler.forEach((dizi, index) => {
        if(dizi.title.toLowerCase().includes(filter.toLowerCase())) {
            grid.innerHTML += `
                <div class="card" onclick="fetchEpisodes(${index})">
                    <div class="badge-imdb">⭐ ${dizi.imdb}</div>
                    <img src="${dizi.img}" loading="lazy">
                    <div class="card-info"><div class="card-title">${dizi.title}</div></div>
                </div>`;
        }
    });
}

function searchSeries() {
    renderMain(document.getElementById('seriesSearch').value);
}

async function fetchEpisodes(index) {
    const dizi = diziler[index];
    toggleLoading(true, "Bölümler listeleniyor...");
    try {
        const response = await fetch(proxy + encodeURIComponent(dizi.link));
        const html = await response.text();
        const doc = new DOMParser().parseFromString(html, "text/html");
        // Senin kodundaki seçiciler
        const items = doc.querySelectorAll('.episode-item, .episodes li, a[href*="/bolum/"]');
        let episodesHTML = '';
        
        items.forEach(item => {
            const a = item.tagName === 'A' ? item : item.querySelector('a');
            if(!a) return;
            const href = a.getAttribute('href');
            const title = a.innerText.trim() || "Bölüm";
            const fullLink = href.startsWith('http') ? href : "[BASE_URL]" + href;
            
            episodesHTML += `
                <div class="episode-item">
                    <a href="javascript:void(0)" onclick="fetchEmbed('${fullLink}')">
                        <img src="${dizi.img}">
                        <div class="ep-info">
                            <span class="ep-title">${title}</span>
                        </div>
                    </a>
                </div>`;
        });
        
        document.getElementById('episode-content').innerHTML = `
            <div class="bolum-header">
                <img src="${dizi.img}">
                <div><h2>${dizi.title}</h2><p>⭐ IMDb: ${dizi.imdb}</p></div>
            </div>
            <div class="last-episodes">${episodesHTML || '<p>Bölüm bulunamadı.</p>'}</div>`;
        
        document.getElementById('main-screen').classList.add('hidden');
        document.getElementById('episodes-screen').classList.remove('hidden');
        window.scrollTo(0,0);
    } catch (e) { alert("Hata!"); }
    toggleLoading(false);
}

async function fetchEmbed(bolumLink) {
    toggleLoading(true, "Video hazırlanıyor...");
    try {
        const response = await fetch(proxy + encodeURIComponent(bolumLink));
        const html = await response.text();
        const doc = new DOMParser().parseFromString(html, "text/html");
        let embedUrl = doc.querySelector('#vast_new iframe')?.getAttribute('src') ||
                       doc.querySelector('.series-player-container iframe')?.getAttribute('src') ||
                       doc.querySelector('iframe')?.getAttribute('src');
        
        if (embedUrl) {
            if(embedUrl.startsWith('//')) embedUrl = 'https:' + embedUrl;
            document.getElementById('player-screen').style.display = 'block';
            document.getElementById('video-container').innerHTML = \`<iframe src="\${embedUrl}" allowfullscreen allow="autoplay"></iframe>\`;
        } else { alert("Kaynak bulunamadı."); }
    } catch (e) { alert("Hata!"); }
    toggleLoading(false);
}

function closePlayer() { document.getElementById('player-screen').style.display = 'none'; document.getElementById('video-container').innerHTML = ''; }
function showMain() { document.getElementById('main-screen').classList.remove('hidden'); document.getElementById('episodes-screen').classList.add('hidden'); }

renderMain();
</script>
</body>
</html>"""
    
    # Değişkenleri yerleştir
    final_html = html_template.replace("[JSON_DATA]", json_data[1:-1]).replace("[BASE_URL]", BASE_URL)
    
    with open("dpalci.html", "w", encoding="utf-8") as f:
        f.write(final_html)

if __name__ == "__main__":
    print("Veriler toplanıyor...")
    data = get_content()
    if data:
        create_html(data)
        print(f"Bitti! {len(data)} içerik dpalci.html dosyasına işlendi.")
