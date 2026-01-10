-- ============================================
-- Backend Benchmark Lab - Database Schema
-- ============================================
-- 실행: cat scripts/init_db.sql | docker compose exec -T postgres psql -U benchmark -d benchmark
-- 멱등성: IF NOT EXISTS / ON CONFLICT DO NOTHING

-- ============================================
-- 1. Users 테이블 (01~08 기본 시나리오용, 1,000명)
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 1,000건 시드 (01~08 시나리오용)
INSERT INTO users (name, email, created_at)
SELECT
    'User' || g,
    'user' || g || '@benchmark.com',
    NOW() - (random() * interval '30 days')
FROM generate_series(1, 1000) AS g
ON CONFLICT (email) DO NOTHING;

-- ============================================
-- 2. Users Pagination 테이블 (09 페이지네이션 시나리오용, 100,000명)
-- ============================================
CREATE TABLE IF NOT EXISTS users_pagination (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 100,000건 시드 (09 페이지네이션 시나리오용)
INSERT INTO users_pagination (name, email, created_at)
SELECT
    'User' || g,
    'pagination' || g || '@benchmark.com',
    NOW() - (random() * interval '30 days')
FROM generate_series(1, 100000) AS g
ON CONFLICT (email) DO NOTHING;

-- ============================================
-- 10-db-column-overhead: 컬럼 수 및 타입별 오버헤드 테스트
-- ============================================

-- ============================================
-- A. 컬럼 수 비교 테이블
-- ============================================

-- 1. Narrow (5개 컬럼)
CREATE TABLE IF NOT EXISTS users_narrow (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW()
);

-- 2. Wide (20개 컬럼)
CREATE TABLE IF NOT EXISTS users_wide (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    -- 추가 15개 컬럼
    phone VARCHAR(20),
    address VARCHAR(500),
    city VARCHAR(100),
    country VARCHAR(100),
    postal_code VARCHAR(20),
    birth_date DATE,
    gender VARCHAR(10),
    occupation VARCHAR(100),
    company VARCHAR(200),
    website VARCHAR(255),
    bio TEXT,
    avatar_url VARCHAR(500),
    last_login TIMESTAMP,
    login_count INTEGER DEFAULT 0,
    preferences JSONB DEFAULT '{}'::jsonb
);

-- 3. Extra Wide (50개 컬럼)
CREATE TABLE IF NOT EXISTS users_extra_wide (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    -- field_01 ~ field_45 (VARCHAR 45개)
    field_01 VARCHAR(100), field_02 VARCHAR(100), field_03 VARCHAR(100),
    field_04 VARCHAR(100), field_05 VARCHAR(100), field_06 VARCHAR(100),
    field_07 VARCHAR(100), field_08 VARCHAR(100), field_09 VARCHAR(100),
    field_10 VARCHAR(100), field_11 VARCHAR(100), field_12 VARCHAR(100),
    field_13 VARCHAR(100), field_14 VARCHAR(100), field_15 VARCHAR(100),
    field_16 VARCHAR(100), field_17 VARCHAR(100), field_18 VARCHAR(100),
    field_19 VARCHAR(100), field_20 VARCHAR(100), field_21 VARCHAR(100),
    field_22 VARCHAR(100), field_23 VARCHAR(100), field_24 VARCHAR(100),
    field_25 VARCHAR(100), field_26 VARCHAR(100), field_27 VARCHAR(100),
    field_28 VARCHAR(100), field_29 VARCHAR(100), field_30 VARCHAR(100),
    field_31 VARCHAR(100), field_32 VARCHAR(100), field_33 VARCHAR(100),
    field_34 VARCHAR(100), field_35 VARCHAR(100), field_36 VARCHAR(100),
    field_37 VARCHAR(100), field_38 VARCHAR(100), field_39 VARCHAR(100),
    field_40 VARCHAR(100), field_41 VARCHAR(100), field_42 VARCHAR(100),
    field_43 VARCHAR(100), field_44 VARCHAR(100), field_45 VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- B. 데이터 타입별 비교 테이블 (각 5개 컬럼)
-- ============================================

-- 1. INTEGER 위주
CREATE TABLE IF NOT EXISTS users_type_int (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    int_col_01 INTEGER DEFAULT 0,
    int_col_02 INTEGER DEFAULT 0,
    int_col_03 INTEGER DEFAULT 0,
    int_col_04 INTEGER DEFAULT 0,
    int_col_05 INTEGER DEFAULT 0
);

-- 2. VARCHAR 위주
CREATE TABLE IF NOT EXISTS users_type_varchar (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    varchar_col_01 VARCHAR(100),
    varchar_col_02 VARCHAR(100),
    varchar_col_03 VARCHAR(100),
    varchar_col_04 VARCHAR(100),
    varchar_col_05 VARCHAR(100)
);

-- 3. TEXT 위주
CREATE TABLE IF NOT EXISTS users_type_text (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    text_col_01 TEXT,
    text_col_02 TEXT,
    text_col_03 TEXT,
    text_col_04 TEXT,
    text_col_05 TEXT
);

-- 4. JSONB 위주
CREATE TABLE IF NOT EXISTS users_type_jsonb (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    json_col_01 JSONB DEFAULT '{}'::jsonb,
    json_col_02 JSONB DEFAULT '{}'::jsonb,
    json_col_03 JSONB DEFAULT '{}'::jsonb,
    json_col_04 JSONB DEFAULT '{}'::jsonb,
    json_col_05 JSONB DEFAULT '{}'::jsonb
);

-- 5. TIMESTAMP 위주
CREATE TABLE IF NOT EXISTS users_type_timestamp (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    ts_col_01 TIMESTAMP,
    ts_col_02 TIMESTAMP,
    ts_col_03 TIMESTAMP,
    ts_col_04 TIMESTAMP,
    ts_col_05 TIMESTAMP
);

-- 6. UUID 위주
CREATE TABLE IF NOT EXISTS users_type_uuid (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    uuid_col_01 UUID,
    uuid_col_02 UUID,
    uuid_col_03 UUID,
    uuid_col_04 UUID,
    uuid_col_05 UUID
);

-- ============================================
-- 시드 데이터 INSERT (각 100,000건)
-- ============================================

-- A. 컬럼 수 비교 테이블
-- ============================================

-- 1. Narrow (5개 컬럼)
INSERT INTO users_narrow (name, email, status, created_at)
SELECT
    'User' || g,
    'narrow' || g || '@benchmark.com',
    CASE WHEN random() > 0.5 THEN 'active' ELSE 'inactive' END,
    NOW() - (random() * interval '30 days')
FROM generate_series(1, 100000) AS g
ON CONFLICT (email) DO NOTHING;

-- 2. Wide (20개 컬럼)
INSERT INTO users_wide (
    name, email, status, created_at,
    phone, address, city, country, postal_code,
    birth_date, gender, occupation, company, website,
    bio, avatar_url, last_login, login_count, preferences
)
SELECT
    'User' || g,
    'wide' || g || '@benchmark.com',
    CASE WHEN random() > 0.5 THEN 'active' ELSE 'inactive' END,
    NOW() - (random() * interval '30 days'),
    '010-' || (1000 + (random() * 8999)::int) || '-' || (1000 + (random() * 8999)::int),
    'Address ' || g,
    'City ' || (g % 100),
    'Country' || (g % 50),
    (10000 + (random() * 899999)::int)::text,
    DATE '1970-01-01' + (random() * 15000)::int,
    CASE WHEN random() > 0.5 THEN 'male' ELSE 'female' END,
    'Occupation ' || (g % 30),
    'Company ' || (g % 200),
    'https://example.com/user/' || g,
    'Bio text for user ' || g || '. Lorem ipsum dolor sit amet.',
    'https://avatar.example.com/' || g || '.jpg',
    NOW() - (random() * interval '7 days'),
    (random() * 1000)::int,
    ('{"theme": "' || CASE WHEN random() > 0.5 THEN 'dark' ELSE 'light' END || '", "lang": "ko"}')::jsonb
FROM generate_series(1, 100000) AS g
ON CONFLICT (email) DO NOTHING;

-- 3. Extra Wide (50개 컬럼)
INSERT INTO users_extra_wide (
    name, email,
    field_01, field_02, field_03, field_04, field_05,
    field_06, field_07, field_08, field_09, field_10,
    field_11, field_12, field_13, field_14, field_15,
    field_16, field_17, field_18, field_19, field_20,
    field_21, field_22, field_23, field_24, field_25,
    field_26, field_27, field_28, field_29, field_30,
    field_31, field_32, field_33, field_34, field_35,
    field_36, field_37, field_38, field_39, field_40,
    field_41, field_42, field_43, field_44, field_45,
    created_at
)
SELECT
    'User' || g,
    'extrawide' || g || '@benchmark.com',
    'val_01_' || g, 'val_02_' || g, 'val_03_' || g, 'val_04_' || g, 'val_05_' || g,
    'val_06_' || g, 'val_07_' || g, 'val_08_' || g, 'val_09_' || g, 'val_10_' || g,
    'val_11_' || g, 'val_12_' || g, 'val_13_' || g, 'val_14_' || g, 'val_15_' || g,
    'val_16_' || g, 'val_17_' || g, 'val_18_' || g, 'val_19_' || g, 'val_20_' || g,
    'val_21_' || g, 'val_22_' || g, 'val_23_' || g, 'val_24_' || g, 'val_25_' || g,
    'val_26_' || g, 'val_27_' || g, 'val_28_' || g, 'val_29_' || g, 'val_30_' || g,
    'val_31_' || g, 'val_32_' || g, 'val_33_' || g, 'val_34_' || g, 'val_35_' || g,
    'val_36_' || g, 'val_37_' || g, 'val_38_' || g, 'val_39_' || g, 'val_40_' || g,
    'val_41_' || g, 'val_42_' || g, 'val_43_' || g, 'val_44_' || g, 'val_45_' || g,
    NOW() - (random() * interval '30 days')
FROM generate_series(1, 100000) AS g
ON CONFLICT (email) DO NOTHING;

-- ============================================
-- B. 데이터 타입별 비교 테이블
-- ============================================

-- 1. INTEGER 위주
INSERT INTO users_type_int (name, email, int_col_01, int_col_02, int_col_03, int_col_04, int_col_05)
SELECT
    'User' || g,
    'int' || g || '@benchmark.com',
    (random() * 1000000)::int,
    (random() * 1000000)::int,
    (random() * 1000000)::int,
    (random() * 1000000)::int,
    (random() * 1000000)::int
FROM generate_series(1, 100000) AS g
ON CONFLICT (email) DO NOTHING;

-- 2. VARCHAR 위주
INSERT INTO users_type_varchar (name, email, varchar_col_01, varchar_col_02, varchar_col_03, varchar_col_04, varchar_col_05)
SELECT
    'User' || g,
    'varchar' || g || '@benchmark.com',
    'varchar_value_01_' || g,
    'varchar_value_02_' || g,
    'varchar_value_03_' || g,
    'varchar_value_04_' || g,
    'varchar_value_05_' || g
FROM generate_series(1, 100000) AS g
ON CONFLICT (email) DO NOTHING;

-- 3. TEXT 위주 (긴 텍스트)
INSERT INTO users_type_text (name, email, text_col_01, text_col_02, text_col_03, text_col_04, text_col_05)
SELECT
    'User' || g,
    'text' || g || '@benchmark.com',
    'Lorem ipsum dolor sit amet, consectetur adipiscing elit. User ' || g || ' text column 01.',
    'Lorem ipsum dolor sit amet, consectetur adipiscing elit. User ' || g || ' text column 02.',
    'Lorem ipsum dolor sit amet, consectetur adipiscing elit. User ' || g || ' text column 03.',
    'Lorem ipsum dolor sit amet, consectetur adipiscing elit. User ' || g || ' text column 04.',
    'Lorem ipsum dolor sit amet, consectetur adipiscing elit. User ' || g || ' text column 05.'
FROM generate_series(1, 100000) AS g
ON CONFLICT (email) DO NOTHING;

-- 4. JSONB 위주
INSERT INTO users_type_jsonb (name, email, json_col_01, json_col_02, json_col_03, json_col_04, json_col_05)
SELECT
    'User' || g,
    'jsonb' || g || '@benchmark.com',
    ('{"id": ' || g || ', "type": "col01", "data": {"nested": "value"}}')::jsonb,
    ('{"id": ' || g || ', "type": "col02", "data": {"nested": "value"}}')::jsonb,
    ('{"id": ' || g || ', "type": "col03", "data": {"nested": "value"}}')::jsonb,
    ('{"id": ' || g || ', "type": "col04", "data": {"nested": "value"}}')::jsonb,
    ('{"id": ' || g || ', "type": "col05", "data": {"nested": "value"}}')::jsonb
FROM generate_series(1, 100000) AS g
ON CONFLICT (email) DO NOTHING;

-- 5. TIMESTAMP 위주
INSERT INTO users_type_timestamp (name, email, ts_col_01, ts_col_02, ts_col_03, ts_col_04, ts_col_05)
SELECT
    'User' || g,
    'timestamp' || g || '@benchmark.com',
    NOW() - (random() * interval '365 days'),
    NOW() - (random() * interval '365 days'),
    NOW() - (random() * interval '365 days'),
    NOW() - (random() * interval '365 days'),
    NOW() - (random() * interval '365 days')
FROM generate_series(1, 100000) AS g
ON CONFLICT (email) DO NOTHING;

-- 6. UUID 위주
INSERT INTO users_type_uuid (name, email, uuid_col_01, uuid_col_02, uuid_col_03, uuid_col_04, uuid_col_05)
SELECT
    'User' || g,
    'uuid' || g || '@benchmark.com',
    gen_random_uuid(),
    gen_random_uuid(),
    gen_random_uuid(),
    gen_random_uuid(),
    gen_random_uuid()
FROM generate_series(1, 100000) AS g
ON CONFLICT (email) DO NOTHING;


-- ============================================
-- 11-db-n-plus-one: N+1 문제 테스트
-- ============================================

-- 1. Authors 테이블 (1,000명)
CREATE TABLE IF NOT EXISTS authors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    bio TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 2. Posts 테이블 (각 author당 5~15개 → 약 10,000 건)
CREATE TABLE IF NOT EXISTS posts (
    id SERIAL PRIMARY KEY,
    author_id INTEGER NOT NULL REFERENCES authors(id),
    title VARCHAR(200) NOT NULL,
    content TEXT,
    view_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 3. FK 인덱스 (N+1 eager loading 시 필수)
CREATE INDEX IF NOT EXISTS idx_posts_author_id ON posts(author_id);

-- ============================================
-- 시드 데이터: authors (1,000명)
-- ============================================
INSERT INTO authors (name, email, bio, created_at)
SELECT
    'Author' || g,
    'author' || g || '@benchmark.com',
    'Bio for author ' || g || '. Writer and content creator.',
    NOW() - (random() * interval '365 days')
FROM generate_series(1, 1000) AS g
ON CONFLICT (email) DO NOTHING;


-- ============================================
-- 시드 데이터: posts (각 author당 5~15개, 약 10,000건)
-- ============================================
INSERT INTO posts (author_id, title, content, view_count, created_at)
SELECT
    a.id,
    'Post ' || p || ' by Author ' || a.id,
    'Content of post ' || p || '. Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
    (random() * 10000)::int,
    a.created_at + (p || ' days')::interval
FROM authors a
CROSS JOIN LATERAL generate_series(1, 5 + (random() * 10)::int) AS p
ON CONFLICT DO NOTHING;


-- ============================================
-- 12-db-bulk-operations: 대량 INSERT/UPDATE 테스트
-- ============================================

-- bulk_items 테이블 (테스트 전 TRUNCATE 후 사용)
CREATE TABLE IF NOT EXISTS bulk_items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    value INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 초기 데이터 없음 (각 벤치마크에서 동적 생성)

-- ============================================
-- 13-db-transactions: 트랜잭션 락 경합 테스트
-- ============================================

-- products 테이블 (재고 관리용)
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    stock INTEGER NOT NULL DEFAULT 0,
    version INTEGER NOT NULL DEFAULT 0, -- Optimistic Lock 용
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 테스트용 상품 시드 (10개 상품, 각 재고 1000개)
INSERT INTO products (name, stock, version, updated_at)
SELECT
    'Product ' || g,
    1000,
    0,
    NOW()
FROM generate_series(1, 10) AS g
ON CONFLICT DO NOTHING;