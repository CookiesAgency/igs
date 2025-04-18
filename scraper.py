import os
import json
import pandas as pd
import time
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import requests
from datetime import datetime

async def scrape_posts_by_url(profile_name, profile_url, num_posts, session_name="IGS_profile"):
    output_dir = f"output/{profile_name}"
    video_dir = os.path.join(output_dir, "videos")
    os.makedirs(video_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--autoplay-policy=no-user-gesture-required"])

        # Persistente sessione utente (salva cookies e login)
        user_data_dir = os.path.join(".auth", session_name)
        os.makedirs(user_data_dir, exist_ok=True)

        state_path = os.path.join(user_data_dir, "state.json")

        # Primo lancio: login manuale, salvataggio stato
        if not os.path.exists(state_path):
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto("https://www.instagram.com/accounts/login/")
            print("⏳ Fai login su Instagram, poi premi invio nel terminale...")
            input()
            await context.storage_state(path=state_path)
            await context.close()

        # Riutilizzo sessione salvata
        context = await browser.new_context(storage_state=state_path)
        page = await context.new_page()

        await page.goto(profile_url)
        await page.wait_for_timeout(3000)

        try:
            follower_element = await page.query_selector("header li:nth-child(2) span span")
            followers_text = await follower_element.inner_text() if follower_element else "0"
            if "k" in followers_text.lower():
                followers = int(float(followers_text.lower().replace("k", "").replace(",", ".")) * 1000)
            elif "m" in followers_text.lower():
                followers = int(float(followers_text.lower().replace("m", "").replace(",", ".")) * 1000000)
            else:
                followers = int(followers_text.replace(".", "").replace(",", ""))
        except:
            followers = 0

        try:
            postcount_element = await page.query_selector("header li:nth-child(1) span span")
            posts_total_text = await postcount_element.inner_text() if postcount_element else "0"
            total_posts = int(posts_total_text.replace(".", "").replace(",", ""))
        except:
            total_posts = 0

        post_links = []
        seen = set()
        while len(post_links) < num_posts:
            anchors = await page.query_selector_all("a")
            for a in anchors:
                href = await a.get_attribute("href")
                if href and ("/p/" in href or "/reel/" in href) and href not in seen:
                    seen.add(href)
                    post_links.append("https://www.instagram.com" + href)
                if len(post_links) >= num_posts:
                    break
            await page.mouse.wheel(0, 8000)
            await page.wait_for_timeout(500)

        post_links = post_links[:num_posts]

        posts_data = []
        post_page = await context.new_page()

        for i, link in enumerate(post_links):
            video_path = os.path.join(video_dir, f"post_{i+1}.mp4")  # evita duplicati
            try:
                start_time = time.time()
                await post_page.goto(link, timeout=8000)
                try:
                    await post_page.wait_for_selector("article", timeout=4000)
                except PlaywrightTimeout:
                    if "/reel/" in link:
                        print("ℹ️ Reel senza <article>, continuo comunque.")
                    else:
                        raise
                await post_page.wait_for_timeout(100)
                elapsed_time = time.time() - start_time
                print(f"⏱️ Tempo apertura post {i+1}: {elapsed_time:.2f} sec")

                # Caption
                t1 = time.time()
                try:
                    caption = await post_page.inner_text("article header + div span")
                except:
                    caption = ""
                print(f"⏱️ Tempo per caption: {time.time() - t1:.2f}s")

                # Testo principale (header post)
                t1b = time.time()
                try:
                    post_text = await post_page.inner_text("h1")
                except:
                    post_text = ""
                print(f"⏱️ Tempo per testo post: {time.time() - t1b:.2f}s")

                # Data di pubblicazione
                t1c = time.time()
                try:
                    timestamp_element = await post_page.query_selector("time")
                    post_date = await timestamp_element.get_attribute("datetime") if timestamp_element else ""
                    if post_date:
                        post_date = datetime.fromisoformat(post_date.replace("Z", "+00:00")).strftime("%d %b %Y")
                except:
                    post_date = ""
                print(f"⏱️ Tempo per data: {time.time() - t1c:.2f}s")

                # Likes
                t2 = time.time()
                likes = 0
                try:
                    # Cerca elemento contenente 'likes' (tipico nei reel)
                    spans = await post_page.query_selector_all("span")
                    for span in spans:
                        text = await span.inner_text()
                        if text and ('likes' in text.lower() or 'mi piace' in text.lower()):
                            digits = ''.join(filter(str.isdigit, text))
                            if digits:
                                likes = int(digits)
                                break
                except:
                    likes = 0
                print(f"⏱️ Tempo per like: {time.time() - t2:.2f}s")

                # Commenti
                t3 = time.time()
                try:
                    comment_blocks = await post_page.query_selector_all("ul ul span")
                    comments = [await el.inner_text() for el in comment_blocks if await el.inner_text() != caption]
                except:
                    comments = []
                comment_count = len(comments)
                print(f"⏱️ Tempo per commenti: {time.time() - t3:.2f}s")

                # Tipo
                try:
                    if "/reel/" in link:
                        post_type = "reel"
                    else:
                        # Conta quanti media ci sono nel post (img o video dentro <ul><li>)
                        items = await post_page.query_selector_all("ul > li div img, ul > li div video")
                        post_type = "carousel" if len(items) > 1 else "image"
                except:
                    post_type = "unknown"

                # Download video se REEL
                if post_type == "reel":
                    try:
                        ld_json_tags = await post_page.query_selector_all('script[type="application/ld+json"]')
                        for tag in ld_json_tags:
                            content = await tag.inner_text()
                            if "VideoObject" in content and "contentUrl" in content:
                                try:
                                    data = json.loads(content)
                                    if isinstance(data, dict) and "contentUrl" in data:
                                        video_url = data["contentUrl"]
                                        print(f"🎯 Video URL trovato da ld+json: {video_url}")
                                        video_resp = requests.get(video_url, headers={"User-Agent": "Mozilla/5.0"})
                                        if video_resp.status_code == 200:
                                            if not os.path.exists(video_path):  # evita duplicati
                                                with open(video_path, "wb") as f:
                                                    f.write(video_resp.content)
                                            print(f"📥 Video scaricato da JSON ld+json: {video_path}")
                                        break
                                except Exception as json_err:
                                    print(f"⚠️ Errore parsing JSON ld+json: {json_err}")
                    except Exception as e:
                        print(f"⚠️ Errore cercando video in script ld+json: {e}")

                    try:
                        video_element = await post_page.query_selector("video")
                        if video_element:
                            video_src = await video_element.get_attribute("src")
                            if video_src:
                                if video_src.startswith("blob:"):
                                    print("🔄 Tentativo di estrarre blob con Playwright handle...")
                                    try:
                                        video_data = await post_page.evaluate_handle("""
                                            async () => {
                                                try {
                                                    const video = document.querySelector("video");
                                                    if (!video || !video.src) return null;
                                                    const res = await fetch(video.src);
                                                    if (!res.ok) throw new Error("Fetch failed");
                                                    const buf = await res.arrayBuffer();
                                                    return [...new Uint8Array(buf)];
                                                } catch (e) {
                                                    console.error("JS Fetch failed:", e);
                                                    return null;
                                                }
                                            }
                                        """)
                                        buffer = await video_data.json_value()
                                        if buffer:
                                            if not os.path.exists(video_path):  # evita duplicati
                                                with open(video_path, "wb") as f:
                                                    f.write(bytes(buffer))
                                            print(f"📥 Video estratto da blob e salvato: {video_path}")
                                        else:
                                            print("❌ Nessun dato ottenuto dal blob video.")
                                    except Exception as e:
                                        print(f"❌ Errore estraendo video blob via handle: {e}")
                                else:
                                    video_resp = requests.get(video_src, headers={"User-Agent": "Mozilla/5.0"})
                                    if video_resp.status_code == 200:
                                        if not os.path.exists(video_path):  # evita duplicati
                                            with open(video_path, "wb") as f:
                                                f.write(video_resp.content)
                                        print(f"📥 Video scaricato direttamente da src: {video_path}")
                    except Exception as e:
                        print(f"❌ Errore estraendo video da tag <video>: {e}")

                if not video_path:
                    print("⚠️ Nessun video scaricato. Skipping fallback.")

                # Screenshot
                t4 = time.time()
                screenshot_path = f"{output_dir}/post_{i+1}.png"
                await post_page.screenshot(path=screenshot_path)
                print(f"⏱️ Tempo per screenshot: {time.time() - t4:.2f}s")

                # Salva HTML della pagina per debug
                with open(f"{output_dir}/post_{i+1}.html", "w", encoding="utf-8") as f:
                    f.write(await post_page.content())

                post_info = {
                    "link": link,
                    "caption": caption,
                    "text": post_text,
                    "date": post_date,
                    "likes": likes,
                    "comments": comments,
                    "comment_count": comment_count,
                    "type": post_type,
                    "screenshot": screenshot_path,
                    "followers": followers,
                    "total_posts_on_profile": total_posts,
                }
                print(f"🔍 Tipo post rilevato: {post_type}")
                posts_data.append(post_info)

                print(f"⏱️ Tempo totale per post {i+1}: {time.time() - start_time:.2f}s")

            except PlaywrightTimeout:
                print(f"⚠️ Timeout su {link}, post saltato")
                video_path = ""
                post_info = {
                    "link": link,
                    "caption": "",
                    "text": "",
                    "date": "",
                    "likes": 0,
                    "comments": [],
                    "comment_count": 0,
                    "type": "unknown",
                    "screenshot": "",
                    "followers": followers,
                    "total_posts_on_profile": total_posts,
                }
                posts_data.append(post_info)
                continue

        await post_page.close()

        # Save metadata
        with open(f"{output_dir}/metadata.json", "w") as f:
            json.dump(posts_data, f, indent=2, ensure_ascii=False)

        # Save CSV
        df = pd.DataFrame(posts_data)
        df.to_csv(f"{output_dir}/posts.csv", index=False)

        await context.close()
        await browser.close()
