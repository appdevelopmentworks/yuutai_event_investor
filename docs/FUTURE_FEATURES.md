# 将来の拡張機能

このドキュメントでは、現在は未実装だが将来的に実装予定の機能を記載します。

---

## 1. 高配当銘柄サポート

### 概要

現在のアプリは**株主優待銘柄**のみを対象としていますが、**高配当銘柄**も同様に「配当狙いの買い上がり」が発生する可能性があります。配当銘柄も権利付最終日前に最適な買入タイミングを分析できるようにする拡張機能です。

### 背景

- 高配当銘柄（配当利回り3%以上など）は、配当金目当てに権利付最終日までに買い上がる傾向がある
- 優待銘柄と同じバックテスト手法が適用可能
- 証券会社のスクリーニング機能で高配当銘柄リストを取得できる

### 実装済みの準備

#### 1. データベーススキーマ拡張

マイグレーションファイル: `data/migrations/add_dividend_columns.sql`

**追加カラム:**
```sql
ALTER TABLE stocks ADD COLUMN dividend_yield REAL;           -- 配当利回り（%）
ALTER TABLE stocks ADD COLUMN dividend_amount REAL;          -- 1株あたり配当金（円）
ALTER TABLE stocks ADD COLUMN market TEXT;                   -- 市場区分（プライム/スタンダード/グロース）
ALTER TABLE stocks ADD COLUMN sector TEXT;                   -- 業種（セクター）
ALTER TABLE stocks ADD COLUMN stock_type TEXT DEFAULT 'yuutai'; -- 銘柄タイプ
ALTER TABLE stocks ADD COLUMN has_yuutai BOOLEAN DEFAULT 1;  -- 優待あり/なし
ALTER TABLE stocks ADD COLUMN has_dividend BOOLEAN DEFAULT 0; -- 配当あり/なし
```

**stock_type の値:**
- `'yuutai'` - 優待のみ（既存銘柄）
- `'dividend'` - 配当のみ
- `'both'` - 優待+配当の両方

**新規ビュー:**
- `v_high_dividend_stocks` - 配当利回り3%以上の銘柄
- `v_yuutai_dividend_stocks` - 優待+配当の両方がある銘柄

#### 2. CSVインポート用テンプレート

ファイル: `templates/dividend_stocks_template.csv`

**推奨CSVフォーマット:**
```csv
code,name,dividend_yield,rights_month,dividend_amount,market,sector
8306,三菱UFJフィナンシャル・グループ,4.5,3,50,プライム,銀行業
9434,ソフトバンク,5.2,3,86,プライム,情報・通信業
8001,伊藤忠商事,3.8,3,170,プライム,卸売業
```

**最小構成（必須項目のみ）:**
```csv
code,name,dividend_yield,rights_month
8306,三菱UFJフィナンシャル・グループ,4.5,3
```

**項目説明:**
- `code` - 4桁の証券コード（必須）
- `name` - 銘柄名（必須）
- `dividend_yield` - 配当利回り（%）（必須）
- `rights_month` - 権利確定月（1-12）（必須）
- `dividend_amount` - 1株あたり配当金（円）（オプション、分析精度向上）
- `market` - 市場区分（オプション、フィルタリング用）
- `sector` - 業種（オプション、セクター分散用）

#### 3. kenrlast設定の追加

ファイル: `config/settings.json`

```json
{
  "kenrlast": 2
}
```

**設定値の意味:**
- `2` - 日本株（権利確定日の2営業日前が権利付最終日）
- `1` - 米国株（権利確定日の1営業日前が権利付最終日）

**重要な設計思想:**
- `rights_date`（権利確定日）はCSVで不要
- `rights_month`（権利確定月）のみで計算可能
- 将来的に日本株のルールが変更（2営業日前→1営業日前）されても、`kenrlast`を変更するだけで対応可能

### 未実装の機能

#### 1. CSVインポート機能（UI）

**実装内容:**
- メニューバー → 「ファイル」 → 「高配当銘柄をインポート」
- ファイル選択ダイアログでCSVを読み込み
- データベースへの一括登録（重複チェック付き）
- 進捗表示ダイアログ

**実装例:**
```python
class DividendImporter:
    def import_from_csv(self, csv_path: str) -> int:
        """CSVから高配当銘柄をインポート"""
        imported_count = 0

        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['code'].startswith('#'):
                    continue  # コメント行をスキップ

                stock_data = {
                    'code': row['code'],
                    'name': row['name'],
                    'dividend_yield': float(row['dividend_yield']),
                    'rights_month': int(row['rights_month']),
                    'dividend_amount': float(row.get('dividend_amount', 0)),
                    'market': row.get('market', ''),
                    'sector': row.get('sector', ''),
                    'stock_type': 'dividend',
                    'has_yuutai': 0,
                    'has_dividend': 1,
                    'data_source': 'csv_import'
                }

                self.db_manager.insert_or_update_stock(stock_data)
                imported_count += 1

        return imported_count
```

#### 2. フィルタリング機能の拡張

**追加フィルター:**
- 銘柄タイプ選択（優待のみ / 配当のみ / 両方 / すべて）
- 配当利回り範囲（例: 3%以上）
- 市場区分（プライム / スタンダード / グロース）
- 業種（セクター）別フィルタ

