# IGS – Instagram Growth Scraper

Uno strumento completo per analizzare post Instagram, fare scraping e scaricare screenshot delle creatività (immagini, caroselli, reel) con ritaglio automatico.

## 🚀 Funzionalità

- Estrazione post da link o profili
- Classificazione automatica (`image`, `carousel`, `reel`)
- Salvataggio screenshot ritagliati (senza UI IG)
- CSV con metadati e immagini
- Interfaccia web via Streamlit

---

## 🧱 Requisiti (uso locale – macOS)

- Python 3.10+
- Homebrew (per Node.js)
- Node.js (`brew install node`)
- Playwright (`pip install playwright`)
- Chromium via `python -m playwright install`
- Xcode Command Line Tools (`xcode-select --install`)

---

## 🛠️ Installazione

```bash
git clone https://github.com/CookiesAgency/igs.git
cd igs
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install