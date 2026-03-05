import asyncio
import json
import re
from playwright.async_api import async_playwright, TimeoutError

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        )

        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )

        page = await context.new_page()

        # Basit ama etkili stealth
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        """)

        print("🚀 Dizipal'a bağlanılıyor...")

        try:
            # ❗ networkidle YOK
            await page.goto(
                "https://dizipal.bar/filmler/",
                wait_until="domcontentloaded",
                timeout=90000
            )

            # Cloudflare JS için bekleme
            await asyncio.sleep(25)

            # Film linki gelene kadar bekle
            await page.wait_for_selector(
                "a[href*='/film/']",
                timeout=60000
            )

            content = await page.content()

            pattern = r'href="(https://dizipal\.uk/film/[^"]+)"[^>]*title="([^"]+)"'
            matches = re.findall(pattern, content)

            movies = []
            seen = set()

            for url, title in matches:
                if url not in seen:
                    movies.append({
                        "title": title.strip(),
                        "url": url
                    })
                    seen.add(url)

            if not movies:
                print("❌ Film bulunamadı.")
                with open("debug_source.txt", "w", encoding="utf-8") as f:
                    f.write(content)
                return

            with open("filmler.json", "w", encoding="utf-8") as f:
                json.dump(movies, f, ensure_ascii=False, indent=4)

            print(f"✅ BAŞARILI: {len(movies)} film kaydedildi.")

        except TimeoutError:
            print("❌ Timeout: Cloudflare sayfayı geçirmedi.")
        except Exception as e:
            print(f"🔥 HATA: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
