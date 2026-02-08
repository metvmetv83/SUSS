import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
import json
import re

async def main():
    async with async_playwright() as p:
        # Tarayıcıyı başlat
        browser = await p.chromium.launch(headless=True)
        # Gerçekçi bir parmak izi oluştur
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        
        page = await context.new_page()
        # Stealth modunu aktif et (Cloudflare'i kandırmak için kritik)
        await stealth_async(page)

        print("🚀 Dizipal'a sızılıyor...")
        try:
            # networkidle yerine domcontentloaded kullanarak timeout riskini azaltıyoruz
            await page.goto("https://dizipal.uk/filmler/", wait_until="domcontentloaded", timeout=60000)
            
            # Cloudflare bekleme sayfasını geçmek için zorunlu bekleme (10 saniye)
            print("⏳ Cloudflare doğrulaması bekleniyor (10sn)...")
            await asyncio.sleep(10)

            content = await page.content()
            
            # Seçiciyi biraz daha genişletelim (Farklı temalara uyum sağlaması için)
            # Hem 'post-item' hem de genel 'article' yapılarını arar
            pattern = r'href="([^"]*/film/[^"]*)"[^>]*title="([^"]+)"'
            matches = re.findall(pattern, content, re.IGNORECASE)
            
            if not matches:
                # Alternatif: Title ve Href yer değiştirmiş olabilir
                pattern = r'title="([^"]+)"[^>]*href="([^"]*/film/[^"]*)"'
                matches = [(m[1], m[0]) for m in re.findall(pattern, content, re.IGNORECASE)]

            movies = []
            seen_urls = set()
            for url, title in matches:
                if url not in seen_urls:
                    movies.append({"title": title.strip(), "url": url.strip()})
                    seen_urls.add(url)
            
            if movies:
                with open("filmler.json", "w", encoding="utf-8") as f:
                    json.dump(movies, f, ensure_ascii=False, indent=4)
                print(f"✅ BAŞARILI: {len(movies)} film yakalandı.")
            else:
                print("⚠️  İçerik boş döndü. Cloudflare hala geçilememiş olabilir.")
                with open("debug.html", "w", encoding="utf-8") as f:
                    f.write(content)

        except Exception as e:
            print(f"❌ Hata: {str(e)}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
