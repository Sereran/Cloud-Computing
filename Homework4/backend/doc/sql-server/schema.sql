DROP TABLE IF EXISTS [dbo].applied_tag;
DROP TABLE IF EXISTS [dbo].library;
DROP TABLE IF EXISTS [dbo].media;
DROP TABLE IF EXISTS [dbo].tag;
DROP TABLE IF EXISTS [dbo].game;
DROP TABLE IF EXISTS [dbo].[user];

CREATE TABLE [dbo].game (
    id INT PRIMARY KEY IDENTITY(1,1),
    title VARCHAR(63),
    description VARCHAR(255)
);

CREATE TABLE [dbo].tag (
    name VARCHAR(15) PRIMARY KEY
);

CREATE TABLE [dbo].[user] (
    email VARCHAR(63) PRIMARY KEY,
    password VARCHAR(63), -- must be stored as a hash
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE TABLE [dbo].media (
    id INT PRIMARY KEY,
    url VARCHAR(1023),
    game_id INT NOT NULL,
    FOREIGN KEY (game_id) REFERENCES [dbo].game(id)
);

CREATE TABLE [dbo].applied_tag (
    game_id INT NOT NULL,
    tag_name VARCHAR(15) NOT NULL,
    FOREIGN KEY (game_id) REFERENCES [dbo].game(id),
    FOREIGN KEY (tag_name) REFERENCES [dbo].tag(name)
);

CREATE TABLE [dbo].library (
    game_id INT NOT NULL,
    user_email VARCHAR(63) NOT NULL,
    FOREIGN KEY (game_id) REFERENCES [dbo].game(id),
    FOREIGN KEY (user_email) REFERENCES [dbo].[user](email)
);