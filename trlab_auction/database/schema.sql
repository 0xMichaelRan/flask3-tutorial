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

ALTER TABLE user
ADD COLUMN notification_bid_activity BOOLEAN DEFAULT FALSE,
ADD COLUMN notification_item_sold BOOLEAN DEFAULT FALSE,
ADD COLUMN notification_added_to_collection BOOLEAN DEFAULT FALSE,
ADD COLUMN notification_review BOOLEAN DEFAULT FALSE;

CREATE TABLE profile_update_history (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME(6) NOT NULL,
    user_id INT NOT NULL,
    field_name VARCHAR(255) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    INDEX idx_timestamp (timestamp),
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB;

CREATE TABLE artwork (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2),
    royalties DECIMAL(4, 1),
    size VARCHAR(50),
    genre VARCHAR(50),
    file_url VARCHAR(255) NOT NULL,
    file_type ENUM('image', 'video', 'audio') NOT NULL,
    on_sale BOOLEAN DEFAULT FALSE,
    unlock_on_purchase BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
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