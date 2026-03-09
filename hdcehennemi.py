import asyncio
import json
import os
from playwright.async_api import async_playwright

# --- AYARLAR ---
BASE_URL = "https://www.hdfilmcehennemi.nl"
OUTPUT_FILE = "filmler.json"
START_PAGE = 1      # Kaldığın sayfadan devam için değiştir
END_PAGE = None     # None = tüm sayfalar, örn: 10 = ilk 10 sayfa
DELAY_BETWEEN_FILMS = 0.5
DELAY_BETWEEN_PAGES = 1.0
# ---------------

async def get_current_films(page):
    posters = await page.query_selector_all("a.poster")
    film_tasks = []
    for poster in posters:
        link = await poster.get_attribute("href")
        if not link:
            continue
        skip_patterns = ['/yil/', '/tur/', '/category/', '/oyuncu/', '/ulke/', '/fragman/', '/film-robotu']
        if any(p in link for p in skip_patterns):
            continue
        img_node = await poster.query_selector("img")
        resim = ""
        if img_node:
            resim = (await img_node.get_attribute("data-src") or
                     await img_node.get_attribute("src") or "")
        name_node = await poster.query_selector("strong.poster-title")
        isim = await name_node.inner_text() if name_node else (
            await poster.get_attribute("title") or "İsim Yok")
        full_url = link if link.startswith("http") else f"{BASE_URL}{link}"
        film_tasks.append({
            "slug": link.strip("/").split("/")[-1],
            "url": full_url,
            "isim": isim.strip(),
            "resim": resim
        })
    return list({v['url']: v for v in film_tasks}.values())


async def get_pagination_info(page):
    try:
        pagination = await page.query_selector("nav.pagination-container")
        if not pagination:
            return 1, 1
        total = int(await pagination.get_attribute("data-pages") or 1)
        current = int(await pagination.get_attribute("data-current-page") or 1)
        return current, total
    except:
        return 1, 1


async def go_next_page(page, current_page):
    next_target = current_page + 1

    # Önce numara butonuna bas
    page_btns = await page.query_selector_all("nav.pagination-container button.page-number")
    for btn in page_btns:
        txt = (await btn.inner_text()).strip()
        if txt == str(next_target):
            disabled = await btn.get_attribute("disabled")
            if not disabled:
                await btn.click()
                await asyncio.sleep(1.5)
                return True

    # Yoksa "Sonraki" butonuna bas
    next_btn = await page.query_selector("nav.pagination-container button.next-page")
    if next_btn:
        disabled = await next_btn.get_attribute("disabled")
        if not disabled:
            await next_btn.click()
            await asyncio.sleep(1.5)
            return True

    return False


async def get_video_link(page, film):
    try:
        await page.goto(film["url"], wait_until="domcontentloaded", timeout=30000)

        rapid_btns = await page.query_selector_all(".alternative-links button.alternative-link")
        rapidrame_btn = None
        for btn in rapid_btns:
            text = (await btn.inner_text()).strip().lower()
            if "rapidrame" in text:
                rapidrame_btn = btn
                break

        if rapidrame_btn:
            await rapidrame_btn.click()
            await asyncio.sleep(0.8)

        iframe = await page.query_selector(
            "iframe.rapidrame, iframe.close, iframe[data-src*='rplayer'], "
            "iframe[src*='rplayer'], iframe[data-src*='embed']"
        )
        video_link = None
        if iframe:
            video_link = (await iframe.get_attribute("src") or
                          await iframe.get_attribute("data-src"))

        if not video_link:
            for ifr in await page.query_selector_all("iframe"):
                src = await ifr.get_attribute("src") or await ifr.get_attribute("data-src") or ""
                if any(kw in src for kw in ["rplayer", "embed", "video", "player"]):
                    video_link = src
                    break

        if video_link:
            if video_link.startswith("//"):
                video_link = "https:" + video_link
            return video_link
    except Exception as e:
        print(f"   ⚠️ {e}")
    return None


async def scrape():
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            final_data = json.load(f)
        print(f"📂 Mevcut veri: {len(final_data)} film")
    else:
        final_data = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--dns-prefetch-disable", "--no-sandbox"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 720},
            # Sistemin DNS'ini kullanması için proxy yok, ama timeout artırıldı
        )

        list_page = await context.new_page()
        film_page = await context.new_page()

        print(f"🌐 Ana sayfa açılıyor: {BASE_URL}")
        try:
            await list_page.goto(f"{BASE_URL}/", wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            print(f"❌ Ana sayfa açılamadı: {e}")
            print(f"\n💡 Çözüm: BASE_URL'yi güncel adresle değiştir.")
            print(f"   Tarayıcında çalışan adres neyse scriptin tepesindeki BASE_URL'ye yaz.")
            await browser.close()
            return

        current_page, total_pages = await get_pagination_info(list_page)
        end = END_PAGE if END_PAGE else total_pages
        print(f"📄 Toplam: {total_pages} sayfa | Taranacak: {START_PAGE} → {end}")

        # START_PAGE'e atla
        while current_page < START_PAGE:
            print(f"⏩ Atlıyorum: {current_page} → {current_page + 1}")
            ok = await go_next_page(list_page, current_page)
            if not ok:
                print("⚠️ Hedef sayfaya ulaşılamadı.")
                break
            new_cur, _ = await get_pagination_info(list_page)
            if new_cur == current_page:
                print("⚠️ Sayfa değişmedi.")
                break
            current_page = new_cur

        total_found = 0
        total_success = 0

        while current_page <= end:
            print(f"\n{'='*50}")
            print(f"📄 SAYFA {current_page}/{end}")
            print(f"{'='*50}")

            film_tasks = await get_current_films(list_page)
            new_films = [f for f in film_tasks if f["slug"] not in final_data]
            print(f"   {len(film_tasks)} film | {len(film_tasks)-len(new_films)} atlandı | {len(new_films)} yeni")
            total_found += len(new_films)

            for film in new_films:
                print(f"   🎬 {film['isim']}", end=" ... ", flush=True)
                video_link = await get_video_link(film_page, film)
                if video_link:
                    final_data[film["slug"]] = {
                        "isim": film["isim"],
                        "resim": film["resim"],
                        "link": video_link
                    }
                    total_success += 1
                    print("✅")
                else:
                    print("❌")
                await asyncio.sleep(DELAY_BETWEEN_FILMS)

            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(final_data, f, ensure_ascii=False, indent=4)
            print(f"   💾 Kaydedildi. Toplam: {len(final_data)} film")

            if current_page >= end:
                break

            await asyncio.sleep(DELAY_BETWEEN_PAGES)
            ok = await go_next_page(list_page, current_page)
            if not ok:
                print("⚠️ Sonraki sayfaya geçilemedi.")
                break

            new_cur, _ = await get_pagination_info(list_page)
            if new_cur == current_page:
                print("⚠️ Sayfa değişmedi.")
                break
            current_page = new_cur

        await browser.close()

    print(f"\n{'='*50}")
    print(f"✅ TAMAMLANDI")
    print(f"   Yeni film : {total_found}")
    print(f"   Başarılı  : {total_success}")
    print(f"   Toplam    : {len(final_data)} film")
    print(f"{'='*50}")


if __name__ == "__main__":
    asyncio.run(scrape())
