from playwright.sync_api import sync_playwright
import os

PROFILE_NAME = "IGS_profile"  # nome che vuoi usare per il profilo
SESSION_DIR = f"playwright_sessions/{PROFILE_NAME}"
os.makedirs(SESSION_DIR, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=False)  # headless=False per fare login manualmente
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://www.instagram.com")

    print("👉 Fai login su Instagram nella finestra aperta.")
    input("🔒 Premi INVIO dopo aver completato il login...")

    context.storage_state(path=f"{SESSION_DIR}/state.json")
    print(f"✅ Sessione salvata in {SESSION_DIR}/state.json")

    browser.close()