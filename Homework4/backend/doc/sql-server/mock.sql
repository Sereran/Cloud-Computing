-- Insert Tags
INSERT INTO [dbo].tag (name) VALUES ('RPG'), ('Action'), ('Indie'), ('Strategy');

-- Insert Users
INSERT INTO [dbo].[user] (email, password, created_at, updated_at)
VALUES 
('admin@example.com', 'ef92b778ba227749f39a8501', GETDATE(), GETDATE()),
('player1@example.com', '88d405027583693e5454652', GETDATE(), GETDATE());

-- Insert Games (IDs will be 1, 2, and 3 via IDENTITY)
INSERT INTO [dbo].game (title, description)
VALUES 
('Night City Adventure', 'A futuristic open-world RPG set in a sprawling metropolis.'),
('Elden Throne', 'An epic fantasy journey through a vast, broken kingdom.'),
('Hades Gate', 'A fast-paced rogue-like dungeon crawler based on Greek mythology.');

-- Insert Media (Using valid Unsplash image URLs)
INSERT INTO [dbo].media (id, url, game_id)
VALUES 
(1, 'https://images.unsplash.com/photo-1605898835373-02f74446e721?auto=format&fit=crop&w=1024', 1),
(2, 'https://images.unsplash.com/photo-1614680376593-902f74cf0d41?auto=format&fit=crop&w=1024', 2),
(3, 'https://images.unsplash.com/photo-1542751371-adc38448a05e?auto=format&fit=crop&w=1024', 3);

-- Insert Applied Tags
INSERT INTO [dbo].applied_tag (game_id, tag_name)
VALUES 
(1, 'RPG'), (1, 'Action'),
(2, 'RPG'), (2, 'Strategy'),
(3, 'Indie'), (3, 'Action');

-- Insert Library (Link users to games)
INSERT INTO [dbo].library (game_id, user_email)
VALUES 
(1, 'admin@example.com'),
(2, 'admin@example.com'),
(3, 'player1@example.com');