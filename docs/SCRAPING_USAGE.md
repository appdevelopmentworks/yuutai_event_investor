# スクレイピング機能 使用ガイド

## クイックスタート

### テストスクリプトで動作確認

```bash
# 基本的なテスト（フォールバック戦略）
python scripts/test_scraper.py

# 特定の月のデータを取得
python scripts/test_scraper.py --month 3

# 特定のソースをテスト
python scripts/test_scraper.py --source 96ut --month 3
python scripts/test_scraper.py --source yutai_net --month 12

# 全ソースからデータを統合
python scripts/test_scraper.py --all --month 3
```

## Pythonコードでの使用

### パターン1: スクレイパーマネージャー（推奨）

```python
from src.scrapers import ScraperManager

# マネージャーを初期化
manager = ScraperManager()

# フォールバック戦略（最初に成功したソースを使用）
stocks = manager.scrape_with_fallback(month=3)

print(f"取得件数: {len(stocks)}件")

for stock in stocks[:5]:  # 最初の5件
    print(f"{stock['code']} - {stock['name']}")
    print(f"  権利確定: {stock['rights_month']}月 ({stock['rights_date']})")
    if stock.get('yuutai_content'):
        print(f"  優待内容: {stock['yuutai_content'][:50]}...")

# 終了時にセッションをクローズ
manager.close_all()
```

### パターン2: 全ソースから取得して統合

```python
from src.scrapers import ScraperManager

manager = ScraperManager()

# 全ソースからデータを取得して重複除去
stocks = manager.scrape_all(month=3)

print(f"統合後の件数: {len(stocks)}件")

# 月別の統計
month_counts = {}
for stock in stocks:
    m = stock.get('rights_month')
    month_counts[m] = month_counts.get(m, 0) + 1

print("\n月別統計:")
for m in sorted(month_counts.keys()):
    print(f"  {m}月: {month_counts[m]}件")

manager.close_all()
```

### パターン3: 特定のソースのみ使用

```python
from src.scrapers import Scraper96ut, ScraperYutaiNet

# 96ut.com から取得
scraper = Scraper96ut()
stocks = scraper.scrape_stocks(term="3月末")
print(f"96ut.com: {len(stocks)}件")
scraper.close()

# yutai.net-ir.ne.jp から取得
scraper = ScraperYutaiNet()
stocks = scraper.scrape_stocks(month=3)
print(f"yutai.net: {len(stocks)}件")
scraper.close()
```

## データベースへのインポート

### スクリプトでの一括インポート

```python
from src.scrapers import ScraperManager
from src.core.database import DatabaseManager

# データ取得
manager = ScraperManager()
stocks = manager.scrape_with_fallback()
manager.close_all()

# データベースに保存
db = DatabaseManager()

success_count = 0
error_count = 0

for stock in stocks:
    try:
        db.insert_or_update_stock(
            code=stock['code'],
            name=stock['name'],
            rights_month=stock['rights_month'],
            rights_date=stock['rights_date'],
            yuutai_genre=stock.get('yuutai_genre', ''),
            yuutai_content=stock.get('yuutai_content', ''),
            min_investment=stock.get('min_investment', 0)
        )
        success_count += 1
    except Exception as e:
        print(f"エラー: {stock['code']} - {e}")
        error_count += 1

print(f"\n成功: {success_count}件")
print(f"失敗: {error_count}件")
```

## サイト構造変更への対応

### ステップ1: エラーログを確認

スクレイピングが失敗した場合、以下のようなログが出力されます：

```
WARNING - 全セレクターが失敗: stock_rows
WARNING - テーブル行が見つかりません: https://96ut.com/stock/list.php?term=3月末&key=y
```

### ステップ2: ブラウザで確認

1. 該当URLをブラウザで開く
2. 開発者ツール（F12）を開く
3. Elements タブで HTML 構造を確認
4. 新しいセレクターを特定

### ステップ3: selectors.json を更新

`src/scrapers/selectors.json` を編集：

```json
{
  "96ut": {
    "stock_rows": [
      "table.new-class-name tr",     // 新しいセレクター
      "table.yuutai-list tr",        // 旧セレクター（フォールバック）
      "div.stock-item"
    ],
    "code": [
      "td.code-cell a",              // 新しいセレクター
      "td.code a",                   // 旧セレクター（フォールバック）
      "span.code"
    ]
  }
}
```

