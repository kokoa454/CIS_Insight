import sqlite3
import os
import logging

import config.config as cfg

def init_db():
    logging.info("Initializing database...")
    
    if not os.path.exists(cfg.DB_PATH):
        os.makedirs(cfg.DB_DIR)

    try:
        conn = sqlite3.connect(cfg.DB_PATH)
        cursor = conn.cursor()

        # User table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS User (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name VARCHAR(16) NOT NULL UNIQUE,
            user_display_name VARCHAR(16) NOT NULL,
            user_password VARCHAR(255) NOT NULL,
            user_icon VARCHAR(128),
            user_news_count INTEGER DEFAULT 0,
            user_preferred_country JSON,
            user_preferred_topic JSON,
            user_admin BOOLEAN NOT NULL DEFAULT 0
        )
        """)

        # News_RSS table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS News_RSS (
            rss_id INTEGER PRIMARY KEY AUTOINCREMENT,
            rss_company TEXT NOT NULL,
            rss_link TEXT NOT NULL UNIQUE,
            rss_create_date DATETIME NOT NULL,
            rss_update_date DATETIME,
            rss_country VARCHAR(16) NOT NULL,
            rss_read_count INTEGER DEFAULT 0
        )
        ''')

        # News table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS News (
            news_id INTEGER PRIMARY KEY AUTOINCREMENT,
            rss_id INTEGER,
            news_title TEXT NOT NULL,
            news_date DATETIME NOT NULL,
            news_content_ru TEXT,
            news_content_ja TEXT,
            news_link TEXT NOT NULL UNIQUE,
            news_country VARCHAR(16) NOT NULL,
            news_topic JSON NOT NULL,
            news_image_url TEXT,
            news_read_count INTEGER DEFAULT 0,
            FOREIGN KEY (rss_id) REFERENCES News_RSS(rss_id)
        )
        ''')

        # Index
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_date ON News(news_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_country ON News(news_country)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_topic ON News(news_topic)')

        conn.commit()
        conn.close()

        logging.info("Database initialized successfully")
    except Exception as e:
        logging.error(f"Failed to initialize database: {e}")
        raise
