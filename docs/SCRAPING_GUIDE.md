# スクレイピングガイド

## 概要

優待情報サイトから銘柄データをスクレイピングして取得する方法を説明します。

**重要:** 多くの優待サイトは動的コンテンツ（JavaScript）を使用しています。Seleniumを使用した方法を推奨します。

## 前提条件

### 方法1: Selenium（推奨）

動的サイトに対応、ブラウザ自動操作で確実にデータ取得

```bash
pip install selenium webdriver-manager
```

### 方法2: BeautifulSoup（シンプルな静的サイト用）

```bash
pip install requests beautifulsoup4 lxml
```

## 推奨される方法：Selenium版

### Yahoo!ファイナンスからスクレイピング（最も確実）

```bash
# 3月の優待銘柄を取得
python scripts/scrape_yahoo_yuutai.py --month 3 --output data/yahoo_yuutai.csv

# 全月の銘柄を取得
python scripts/scrape_yahoo_yuutai.py --output data/yahoo_yuutai.csv

# ブラウザを表示して動作確認（デバッグ用）
python scripts/scrape_yahoo_yuutai.py --month 3 --show-browser
```

**メリット:**
- Yahoo!ファイナンスは信頼性が高い
- データが正確で最新
- Selenium対応で動的コンテンツも取得可能

### 96ut.com Selenium版

```bash
# 3月の優待銘柄を取得
python scripts/scrape_yuutai_selenium.py --month 3 --output data/scraped_yuutai.csv

# 全月の銘柄を取得
python scripts/scrape_yuutai_selenium.py --output data/scraped_yuutai.csv

# ブラウザを表示して動作確認
python scripts/scrape_yuutai_selenium.py --month 3 --show-browser
```

## 基本的な使い方（BeautifulSoup版 - 非推奨）

**注意:** 多くのサイトは動的コンテンツを使用しているため、この方法では取得できない場合があります。

### 1. 96ut.comから全銘柄を取得

```bash
python scripts/scrape_yuutai_data.py --site 96ut --output data/scraped_yuutai.csv
```

- 全12ヶ月分の優待銘柄を取得
- 出力: `data/scraped_yuutai.csv`

### 2. 特定の月のみ取得

```bash
python scripts/scrape_yuutai_data.py --site 96ut --month 3 --output data/march_yuutai.csv
```

- 3月の権利確定銘柄のみ取得
- `--month` オプションで1-12の月を指定

### 3. リクエスト間隔を調整

```bash
python scripts/scrape_yuutai_data.py --site 96ut --delay 2.0
```

- `--delay` オプションでリクエスト間隔を秒単位で指定（デフォルト: 1.0秒）
- サーバーへの負荷を考慮して適切な間隔を設定

## 対応サイト

### 96ut.com（推奨）

**特徴:**
- シンプルなHTML構造
- 月別リストが利用可能
- スクレイピングが比較的容易

**取得できるデータ:**
- 銘柄コード
- 銘柄名
- 権利確定月
- 優待内容
- 優待ジャンル

**使用例:**
```bash
python scripts/scrape_yuutai_data.py --site 96ut --month 12
```

### yutai.net-ir.ne.jp（実験的）

**注意:**
- 動的コンテンツ（JavaScript）を使用
- APIエンドポイントの特定が必要
- 現在のスクリプトは基本的な静的HTMLのみ対応

**改善が必要:**
このサイトから完全なデータを取得するには、以下のいずれかの方法が必要です：

1. **Seleniumを使用** - ブラウザを自動操作
2. **APIエンドポイントを特定** - JSONデータを直接取得

詳細は「高度なスクレイピング」セクションを参照。

## 取得後のワークフロー

### 1. スクレイピング実行

```bash
python scripts/scrape_yuutai_data.py --site 96ut --output data/scraped_yuutai.csv
```

### 2. データ確認

```bash
# CSVファイルの内容を確認
type data\scraped_yuutai.csv
```

または、Excelで開いて内容を確認・編集。

### 3. アプリにインポート

1. アプリを起動
2. 「ファイル」→「CSVから銘柄をインポート」（Ctrl+I）
3. `data/scraped_yuutai.csv` を選択
4. 「インポート開始」をクリック

### 4. バックテスト実行

- 銘柄を選択すると自動的にバックテスト実行
- または「ツール」→「データ更新」で一括実行

## トラブルシューティング

### Q1: スクレイピングが失敗する

**原因:**
- サイトの構造が変更された
- ネットワーク接続の問題
- サーバーがアクセスをブロック

**対処法:**
1. インターネット接続を確認
2. `--delay` オプションで間隔を長くする（例: `--delay 3.0`）
3. サイトの構造が変更されていないかブラウザで確認
4. スクリプトを最新版に更新

### Q2: データが空またはおかしい

**原因:**
- HTML構造の変更
- パース処理のエラー

**対処法:**
1. エラーメッセージを確認
2. 出力CSVファイルを開いて内容を確認
3. サイトをブラウザで開いて構造を確認
4. スクリプトのパース処理を調整（詳細は「カスタマイズ」セクション）

