# ============================================================
# STREAMSMART - Pipeline Python
# Connexion SQLite + Pandas + API Last.fm + RFM + Écriture BDD
# ============================================================

import sqlite3
import pandas as pd
import requests
import os
from datetime import datetime
from dotenv import load_dotenv

# Chargement des variables d'environnement (.env)
load_dotenv()

DB_PATH = "streamsmart.db"
LASTFM_API_KEY = os.getenv("LASTFM_API_KEY", "demo_key")

# ============================================================
# 1. CONNEXION À LA BASE
# ============================================================

def get_connection():
    """Retourne une connexion SQLite"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ============================================================
# 2. CHARGEMENT DES DONNÉES AVEC PANDAS
# ============================================================

def load_data():
    """Charge les données depuis la vue v_user_stats"""
    conn = get_connection()

    # Données utilisateurs depuis la vue
    df_users = pd.read_sql_query("SELECT * FROM v_user_stats", conn)

    # Données d'écoutes brutes
    df_listens = pd.read_sql_query("""
        SELECT 
            l.user_id,
            l.listened_at,
            l.completed,
            t.genre,
            t.artist,
            t.title
        FROM listens l
        JOIN tracks t ON l.track_id = t.track_id
    """, conn)

    # Abonnements actifs
    df_subs = pd.read_sql_query("""
        SELECT user_id, plan, monthly_price, start_date
        FROM subscriptions
        WHERE end_date IS NULL
    """, conn)

    conn.close()

    print(f"✅ Données chargées : {len(df_users)} utilisateurs, {len(df_listens)} écoutes")
    return df_users, df_listens, df_subs


# ============================================================
# 3. APPEL API LAST.FM - Enrichissement des tracks
# ============================================================

def get_artist_tags(artist_name, api_key):
    """
    Appelle l'API Last.fm pour récupérer les tags (genres) d'un artiste.
    
    Paramètres:
        artist_name (str) : nom de l'artiste
        api_key (str)     : clé API Last.fm
    
    Retourne:
        str : premier tag trouvé, ou 'Unknown' si erreur
    """
    url = "https://ws.audioscrobbler.com/2.0/"
    params = {
        "method": "artist.gettoptags",
        "artist": artist_name,
        "api_key": api_key,
        "format": "json"
    }
    try:
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        tags = data.get("toptags", {}).get("tag", [])
        if tags:
            # Retourne le premier tag significatif
            return tags[0]["name"].capitalize()
        return "Unknown"
    except Exception:
        return "Unknown"


def enrich_tracks_with_api():
    """
    Enrichit les tracks avec les genres Last.fm.
    Retourne un dictionnaire artiste -> genre enrichi.
    """
    conn = get_connection()
    df_tracks = pd.read_sql_query("SELECT DISTINCT artist FROM tracks", conn)
    conn.close()

    print(f"\n🎵 Enrichissement via API Last.fm pour {len(df_tracks)} artistes...")
    genre_map = {}

    for artist in df_tracks["artist"]:
        tag = get_artist_tags(artist, LASTFM_API_KEY)
        genre_map[artist] = tag
        print(f"   {artist} → {tag}")

    return genre_map


# ============================================================
# 4. CALCUL RFM
# ============================================================

def calculate_rfm(df_users, df_listens, df_subs):
    """
    Calcule les scores RFM pour chaque utilisateur.
    
    - Recency  : jours depuis la dernière écoute (moins = mieux)
    - Frequency: nombre total d'écoutes
    - Monetary : revenus estimés (monthly_price * mois d'abonnement)
    
    Paramètres:
        df_users   (DataFrame) : données utilisateurs depuis la vue
        df_listens (DataFrame) : données d'écoutes brutes
        df_subs    (DataFrame) : abonnements actifs
    
    Retourne:
        DataFrame avec scores et segments RFM
    """
    print("\n📊 Calcul RFM en cours...")

    # ── Recency ──────────────────────────────────────────────
    # Utilise days_since_last_listen de la vue
    df_rfm = df_users[["user_id", "full_name", "email", "country", "plan", "monthly_price",
                        "total_listens", "days_since_last_listen"]].copy()

    # Remplace les NaN (users sans écoutes) par valeur maximale
    df_rfm["days_since_last_listen"] = df_rfm["days_since_last_listen"].fillna(9999)
    df_rfm["total_listens"] = df_rfm["total_listens"].fillna(0)

    # ── Monetary ─────────────────────────────────────────────
    # Calcul : monthly_price * nombre de mois depuis l'abonnement
    df_subs["start_date"] = pd.to_datetime(df_subs["start_date"])
    df_subs["months_subscribed"] = (
        (datetime.now() - df_subs["start_date"]).dt.days / 30
    ).round(1)
    df_subs["monetary"] = (df_subs["monthly_price"] * df_subs["months_subscribed"]).round(2)

    df_rfm = df_rfm.merge(
        df_subs[["user_id", "monetary"]],
        on="user_id",
        how="left"
    )
    df_rfm["monetary"] = df_rfm["monetary"].fillna(0)

    # ── Scores RFM (1 à 3) ───────────────────────────────────
    # Recency : moins de jours = meilleur score
    df_rfm["r_score"] = pd.cut(
        df_rfm["days_since_last_listen"],
        bins=[-1, 30, 180, 9999],
        labels=[3, 2, 1]
    ).astype(int)

    # Frequency : plus d'écoutes = meilleur score
    df_rfm["f_score"] = pd.cut(
        df_rfm["total_listens"],
        bins=[-1, 2, 5, 9999],
        labels=[1, 2, 3]
    ).astype(int)

    # Monetary : plus de revenus = meilleur score
    df_rfm["m_score"] = pd.cut(
        df_rfm["monetary"],
        bins=[-1, 0, 100, 9999],
        labels=[1, 2, 3]
    ).astype(int)

    # Score total RFM
    df_rfm["rfm_score"] = df_rfm["r_score"] + df_rfm["f_score"] + df_rfm["m_score"]

    # ── Segmentation ─────────────────────────────────────────
    def assign_segment(row):
        score = row["rfm_score"]
        r = row["r_score"]
        if score == 9:
            return "Champion"
        elif score >= 7:
            return "Loyal"
        elif score >= 5 and r >= 2:
            return "Potentiel"
        elif score >= 4 and r == 1:
            return "À risque"
        else:
            return "Inactif"

    df_rfm["segment"] = df_rfm.apply(assign_segment, axis=1)

    # Renommage pour cohérence avec la BDD
    df_rfm.rename(columns={
        "days_since_last_listen": "recency",
        "total_listens": "frequency"
    }, inplace=True)

    print(f"✅ RFM calculé pour {len(df_rfm)} utilisateurs")
    print("\n📋 Répartition des segments :")
    print(df_rfm["segment"].value_counts().to_string())

    return df_rfm


# ============================================================
# 5. ÉCRITURE DES RÉSULTATS DANS LA BASE
# ============================================================

def save_rfm_to_db(df_rfm, genre_map):
    """
    Écrit les résultats RFM enrichis dans la table rfm_segments.
    
    Paramètres:
        df_rfm    (DataFrame) : résultats RFM
        genre_map (dict)      : mapping artiste -> genre Last.fm
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Récupère le genre le plus écouté par user pour l'enrichissement
    conn2 = get_connection()
    df_top_genre = pd.read_sql_query("""
        SELECT 
            l.user_id,
            t.artist,
            COUNT(*) as cnt
        FROM listens l
        JOIN tracks t ON l.track_id = t.track_id
        GROUP BY l.user_id, t.artist
    """, conn2)
    conn2.close()

    # Genre enrichi = genre Last.fm de l'artiste le plus écouté par user
    df_top_artist = df_top_genre.sort_values("cnt", ascending=False).drop_duplicates("user_id")
    df_top_artist["genre_enrichi"] = df_top_artist["artist"].map(genre_map).fillna("Unknown")

    df_rfm = df_rfm.merge(
        df_top_artist[["user_id", "genre_enrichi"]],
        on="user_id",
        how="left"
    )
    df_rfm["genre_enrichi"] = df_rfm["genre_enrichi"].fillna("Unknown")

    # Supprime les anciens résultats
    cursor.execute("DELETE FROM rfm_segments")

    # Insertion des nouveaux résultats
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for _, row in df_rfm.iterrows():
        cursor.execute("""
            INSERT INTO rfm_segments 
            (user_id, full_name, email, country, plan, recency, frequency, monetary,
             r_score, f_score, m_score, rfm_score, segment, genre_enrichi, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            int(row["user_id"]),
            row["full_name"],
            row["email"],
            row["country"],
            row["plan"] if row["plan"] else "free",
            int(row["recency"]),
            int(row["frequency"]),
            float(row["monetary"]),
            int(row["r_score"]),
            int(row["f_score"]),
            int(row["m_score"]),
            int(row["rfm_score"]),
            row["segment"],
            row["genre_enrichi"],
            now
        ))

    conn.commit()
    conn.close()
    print(f"\n✅ {len(df_rfm)} résultats écrits dans rfm_segments")


# ============================================================
# 6. MAIN
# ============================================================

if __name__ == "__main__":
    print("=" * 55)
    print("  STREAMSMART - Pipeline RFM")
    print("=" * 55)

    # Chargement
    df_users, df_listens, df_subs = load_data()

    # Enrichissement API
    genre_map = enrich_tracks_with_api()

    # Calcul RFM
    df_rfm = calculate_rfm(df_users, df_listens, df_subs)

    # Sauvegarde
    save_rfm_to_db(df_rfm, genre_map)

    print("\n🎉 Pipeline terminé ! Lance dashboard.py pour voir le dashboard.")