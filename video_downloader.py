import os
import subprocess
from datetime import datetime
import pandas as pd

def scarica_video_reel(df, profile_name, csv_path, cookie_path=None):
    reel_df = df[df["type"] == "reel"].copy()
    if reel_df.empty:
        print("⚠️ Nessun reel trovato nel dataframe.")
        return df

    video_dir = os.path.join("output", profile_name, "video")
    os.makedirs(video_dir, exist_ok=True)

    for idx, row in reel_df.iterrows():
        link = row["link"]
        print(f"🎬 Provo a scaricare il video da: {link}")
        try:
            post_date_raw = row.get("date", "").strip()
            if post_date_raw:
                post_date_str = post_date_raw.replace(" ", "_").replace("/", "-")
            else:
                post_date_str = "unknown_date"
            filename = f"{profile_name}_reel_{post_date_str}.mp4"
            output_path = os.path.join(video_dir, filename)

            if os.path.exists(output_path):
                print(f"⏩ Video già scaricato: {output_path}")
                df.at[idx, "video_path"] = output_path
                continue

            if not cookie_path:
                cookie_path = os.path.join("IGS", "session", "instagram_cookies.txt")
            if not os.path.exists(cookie_path):
                print(f"⚠️ Cookie file non trovato: {cookie_path}")
                df.at[idx, "video_path"] = "cookie_missing"
                continue
            
            cmd = [
                "yt-dlp",
                "--cookies", cookie_path,
                "-o", output_path,
                link
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)

            print("stdout:", result.stdout)
            print("stderr:", result.stderr)

            if result.returncode == 0:
                # Verifica che il file sia stato creato correttamente
                if not os.path.exists(output_path):
                    # Cerca il file MP4 più recente nella cartella video
                    mp4_files = [f for f in os.listdir(video_dir) if f.endswith(".mp4")]
                    if mp4_files:
                        mp4_files = sorted(mp4_files, key=lambda f: os.path.getmtime(os.path.join(video_dir, f)), reverse=True)
                        latest_file = os.path.join(video_dir, mp4_files[0])
                        os.rename(latest_file, output_path)
                        print(f"📁 File rinominato da {latest_file} a {output_path}")
                    else:
                        print(f"⚠️ Nessun file MP4 trovato per rinominare {link}")
                        df.at[idx, "video_path"] = "errore"
                        continue

                df.at[idx, "video_path"] = output_path
            else:
                print(f"❌ Errore durante il download del video: {link}")
                df.at[idx, "video_path"] = "errore"

        except Exception as e:
            print(f"❌ Errore imprevisto per {link}: {e}")
            df.at[idx, "video_path"] = "errore"

    df.to_csv(csv_path, index=False)
    return df