### Q3: 取得が遅い

**原因:**
- デフォルトの`--delay`が1秒に設定されている
- 12ヶ月分のデータを取得する場合は時間がかかる

**対処法:**
1. 特定の月のみ取得: `--month 3`
2. delayを短くする（推奨しません）: `--delay 0.5`

**注意:** サーバーへの負荷を考慮して、過度に短い間隔は避けてください。

### Q4: 「403 Forbidden」エラー

**原因:**
- サーバーがスクレイピングをブロック
- User-Agentが拒否された

**対処法:**
1. `--delay`を長くする（例: `--delay 3.0`）
2. 手動でブラウザからデータを取得してCSVに保存
3. 証券会社のデータを代わりに使用（`REAL_DATA_GUIDE.md`参照）

## 高度なスクレイピング

### Seleniumを使用した動的コンテンツの取得

動的にJavaScriptで生成されるコンテンツを取得する場合、Seleniumが有効です。

**インストール:**
```bash
pip install selenium webdriver-manager
```

**サンプルコード:**
```python
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# Chromeドライバーを自動セットアップ
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

# ページにアクセス
driver.get("https://yutai.net-ir.ne.jp/search/")

# JavaScriptの実行完了を待つ
driver.implicitly_wait(10)

# 要素を取得
stocks = driver.find_elements(By.CLASS_NAME, "stock-item")

for stock in stocks:
    code = stock.find_element(By.CLASS_NAME, "code").text
    name = stock.find_element(By.CLASS_NAME, "name").text
    print(f"{code}: {name}")

driver.quit()
```

### APIエンドポイントの特定方法

多くの動的サイトはバックグラウンドでJSONデータを取得しています。

**手順:**

1. **ブラウザの開発者ツールを開く**
   - Chrome: F12キー
   - 「Network」タブを選択

2. **ページをリロード**
   - Ctrl+R

3. **XHR/Fetchフィルタを適用**
   - JSONデータのリクエストを探す

4. **エンドポイントをコピー**
   - リクエストURLとパラメータを確認

5. **Pythonで直接アクセス**
   ```python
   import requests

   url = "https://example.com/api/stocks"
   params = {'month': 3, 'limit': 100}

   response = requests.get(url, params=params)
   data = response.json()

   for stock in data['results']:
       print(f"{stock['code']}: {stock['name']}")
   ```

## カスタマイズ

スクリプトをカスタマイズしてサイト構造の変更に対応できます。

### パース処理の変更例

`scripts/scrape_yuutai_data.py` の `Ut96Scraper.scrape()` メソッド:

```python
# テーブルのセレクタを変更
table = soup.find('table', class_='stock-list')  # クラス名を追加

# カラムのインデックスを調整
code = cols[0].get_text(strip=True)  # 1列目
name = cols[1].get_text(strip=True)  # 2列目
yuutai_content = cols[3].get_text(strip=True)  # 4列目に変更
```

### 新しいサイトのスクレイパー追加

```python
class NewSiteScraper(YuutaiScraper):
    """新しいサイトのスクレイパー"""

    BASE_URL = "https://example.com/yuutai/"

    def scrape(self, month: Optional[int] = None) -> List[Dict]:
        stocks = []

        # ページを取得
        soup = self.fetch_page(self.BASE_URL)

        # パース処理を実装
        # ...

        return stocks
```

## 倫理的な考慮事項

スクレイピングを行う際は以下の点に注意してください：

1. **robots.txtを確認**
   - サイトのルールを尊重する
   - 禁止されている場合はスクレイピングしない

2. **適切な間隔を設ける**
   - サーバーへの負荷を考慮
   - 最低でも1秒以上の間隔を設ける

3. **User-Agentを設定**
   - 自分が誰であるかを明示
   - 連絡先を含めることが推奨される

4. **利用規約を確認**
   - サイトの利用規約でスクレイピングが禁止されていないか確認

5. **商用利用の注意**
   - データの商用利用が許可されているか確認

## 代替手段

スクレイピングが困難な場合、以下の代替手段があります：

1. **手動でのCSV作成**
   - `REAL_DATA_GUIDE.md`参照
   - 証券会社のデータを利用

2. **公式APIの利用**
   - 一部の証券会社はAPI提供
   - SBI証券、楽天証券など

3. **主要銘柄テンプレート**
   ```bash
   python scripts/create_yuutai_csv_template.py
   ```

## まとめ

スクレイピングの要点：

1. ✅ **96ut.comが推奨** - シンプルで取得しやすい
2. ✅ **適切な間隔を設ける** - サーバーへの配慮
3. ✅ **データを必ず確認** - 不正確なデータに注意
4. ✅ **代替手段を検討** - スクレイピングが困難な場合
5. ✅ **倫理的に実施** - robots.txtと利用規約を尊重

---

**最終更新**: 2025-11-07
**バージョン**: 1.0.0
