# 📊 データベース設計書

## データベース概要

- **データベース種別:** SQLite3
- **ファイル名:** yuutai.db
- **文字コード:** UTF-8
- **配置場所:** `data/yuutai.db`

---

## テーブル定義

### 1. stocks（銘柄マスタテーブル）

優待銘柄の基本情報を管理

```sql
CREATE TABLE stocks (
    code TEXT PRIMARY KEY,              -- 証券コード（例: 8151）
    name TEXT NOT NULL,                 -- 銘柄名（例: 三菱商事）
    rights_month INTEGER,               -- 権利確定月（1-12）
    yuutai_genre TEXT,                  -- 優待ジャンル（食品、金券等）
    yuutai_content TEXT,                -- 優待内容（簡易）
    yuutai_detail TEXT,                 -- 優待内容（詳細）
    min_shares INTEGER,                 -- 最低必要株数
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,  -- 最終更新日時
    data_source TEXT                    -- データソース（96ut/net-ir）
);

-- インデックス
CREATE INDEX idx_stocks_rights_month ON stocks(rights_month);
CREATE INDEX idx_stocks_genre ON stocks(yuutai_genre);
```

**カラム説明:**

| カラム名 | データ型 | 制約 | 説明 | 例 |
|---------|---------|------|------|-----|
| code | TEXT | PRIMARY KEY | 証券コード（4桁） | 8151 |
| name | TEXT | NOT NULL | 銘柄名 | 三菱商事 |
| rights_month | INTEGER | | 権利確定月 | 3 |
| yuutai_genre | TEXT | | 優待ジャンル | 金券・ギフト券 |
| yuutai_content | TEXT | | 優待内容（簡易） | QUOカード500円 |
| yuutai_detail | TEXT | | 優待内容（詳細） | 100株以上でQUOカード500円相当 |
| min_shares | INTEGER | | 最低必要株数 | 100 |
| last_updated | DATETIME | DEFAULT CURRENT_TIMESTAMP | 最終更新日時 | 2024-11-06 10:00:00 |
| data_source | TEXT | | データ取得元 | 96ut |

---

### 2. price_history（株価履歴テーブル）

日次の株価データを管理

```sql
CREATE TABLE price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL,                 -- 証券コード
    date DATE NOT NULL,                 -- 日付
    open REAL,                          -- 始値
    high REAL,                          -- 高値
    low REAL,                           -- 安値
    close REAL NOT NULL,                -- 終値（必須）
    volume INTEGER,                     -- 出来高
    FOREIGN KEY (code) REFERENCES stocks(code) ON DELETE CASCADE,
    UNIQUE(code, date)                  -- 同一銘柄・同一日付のデータは1件のみ
);

-- インデックス
CREATE INDEX idx_price_code_date ON price_history(code, date);
CREATE INDEX idx_price_date ON price_history(date);
```

**カラム説明:**

| カラム名 | データ型 | 制約 | 説明 | 例 |
|---------|---------|------|------|-----|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 自動採番ID | 1 |
| code | TEXT | NOT NULL, FOREIGN KEY | 証券コード | 8151 |
| date | DATE | NOT NULL | 日付 | 2024-03-15 |
| open | REAL | | 始値 | 2500.0 |
| high | REAL | | 高値 | 2550.0 |
| low | REAL | | 安値 | 2480.0 |
| close | REAL | NOT NULL | 終値 | 2520.0 |
| volume | INTEGER | | 出来高 | 1500000 |

---

### 3. simulation_cache（シミュレーション結果キャッシュテーブル）

計算済みのシミュレーション結果をキャッシュ

```sql
CREATE TABLE simulation_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL,                 -- 証券コード
    rights_month INTEGER NOT NULL,      -- 権利確定月
    buy_days_before INTEGER NOT NULL,   -- 何日前に購入
    win_count INTEGER DEFAULT 0,        -- 勝数
    lose_count INTEGER DEFAULT 0,       -- 負数
    win_rate REAL DEFAULT 0.0,          -- 勝率（0.0-1.0）
    expected_return REAL DEFAULT 0.0,   -- 期待リターン（%）
    avg_win_return REAL DEFAULT 0.0,    -- 勝平均リターン（%）
    max_win_return REAL DEFAULT 0.0,    -- 最大勝ちリターン（%）
    avg_lose_return REAL DEFAULT 0.0,   -- 負平均リターン（%）
    max_lose_return REAL DEFAULT 0.0,   -- 最大負けリターン（%）
    calculated_at DATETIME DEFAULT CURRENT_TIMESTAMP,  -- 計算日時
    FOREIGN KEY (code) REFERENCES stocks(code) ON DELETE CASCADE,
    UNIQUE(code, rights_month, buy_days_before)
);

-- インデックス
CREATE INDEX idx_simulation_code ON simulation_cache(code);
CREATE INDEX idx_simulation_score ON simulation_cache(expected_return DESC, win_rate DESC);
```

**カラム説明:**

