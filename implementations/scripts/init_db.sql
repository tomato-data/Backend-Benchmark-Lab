-- implementations/scripts/init_data.sql
DELETE FROM users;

INSERT INTO users (name, email)
SELECT
    'User' || g,
    'user' || g || '@benchmark.test'
FROM generate_series(1, 1000) AS g;