# スクレイピング機能アーキテクチャ

## 概要

Yuutai Event Investor のスクレイピング機能は、保守性と独立性を重視した設計になっています。サイト構造の変更に柔軟に対応できるよう、以下の設計原則に従っています。

## 設計原則

### 1. 抽象基底クラスによる共通インターフェース

`BaseScraper` 抽象基底クラスを継承することで、全スクレイパーが統一的なインターフェースを持ちます。

```python
from src.scrapers import BaseScraper

class MyScraper(BaseScraper):
    def get_site_name(self) -> str:
        return "my_site"

    def get_base_url(self) -> str:
        return "https://example.com"

    def scrape_stocks(self, **kwargs) -> List[Dict[str, Any]]:
        # スクレイピング実装
        pass
```

### 2. セレクター外部化

サイト構造の変更に対応するため、CSSセレクターは `selectors.json` ファイルに外部化されています。

**src/scrapers/selectors.json**:
```json
{
  "my_site": {
    "stock_rows": [
      "table.yuutai-list tr",
      "div.stock-item",  // フォールバック
      "tr.stock-row"     // 第2フォールバック
    ],
    "code": [
      "td.code a",
      "span.code"
    ]
  }
}
```

サイト構造が変更された場合、**コードを変更せず** JSON ファイルのセレクターを更新するだけで対応できます。

### 3. 複数セレクター試行

`try_selectors()` メソッドは、複数のセレクターを順番に試行します：

```python
# 複数のセレクターを自動的に試行
rows = self.try_selectors(soup, "stock_rows", method='select')
```

最初のセレクターが失敗しても、フォールバックセレクターが自動的に試されます。

### 4. リトライ機構

ネットワークエラーなどの一時的な問題に対処するため、自動リトライ機能を実装しています：

```python
# 最大3回まで自動リトライ
soup = self.fetch_page(url, retries=0)
```

### 5. スクレイパーマネージャー

`ScraperManager` は複数のスクレイパーを統合管理し、以下の機能を提供します：

- **フォールバック戦略**: 1つのスクレイパーが失敗しても次を試行
- **データ統合**: 複数ソースからデータを取得して重複除去
- **優先順位管理**: より信頼性の高いソースを優先

```python
from src.scrapers import ScraperManager

manager = ScraperManager()

# フォールバック戦略（最初に成功したソースを使用）
stocks = manager.scrape_with_fallback(month=3)

# 全ソースから取得して統合
stocks = manager.scrape_all(month=3)
```

## ディレクトリ構造

```
src/scrapers/
├── __init__.py                  # パッケージ初期化
├── base_scraper.py              # 抽象基底クラス
├── scraper_96ut.py              # 96ut.com スクレイパー
├── scraper_yutai_net.py         # yutai.net-ir.ne.jp スクレイパー
├── scraper_manager.py           # スクレイパーマネージャー
└── selectors.json               # CSSセレクター設定（外部化）
```

## 使用方法

### 基本的な使用例

```python
from src.scrapers import ScraperManager

# マネージャーを初期化
manager = ScraperManager()

# 3月の銘柄を取得（フォールバック戦略）
stocks = manager.scrape_with_fallback(month=3)

for stock in stocks:
    print(f"{stock['code']} - {stock['name']}")
    print(f"  権利確定: {stock['rights_month']}月")
    print(f"  優待内容: {stock['yuutai_content']}")

# 終了時にセッションをクローズ
manager.close_all()
```

### 特定のソースからのみ取得

```python
from src.scrapers import Scraper96ut, ScraperYutaiNet

# 96ut.com から取得
scraper = Scraper96ut()
stocks = scraper.scrape_stocks(term="3月末")
scraper.close()

# yutai.net-ir.ne.jp から取得
scraper = ScraperYutaiNet()
stocks = scraper.scrape_stocks(month=3)
scraper.close()
```

### テストスクリプトの使用

