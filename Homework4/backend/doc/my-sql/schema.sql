DROP TABLE applied_tag;
DROP TABLE library;
DROP TABLE media;
DROP TABLE tag;
DROP TABLE game;
DROP TABLE user;

CREATE TABLE `cloud_homework`.`game` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `title` varchar(63),
  `description` varchar(255)
);

CREATE TABLE `cloud_homework`.`tag` (
  `name` varchar(15) PRIMARY KEY
);

CREATE TABLE `cloud_homework`.`user` (
  `email` varchar(63) PRIMARY KEY,
  `password` varchar(63) COMMENT 'must be stored as a hash',
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL
);

CREATE TABLE `cloud_homework`.`media` (
  `id` int PRIMARY KEY,
  `url` varchar(1023),
  `game_id` int NOT NULL
);

CREATE TABLE `cloud_homework`.`applied_tag` (
  `game_id` int NOT NULL,
  `tag_name` varchar(15) NOT NULL
);

CREATE TABLE `cloud_homework`.`library` (
  `game_id` int NOT NULL,
  `user_email` varchar(63) NOT NULL
);

ALTER TABLE `media` ADD FOREIGN KEY (`game_id`) REFERENCES `game` (`id`);

ALTER TABLE `applied_tag` ADD FOREIGN KEY (`game_id`) REFERENCES `game` (`id`);

ALTER TABLE `applied_tag` ADD FOREIGN KEY (`tag_name`) REFERENCES `tag` (`name`);

ALTER TABLE `library` ADD FOREIGN KEY (`game_id`) REFERENCES `game` (`id`);

ALTER TABLE `library` ADD FOREIGN KEY (`user_email`) REFERENCES `user` (`email`);
