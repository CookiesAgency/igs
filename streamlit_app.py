import streamlit as st
st.set_page_config(page_title="📸 Instagram Post Analyzer", layout="centered")
import pandas as pd
import os
import asyncio
import sys
from scraper import scrape_posts_by_url
from image_downloader import screenshot_images_from_post_url_batch
from video_downloader import scarica_video_reel

# Ensure the session directory exists
os.makedirs("IGS/session", exist_ok=True)

st.info("🔐 Per iniziare, effettua il login su Instagram se richiesto.")
st.title("📸 Instagram Post Analyzer")

profile = st.text_input("Nome brand (usato per creare la cartella)", "la_saponaria")
profile_url = st.text_input("Link della pagina Instagram", f"https://www.instagram.com/{profile.strip().lstrip('@')}/")
if "instagram.com" in profile_url:
    try:
        path = profile_url.split("instagram.com/")[1].split("/")[0]
        profile_url = f"https://www.instagram.com/{path}/"
    except IndexError:
        profile_url = ""
num_posts = st.slider("Numero di post da analizzare", min_value=1, max_value=50, value=5)

csv_path = f"output/{profile}/posts.csv"
df = None
if os.path.exists(csv_path):
    try:
        df = pd.read_csv(csv_path)
        st.info(f"📁 CSV trovato per il brand '{profile}' e pronto per l'uso.")
        if "type" in df.columns:
            num_reel = df[df["type"] == "reel"].shape[0]
            st.info(f"🎞️ Numero totale di video Reel trovati: {num_reel}")
        if "profile_url" in df.columns:
            temp_url = df["profile_url"].iloc[0]
            if temp_url and "instagram.com/" in temp_url and temp_url.strip() != "https://www.instagram.com/":
                profile_url = temp_url
    except Exception as e:
        st.warning(f"⚠️ Errore nel caricamento del CSV: {e}")

if st.button("🔐 Esegui login Instagram (solo se richiesto)"):
    st.info("🌐 Apri il browser e accedi al profilo Instagram manualmente.")
    os.system(f"{sys.executable} setup_login.py IGS_profile --timeout 60")

if st.button("1️⃣ Avvia scraping profilo"):
    async def run_scraping():
        global df
        try:
            await scrape_posts_by_url(profile, profile_url, num_posts)

            if not os.path.exists(csv_path):
                st.warning("⚠️ Il file CSV non esiste. Qualcosa è andato storto durante lo scraping.")
                return

            st.success("✅ Scraping completato con successo!")

            df = pd.read_csv(csv_path)
            if "type" in df.columns:
                num_reel = df[df["type"] == "reel"].shape[0]
                st.info(f"🎞️ Trovati {num_reel} reel nel profilo.")
            df["profile_url"] = profile_url
            df.to_csv(csv_path, index=False)

            if os.path.exists(csv_path):
                st.subheader("📄 Anteprima dei dati estratti")
                st.dataframe(df)

                with open(csv_path, "rb") as f:
                    st.download_button(
                        label="📥 Scarica CSV",
                        data=f,
                        file_name=f"{profile}_posts.csv",
                        mime="text/csv"
                    )

                st.subheader("📊 Statistiche sintetiche")
                try:
                    if "likes" in df.columns:
                        media_like = pd.to_numeric(df["likes"], errors="coerce").fillna(0).mean()
                        st.metric("❤️ Media Like per post", f"{media_like:.1f}")
                    if "comment_count" in df.columns:
                        media_commenti = pd.to_numeric(df["comment_count"], errors="coerce").fillna(0).mean()
                        st.metric("💬 Media Commenti per post", f"{media_commenti:.1f}")
                except:
                    st.warning("⚠️ Impossibile calcolare le metriche.")
        except Exception as e:
            st.error(f"❌ Errore durante lo scraping: {e}")
    asyncio.run(run_scraping())

st.markdown("### 🎬 Scarica i video Reel (opzionale)")
if os.path.exists(csv_path):
    if df is not None and "type" in df.columns:
        num_reel = df[df["type"] == "reel"].shape[0]
        st.info(f"🎞️ Trovati {num_reel} reel nel CSV del profilo.")

    if "type" in df.columns:
        num_reel = df[df["type"] == "reel"].shape[0]
        st.info(f"🎞️ Trovati {num_reel} reel nel profilo.")

        if num_reel > 0:
            if st.button("2️⃣ Scarica video Reel"):
                try:
                    reel_df = df[df["type"] == "reel"]
                    if reel_df.empty:
                        st.warning("⚠️ Nessun Reel marcato. Uso fallback su link '/reel/'.")
                        reel_df = df[df["link"].str.contains("/reel/", na=False)].copy()
                        reel_df["type"] = "reel"

                    # Update the cookie path
                    cookie_path = "IGS/session/instagram_cookies.txt"
                    df = scarica_video_reel(df, profile, csv_path, cookie_path=cookie_path)

                    for idx, row in df.iterrows():
                        if row.get("type") == "reel" and "video_path" in row and pd.notna(row["video_path"]):
                            video_path = row["video_path"]
                            if os.path.exists(video_path):
                                post_date = row.get("date", f"{idx}")
                                base_dir = os.path.dirname(video_path)
                                new_name = f"{profile}_reel_{post_date}.mp4"
                                new_path = os.path.join(base_dir, new_name)

                                counter = 1
                                while os.path.exists(new_path):
                                    new_name = f"{profile}_reel_{post_date}_{counter}.mp4"
                                    new_path = os.path.join(base_dir, new_name)
                                    counter += 1

                                os.rename(video_path, new_path)
                                df.at[idx, "video_path"] = new_path

                    df.to_csv(csv_path, index=False)
                    st.success("✅ Video scaricati e CSV aggiornato.")
                    st.dataframe(df)
                except Exception as e:
                    st.error(f"❌ Errore durante il download dei Reel: {e}")
        else:
            st.warning("⚠️ Nessun reel trovato nel CSV.")
    
st.markdown("### 🖼️ Scarica immagini da post e caroselli")
if os.path.exists(csv_path):
    if st.button("3️⃣ Scarica immagini post e caroselli", key="scarica_immagini"):
        try:
            image_dir = os.path.join("output", profile, "immagini")
            os.makedirs(image_dir, exist_ok=True)

            df = pd.read_csv(csv_path)
            df = screenshot_images_from_post_url_batch(df=df, output_dir=image_dir, profile_name=profile)
            df.to_csv(csv_path, index=False)
            st.success("✅ Immagini scaricate e CSV aggiornato.")
            st.dataframe(df)
        except Exception as e:
            st.error(f"❌ Errore durante il download delle immagini: {e}")
else:
    st.warning("⚠️ CSV non trovato. Esegui prima lo scraping.")