### ステップ4: テスト

```bash
python scripts/test_scraper.py --source 96ut --month 3
```

成功すれば、コード変更なしで修正完了です！

## トラブルシューティング

### 問題: データが取得できない

**確認事項:**
1. ネットワーク接続を確認
2. サイトがアクセス可能か確認（ブラウザで開く）
3. ログを詳細モードで確認

**解決策:**
```bash
# ログレベルをDEBUGに設定して実行
python scripts/test_scraper.py --source 96ut --month 3
```

### 問題: 一部の銘柄が取得できない

**原因:** データ検証で弾かれている可能性があります

**確認方法:**
ログに以下のようなメッセージがないか確認：
```
WARNING - 必須フィールド不足: code
WARNING - 無効な証券コード: ABC
WARNING - 無効な権利確定月: 13
```

**解決策:**
- セレクターが正しいか確認
- HTML構造が想定と異なる可能性

### 問題: 古いデータが表示される

**原因:** データベースにキャッシュされています

**解決策:**
```python
from src.core.database import DatabaseManager

db = DatabaseManager()
db.execute("DELETE FROM simulation_cache")
```

## ベストプラクティス

### 1. マネージャーを使用する

個別のスクレイパーではなく、`ScraperManager` を使用することを推奨します。フォールバック機能により、1つのソースが失敗しても他のソースから取得できます。

### 2. セッションを適切にクローズ

```python
manager = ScraperManager()
try:
    stocks = manager.scrape_with_fallback()
finally:
    manager.close_all()  # 必ずクローズ
```

### 3. エラーハンドリング

```python
try:
    stocks = manager.scrape_with_fallback(month=3)
except Exception as e:
    logging.error(f"スクレイピングエラー: {e}")
    # フォールバック処理
    stocks = []
```

### 4. データ検証

取得したデータは自動的に検証されますが、追加の検証を行うこともできます：

```python
valid_stocks = [
    stock for stock in stocks
    if len(stock.get('name', '')) > 0 and
       1 <= stock.get('rights_month', 0) <= 12
]
```

## パフォーマンス最適化

### 特定の月のみ取得

全月ではなく、必要な月のみ取得すると高速です：

```python
# 3月のみ
stocks = manager.scrape_with_fallback(month=3)

# 全月（遅い）
stocks = manager.scrape_with_fallback()
```

### 並列処理

複数の月を並列で取得：

```python
from concurrent.futures import ThreadPoolExecutor

def scrape_month(month):
    manager = ScraperManager()
    stocks = manager.scrape_with_fallback(month=month)
    manager.close_all()
    return stocks

with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(scrape_month, [3, 6, 9, 12]))

all_stocks = []
for stocks in results:
    all_stocks.extend(stocks)
```

## 高度な使用例

### カスタムスクレイパーの作成

```python
from src.scrapers import BaseScraper

class MyCustomScraper(BaseScraper):
    def get_site_name(self) -> str:
        return "my_site"

    def get_base_url(self) -> str:
        return "https://mysite.com"

    def scrape_stocks(self, **kwargs) -> List[Dict[str, Any]]:
        url = f"{self.get_base_url()}/yuutai"
        soup = self.fetch_page(url)

        if not soup:
            return []

        stocks = []
        rows = soup.select("table.yuutai tr")

        for row in rows:
            stock = self._parse_row(row)
            if stock and self.validate_stock_data(stock):
                stocks.append(stock)

        return stocks

    def _parse_row(self, row):
        # パース処理
        pass

# 使用
scraper = MyCustomScraper()
stocks = scraper.scrape_stocks()
scraper.close()
```

## まとめ

✅ `ScraperManager` を使用してフォールバック機能を活用
✅ `selectors.json` を編集してサイト構造変更に対応
✅ テストスクリプトで動作確認
✅ セッションを適切にクローズ
✅ エラーログを確認して問題を早期発見

詳細なアーキテクチャについては、`docs/SCRAPING_ARCHITECTURE.md` を参照してください。
