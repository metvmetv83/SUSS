import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import re
import subprocess
import os
import html

# --- AYARLAR ---
BASE_URL = "https://dizipal.cx"
PLATFORM_SLUG = "hbomax"
OUTPUT_FILE = "hbomax.json"


def get_chrome_version():
    try:
        output = subprocess.check_output(
            ['google-chrome', '--version']
        ).decode('utf-8')
        version = re.search(r'Google Chrome (\d+)', output).group(1)
        return int(version)
    except:
        return None


def clean_key(text):
    text = html.unescape(text)
    text = re.sub(r'[\s\:\,\'’"”]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


def get_full_res_image(srcset):
    if not srcset:
        return ""
    links = [s.strip().split(' ')[0] for s in srcset.split(',')]
    return links[-1] if links else ""


def wait_for_cloudflare(driver, timeout=40):
    print("Cloudflare geçişi bekleniyor...")
    start = time.time()

    while time.time() - start < timeout:
        if "Just a moment" not in driver.title and "Cloudflare" not in driver.title:
            if len(driver.page_source) > 50000:
                print("Cloudflare geçildi.")
                return True
        time.sleep(2)

    print("Cloudflare geçilemedi.")
    return False


def scrape_hbomax():

    version = get_chrome_version()
    print(f"Sistem Chrome Versiyonu: {version}")

    options = uc.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-extensions')
    options.add_argument('--lang=tr')

    driver = uc.Chrome(options=options, version_main=version)
    wait = WebDriverWait(driver, 15)

    results = {}

    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                results = json.load(f)
            print(f"Mevcut dosya yüklendi: {len(results)} içerik")
        except:
            pass

    try:
        driver.get(BASE_URL)

        if not wait_for_cloudflare(driver):
            driver.quit()
            return

        page_num = 1

        while True:
            platform_url = f"{BASE_URL}/platform/{PLATFORM_SLUG}/page/{page_num}/"
            print(f"\n--- Sayfa {page_num} ---")

            driver.get(platform_url)
            time.sleep(3)

            items = driver.find_elements(By.CLASS_NAME, "post-item")

            # Eğer boşsa gerçekten mi boş yoksa CF mi kontrol et
            if not items:
                if len(driver.page_source) < 50000:
                    print("Muhtemelen CF tekrar devrede. Bekleniyor...")
                    time.sleep(10)
                    continue
                print("Sayfa boş. İşlem tamam.")
                break

            page_contents = []

            for item in items:
                try:
                    anchor = item.find_element(By.TAG_NAME, "a")
                    img = item.find_element(By.TAG_NAME, "img")
                    title = anchor.get_attribute("title")

                    key = clean_key(title)
                    if key in results:
                        continue

                    page_contents.append({
                        "title": title,
                        "url": anchor.get_attribute("href"),
                        "img": get_full_res_image(
                            img.get_attribute("srcset")
                        ) or img.get_attribute("src"),
                        "key": key
                    })
                except:
                    continue

            print(f"Yeni içerik: {len(page_contents)}")

            for content in page_contents:
                try:
                    print(f"> {content['title']}")
                    driver.get(content['url'])
                    time.sleep(2)

                    key = content['key']
                    results[key] = {
                        "isim": content['title'],
                        "resim": content['img'],
                        "bolumler": []
                    }

                    episode_elements = driver.find_elements(
                        By.CSS_SELECTOR, "a[href*='bolum']"
                    )
                    iframes = driver.find_elements(By.TAG_NAME, "iframe")

                    # Film
                    if not episode_elements and iframes:
                        embed_src = iframes[0].get_attribute("src")
                        results[key]["bolumler"].append({
                            "bolum_baslik": f"{content['title']} (Film)",
                            "link": embed_src
                        })
                        continue

                    # Dizi
                    season_elements = driver.find_elements(
                        By.CSS_SELECTOR, "a[href*='?sezon=']"
                    )

                    season_urls = set()

                    for s in season_elements:
                        season_urls.add(s.get_attribute("href"))

                    if not season_urls:
                        season_urls.add(content['url'])

                    all_episode_urls = []

                    for s_link in sorted(season_urls):
                        driver.get(s_link)
                        time.sleep(1)

                        eps = driver.find_elements(
                            By.CSS_SELECTOR, "a[href*='bolum']"
                        )

                        for ep in eps:
                            url = ep.get_attribute("href")
                            if url not in all_episode_urls:
                                all_episode_urls.append(url)

                    print(f"  Bölüm sayısı: {len(all_episode_urls)}")

                    ep_count = 1

                    for ep_url in all_episode_urls:
                        try:
                            driver.get(ep_url)

                            wait.until(
                                EC.presence_of_element_located(
                                    (By.TAG_NAME, "iframe")
                                )
                            )

                            iframe = driver.find_element(
                                By.TAG_NAME, "iframe"
                            )

                            src = iframe.get_attribute("src")

                            results[key]["bolumler"].append({
                                "bolum_baslik":
                                f"{content['title']} {ep_count}. Bölüm",
                                "link": src
                            })

                            ep_count += 1

                        except:
                            continue

                except Exception as e:
                    print("Hata:", e)
                    continue

            page_num += 1

    except Exception as e:
        print("Kritik Hata:", e)

    finally:
        driver.quit()

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"Toplam {len(results)} içerik kaydedildi.")


if __name__ == "__main__":
    scrape_hbomax()