**UI配置:**
```
┌─ フィルターパネル ─────┐
│ 権利確定月: [3月▼]     │
│ 銘柄タイプ:            │
│   ☑ 優待               │
│   ☐ 配当               │
│   ☐ 優待+配当          │
│                        │
│ 配当利回り:            │
│   最小: [3.0] %        │
│   最大: [___] %        │
│                        │
│ 市場区分:              │
│   ☑ プライム           │
│   ☐ スタンダード       │
│   ☐ グロース           │
└────────────────────────┘
```

#### 3. 銘柄リスト表示の拡張

**追加列:**
- 配当利回り（%）
- 配当金額（円）
- 市場区分
- 業種

**表示例:**
```
┌───────────────────────────────────────────────────────┐
│コード│銘柄名              │権利月│タイプ│配当  │最適日│
├─────┼────────────────────┼──────┼──────┼──────┼──────┤
│8306  │三菱UFJ FG          │3月   │配当  │4.5%  │15日前│
│9434  │ソフトバンク        │3月   │配当  │5.2%  │20日前│
│7453  │良品計画            │2月   │両方  │3.8%  │10日前│
└───────────────────────────────────────────────────────┘
```

#### 4. 自動スクレイピング機能（オプション）

将来的に配当情報を自動取得したい場合のデータソース候補:

**データソース:**
- **minkabu.jp** - 配当利回りランキング
- **kabutan.jp** - 高配当利回りランキング
- **Yahoo!ファイナンス** - 配当利回り検索
- **証券会社API** - 楽天証券、SBI証券など

**実装例:**
```python
class DividendScraper:
    def scrape_high_dividend_stocks(self, min_yield: float = 3.0) -> List[Dict]:
        """高配当銘柄をスクレイピング"""
        # minkabu.jp の配当利回りランキングから取得
        url = f"https://minkabu.jp/screening?配当利回り={min_yield}"
        # スクレイピング処理
        pass
```

#### 5. 詳細分析パネルの拡張

**配当銘柄専用の表示項目:**
- 配当利回り（%）
- 1株配当金（円）
- 予想配当利回り
- 配当性向
- 連続増配年数

**表示例:**
```
┌─ 銘柄情報 ──────────────┐
│ 8306 三菱UFJ FG         │
│ 市場: プライム          │
│ 業種: 銀行業            │
│                         │
│ 配当利回り: 4.5%        │
│ 1株配当金: 50円         │
│ 配当性向: 40%           │
│                         │
│ 最適買入日: 15日前      │
│ 勝率: 75%               │
│ 期待リターン: +2.3%     │
└─────────────────────────┘
```

### 実装の優先順位

1. **Phase 1（必須）**: CSVインポート機能の実装
2. **Phase 2（推奨）**: フィルタリング機能の拡張
3. **Phase 3（推奨）**: 銘柄リスト表示の拡張
4. **Phase 4（オプション）**: 自動スクレイピング機能
5. **Phase 5（オプション）**: 詳細分析パネルの拡張

### データ取得方法（ユーザー向け）

#### 証券会社のスクリーニング機能を使う方法

**楽天証券の例:**
1. 楽天証券にログイン
2. 「国内株式」 → 「スーパースクリーナー」
3. 条件設定:
   - 配当利回り: 3.0%以上
   - 市場: プライム
   - 時価総額: 100億円以上（流動性確保）
4. 結果をCSVでエクスポート
5. CSVを`templates/dividend_stocks_template.csv`のフォーマットに変換

**SBI証券の例:**
1. SBI証券にログイン
2. 「国内株式」 → 「スクリーニング」
3. 条件設定:
   - 配当利回り（予想）: 3.0%以上
   - PER: 15倍以下（割安株）
   - 自己資本比率: 40%以上（財務健全性）
4. 結果をダウンロード

### kenrlast変更時の影響範囲

**将来的に日本株のルールが変更された場合:**

1. `config/settings.json` を編集:
```json
{
  "kenrlast": 1  // 2 → 1 に変更
}
```

2. シミュレーションキャッシュをクリア:
```sql
DELETE FROM simulation_cache;
```

3. アプリを再起動してバックテスト再実行

**影響を受けるコード:**
- `src/core/calculator.py` - kenrlastパラメータを使用
- すべてのバックテスト計算が自動的に1営業日前基準に変更される

**影響を受けないコード:**
- データベーススキーマ
- UI表示ロジック
- フィルター機能

### 注意事項

#### 配当銘柄特有のリスク

1. **流動性リスク**: 優待銘柄ほど買い上がりが顕著ではない可能性
2. **配当落ち**: 権利落ち日に株価が配当金額分下落する
3. **税金**: 配当所得税（約20%）を考慮する必要あり

#### バックテスト精度

- 配当銘柄は優待銘柄ほど「イベント性」が強くない
- 勝率が優待銘柄より低い可能性がある
- 十分なバックテスト期間（10年以上）が必要

---

## 2. その他の将来機能

### 2.1 ポートフォリオ最適化

- 現代ポートフォリオ理論（MPT）の適用
- シャープレシオ最大化
- リスクパリティ戦略

### 2.2 機械学習による予測

- 過去の価格パターンから最適日を予測
- Random Forest / XGBoost の適用
- 特徴量エンジニアリング

### 2.3 リアルタイム通知

- LINE通知連携
- Slack連携
- メール通知

---

**最終更新**: 2025-01-11
**バージョン**: 1.0.0
