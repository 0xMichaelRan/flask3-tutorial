-- This is deprecated since we are using MySQL now

DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS artwork;
DROP TABLE IF EXISTS bid;

CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    bio TEXT,
    instagram_id TEXT,
    youtube_id TEXT,
    profile_photo_url TEXT,
    cover_photo_url TEXT,
    password TEXT NOT NULL
);

CREATE TABLE artwork (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  artist_id INTEGER NOT NULL,
  created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  artwork_title TEXT NOT NULL,
  artwork_body TEXT NOT NULL,
  FOREIGN KEY (artist_id) REFERENCES user (id)
);

CREATE TABLE bid (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  bidder_id INTEGER NOT NULL,
  artwork_id INTEGER NOT NULL,
  bid_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  bid_amount INTEGER NOT NULL,
  FOREIGN KEY (bidder_id) REFERENCES user (id),
  FOREIGN KEY (artwork_id) REFERENCES artwork (id)
);
