# ============================================================
# STREAMSMART - Setup base de données SQLite
# Ce script crée la base et insère toutes les données
# ============================================================

import sqlite3
import os

DB_PATH = "streamsmart.db"

def create_database():
    """Crée la base SQLite et toutes les tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Activation des foreign keys dans SQLite
    cursor.execute("PRAGMA foreign_keys = ON")

    # ── TABLES ──────────────────────────────────────────────

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name  TEXT NOT NULL,
            last_name   TEXT NOT NULL,
            email       TEXT NOT NULL UNIQUE,
            country     TEXT NOT NULL,
            created_at  TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            subscription_id  INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id          INTEGER NOT NULL,
            plan             TEXT NOT NULL CHECK(plan IN ('free','premium','family')),
            monthly_price    REAL NOT NULL,
            start_date       TEXT NOT NULL,
            end_date         TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tracks (
            track_id      INTEGER PRIMARY KEY AUTOINCREMENT,
            title         TEXT NOT NULL,
            artist        TEXT NOT NULL,
            genre         TEXT,
            duration_s    INTEGER NOT NULL,
            release_year  INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS playlists (
            playlist_id  INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER NOT NULL,
            name         TEXT NOT NULL,
            created_at   TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS playlist_tracks (
            playlist_id  INTEGER NOT NULL,
            track_id     INTEGER NOT NULL,
            added_at     TEXT NOT NULL,
            PRIMARY KEY (playlist_id, track_id),
            FOREIGN KEY (playlist_id) REFERENCES playlists(playlist_id),
            FOREIGN KEY (track_id) REFERENCES tracks(track_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS listens (
            listen_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER NOT NULL,
            track_id     INTEGER NOT NULL,
            listened_at  TEXT NOT NULL,
            completed    INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (track_id) REFERENCES tracks(track_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rfm_segments (
            user_id        INTEGER PRIMARY KEY,
            full_name      TEXT,
            email          TEXT,
            country        TEXT,
            plan           TEXT,
            recency        INTEGER,
            frequency      INTEGER,
            monetary       REAL,
            r_score        INTEGER,
            f_score        INTEGER,
            m_score        INTEGER,
            rfm_score      INTEGER,
            segment        TEXT,
            genre_enrichi  TEXT,
            updated_at     TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    conn.commit()
    print("✅ Tables créées")
    return conn

def insert_data(conn):
    """Insère toutes les données de test"""
    cursor = conn.cursor()

    # ── USERS ───────────────────────────────────────────────
    users = [
        ('Alice','Martin','alice.martin@email.com','France','2022-01-15'),
        ('Bob','Dupont','bob.dupont@email.com','France','2022-03-10'),
        ('Clara','Leroy','clara.leroy@email.com','Belgique','2022-05-22'),
        ('David','Moreau','david.moreau@email.com','France','2022-07-01'),
        ('Eva','Simon','eva.simon@email.com','Suisse','2022-08-14'),
        ('François','Laurent','francois.laurent@email.com','France','2022-09-30'),
        ('Grace','Petit','grace.petit@email.com','Canada','2023-01-05'),
        ('Hugo','Bernard','hugo.bernard@email.com','France','2023-02-18'),
        ('Inès','Thomas','ines.thomas@email.com','France','2023-04-11'),
        ('Jules','Robert','jules.robert@email.com','Belgique','2023-06-25'),
        ('Karine','Richard','karine.richard@email.com','France','2023-07-09'),
        ('Luc','Durand','luc.durand@email.com','France','2023-08-22'),
        ('Marie','Girard','marie.girard@email.com','Suisse','2023-09-15'),
        ('Nathan','Blanc','nathan.blanc@email.com','France','2023-10-03'),
        ('Olivia','Garnier','olivia.garnier@email.com','Canada','2023-11-17'),
        ('Pierre','Fabre','pierre.fabre@email.com','France','2024-01-08'),
        ('Quin','Rousseau','quin.rousseau@email.com','France','2024-02-14'),
        ('Rachel','Bonnet','rachel.bonnet@email.com','Belgique','2024-03-20'),
        ('Samuel','Lambert','samuel.lambert@email.com','France','2024-04-05'),
        ('Tina','Morel','tina.morel@email.com','France','2024-05-19'),
        ('Ugo','Fontaine','ugo.fontaine@email.com','France','2024-06-01'),
        ('Véra','Chevalier','vera.chevalier@email.com','Suisse','2024-07-13'),
        ('William','Robin','william.robin@email.com','France','2024-08-27'),
        ('Xena','Boyer','xena.boyer@email.com','France','2024-09-10'),
        ('Yann','Nicolas','yann.nicolas@email.com','France','2024-10-22'),
        ('Zoé','Mercier','zoe.mercier@email.com','Belgique','2024-11-05'),
        ('Adam','Lefebvre','adam.lefebvre@email.com','France','2024-12-01'),
        ('Bénédicte','Henry','benedicte.henry@email.com','France','2025-01-14'),
        ('Cyril','Lecomte','cyril.lecomte@email.com','Canada','2025-02-28'),
        ('Diane','Renard','diane.renard@email.com','France','2025-03-15'),
    ]
    cursor.executemany("INSERT OR IGNORE INTO users (first_name,last_name,email,country,created_at) VALUES (?,?,?,?,?)", users)

    # ── SUBSCRIPTIONS ────────────────────────────────────────
    subscriptions = [
        (1,'premium',9.99,'2022-01-15',None),
        (2,'free',0.00,'2022-03-10',None),
        (3,'premium',9.99,'2022-05-22','2024-05-22'),
        (4,'family',14.99,'2022-07-01',None),
        (5,'premium',9.99,'2022-08-14',None),
        (6,'free',0.00,'2022-09-30',None),
        (7,'premium',9.99,'2023-01-05',None),
        (8,'family',14.99,'2023-02-18',None),
        (9,'free',0.00,'2023-04-11',None),
        (10,'premium',9.99,'2023-06-25','2024-06-25'),
        (11,'premium',9.99,'2023-07-09',None),
        (12,'free',0.00,'2023-08-22',None),
        (13,'family',14.99,'2023-09-15',None),
        (14,'premium',9.99,'2023-10-03',None),
        (15,'free',0.00,'2023-11-17',None),
        (16,'premium',9.99,'2024-01-08',None),
        (17,'family',14.99,'2024-02-14',None),
        (18,'free',0.00,'2024-03-20',None),
        (19,'premium',9.99,'2024-04-05',None),
        (20,'free',0.00,'2024-05-19',None),
        (21,'premium',9.99,'2024-06-01',None),
        (22,'family',14.99,'2024-07-13',None),
        (23,'free',0.00,'2024-08-27',None),
        (24,'premium',9.99,'2024-09-10',None),
        (25,'free',0.00,'2024-10-22',None),
        (26,'premium',9.99,'2024-11-05',None),
        (27,'family',14.99,'2024-12-01',None),
        (28,'free',0.00,'2025-01-14',None),
        (29,'premium',9.99,'2025-02-28',None),
        (30,'free',0.00,'2025-03-15',None),
    ]
    cursor.executemany("INSERT OR IGNORE INTO subscriptions (user_id,plan,monthly_price,start_date,end_date) VALUES (?,?,?,?,?)", subscriptions)

    # ── TRACKS ───────────────────────────────────────────────
    tracks = [
        ('Blinding Lights','The Weeknd','Pop',200,2019),
        ('Bohemian Rhapsody','Queen','Rock',354,1975),
        ('Shape of You','Ed Sheeran','Pop',234,2017),
        ('Lose Yourself','Eminem','Hip-Hop',326,2002),
        ('Bad Guy','Billie Eilish','Pop',194,2019),
        ('Levitating','Dua Lipa','Pop',203,2020),
        ('Smells Like Teen Spirit','Nirvana','Rock',301,1991),
        ("God's Plan",'Drake','Hip-Hop',198,2018),
        ('Shallow','Lady Gaga','Pop',216,2018),
        ('Sicko Mode','Travis Scott','Hip-Hop',312,2018),
        ('Someone Like You','Adele','Soul',285,2011),
        ('Uptown Funk','Bruno Mars','Funk',270,2014),
        ('Watermelon Sugar','Harry Styles','Pop',174,2019),
        ('Rockstar','Post Malone','Hip-Hop',218,2017),
        ('Dancing Queen','ABBA','Disco',231,1976),
        ('Montero','Lil Nas X','Pop',137,2021),
        ('Peaches','Justin Bieber','R&B',198,2021),
        ('Heat Waves','Glass Animals','Indie',238,2020),
        ('As It Was','Harry Styles','Pop',167,2022),
        ('Stay','The Kid LAROI','Pop',141,2021),
        ('Industry Baby','Lil Nas X','Hip-Hop',212,2021),
        ('Easy On Me','Adele','Soul',224,2021),
        ('Butter','BTS','K-Pop',164,2021),
        ('Midnight Rain','Taylor Swift','Pop',174,2022),
        ('Anti-Hero','Taylor Swift','Pop',200,2022),
        ('Flowers','Miley Cyrus','Pop',200,2023),
        ('Cruel Summer','Taylor Swift','Pop',178,2019),
        ('Creepin','Metro Boomin','Hip-Hop',221,2022),
        ('Rich Flex','Drake','Hip-Hop',201,2022),
        ('Calm Down','Rema','Afrobeats',239,2022),
        ('Unholy','Sam Smith','Pop',156,2022),
        ('Escapism','RAYE','R&B',195,2022),
        ('Vampire','Olivia Rodrigo','Pop',219,2023),
        ('Ella Baila Sola','Eslabon Armado','Regional Mexican',195,2023),
        ('Shakira','Bzrp','Latin Pop',212,2023),
    ]
    cursor.executemany("INSERT OR IGNORE INTO tracks (title,artist,genre,duration_s,release_year) VALUES (?,?,?,?,?)", tracks)

    # ── PLAYLISTS ────────────────────────────────────────────
    playlists = [
        (1,'Morning Vibes','2022-02-01'),
        (1,'Workout Mix','2022-06-15'),
        (2,'Chill Evening','2022-04-10'),
        (4,'Family Road Trip','2022-08-01'),
        (5,'Swiss Alps Focus','2022-09-01'),
        (7,'Pop Favorites','2023-02-01'),
        (8,'Throwback Classics','2023-03-10'),
        (11,'Hip-Hop Essentials','2023-08-01'),
        (13,'Sunday Brunch','2023-10-01'),
        (16,'Late Night Drive','2024-02-01'),
        (19,'Study Session','2024-05-01'),
        (21,'Feel Good Hits','2024-07-01'),
        (24,'Party Starters','2024-10-01'),
        (26,'New Discoveries','2024-12-01'),
        (29,'Focus Mode','2025-03-01'),
    ]
    cursor.executemany("INSERT OR IGNORE INTO playlists (user_id,name,created_at) VALUES (?,?,?)", playlists)

    # ── PLAYLIST_TRACKS ──────────────────────────────────────
    playlist_tracks = [
        (1,1,'2022-02-05'),(1,3,'2022-02-05'),(1,6,'2022-03-01'),(1,9,'2022-04-10'),
        (2,4,'2022-06-16'),(2,8,'2022-06-16'),(2,10,'2022-07-01'),(2,12,'2022-08-01'),
        (3,2,'2022-04-12'),(3,7,'2022-04-12'),(3,15,'2022-05-01'),
        (4,15,'2022-08-05'),(4,2,'2022-08-05'),(4,11,'2022-09-01'),
        (5,5,'2022-09-05'),(5,18,'2022-10-01'),(5,19,'2023-01-01'),
        (6,1,'2023-02-05'),(6,3,'2023-02-05'),(6,6,'2023-03-01'),(6,13,'2023-04-01'),(6,25,'2023-05-01'),
        (7,2,'2023-03-15'),(7,7,'2023-03-15'),(7,15,'2023-04-01'),(7,11,'2023-05-01'),
        (8,4,'2023-08-05'),(8,8,'2023-08-05'),(8,10,'2023-09-01'),(8,14,'2023-10-01'),(8,21,'2023-11-01'),
        (9,11,'2023-10-05'),(9,22,'2023-10-05'),(9,9,'2023-11-01'),
        (10,16,'2024-02-05'),(10,20,'2024-02-05'),(10,25,'2024-03-01'),(10,31,'2024-04-01'),
        (11,18,'2024-05-05'),(11,19,'2024-05-05'),(11,24,'2024-06-01'),(11,23,'2024-07-01'),
        (12,26,'2024-07-05'),(12,27,'2024-07-05'),(12,33,'2024-08-01'),
        (13,29,'2024-10-05'),(13,28,'2024-10-05'),(13,30,'2024-11-01'),(13,35,'2024-12-01'),
        (14,31,'2024-12-05'),(14,32,'2024-12-05'),(14,33,'2025-01-01'),
        (15,18,'2025-03-05'),(15,19,'2025-03-05'),(15,24,'2025-04-01'),
    ]
    cursor.executemany("INSERT OR IGNORE INTO playlist_tracks (playlist_id,track_id,added_at) VALUES (?,?,?)", playlist_tracks)

    # ── LISTENS ──────────────────────────────────────────────
    listens = [
        # Champions RFM
        (1,1,'2025-05-10 08:00:00',1),(1,3,'2025-05-12 09:00:00',1),(1,6,'2025-05-15 10:00:00',1),
        (1,9,'2025-05-18 11:00:00',1),(1,12,'2025-05-20 12:00:00',1),(1,25,'2025-05-22 08:00:00',1),
        (1,1,'2025-04-05 08:00:00',1),(1,3,'2025-04-10 09:00:00',1),(1,6,'2025-04-15 10:00:00',1),
        (4,4,'2025-05-11 14:00:00',1),(4,8,'2025-05-13 15:00:00',1),(4,10,'2025-05-16 16:00:00',1),
        (4,14,'2025-05-19 17:00:00',1),(4,21,'2025-05-21 18:00:00',1),
        (4,4,'2025-04-08 14:00:00',1),(4,8,'2025-04-12 15:00:00',1),
        (7,1,'2025-05-09 20:00:00',1),(7,3,'2025-05-14 21:00:00',1),(7,6,'2025-05-17 22:00:00',1),
        (7,13,'2025-05-20 20:00:00',1),(7,25,'2025-05-23 21:00:00',1),
        (7,1,'2025-03-05 20:00:00',1),(7,3,'2025-03-15 21:00:00',1),
        # Actifs
        (2,2,'2025-04-20 10:00:00',1),(2,7,'2025-04-25 11:00:00',1),(2,15,'2025-05-01 12:00:00',1),
        (5,5,'2025-04-18 09:00:00',1),(5,18,'2025-05-05 10:00:00',1),(5,19,'2025-05-10 11:00:00',1),
        (8,4,'2025-04-22 14:00:00',1),(8,10,'2025-05-08 15:00:00',1),(8,14,'2025-05-15 16:00:00',1),
        (11,8,'2025-04-15 18:00:00',1),(11,10,'2025-05-03 19:00:00',1),(11,21,'2025-05-12 20:00:00',1),
        (16,16,'2025-04-10 21:00:00',1),(16,20,'2025-04-28 22:00:00',1),(16,25,'2025-05-05 21:00:00',1),
        (19,18,'2025-04-05 08:00:00',1),(19,24,'2025-04-20 09:00:00',1),(19,19,'2025-05-02 10:00:00',1),
        (21,26,'2025-03-25 11:00:00',1),(21,27,'2025-04-10 12:00:00',1),(21,33,'2025-04-22 13:00:00',1),
        # À risque
        (3,1,'2025-01-15 09:00:00',1),(3,3,'2025-01-20 10:00:00',0),
        (6,2,'2024-12-10 10:00:00',1),(6,7,'2024-12-15 11:00:00',0),
        (9,5,'2024-11-20 11:00:00',1),(9,11,'2024-11-25 12:00:00',1),
        (12,3,'2024-10-10 12:00:00',0),(12,6,'2024-10-18 13:00:00',1),
        (15,1,'2024-09-05 13:00:00',1),(15,9,'2024-09-10 14:00:00',0),
        # Inactifs
        (10,4,'2024-03-01 14:00:00',1),(10,8,'2024-03-05 15:00:00',1),
        (18,2,'2024-02-10 15:00:00',1),(18,7,'2024-02-15 16:00:00',0),
        (20,1,'2024-01-05 16:00:00',1),(20,3,'2024-01-10 17:00:00',1),
        (23,5,'2023-12-01 17:00:00',0),(23,11,'2023-12-08 18:00:00',1),
        (25,2,'2023-11-05 18:00:00',1),(25,7,'2023-11-10 19:00:00',1),
        (28,1,'2023-10-01 19:00:00',1),(28,4,'2023-10-05 20:00:00',0),
        (30,3,'2023-09-10 20:00:00',1),(30,6,'2023-09-15 21:00:00',1),
        # Supplémentaires
        (13,11,'2025-05-01 09:00:00',1),(13,22,'2025-05-05 10:00:00',1),(13,9,'2025-05-10 11:00:00',1),
        (14,25,'2025-04-30 12:00:00',1),(14,27,'2025-05-07 13:00:00',1),
        (17,16,'2025-04-25 14:00:00',1),(17,20,'2025-05-02 15:00:00',1),
        (22,30,'2025-04-20 16:00:00',1),(22,35,'2025-05-01 17:00:00',1),
        (24,29,'2025-04-18 18:00:00',1),(24,28,'2025-05-03 19:00:00',1),
        (26,31,'2025-04-15 20:00:00',1),(26,32,'2025-04-28 21:00:00',1),
        (27,18,'2025-04-10 08:00:00',1),(27,19,'2025-04-22 09:00:00',1),
        (29,24,'2025-03-20 10:00:00',1),(29,23,'2025-04-01 11:00:00',1),
    ]
    cursor.executemany("INSERT OR IGNORE INTO listens (user_id,track_id,listened_at,completed) VALUES (?,?,?,?)", listens)

    conn.commit()
    print("✅ Données insérées")

def create_view(conn):
    """Crée la vue v_user_stats"""
    cursor = conn.cursor()
    cursor.execute("DROP VIEW IF EXISTS v_user_stats")
    cursor.execute("""
        CREATE VIEW v_user_stats AS
        SELECT 
            u.user_id,
            u.first_name || ' ' || u.last_name AS full_name,
            u.email,
            u.country,
            s.plan,
            s.monthly_price,
            COUNT(DISTINCT l.listen_id) AS total_listens,
            MAX(l.listened_at) AS last_listen,
            CAST(JULIANDAY('now') - JULIANDAY(MAX(l.listened_at)) AS INTEGER) AS days_since_last_listen,
            ROUND(SUM(CASE WHEN l.completed = 1 THEN t.duration_s ELSE 0 END) / 60.0, 1) AS total_minutes_listened
        FROM users u
        LEFT JOIN subscriptions s ON u.user_id = s.user_id AND s.end_date IS NULL
        LEFT JOIN listens l ON u.user_id = l.user_id
        LEFT JOIN tracks t ON l.track_id = t.track_id
        GROUP BY u.user_id, full_name, u.email, u.country, s.plan, s.monthly_price
    """)
    conn.commit()
    print("✅ Vue v_user_stats créée")

if __name__ == "__main__":
    # Supprime l'ancienne base si elle existe
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("🗑️  Ancienne base supprimée")

    conn = create_database()
    insert_data(conn)
    create_view(conn)
    conn.close()

    print(f"\n🎉 Base '{DB_PATH}' prête ! Tu peux maintenant lancer main.py")