| カラム名 | データ型 | 制約 | 説明 | 例 |
|---------|---------|------|------|-----|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 自動採番ID | 1 |
| code | TEXT | NOT NULL, FOREIGN KEY | 証券コード | 8151 |
| rights_month | INTEGER | NOT NULL | 権利確定月 | 3 |
| buy_days_before | INTEGER | NOT NULL | 何日前に購入 | 18 |
| win_count | INTEGER | DEFAULT 0 | 勝数 | 8 |
| lose_count | INTEGER | DEFAULT 0 | 負数 | 4 |
| win_rate | REAL | DEFAULT 0.0 | 勝率 | 0.667 |
| expected_return | REAL | DEFAULT 0.0 | 期待リターン | 4.2 |
| avg_win_return | REAL | DEFAULT 0.0 | 勝平均リターン | 6.5 |
| max_win_return | REAL | DEFAULT 0.0 | 最大勝ちリターン | 12.3 |
| avg_lose_return | REAL | DEFAULT 0.0 | 負平均リターン | -2.1 |
| max_lose_return | REAL | DEFAULT 0.0 | 最大負けリターン | -5.8 |
| calculated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 計算日時 | 2024-11-06 10:00:00 |

---

### 4. watchlist（ウォッチリストテーブル）

ユーザーが注目している銘柄を管理

```sql
CREATE TABLE watchlist (
    code TEXT PRIMARY KEY,              -- 証券コード
    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,  -- 追加日時
    memo TEXT,                          -- メモ
    FOREIGN KEY (code) REFERENCES stocks(code) ON DELETE CASCADE
);

-- インデックス
CREATE INDEX idx_watchlist_added ON watchlist(added_at DESC);
```

**カラム説明:**

| カラム名 | データ型 | 制約 | 説明 | 例 |
|---------|---------|------|------|-----|
| code | TEXT | PRIMARY KEY, FOREIGN KEY | 証券コード | 8151 |
| added_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 追加日時 | 2024-11-06 10:00:00 |
| memo | TEXT | | ユーザーメモ | 配当利回り良好 |

---

### 5. notifications（通知設定テーブル）

買いタイミングの通知設定を管理

```sql
CREATE TABLE notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL,                 -- 証券コード
    target_date DATE NOT NULL,          -- 目標購入日
    notified BOOLEAN DEFAULT 0,         -- 通知済みフラグ
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,  -- 作成日時
    FOREIGN KEY (code) REFERENCES stocks(code) ON DELETE CASCADE
);

-- インデックス
CREATE INDEX idx_notifications_date ON notifications(target_date);
CREATE INDEX idx_notifications_code ON notifications(code);
```

**カラム説明:**

| カラム名 | データ型 | 制約 | 説明 | 例 |
|---------|---------|------|------|-----|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 自動採番ID | 1 |
| code | TEXT | NOT NULL, FOREIGN KEY | 証券コード | 8151 |
| target_date | DATE | NOT NULL | 目標購入日 | 2025-03-10 |
| notified | BOOLEAN | DEFAULT 0 | 通知済みフラグ | 0 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 作成日時 | 2024-11-06 10:00:00 |

---

## ER図（Entity Relationship Diagram）

```
┌─────────────────┐
│     stocks      │
│─────────────────│
│ code (PK)       │────┐
│ name            │    │
│ rights_month    │    │
│ yuutai_genre    │    │
│ yuutai_content  │    │
│ yuutai_detail   │    │
│ min_shares      │    │
│ last_updated    │    │
│ data_source     │    │
└─────────────────┘    │
                       │
        ┌──────────────┼──────────────┬──────────────┬──────────────┐
        │              │              │              │              │
        ▼              ▼              ▼              ▼              ▼
┌─────────────────┐ ┌──────────────┐ ┌─────────────┐ ┌────────────┐
│ price_history   │ │ simulation   │ │  watchlist  │ │notifications│
│─────────────────│ │   _cache     │ │─────────────│ │────────────│
│ id (PK)         │ │──────────────│ │ code (PK,FK)│ │ id (PK)    │
│ code (FK)       │ │ id (PK)      │ │ added_at    │ │ code (FK)  │
│ date            │ │ code (FK)    │ │ memo        │ │ target_date│
│ open            │ │ rights_month │ └─────────────┘ │ notified   │
│ high            │ │ buy_days_...│                  │ created_at │
│ low             │ │ win_count    │                  └────────────┘
│ close           │ │ lose_count   │
│ volume          │ │ win_rate     │
└─────────────────┘ │ expected_... │
                    │ avg_win_...  │
                    │ max_win_...  │
                    │ avg_lose_... │
                    │ max_lose_... │
                    │ calculated...│
                    └──────────────┘
```

---

## 初期化スクリプト

### create_tables.sql

