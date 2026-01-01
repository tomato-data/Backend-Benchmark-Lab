-- ============================================
-- Backend Benchmark Lab - Database Schema
-- ============================================
-- 실행: cat scripts/init_db.sql | docker compose exec -T postgres psql -U benchmark -d benchmark
-- 멱등성: IF NOT EXISTS / ON CONFLICT DO NOTHING

-- ============================================
-- 1. Users 테이블 (기본 + pagination)
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 100,000건 시드 (ON CONFLICT로 멱등성 보장)
INSERT INTO users (name, email, created_at)
SELECT
    'User' || g,
    'user' || g || '@benchmark.test',
    NOW() - (random() * interval '30 days')
FROM generate_series(1, 100000) AS g
ON CONFLICT (email) DO NOTHING;

-- ============================================
-- 2. Column Overhead 테스트 테이블들 (10-db-column-overhead)
-- ============================================
-- 향후 추가 예정:
-- - users_narrow (5개 컬럼)
-- - users_wide (20개 컬럼)
-- - users_extra_wide (50개 컬럼)
-- - users_type_int, users_type_varchar, users_type_text,
--   users_type_jsonb, users_type_timestamp, users_type_uuid
