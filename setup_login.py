from playwright.sync_api import sync_playwright
import os
import time
import shutil
import argparse

def inizializza_sessione_instagram(profile_name, timeout=60):
    user_data_dir = os.path.join("playwright_sessions", profile_name)
    if os.path.exists(user_data_dir):
        shutil.rmtree(user_data_dir)
    os.makedirs(user_data_dir, exist_ok=True)

    singleton_lock_path = os.path.join(user_data_dir, "SingletonLock")
    if os.path.exists(singleton_lock_path):
        os.remove(singleton_lock_path)

    state_path = os.path.join(user_data_dir, "state.json")
    if os.path.exists(state_path):
        print(f"⚠️ Sessione già esistente per {profile_name}. Verrà rimossa per consentire un nuovo login.")
        os.remove(state_path)

    with sync_playwright() as p:
        is_render = os.environ.get("RENDER", "false").lower() == "true"
        
        if is_render:
            context = p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=True,
                args=["--no-sandbox"]
            )
        else:
            context = p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=False,
                channel="chrome"
            )
        print("\n🟢 Chrome avviato con profilo persistente")
        print("👉 Effettua il login manualmente su Instagram nella finestra aperta")
        print("   e poi CHIUDI la finestra quando hai terminato.\n")
        
        def wait_for_browser_close(context, timeout=60):
            print("⏳ Attesa chiusura browser per completare il login (timeout: 1 minuto)...")
            start_time = time.time()

            while time.time() - start_time < timeout:
                if not context.pages or all(page.is_closed() for page in context.pages):
                    print("✅ Browser chiuso, procedo con il salvataggio della sessione.")
                    return True
                time.sleep(1)

            print("⚠️ Timeout raggiunto. Continuo comunque.")
            return False

        wait_for_browser_close(context, timeout)
        context.close()
        
        # Salva i cookie della sessione per yt-dlp
        try:
            cookies_path = os.path.join("IGS", "session", "instagram_cookies.txt")
            os.makedirs(os.path.dirname(cookies_path), exist_ok=True)

            # Recupera i cookie da una pagina Instagram
            page = context.new_page()
            page.goto("https://www.instagram.com", timeout=60000)
            cookies = context.cookies()
            cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])

            with open(cookies_path, "w") as f:
                f.write(cookie_str)

            print(f"✅ Cookie salvati in {cookies_path}")
        except Exception as e:
            print(f"❌ Errore durante il salvataggio dei cookie: {e}")

        print("✅ Login completato e sessione salvata.")

def parse_args():
    parser = argparse.ArgumentParser(description="Inizializza una sessione Instagram con un profilo specifico.")
    parser.add_argument("profile_name", help="Nome del profilo da usare per la sessione")
    parser.add_argument("--timeout", type=int, default=60, help="Timeout per il login manuale (in secondi)")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    inizializza_sessione_instagram(args.profile_name, args.timeout)