```sql
-- データベース初期化スクリプト

-- 既存テーブルの削除（開発用）
DROP TABLE IF EXISTS notifications;
DROP TABLE IF EXISTS watchlist;
DROP TABLE IF EXISTS simulation_cache;
DROP TABLE IF EXISTS price_history;
DROP TABLE IF EXISTS stocks;

-- 1. 銘柄マスタテーブル
CREATE TABLE stocks (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    rights_month INTEGER,
    yuutai_genre TEXT,
    yuutai_content TEXT,
    yuutai_detail TEXT,
    min_shares INTEGER,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    data_source TEXT
);

CREATE INDEX idx_stocks_rights_month ON stocks(rights_month);
CREATE INDEX idx_stocks_genre ON stocks(yuutai_genre);

-- 2. 株価履歴テーブル
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

-- 3. シミュレーション結果キャッシュテーブル
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

-- 4. ウォッチリストテーブル
CREATE TABLE watchlist (
    code TEXT PRIMARY KEY,
    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    memo TEXT,
    FOREIGN KEY (code) REFERENCES stocks(code) ON DELETE CASCADE
);

CREATE INDEX idx_watchlist_added ON watchlist(added_at DESC);

-- 5. 通知設定テーブル
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
```

---

## サンプルデータ

### stocks テーブル

```sql
INSERT INTO stocks (code, name, rights_month, yuutai_genre, yuutai_content, min_shares, data_source) VALUES
('8151', '三菱商事', 3, '金券・ギフト券', 'QUOカード500円', 100, '96ut'),
('9202', 'ANAホールディングス', 3, '優待券', '国内線50%割引券', 100, '96ut'),
('7201', '日産自動車', 3, 'カタログ', '自社製品カタログギフト', 100, 'net-ir');
```

### watchlist テーブル

```sql
INSERT INTO watchlist (code, memo) VALUES
('8151', '配当利回り良好'),
('9202', '優待券が魅力的');
```

---

## データアクセスパターン

### 1. 銘柄検索（フィルター付き）

```sql
SELECT 
    s.code,
    s.name,
    s.rights_month,
    s.yuutai_content,
    sc.buy_days_before,
    sc.win_rate,
    sc.expected_return
FROM stocks s
LEFT JOIN (
    SELECT code, rights_month, buy_days_before, win_rate, expected_return
    FROM simulation_cache
    WHERE (code, rights_month, win_rate * expected_return) IN (
        SELECT code, rights_month, MAX(win_rate * expected_return)
        FROM simulation_cache
        GROUP BY code, rights_month
    )
) sc ON s.code = sc.code AND s.rights_month = sc.rights_month
WHERE s.rights_month = 3
  AND sc.win_rate >= 0.6
  AND sc.expected_return >= 3.0
ORDER BY sc.expected_return DESC, sc.win_rate DESC;
```

### 2. 個別銘柄の詳細シミュレーション結果

```sql
SELECT 
    buy_days_before,
    win_count,
    lose_count,
    win_rate,
    expected_return,
    avg_win_return,
    max_win_return,
    avg_lose_return,
    max_lose_return
FROM simulation_cache
WHERE code = '8151' AND rights_month = 3
ORDER BY buy_days_before;
```

### 3. ウォッチリスト銘柄の取得

```sql
SELECT 
    s.code,
    s.name,
    s.rights_month,
    w.memo,
    w.added_at
FROM watchlist w
JOIN stocks s ON w.code = s.code
ORDER BY w.added_at DESC;
```

### 4. 通知対象の取得（本日から3日以内）

```sql
SELECT 
    n.id,
    n.code,
    s.name,
    n.target_date,
    julianday(n.target_date) - julianday('now') as days_until
FROM notifications n
JOIN stocks s ON n.code = s.code
WHERE n.notified = 0
  AND julianday(n.target_date) - julianday('now') BETWEEN 0 AND 3
ORDER BY n.target_date;
```

---

## パフォーマンス最適化

### 1. インデックス戦略

- **頻繁に検索される列にインデックス:**
  - `stocks.rights_month`
  - `price_history(code, date)`
  - `simulation_cache.expected_return, win_rate`

### 2. キャッシュ戦略

- シミュレーション結果は`simulation_cache`テーブルに保存
- 株価データ更新時のみ再計算
- キャッシュの有効期限: 株価データ更新日

### 3. データ削除ポリシー

```sql
-- 古い株価データの削除（ユーザー設定に応じて）
DELETE FROM price_history 
WHERE date < date('now', '-5 year');

-- 古いシミュレーションキャッシュの削除
DELETE FROM simulation_cache
WHERE calculated_at < datetime('now', '-7 day');
```

---

## バックアップ・リストア

### バックアップ

```bash
# データベース全体をバックアップ
sqlite3 data/yuutai.db ".backup data/yuutai_backup_$(date +%Y%m%d).db"

# CSV形式でエクスポート
sqlite3 data/yuutai.db -header -csv "SELECT * FROM stocks;" > stocks_backup.csv
```

### リストア

```bash
# バックアップから復元
cp data/yuutai_backup_20241106.db data/yuutai.db

# CSV形式からインポート
sqlite3 data/yuutai.db <<EOF
.mode csv
.import stocks_backup.csv stocks
EOF
```

---

## マイグレーション管理

将来的なテーブル構造変更に備えたバージョン管理

```sql
CREATE TABLE schema_version (
    version INTEGER PRIMARY KEY,
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

INSERT INTO schema_version (version, description) VALUES
(1, 'Initial schema creation');
```
