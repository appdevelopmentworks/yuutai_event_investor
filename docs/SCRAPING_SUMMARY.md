# スクレイピング機能まとめ

## 作成したスクリプト

優待データを取得するための3つのスクレイピングスクリプトを用意しました。

### 1. `scripts/scrape_yahoo_yuutai.py` ⭐推奨

**対象サイト:** Yahoo!ファイナンス 株主優待検索
**技術:** Selenium（ブラウザ自動操作）

**特徴:**
- 最も信頼性が高い
- データが正確で最新
- 動的コンテンツに対応

**使い方:**
```bash
# Seleniumをインストール
pip install selenium webdriver-manager

# 3月の優待銘柄を取得
python scripts/scrape_yahoo_yuutai.py --month 3 --output data/yahoo_yuutai.csv

# 全月の銘柄を取得
python scripts/scrape_yahoo_yuutai.py --output data/yahoo_yuutai.csv

# デバッグ（ブラウザを表示）
python scripts/scrape_yahoo_yuutai.py --month 3 --show-browser
```

**メリット:**
- ✅ Yahoo!は日本最大の金融情報サイト
- ✅ データの信頼性が高い
- ✅ 検索機能が充実
- ✅ 動的コンテンツもしっかり取得

**デメリット:**
- ❌ Seleniumのインストールが必要
- ❌ 実行に時間がかかる（ブラウザ起動のため）

---

### 2. `scripts/scrape_yuutai_selenium.py`

**対象サイト:** 96ut.com
**技術:** Selenium（ブラウザ自動操作）

**特徴:**
- 動的コンテンツに対応
- 複数のHTML構造パターンに対応
- デバッグ機能付き（ページソース保存）

**使い方:**
```bash
# 3月の優待銘柄を取得
python scripts/scrape_yuutai_selenium.py --month 3 --output data/scraped_yuutai.csv

# 全月の銘柄を取得
python scripts/scrape_yuutai_selenium.py --output data/scraped_yuutai.csv

# デバッグ（ブラウザを表示）
python scripts/scrape_yuutai_selenium.py --month 3 --show-browser
```

**メリット:**
- ✅ 96ut.comは優待専門サイト
- ✅ 動的コンテンツに対応
- ✅ デバッグ機能でトラブルシューティングが容易

**デメリット:**
- ❌ サイト構造の変更に影響されやすい
- ❌ Seleniumのインストールが必要

---

### 3. `scripts/scrape_yuutai_data.py`

**対象サイト:** 96ut.com, yutai.net-ir.ne.jp
**技術:** BeautifulSoup（軽量スクレイピング）

**特徴:**
- シンプルで軽量
- 静的HTMLに対応
- インストールが簡単

**使い方:**
```bash
# 必要なライブラリをインストール
pip install requests beautifulsoup4 lxml

# 96ut.comから取得
python scripts/scrape_yuutai_data.py --site 96ut --month 3 --output data/scraped.csv

# リクエスト間隔を調整
python scripts/scrape_yuutai_data.py --site 96ut --month 3 --delay 2.0
```

**メリット:**
- ✅ 軽量で高速
- ✅ インストールが簡単
- ✅ サーバー負荷が少ない

**デメリット:**
- ❌ 動的コンテンツに非対応
- ❌ JavaScriptで生成されるデータは取得できない
- ❌ **現在、多くのサイトは動的コンテンツを使用しているため機能しない可能性が高い**

---

## 推奨される使い方

### 初めての方

**ステップ1:** Yahoo!ファイナンス版を使う

```bash
# Seleniumをインストール
pip install selenium webdriver-manager

# 3月の優待銘柄を取得
python scripts/scrape_yahoo_yuutai.py --month 3 --output data/yahoo_yuutai.csv
```

**ステップ2:** データを確認

```bash
# Excelで開いて確認
start data/yahoo_yuutai.csv
```

**ステップ3:** アプリにインポート

