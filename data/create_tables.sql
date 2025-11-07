-- データベース初期化スクリプト
-- Yuutai Event Investor Database Schema
-- Version: 1.0.0
-- Date: 2024-11-06

-- 既存テーブルの削除（開発用）
DROP TABLE IF EXISTS notifications;
DROP TABLE IF EXISTS watchlist;
DROP TABLE IF EXISTS simulation_cache;
DROP TABLE IF EXISTS price_history;
DROP TABLE IF EXISTS stocks;
DROP TABLE IF EXISTS schema_version;

-- ========================================
-- 1. 銘柄マスタテーブル
-- ========================================
CREATE TABLE stocks (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    rights_month INTEGER,
    rights_date DATE,
    yuutai_genre TEXT,
    yuutai_content TEXT,
    yuutai_detail TEXT,
    min_shares INTEGER,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    data_source TEXT
);

CREATE INDEX idx_stocks_rights_month ON stocks(rights_month);
CREATE INDEX idx_stocks_genre ON stocks(yuutai_genre);

-- ========================================
-- 2. 株価履歴テーブル
-- ========================================
CREATE TABLE price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL,
    date DATE NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL NOT NULL,
    volume INTEGER,
    FOREIGN KEY (code) REFERENCES stocks(code) ON DELETE CASCADE,
    UNIQUE(code, date)
);

CREATE INDEX idx_price_code_date ON price_history(code, date);
CREATE INDEX idx_price_date ON price_history(date);

-- ========================================
-- 3. シミュレーション結果キャッシュテーブル
-- ========================================
CREATE TABLE simulation_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL,
    rights_month INTEGER NOT NULL,
    buy_days_before INTEGER NOT NULL,
    win_count INTEGER DEFAULT 0,
    lose_count INTEGER DEFAULT 0,
    win_rate REAL DEFAULT 0.0,
    expected_return REAL DEFAULT 0.0,
    avg_win_return REAL DEFAULT 0.0,
    max_win_return REAL DEFAULT 0.0,
    avg_lose_return REAL DEFAULT 0.0,
    max_lose_return REAL DEFAULT 0.0,
    calculated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (code) REFERENCES stocks(code) ON DELETE CASCADE,
    UNIQUE(code, rights_month, buy_days_before)
);

CREATE INDEX idx_simulation_code ON simulation_cache(code);
CREATE INDEX idx_simulation_score ON simulation_cache(expected_return DESC, win_rate DESC);

-- ========================================
-- 4. ウォッチリストテーブル
-- ========================================
CREATE TABLE watchlist (
    code TEXT PRIMARY KEY,
    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    memo TEXT,
    FOREIGN KEY (code) REFERENCES stocks(code) ON DELETE CASCADE
);

CREATE INDEX idx_watchlist_added ON watchlist(added_at DESC);

-- ========================================
-- 5. 通知設定テーブル
-- ========================================
CREATE TABLE notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL,
    target_date DATE NOT NULL,
    notified BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (code) REFERENCES stocks(code) ON DELETE CASCADE
);

CREATE INDEX idx_notifications_date ON notifications(target_date);
CREATE INDEX idx_notifications_code ON notifications(code);

-- ========================================
-- 6. スキーマバージョン管理テーブル
-- ========================================
CREATE TABLE schema_version (
    version INTEGER PRIMARY KEY,
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

INSERT INTO schema_version (version, description) VALUES
(1, 'Initial schema creation - v1.0.0');

-- ========================================
-- サンプルデータ（開発用）
-- ========================================
-- INSERT INTO stocks (code, name, rights_month, yuutai_genre, yuutai_content, min_shares, data_source) VALUES
-- ('8151', '三菱商事', 3, '金券・ギフト券', 'QUOカード500円', 100, '96ut'),
-- ('9202', 'ANAホールディングス', 3, '優待券', '国内線50%割引券', 100, '96ut'),
-- ('7201', '日産自動車', 3, 'カタログ', '自社製品カタログギフト', 100, 'net-ir');