```bash
# マネージャーを使用（フォールバック戦略）
python scripts/test_scraper.py

# 96ut.com を個別にテスト
python scripts/test_scraper.py --source 96ut --month 3

# yutai.net-ir.ne.jp を個別にテスト
python scripts/test_scraper.py --source yutai_net --month 12

# 全ソースからデータ取得
python scripts/test_scraper.py --all
```

## サイト構造変更への対応方法

### ステップ1: 問題の確認

スクレイピングが失敗した場合、ログを確認します：

```
WARNING - 全セレクターが失敗: stock_rows
WARNING - テーブル行が見つかりません: https://example.com
```

### ステップ2: 新しいセレクターを特定

ブラウザの開発者ツールでHTMLを調査し、新しいセレクターを特定します。

### ステップ3: selectors.json を更新

```json
{
  "96ut": {
    "stock_rows": [
      "table.new-class tr",        // 新しいセレクター
      "table.yuutai-list tr",      // 旧セレクター（フォールバック）
      "div.stock-item"
    ]
  }
}
```

### ステップ4: テスト

```bash
python scripts/test_scraper.py --source 96ut --month 3
```

## エラーハンドリング

### ログレベル

- **INFO**: 正常な動作（取得件数、開始/終了）
- **WARNING**: 非致命的な問題（セレクター失敗、データ不足）
- **ERROR**: 致命的なエラー（ネットワーク障害、パースエラー）

### リトライ戦略

1. **自動リトライ**: ネットワークエラーは最大3回まで自動リトライ
2. **スクレイパーフォールバック**: 1つのスクレイパーが失敗しても他を試行
3. **セレクターフォールバック**: 複数のCSSセレクターを順番に試行

## データ検証

`validate_stock_data()` メソッドは以下をチェックします：

- 必須フィールドの存在（code, name, rights_month）
- 証券コードの形式（4桁の数字）
- 権利確定月の範囲（1-12）

不正なデータは自動的にフィルタリングされます。

## パフォーマンス考慮事項

### セッション再利用

`requests.Session()` を使用して、HTTPコネクションを再利用します。

### リトライ遅延

サーバー負荷を考慮し、リトライ時は2秒間待機します。

### データキャッシュ

重複データは自動的に除去されます（証券コード + 権利確定月で判定）。

## セキュリティ考慮事項

### User-Agent設定

適切な User-Agent ヘッダーを設定し、通常のブラウザとして振る舞います。

### リクエスト頻度

過度なリクエストを避けるため、リトライ間隔を設ける必要があります。

## 今後の拡張性

### 新しいスクレイパーの追加

1. `BaseScraper` を継承
2. 必須メソッドを実装
3. `selectors.json` にセレクター追加
4. `ScraperManager` に登録

```python
# src/scrapers/scraper_new_site.py
from .base_scraper import BaseScraper

class ScraperNewSite(BaseScraper):
    def get_site_name(self) -> str:
        return "new_site"

    def get_base_url(self) -> str:
        return "https://newsite.com"

    def scrape_stocks(self, **kwargs) -> List[Dict[str, Any]]:
        # 実装
        pass

# src/scrapers/scraper_manager.py に追加
self.scrapers['new_site'] = ScraperNewSite(config_path)
self.priority = ['new_site', 'yutai_net', '96ut']
```

## トラブルシューティング

### よくある問題

**Q: 「全セレクターが失敗」エラーが出る**
A: サイト構造が変更されています。`selectors.json` を更新してください。

**Q: データが取得できない**
A:
1. ネットワーク接続を確認
2. サイトがアクセス可能か確認
3. ログを確認してエラー内容を特定

**Q: 古いデータが表示される**
A: データベースのキャッシュをクリアしてください：
```sql
DELETE FROM simulation_cache;
```

## まとめ

このアーキテクチャにより：

✅ **保守性**: セレクター変更時はJSONファイルのみ編集
✅ **独立性**: 各スクレイパーは独立して動作
✅ **柔軟性**: フォールバック戦略で堅牢性を確保
✅ **拡張性**: 新しいスクレイパーを簡単に追加
✅ **テスト容易性**: 各スクレイパーを個別にテスト可能

サイト構造の変更に対して、コード変更を最小限に抑えながら柔軟に対応できます。
