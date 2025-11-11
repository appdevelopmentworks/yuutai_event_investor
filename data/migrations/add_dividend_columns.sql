-- マイグレーション: 配当銘柄サポート追加
-- Version: 1.1.0
-- Date: 2025-01-11
-- Description: 株主優待銘柄と配当銘柄の両方に対応

-- ========================================
-- 1. stocks テーブルに配当関連カラムを追加
-- ========================================

-- 配当利回り（%）
ALTER TABLE stocks ADD COLUMN dividend_yield REAL;

-- 1株あたり配当金（円）
ALTER TABLE stocks ADD COLUMN dividend_amount REAL;

-- 市場区分（プライム/スタンダード/グロース）
ALTER TABLE stocks ADD COLUMN market TEXT;

-- 業種（セクター）
ALTER TABLE stocks ADD COLUMN sector TEXT;

-- 銘柄タイプ（yuutai=優待のみ、dividend=配当のみ、both=両方）
ALTER TABLE stocks ADD COLUMN stock_type TEXT DEFAULT 'yuutai';

-- 優待あり/なしフラグ
ALTER TABLE stocks ADD COLUMN has_yuutai BOOLEAN DEFAULT 1;

-- 配当あり/なしフラグ
ALTER TABLE stocks ADD COLUMN has_dividend BOOLEAN DEFAULT 0;

-- ========================================
-- 2. インデックスの追加
-- ========================================

-- 配当利回りでのソート用
CREATE INDEX IF NOT EXISTS idx_stocks_dividend_yield ON stocks(dividend_yield DESC);

-- 銘柄タイプでのフィルタ用
CREATE INDEX IF NOT EXISTS idx_stocks_type ON stocks(stock_type);

-- 市場区分でのフィルタ用
CREATE INDEX IF NOT EXISTS idx_stocks_market ON stocks(market);

-- 業種でのフィルタ用
CREATE INDEX IF NOT EXISTS idx_stocks_sector ON stocks(sector);

-- ========================================
-- 3. ビューの更新
-- ========================================

-- 高配当銘柄ビュー（配当利回り3%以上）
CREATE VIEW IF NOT EXISTS v_high_dividend_stocks AS
SELECT
    s.code,
    s.name,
    s.dividend_yield,
    s.dividend_amount,
    s.rights_month,
    s.market,
    s.sector,
    s.stock_type,
    sc.win_rate,
    sc.expected_return,
    sc.buy_days_before AS optimal_days
FROM stocks s
LEFT JOIN (
    SELECT
        code,
        rights_month,
        MAX(expected_return * win_rate) AS score,
        buy_days_before,
        win_rate,
        expected_return
    FROM simulation_cache
    GROUP BY code, rights_month
) sc ON s.code = sc.code AND s.rights_month = sc.rights_month
WHERE s.dividend_yield >= 3.0
  AND s.has_dividend = 1
ORDER BY s.dividend_yield DESC;

-- 優待+配当銘柄ビュー
CREATE VIEW IF NOT EXISTS v_yuutai_dividend_stocks AS
SELECT
    s.code,
    s.name,
    s.dividend_yield,
    s.dividend_amount,
    s.rights_month,
    s.yuutai_genre,
    s.yuutai_content,
    s.market,
    s.sector,
    sc.win_rate,
    sc.expected_return,
    sc.buy_days_before AS optimal_days
FROM stocks s
LEFT JOIN (
    SELECT
        code,
        rights_month,
        MAX(expected_return * win_rate) AS score,
        buy_days_before,
        win_rate,
        expected_return
    FROM simulation_cache
    GROUP BY code, rights_month
) sc ON s.code = sc.code AND s.rights_month = sc.rights_month
WHERE s.stock_type = 'both'
ORDER BY sc.expected_return DESC;

-- ========================================
-- 4. スキーマバージョンの更新
-- ========================================

INSERT INTO schema_version (version, description) VALUES
(2, 'Add dividend stock support - v1.1.0');

-- ========================================
-- 5. 既存データの更新（オプション）
-- ========================================

-- 既存の優待銘柄は has_yuutai=1, has_dividend=0, stock_type='yuutai' のまま
-- 新規インポートされる配当銘柄は has_yuutai=0, has_dividend=1, stock_type='dividend' となる
