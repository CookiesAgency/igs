# scraper.py

import os
import json
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright

async def scrape_posts_by_url(PROFILE, PROFILE_URL, NUM_POSTS):
    BASE_DIR = f"data/{PROFILE}"
    os.makedirs(BASE_DIR, exist_ok=True)
    USER_DATA_DIR = "./user-data"

    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            USER_DATA_DIR,
            headless=False,
            viewport={"width": 1200, "height": 1500},
            args=["--disable-blink-features=AutomationControlled"]
        )

        page = browser.pages[0] if browser.pages else await browser.new_page()

        # Stealth script
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
        await page.add_init_script("window.navigator.chrome = { runtime: {} };")
        await page.add_init_script("Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });")
        await page.add_init_script("Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });")

        print(f"🌐 Apro il profilo: {PROFILE_URL}")
        await page.goto(PROFILE_URL)
        await asyncio.sleep(3)

        print("🔄 Scroll per caricare i post...")
        for _ in range(8):
            await page.mouse.wheel(0, 3000)
            await asyncio.sleep(1.2)

        print("🔍 Estrazione link post...")
        links = await page.locator("a[href*='/p/'], a[href*='/reel/']").evaluate_all("els => els.map(e => e.href)")
        POST_URLS = list(dict.fromkeys(links))[:NUM_POSTS]
        print(f"✅ Trovati {len(POST_URLS)} link da analizzare.")

        for idx, post_url in enumerate(POST_URLS):
            video_error = False
            print(f"➡️ Apro il post {idx+1}: {post_url}")
            await page.goto(post_url)
            await asyncio.sleep(3)

            # Prova a interagire con il player video
            try:
                video_player = page.locator("video").first
                if await video_player.count() > 0:
                    await video_player.click()
                    await asyncio.sleep(1)
            except:
                video_error = True

            date_str = "unknown"
            try:
                date_element = page.locator("time").first
                if await date_element.count() > 0:
                    date_str = await date_element.get_attribute("datetime")
            except:
                pass

            caption_element = page.locator(".x1lliihq .x1k6rc7s").first
            caption = await caption_element.inner_text() if await caption_element.count() > 0 else "No caption"

            try:
                likes_element = page.locator("xpath=(//span[contains(text(),'Piace a') or contains(text(),'likes') or contains(text(),'visualizzazioni') or contains(text(),'views')]/preceding-sibling::span)[1]")
                if await likes_element.count() > 0:
                    likes = await likes_element.inner_text()
                else:
                    og_desc = await page.locator("meta[property='og:description']").get_attribute("content")
                    if og_desc:
                        import re
                        match = re.search(r"(\\d+) likes", og_desc)
                        likes = match.group(1) if match else "0"
                    else:
                        likes = "0"
            except:
                likes = "0"

            comments = "0"
            try:
                comments_element = await page.query_selector_all("ul ul")
                comments = str(len(comments_element))
            except:
                pass

            tipo = "reel" if "/reel/" in post_url else "post"

            folder = os.path.join(BASE_DIR, f"post_{idx+1}")
            os.makedirs(folder, exist_ok=True)
            screenshot_path = os.path.join(folder, "screenshot.jpg")
            await page.screenshot(path=screenshot_path)

            metadata = {
                "url": post_url,
                "caption": caption,
                "likes": likes,
                "comments": comments,
                "data_pubblicazione": date_str,
                "screenshot": screenshot_path,
                "note": "⚠️ Video non disponibile o bloccato" if video_error else "",
                "tipo": tipo
            }

            with open(os.path.join(folder, "metadata.json"), "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=4, ensure_ascii=False)

            print(f"✅ Post {idx+1} salvato")

        await browser.close()

    # Esporta CSV
    import csv
    csv_path = os.path.join(BASE_DIR, "posts_summary.csv")
    with open(csv_path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["url", "caption", "likes", "comments", "data_pubblicazione", "screenshot", "note", "tipo", "engagement_rate"])
        writer.writeheader()

        for i in range(len(POST_URLS)):
            meta_path = os.path.join(BASE_DIR, f"post_{i+1}", "metadata.json")
            if os.path.exists(meta_path):
                with open(meta_path, encoding="utf-8") as f:
                    data = json.load(f)
                    try:
                        likes = int(data.get("likes", "0"))
                        comments = int(data.get("comments", "0"))
                        engagement = likes + comments
                    except:
                        engagement = "error"
                    data["engagement_rate"] = engagement
                    writer.writerow(data)

    print(f"📄 File CSV esportato in: {csv_path}")
