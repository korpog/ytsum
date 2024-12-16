DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS summary;
DROP TABLE IF EXISTS category;
DROP TABLE IF EXISTS user_favorite_summary;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);

CREATE TABLE category (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  category_name TEXT UNIQUE NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE summary (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id INTEGER NOT NULL,
  category_id INTEGER NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  yt_url TEXT UNIQUE NOT NULL,
  yt_title TEXT UNIQUE NOT NULL,
  yt_channel_name TEXT,
  transcript TEXT NOT NULL,
  summary_text TEXT NOT NULL,
  FOREIGN KEY (author_id) REFERENCES user (id),
  FOREIGN KEY (category_id) REFERENCES category (id)
);

CREATE TABLE user_favorite_summary (
  user_id INTEGER NOT NULL,
  summary_id INTEGER NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id, summary_id),
  FOREIGN KEY (user_id) REFERENCES user (id),
  FOREIGN KEY (summary_id) REFERENCES summary (id)
);

-- Seed categories
INSERT OR IGNORE INTO category (category_name, created_at)
VALUES 
    ('Entertainment', '2024-11-11 00:00:00'),
    ('Science', '2024-11-11 00:00:00'),
    ('Other', '2024-11-11 00:00:00');