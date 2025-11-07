# 📘 株主優待イベント投資分析ツール - 要求定義書

## 🎯 プロジェクト概要

**プロジェクト名:** Yuutai Event Investor  
**バージョン:** 1.0.0  
**作成日:** 2024-11-06  
**目的:** 株主優待の権利確定日を利用したイベント投資の最適タイミングを予測・分析するデスクトップアプリケーション

---

## 📋 要求定義サマリー

### 1. データ管理要件

#### 1.1 データソース
- **96ut.com** (https://96ut.com/yuutai/)
- **yutai.net-ir.ne.jp** (https://yutai.net-ir.ne.jp/)

#### 1.2 データ保存方式
- **採用技術:** SQLite + JSON設定ファイル
- **選定理由:**
  - ローカル完結で外部サーバー不要
  - トランザクション対応で堅牢
  - 高速な検索・ソート機能
  - バックアップが容易（.dbファイル1つ）
  - 将来的なデータ量増加に対応可能

#### 1.3 データ更新方針
- **更新方法:** 手動更新ボタン
- **更新頻度:** 半年～1年に1度まとめて更新
- **注意事項:** スクレイピング対象サイトの仕様変更に対応できる柔軟な設計

#### 1.4 過去データ保持期間
- **設定方法:** ユーザー設定可能
- **推奨値:** 3年～10年分
- **デフォルト:** 5年分

---

### 2. UI/UX要件

#### 2.1 メイン画面構成
- **レイアウト:** 左サイドバー（銘柄リスト）+ 右詳細エリア
- **テーマ:** ダークモード/ライトモード自動切替
- **デザイン:** フレームレス + アニメーション + モダンUI

#### 2.2 銘柄リスト表示項目（優先順）
1. 証券コード
2. 銘柄名
3. 権利確定月
4. 推奨買入日（何日前）
5. 勝率
6. 期待リターン
7. 優待内容（簡易表示）
8. 必要投資金額

#### 2.3 チャート表示形式
- **折れ線グラフ:** 期待値推移（1～120日前）
- **棒グラフ:** 各タイミングでの勝率
- **散布図:** 過去の勝ち/負けトレード（緑/赤プロット）
- **機能:** 複数グラフを切り替え可能
- **改善:** 既存のStreamlitアプリを基準により見やすく改良

---

### 3. 検索・フィルター機能要件

#### 3.1 フィルター条件
1. **権利確定月:** 月別で絞り込み（マルチセレクト可能）
2. **勝率:** スライダーで範囲指定 + 高い順ソート
3. **期待リターン:** スライダーで範囲指定 + 高い順ソート
4. **必要投資金額:** ユーザーが上限を設定可能
5. **優待ジャンル:** チェックボックスで複数選択

#### 3.2 複数条件の組み合わせ
- **対応:** はい（AND/OR条件）
- **UI:** フィルターパネルで直感的に設定可能

---

### 4. シミュレーション・分析機能要件

#### 4.1 バックテスト期間
- **デフォルト:** 取得可能な全データ期間
- **調整:** ユーザーが期間を変更可能

#### 4.2 複数銘柄比較
- **方式:** 月別で比較
- **表示:** 同一権利確定月の銘柄を一覧で比較

#### 4.3 権利付最終日の判定基準
- **方式:** ユーザーが選択可能（現行Streamlitアプリと同様）
- **デフォルト値:**
  - 日本株: 2営業日前
  - 米国株: 1営業日前
- **柔軟性:** 規則変更時に設定変更可能

#### 4.4 シミュレーション範囲
- **期間:** 約6ヶ月前から（最大120営業日前）
- **分析内容:** どのタイミング（何日前）で買うのが最適か予測
- **評価指標:** 過去の事例から勝率・期待リターンを計算

---

### 5. 通知・アラート機能要件

#### 5.1 買いタイミング通知
- **機能:** あり
- **通知内容:**
  - 「〇〇（銘柄名）の最適買入日まであと3日です」
  - 「〇〇の最適買入日は本日です！」
- **通知方法:**
  - Windows: デスクトップ通知
  - macOS: Notification Center
  - Linux: notify-send

#### 5.2 ウォッチリスト機能
- **機能:** あり
- **用途:** お気に入り銘柄を登録し優先表示
- **通知:** ウォッチリスト銘柄の最適買入日が近づいたら自動通知

---

### 6. データ出力・共有機能要件

#### 6.1 分析結果エクスポート
- **CSV出力:** 銘柄リスト・シミュレーション結果
- **スクリーンショット:** 現在表示中の画面を画像保存

#### 6.2 設定のインポート/エクスポート
- **機能:** 必要
- **用途:** 複数PC間で設定を共有
- **形式:** JSON形式

---

### 7. その他の機能要件

#### 7.1 ポートフォリオ管理機能
- **実装:** いいえ
- **理由:** 分析ツールに特化

#### 7.2 リアルタイム株価表示
- **実装:** いいえ
- **データ:** 日次終値のみ使用（yfinanceから取得）

#### 7.3 追加予定機能
- 思いついた際に追加

---

### 8. 優先順位

#### 最優先で実装すべき機能（トップ3）
1. **最適買入日の自動計算**
2. **個別銘柄の詳細分析**
3. **銘柄リスト表示・ソート**

---

## 🏗️ 技術スタック

### フロントエンド
- **UIフレームワーク:** PySide6
- **UIライブラリ:** QFluentWidgets または qmaterial
- **テーマ:** qdarktheme（ダーク/ライト自動切替）
- **デザイン:** フレームレス + アニメーション + モダンUI

### バックエンド
- **言語:** Python 3.10+
- **データベース:** SQLite3
- **設定管理:** JSON
- **株価データ取得:** yfinance
- **スクレイピング:** BeautifulSoup4 / Selenium（必要に応じて）

### データ可視化
- **チャートライブラリ:** matplotlib / PyQtGraph
- **データ処理:** pandas, numpy

### 配布
- **初期:** PyInstaller (onefolder形式)
- **将来:** Nuitkaへ移行予定

---

## 📊 データベース設計

### テーブル構成

#### 1. stocks（銘柄マスタ）
```sql
CREATE TABLE stocks (
    code TEXT PRIMARY KEY,              -- 証券コード
    name TEXT NOT NULL,                 -- 銘柄名
    rights_month INTEGER,               -- 権利確定月
    yuutai_genre TEXT,                  -- 優待ジャンル
    yuutai_content TEXT,                -- 優待内容（簡易）
    yuutai_detail TEXT,                 -- 優待内容（詳細）
    min_shares INTEGER,                 -- 最低必要株数
    last_updated DATETIME,              -- 最終更新日
    data_source TEXT                    -- データソース（96ut/net-ir）
);
```

#### 2. price_history（株価履歴）
```sql
CREATE TABLE price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL,
    date DATE NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume INTEGER,
    FOREIGN KEY (code) REFERENCES stocks(code),
    UNIQUE(code, date)
);
```

#### 3. simulation_cache（シミュレーション結果キャッシュ）
```sql
CREATE TABLE simulation_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL,
    rights_month INTEGER,
    buy_days_before INTEGER,            -- 何日前に購入
    win_count INTEGER,                  -- 勝数
    lose_count INTEGER,                 -- 負数
    win_rate REAL,                      -- 勝率
    expected_return REAL,               -- 期待リターン
    avg_win_return REAL,                -- 勝平均
    max_win_return REAL,                -- 最大勝ち
    avg_lose_return REAL,               -- 負平均
    max_lose_return REAL,               -- 最大負け
    calculated_at DATETIME,             -- 計算日時
    FOREIGN KEY (code) REFERENCES stocks(code),
    UNIQUE(code, rights_month, buy_days_before)
);
```

#### 4. watchlist（ウォッチリスト）
```sql
CREATE TABLE watchlist (
    code TEXT PRIMARY KEY,
    added_at DATETIME,
    memo TEXT,
    FOREIGN KEY (code) REFERENCES stocks(code)
);
```

#### 5. notifications（通知設定）
```sql
CREATE TABLE notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL,
    target_date DATE,                   -- 目標購入日
    notified BOOLEAN DEFAULT 0,         -- 通知済みフラグ
    FOREIGN KEY (code) REFERENCES stocks(code)
);
```

---

## 🎨 UI設計

### メイン画面レイアウト
```
┌─────────────────────────────────────────────────────┐
│  [☰] Yuutai Event Investor    [🔄更新] [⚙設定] [🌙] │ ← ヘッダー
├──────────────┬──────────────────────────────────────┤
│              │  📊 詳細分析エリア                    │
│  銘柄リスト  │  ┌────────────────────────────────┐  │
│  ┌────────┐ │  │ 銘柄情報カード                 │  │
│  │フィルター │  │ 8151 三菱商事                  │  │
│  │💰金額    │  │ 権利確定: 3月末                │  │
│  │📅月      │  │ 推奨買入: 18日前               │  │
│  │📈勝率    │  │ 勝率: 67.5% | 期待: +4.2%     │  │
│  │🏷ジャンル │  └────────────────────────────────┘  │
│  └────────┘ │                                       │
│              │  [折れ線] [棒グラフ] [散布図]         │
│  ┌────────┐ │  ┌────────────────────────────────┐  │
│  │証券コード│ │  │                                │  │
│  │銘柄名    │ │  │   📈 期待リターン推移グラフ    │  │
│  │推奨日    │ │  │                                │  │
│  │勝率 期待 │ │  │                                │  │
│  │⭐       │ │  └────────────────────────────────┘  │
│  ├────────┤ │                                       │
│  │8151     │ │  [詳細統計テーブル]                  │
│  │三菱商事  │ │  ┌────────┬────────┬────────┐     │
│  │18日前   │ │  │買入日   │勝率    │期待値  │     │
│  │67.5% ⭐ │ │  ├────────┼────────┼────────┤     │
│  ├────────┤ │  │30日前  │ 65.2% │ +3.8%  │     │
│  │...      │ │  │20日前  │ 68.1% │ +4.5%  │     │
│  └────────┘ │  │18日前  │ 67.5% │ +4.2%  │     │
│              │  └────────┴────────┴────────┘     │
└──────────────┴──────────────────────────────────────┘
```

### カラーテーマ設計
```python
THEME_CONFIG = {
    "dark": {
        "primary": "#1E90FF",          # メインカラー
        "success": "#10B981",          # 勝ちトレード
        "danger": "#EF4444",           # 負けトレード
        "background": "#1E1E1E",
        "surface": "#2D2D2D",
        "text": "#E0E0E0"
    },
    "light": {
        "primary": "#2196F3",
        "success": "#4CAF50",
        "danger": "#F44336",
        "background": "#FAFAFA",
        "surface": "#FFFFFF",
        "text": "#212121"
    }
}
```

---

## 🔧 スクレイピング設計

### 柔軟な設計（サイト仕様変更対応）

#### 設定ファイル例: scraping_config.json
```json
{
    "96ut": {
        "version": "2024-11",
        "base_url": "https://96ut.com/yuutai/",
        "selectors": {
            "stock_code": "td.code",
            "stock_name": "td.name",
            "rights_month": "td.month",
            "yuutai_content": "td.content"
        },
        "fallback_selectors": {
            "stock_code": ["div.stock-code", "span.code"],
            "stock_name": ["div.stock-name", "span.name"]
        }
    },
    "net-ir": {
        "version": "2024-11",
        "base_url": "https://yutai.net-ir.ne.jp/",
        "selectors": {
            "stock_code": "td.meigara_cd",
            "stock_name": "td.meigara_name",
            "rights_month": "td.month"
        },
        "fallback_selectors": {
            "stock_code": ["div.code", "span.cd"],
            "stock_name": ["div.name", "span.meigara"]
        }
    }
}
```

### エラーハンドリング戦略
- 複数セレクター試行（fallback_selectors）
- エラーログ記録で変更箇所を特定
- 取得失敗時の通知機能
- 手動データ追加機能（緊急対応用）

---

## 📂 プロジェクト構成

```
yuutai_event_investor/
├── main.py                          # エントリーポイント
├── requirements.txt                 # 依存パッケージ
├── README.md                        # プロジェクト説明
├── config/
│   ├── settings.json               # ユーザー設定
│   ├── scraping_config.json        # スクレイピング設定
│   └── theme_config.json           # テーマ設定
├── data/
│   ├── yuutai.db                   # SQLiteデータベース
│   └── cache/                      # 一時キャッシュ
├── docs/
│   ├── requirements.md             # 要求定義書（本ファイル）
│   ├── database_schema.md          # DB設計書
│   ├── ui_mockup.md                # UI設計書
│   └── api_reference.md            # API仕様書
├── src/
│   ├── __init__.py
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── main_window.py          # メインウィンドウ
│   │   ├── stock_list_widget.py    # 銘柄リストウィジェット
│   │   ├── detail_panel.py         # 詳細パネル
│   │   ├── chart_widget.py         # チャート表示ウィジェット
│   │   ├── filter_widget.py        # フィルターウィジェット
│   │   └── settings_dialog.py      # 設定ダイアログ
│   ├── core/
│   │   ├── __init__.py
│   │   ├── database.py             # データベース操作
│   │   ├── calculator.py           # 期待値計算エンジン
│   │   ├── backtester.py           # バックテストエンジン
│   │   ├── notifier.py             # 通知機能
│   │   └── config_manager.py       # 設定管理
│   ├── scraping/
│   │   ├── __init__.py
│   │   ├── base_scraper.py         # スクレイパー基底クラス
│   │   ├── scraper_96ut.py         # 96ut.comスクレイパー
│   │   ├── scraper_netir.py        # net-irスクレイパー
│   │   └── data_validator.py       # データ検証
│   └── utils/
│       ├── __init__.py
│       ├── ticker_utils.py         # ティッカー処理
│       ├── date_utils.py           # 日付処理
│       ├── export.py               # エクスポート機能
│       └── logger.py               # ロギング
├── resources/
│   ├── icons/                      # アイコン素材
│   ├── themes/                     # テーマファイル
│   └── images/                     # 画像素材
└── tests/
    ├── __init__.py
    ├── test_calculator.py
    ├── test_database.py
    └── test_scraper.py
```

---

## 📅 開発ロードマップ

### Phase 1: 基盤構築（Week 1-2）
- [x] 要求定義完了
- [ ] プロジェクト構成作成
- [ ] データベース設計・実装
- [ ] 既存コードの関数移植
- [ ] PySide6プロジェクト初期化

### Phase 2: コア機能実装（Week 3-4）
- [ ] 最適買入日計算エンジン
- [ ] バックテストエンジン
- [ ] yfinanceデータ取得・キャッシュ機能
- [ ] 設定管理システム

### Phase 3: UI実装（Week 5-6）
- [ ] メインウィンドウ（QFluentWidgets）
- [ ] 銘柄リスト（ソート・フィルター）
- [ ] チャート表示（matplotlib統合）
- [ ] ダーク/ライトテーマ切替

### Phase 4: スクレイピング実装（Week 7）
- [ ] 96ut.comスクレイパー
- [ ] yutai.net-ir.ne.jpスクレイパー
- [ ] エラーハンドリング・ログ記録
- [ ] データ検証機能

### Phase 5: 追加機能（Week 8）
- [ ] ウォッチリスト機能
- [ ] 通知機能
- [ ] CSV/スクリーンショット出力
- [ ] 設定インポート/エクスポート

### Phase 6: 配布準備（Week 9-10）
- [ ] PyInstaller onefolder作成
- [ ] テスト・バグ修正
- [ ] ユーザーマニュアル作成
- [ ] リリース準備

---

## ✅ 次のアクションアイテム

1. プロジェクト構成の作成
2. データベーススキーマの実装
3. 既存Streamlitコードのリファクタリング
4. UIモックアップの作成
5. スクレイピングのプロトタイプ開発

---

## 📝 備考

- 本ドキュメントは開発中に随時更新される
- 新しい要件や変更事項があれば、変更履歴に記録する
- 技術的な詳細は別途設計書に記載する
