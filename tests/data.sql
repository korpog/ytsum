INSERT INTO user
    (username, password)
VALUES
    ('test', 'pbkdf2:sha256:50000$TCI4GzcX$0de171a4f4dac32e3364c7ddc7c14f3e2fa61f2d17574483f7ffbb431b4acb2f'),
    ('other', 'pbkdf2:sha256:50000$kJPKsz6N$d2d4784f1b030a9761f5ccaeeaca413f27f2ecb76d6168407af962ddce849f79');


INSERT INTO summary
    (yt_url, yt_title, yt_channel_name, transcript, summary_text, author_id, category_id, created_at)
VALUES
    ('https://www.youtube.com/watch?v=dQw4w9WgXcQ', 'fake title', 'RLM', 'fake transcript', 'fake summary', 1, 1, '2024-11-11 00:00:00'),
    ('https://www.youtube.com/watch?v=cNsTMNxOzqQ', 'fake title2', 'PT', 'fake transcript2', 'fake summary2', 2, 2, '2024-11-12 00:00:00');

INSERT INTO user_favorite_summary
    (user_id, summary_id, created_at)
VALUES
    (1, 1, '2024-12-12 00:00:00'),
    (1, 2, '2024-12-12 01:00:00'),
    (2, 1, '2024-12-11 01:00:00');

    