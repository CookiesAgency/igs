import os
import pandas as pd
from playwright.sync_api import sync_playwright
from PIL import Image

def screenshot_images_from_post_url(post_url, image_dir, filename_prefix, profile_name, post_type=None):
    image_paths = []
    try:
        with sync_playwright() as p:
            is_render = os.environ.get("RENDER", "false").lower() == "true"
            if is_render:
                browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            else:
                browser = p.chromium.launch(headless=False, channel="chrome")
            context = browser.new_context(storage_state="playwright_sessions/IGS_profile/state.json")
            page = context.new_page()

            if "?img_index=" in post_url or "type" in post_url:
                base_url = post_url.split("?")[0]
            else:
                base_url = post_url

            # Controlla se è un carosello basandosi sul post_type
            if post_type == "image":
                try:
                    indexed_url = f"{base_url}?img_index=1"
                    print(f"🔗 Apertura immagine singola: {indexed_url}")
                    page.goto(indexed_url, timeout=15000)
                    page.wait_for_selector("article", timeout=10000)
                    page.wait_for_timeout(2000)
                    path = os.path.join(image_dir, f"{filename_prefix}_img1.jpg")
                    page.screenshot(path=path, full_page=False)
                    print(f"📸 Immagine salvata: {path}")
                    # Ritaglio immagine dopo lo screenshot
                    image = Image.open(path)
                    left = 355
                    top = 29
                    right = 836
                    bottom = image.height - 92
                    cropped = image.crop((left, top, right, bottom))  # (left, top, right, bottom)
                    cropped.save(path)
                    print(f"✂️ Immagine ritagliata salvata in: {path}")
                    image_paths.append(path)
                except Exception as e:
                    print(f"⚠️ Errore immagine singola: {e}")
            else:
                # Carosello (default)
                for i in range(1, 11):
                    indexed_url = f"{base_url}?img_index={i}"
                    print(f"🔗 Apertura immagine carosello {i}: {indexed_url}")
                    try:
                        page.goto(indexed_url, timeout=15000)
                        page.wait_for_selector("article", timeout=10000)
                        page.wait_for_timeout(2000)
                        path = os.path.join(image_dir, f"{filename_prefix}_img{i}.jpg")
                        page.screenshot(path=path, full_page=False)
                        print(f"✅ Salvata immagine {i}: {indexed_url}")
                        # Ritaglio immagine dopo lo screenshot
                        try:
                            image = Image.open(path)
                            left = 355
                            top = 29
                            right = 836  # 240 + 800
                            bottom = image.height - 92
                            cropped = image.crop((left, top, right, bottom))  # (left, top, right, bottom)
                            cropped.save(path)
                            print(f"✂️ Immagine ritagliata salvata in: {path}")
                        except Exception as e:
                            print(f"⚠️ Errore durante il ritaglio: {e}")
                        image_paths.append(path)
                        missing_images_count = 0
                    except Exception as e:
                        print(f"⚠️ Errore immagine {i}: {e}")
                        missing_images_count += 1
                        if missing_images_count >= 3:
                            print("🚫 Tre immagini consecutive mancanti, interrompo il ciclo.")
                            break

            context.close()
            browser.close()
    except Exception as e:
        print(f"⚠️ Errore screenshot immagini: {e}")
    return image_paths

def screenshot_images_from_post_url_batch(df, image_dir=None, output_dir=None, profile_name=None):
    if output_dir is not None:
        image_dir = output_dir
    if image_dir is None:
        raise ValueError("Devi specificare image_dir o output_dir.")

    for i, row in df.iterrows():
        post_type = str(row.get("type", "")).lower()
        if post_type == "reel":
            print(f"⏭️ Riga {i+1} — post di tipo 'reel', salto lo screenshot.")
            continue
            
        post_url = row["link"]
        print(f"🔗 URL in elaborazione: {post_url}")
        post_date = row["date"] if "date" in row and not pd.isna(row["date"]) else f"post_{i+1}"
        image_paths = screenshot_images_from_post_url(post_url, image_dir=image_dir, filename_prefix=f"{profile_name}_post_{i+1}", profile_name=profile_name, post_type=post_type)

        if len(image_paths) > 1:
            # Carosello
            carousel_dir = os.path.join(image_dir, f"{profile_name}_carosello_{post_date}")
            os.makedirs(carousel_dir, exist_ok=True)
            moved_files = []
            for path in image_paths:
                filename = os.path.basename(path)
                new_path = os.path.join(carousel_dir, filename)
                os.rename(path, new_path)
                moved_files.append(new_path)
            df.at[i, "image"] = ", ".join(moved_files)
            print(f"📂 Immagini del carosello salvate in: {carousel_dir}")
        elif image_paths:
            # Post singolo
            image_filename = f"{profile_name}_post_{post_date}.jpg"
            final_path = os.path.join(image_dir, image_filename)
            os.rename(image_paths[0], final_path)
            df.at[i, "image"] = final_path
            print(f"📸 Immagine singola salvata: {final_path}")

    return df

__all__ = [
    "screenshot_images_from_post_url",
    "screenshot_images_from_post_url_batch"
]