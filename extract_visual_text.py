import os
import json
from PIL import Image
import pytesseract

profile_name = "la_saponaria"
INPUT_METADATA = f"output/{profile_name}/metadata.json"
OUTPUT_TEXT_DIR = f"output/{profile_name}/transcripts"
os.makedirs(OUTPUT_TEXT_DIR, exist_ok=True)

def extract_text_from_image(image_path):
    try:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image, lang="ita")
        return text.strip()
    except Exception as e:
        print(f"Errore OCR immagine {image_path}: {e}")
        return ""

def main():
    if not os.path.exists(INPUT_METADATA):
        print("⚠️ File metadata.json non trovato.")
        return

    with open(INPUT_METADATA, "r") as f:
        posts = json.load(f)

    for post in posts:
        post_type = post.get("type")
        screenshot_path = post.get("screenshot")
        post_id = os.path.basename(screenshot_path).replace(".png", "")

        extracted_text = ""
        if post_type in ["image", "carousel", "reel"] and os.path.exists(screenshot_path):
            extracted_text = extract_text_from_image(screenshot_path)

        post["extracted_text"] = extracted_text

        with open(f"{OUTPUT_TEXT_DIR}/{post_id}.txt", "w") as out_text:
            out_text.write(extracted_text)

    with open(INPUT_METADATA, "w") as f:
        json.dump(posts, f, indent=2, ensure_ascii=False)

    print(f"✅ Testo estratto e salvato in {OUTPUT_TEXT_DIR} e metadata.json aggiornato.")

if __name__ == "__main__":
    main()