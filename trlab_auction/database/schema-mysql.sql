DROP TABLE IF EXISTS bid;
DROP TABLE IF EXISTS artwork;
DROP TABLE IF EXISTS user;

CREATE TABLE user (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    bio TEXT,
    instagram_id VARCHAR(30),
    youtube_id VARCHAR(30),
    profile_photo_url VARCHAR(255),
    cover_photo_url VARCHAR(255),
    password VARCHAR(255) NOT NULL
);

CREATE TABLE artwork (
    id INT AUTO_INCREMENT PRIMARY KEY,
    artist_id INT NOT NULL,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    artwork_title VARCHAR(255) NOT NULL,
    artwork_body TEXT NOT NULL,
    FOREIGN KEY (artist_id) REFERENCES user(id)
);

CREATE TABLE bid (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bidder_id INT NOT NULL,
    artwork_id INT NOT NULL,
    bid_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    bid_amount DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (bidder_id) REFERENCES user(id),
    FOREIGN KEY (artwork_id) REFERENCES artwork(id)
);

ALTER TABLE user
ADD COLUMN notification_bid_activity BOOLEAN DEFAULT FALSE,
ADD COLUMN notification_item_sold BOOLEAN DEFAULT FALSE,
ADD COLUMN notification_added_to_collection BOOLEAN DEFAULT FALSE,
ADD COLUMN notification_review BOOLEAN DEFAULT FALSE;