1. アプリを起動: `python main.py`
2. メニュー → 「ファイル」→「CSVから銘柄をインポート」（Ctrl+I）
3. `data/yahoo_yuutai.csv` を選択

---

### 上級者向け

複数のソースからデータを取得して比較・統合

```bash
# Yahoo!から取得
python scripts/scrape_yahoo_yuutai.py --month 3 --output data/yahoo_3.csv

# 96ut.comから取得
python scripts/scrape_yuutai_selenium.py --month 3 --output data/96ut_3.csv

# 2つのCSVを比較して確認
# Excelで開いて重複削除・統合
```

---

## トラブルシューティング

### Q1: "Seleniumがインストールされていません"

```bash
pip install selenium webdriver-manager
```

### Q2: "ブラウザの起動に失敗しました"

**原因:** ChromeDriverが見つからない、またはChromeがインストールされていない

**対処法:**
1. Google Chromeをインストール
2. `webdriver-manager` が自動でChromeDriverをダウンロード
3. それでも失敗する場合は `--show-browser` で動作確認

### Q3: "データを取得できませんでした"

**対処法:**

1. **ブラウザを表示してデバッグ**
   ```bash
   python scripts/scrape_yahoo_yuutai.py --month 3 --show-browser
   ```

2. **サイト構造が変更されていないか確認**
   - ブラウザで直接サイトにアクセス
   - データが表示されるか確認

3. **代替手段を使用**
   - 手動でCSV作成（`REAL_DATA_GUIDE.md`参照）
   - テンプレートCSV使用（`create_yuutai_csv_template.py`）

### Q4: エラーメッセージが大量に出る

**原因:** HTML構造が想定と異なる

**対処法:**
1. `debug_page_*.html` ファイルを確認（自動生成）
2. スクリプトのセレクタを調整（カスタマイズ必要）
3. 代替スクリプトを試す

---

## 代替手段

スクレイピングが困難な場合：

### 1. テンプレートCSVを使用

```bash
python scripts/create_yuutai_csv_template.py
```

13件の主要優待銘柄が含まれるCSVを生成

### 2. 手動でCSV作成

`REAL_DATA_GUIDE.md` を参照して、証券会社のデータから手動でCSVを作成

### 3. 既存のCSVを編集

```bash
# テンプレートをコピー
copy data\major_yuutai_stocks.csv data\my_stocks.csv

# Excelで編集
start data\my_stocks.csv
```

---

## 倫理的な考慮事項

スクレイピングを行う際の注意点：

1. ✅ **robots.txtを確認** - サイトのルールを尊重
2. ✅ **適切な間隔を設ける** - サーバー負荷を考慮（最低1秒）
3. ✅ **個人利用の範囲内** - 商用利用は利用規約を確認
4. ✅ **データの正確性を確認** - スクレイピングデータは必ず検証
5. ❌ **過度なリクエストを避ける** - サーバーに負荷をかけない

---

## まとめ

### 推奨される順序

1. **Yahoo!ファイナンス版** (`scrape_yahoo_yuutai.py`) - 最も確実
2. **96ut.com Selenium版** (`scrape_yuutai_selenium.py`) - 代替手段
3. **手動CSV作成** - 最も確実だが手間がかかる

### インストールコマンド

```bash
# Selenium版を使う場合（推奨）
pip install selenium webdriver-manager

# BeautifulSoup版を使う場合
pip install requests beautifulsoup4 lxml

# 両方インストール
pip install -r requirements.txt
```

### クイックスタート

```bash
# 1. Seleniumをインストール
pip install selenium webdriver-manager

# 2. Yahoo!から3月の優待銘柄を取得
python scripts/scrape_yahoo_yuutai.py --month 3 --output data/yuutai.csv

# 3. アプリを起動してインポート
python main.py
# メニュー → ファイル → CSVから銘柄をインポート → data/yuutai.csv
```

---

**最終更新:** 2025-11-07
**作成者:** Yuutai Event Investor Team
