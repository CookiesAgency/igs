# streamlit_app.py

import streamlit as st
import os
import asyncio
from scraper import scrape_posts_by_url

st.set_page_config(page_title="IGS - Instagram Scraper", layout="centered")
st.title("📸 Instagram Post Analyzer")

PROFILE = st.text_input("🔤 Nome brand (usato per creare la cartella)", value="la_saponaria")
PROFILE_URL = st.text_input("🔗 Link della pagina Instagram", value="https://www.instagram.com/la_saponaria/?hl=en")
NUM_POSTS = st.slider("📌 Numero di post da analizzare", min_value=1, max_value=50, value=5)

if st.button("🚀 Avvia scraping"):
    st.info("📡 Inizio scraping dei post...")
    asyncio.run(scrape_posts_by_url(PROFILE, PROFILE_URL, NUM_POSTS))
    st.success(f"✅ Scraping completato. Controlla la cartella: data/{PROFILE}/")

    csv_path = os.path.join("data", PROFILE, "posts_summary.csv")
    if os.path.exists(csv_path):
        st.markdown("---")
        st.subheader("📊 Risultati")
        import pandas as pd
        df = pd.read_csv(csv_path)
        st.dataframe(df)

        with open(csv_path, "rb") as f:
            st.download_button(
                label="⬇️ Scarica CSV",
                data=f,
                file_name=f"{PROFILE}_posts_summary.csv",
                mime="text/csv"
            )
    else:
        st.warning("⚠️ Nessun file CSV trovato. Qualcosa potrebbe essere andato storto.")
