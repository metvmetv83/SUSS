import asyncio
from playwright.async_api import async_playwright
import json
import re

async def main():
    async with async_playwright() as p:
        # Gerçek bir tarayıcı başlat
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        print("🔍 Dizipal'a gidiliyor...")
        try:
            # Sayfayı aç ve Cloudflare'in çözülmesini bekle
            await page.goto("https://dizipal.uk/filmler/", wait_until="networkidle", timeout=60000)
            
            # İçeriğin yüklenmesi için 5 saniye ekstra bekle
            await page.wait_for_timeout(5000)

            content = await page.content()
            
            # Film bilgilerini ayıkla (Regex ile)
            pattern = r'<div[^>]*class="[^"]*post-item[^"]*"[^>]*>.*?<a[^>]*href="([^"]+)"[^>]*title="([^"]+)"'
            matches = re.findall(pattern, content, re.DOTALL)
            
            movies = [{"title": m[1].strip(), "url": m[0].strip()} for m in matches]
            
            if movies:
                with open("filmler.json", "w", encoding="utf-8") as f:
                    json.dump(movies, f, ensure_ascii=False, indent=4)
                print(f"✅ Başarılı: {len(movies)} film kaydedildi.")
            else:
                print("⚠️  Sayfa yüklendi ama film bulunamadı. Seçicileri kontrol et.")
                # Hata ayıklama için sayfa kaynağını kaydet
                with open("debug.html", "w", encoding="utf-8") as f:
                    f.write(content)

        except Exception as e:
            print(f"❌ Bir hata oluştu: {e}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
