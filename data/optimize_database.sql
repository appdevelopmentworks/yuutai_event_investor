-- データベース最適化スクリプト
-- Yuutai Event Investor Database Optimization
-- Version: 1.1.0
-- Date: 2024-11-07

-- ========================================
-- 追加インデックスの作成
-- ========================================

-- 銘柄検索用の複合インデックス
CREATE INDEX IF NOT EXISTS idx_stocks_month_genre ON stocks(rights_month, yuutai_genre);

-- シミュレーション結果の複数ソート用インデックス
CREATE INDEX IF NOT EXISTS idx_simulation_win_rate ON simulation_cache(win_rate DESC);
CREATE INDEX IF NOT EXISTS idx_simulation_expected_return ON simulation_cache(expected_return DESC);
CREATE INDEX IF NOT EXISTS idx_simulation_code_month ON simulation_cache(code, rights_month);

-- 株価履歴の範囲検索用インデックス
CREATE INDEX IF NOT EXISTS idx_price_code_date_close ON price_history(code, date, close);

-- 通知の効率的な検索用インデックス
CREATE INDEX IF NOT EXISTS idx_notifications_date_notified ON notifications(target_date, notified);

-- ========================================
-- ANALYZE実行（統計情報の更新）
-- ========================================
ANALYZE;

-- ========================================
-- VACUUM実行（データベース最適化）
-- 注意: 大きなデータベースの場合、時間がかかる可能性があります
-- ========================================
-- VACUUM;

-- ========================================
-- 便利なビューの作成
-- ========================================

-- ウォッチリスト詳細ビュー
CREATE VIEW IF NOT EXISTS v_watchlist_detail AS
SELECT
    w.code,
    s.name,
    s.rights_month,
    s.rights_date,
    s.yuutai_genre,
    s.yuutai_content,
    w.added_at,
    w.memo,
    -- 最新のシミュレーション結果を取得
    (SELECT expected_return FROM simulation_cache sc
     WHERE sc.code = w.code
     ORDER BY sc.expected_return DESC
     LIMIT 1) as expected_return,
    (SELECT win_rate FROM simulation_cache sc
     WHERE sc.code = w.code
     ORDER BY sc.expected_return DESC
     LIMIT 1) as win_rate,
    (SELECT buy_days_before FROM simulation_cache sc
     WHERE sc.code = w.code
     ORDER BY sc.expected_return DESC
     LIMIT 1) as optimal_days
FROM watchlist w
JOIN stocks s ON w.code = s.code
ORDER BY w.added_at DESC;

-- 今日の通知ビュー
CREATE VIEW IF NOT EXISTS v_today_notifications AS
SELECT
    n.id,
    n.code,
    s.name,
    s.rights_month,
    s.rights_date,
    n.target_date,
    n.notified
FROM notifications n
JOIN stocks s ON n.code = s.code
WHERE n.target_date = DATE('now')
  AND n.notified = 0;

-- 高勝率銘柄ビュー（勝率70%以上）
CREATE VIEW IF NOT EXISTS v_high_winrate_stocks AS
SELECT DISTINCT
    s.code,
    s.name,
    s.rights_month,
    s.rights_date,
    s.yuutai_genre,
    sc.win_rate,
    sc.expected_return,
    sc.buy_days_before as optimal_days
FROM stocks s
JOIN simulation_cache sc ON s.code = sc.code
WHERE sc.win_rate >= 0.7
ORDER BY sc.expected_return DESC, sc.win_rate DESC;

-- ========================================
-- スキーマバージョン更新
-- ========================================
INSERT OR IGNORE INTO schema_version (version, description) VALUES
(2, 'Database optimization - added composite indexes and views');
