-- データベース初期化スクリプト
-- Yuutai Event Investor Database Schema
-- Version: 2.0.0
-- Date: 2025-11-07
-- 変更点: stocksテーブルの主キーを(code, rights_month)の複合キーに変更

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
-- 主キーを複合キー(code, rights_month)に変更
-- 理由: 同じ銘柄が複数の月に優待を実施する場合に対応
CREATE TABLE stocks (
    code TEXT NOT NULL,
    rights_month INTEGER NOT NULL,
    name TEXT NOT NULL,
    rights_date DATE,
    yuutai_genre TEXT,
    yuutai_content TEXT,
    yuutai_detail TEXT,
    min_shares INTEGER,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    data_source TEXT,
    PRIMARY KEY (code, rights_month)
);

CREATE INDEX idx_stocks_code ON stocks(code);
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
    FOREIGN KEY (code, rights_month) REFERENCES stocks(code, rights_month) ON DELETE CASCADE,
    UNIQUE(code, rights_month, buy_days_before)
);

CREATE INDEX idx_simulation_code ON simulation_cache(code);
CREATE INDEX idx_simulation_code_month ON simulation_cache(code, rights_month);
CREATE INDEX idx_simulation_score ON simulation_cache(expected_return DESC, win_rate DESC);

-- ========================================
-- 4. ウォッチリストテーブル
-- ========================================
-- 複合主キーに変更（同じ銘柄の異なる権利確定月を個別にウォッチ可能）
CREATE TABLE watchlist (
    code TEXT NOT NULL,
    rights_month INTEGER NOT NULL,
    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    memo TEXT,
    PRIMARY KEY (code, rights_month),
    FOREIGN KEY (code, rights_month) REFERENCES stocks(code, rights_month) ON DELETE CASCADE
);

CREATE INDEX idx_watchlist_added ON watchlist(added_at DESC);
CREATE INDEX idx_watchlist_code ON watchlist(code);

-- ========================================
-- 5. 通知設定テーブル
-- ========================================
CREATE TABLE notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL,
    rights_month INTEGER NOT NULL,
    target_date DATE NOT NULL,
    notified BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (code, rights_month) REFERENCES stocks(code, rights_month) ON DELETE CASCADE
);

CREATE INDEX idx_notifications_date ON notifications(target_date);
CREATE INDEX idx_notifications_code ON notifications(code);
CREATE INDEX idx_notifications_code_month ON notifications(code, rights_month);

-- ========================================
-- 6. スキーマバージョン管理テーブル
-- ========================================
CREATE TABLE schema_version (
    version INTEGER PRIMARY KEY,
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

INSERT INTO schema_version (version, description) VALUES
(2, 'Schema v2.0.0 - Changed PRIMARY KEY to (code, rights_month) for multiple yuutai per stock');
