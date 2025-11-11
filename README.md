# Yuutai Event Investor 📈

> 株主優待イベント投資の最適タイミングを予測・分析するデスクトップアプリケーション

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/PySide6-latest-green.svg)](https://pypi.org/project/PySide6/)

---

## 📋 概要

**Yuutai Event Investor** は、株主優待の権利確定日を利用したイベント投資において、最適な買入タイミングを予測・分析するためのデスクトップアプリケーションです。過去の株価データから統計的に最も勝率が高く、期待リターンが大きいタイミングを自動計算します。

### 主な機能

- 🎯 **最適買入日の自動計算**: 約6ヶ月前（120営業日前）から1日前までの全期間をスキャンし、最適なタイミングを提示
- 📊 **詳細なバックテスト分析**: 勝率、期待リターン、平均リターン、最大損失などを計算
- 🔍 **柔軟な検索・フィルター**: 権利確定月、勝率、期待リターン、投資金額などで絞り込み
- 📈 **視覚的なチャート表示**: 折れ線グラフ、棒グラフ、散布図で分析結果を可視化
- ⭐ **ウォッチリスト機能**: 気になる銘柄を登録して優先表示
- 🔔 **買いタイミング通知**: 最適買入日が近づいたら自動通知
- 💾 **データエクスポート**: CSV出力、スクリーンショット保存、設定の共有

---

## 🎥 スクリーンショット

*Coming soon...*

---

## 🚀 クイックスタート

### 必要要件

- Python 3.10 以上
- Windows 10/11（macOS, Linuxでも動作可能）

### インストール

#### 方法1: 実行ファイルから（推奨）

1. [Releases](https://github.com/yourusername/yuutai_event_investor/releases) から最新版をダウンロード
2. ZIPファイルを解凍
3. `YuutaiEventInvestor.exe` を実行

#### 方法2: ソースコードから

```bash
# リポジトリをクローン
git clone https://github.com/yourusername/yuutai_event_investor.git
cd yuutai_event_investor

# 仮想環境を作成（推奨）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存パッケージをインストール
pip install -r requirements.txt

# アプリケーションを起動
python main.py
```

---

## 📖 使い方

### 1. 初回起動時 - データ取得

初回起動時は、優待銘柄データを取得する必要があります。以下の2つの方法があります：

#### 方法A: スクリプトから取得（推奨）

```bash
# 全月の優待銘柄を取得してデータベースに保存
python scripts/fetch_all_yuutai_stocks.py

# 特定月のみ取得（例: 3月）
python scripts/fetch_all_yuutai_stocks.py --month 3

# CSVに出力してから内容を確認したい場合
python scripts/export_yuutai_to_csv.py --output data/yuutai_stocks.csv
```

**データソース**:
- 主要ソース: [kabuyutai.com](https://www.kabuyutai.com) （最も信頼性が高い）
- フォールバックソース: [yutai.net-ir.ne.jp](https://yutai.net-ir.ne.jp/), [96ut.com](https://96ut.com/yuutai/)

**取得時間の目安**:
- 全月取得: 約5-10分（1500件程度）
- 特定月取得: 約30秒-2分（100-400件程度）

#### 方法B: アプリから取得

1. アプリを起動して、メニューバーの「データ更新」ボタンをクリック
2. スクレイピングが完了するまで待機（約5-10分）
3. データ更新完了後、銘柄リストが表示されます

### 2. 銘柄の検索とフィルター

- **権利確定月で絞り込み**: 「3月優待」「9月優待」など
- **勝率・期待リターンで絞り込み**: スライダーで範囲指定
- **投資金額で絞り込み**: 上限金額を設定
- **並び替え**: 勝率順、期待リターン順など

### 3. 個別銘柄の詳細分析

1. 銘柄リストから銘柄をクリック
2. 右側の詳細パネルに以下が表示されます：
   - 銘柄情報カード（推奨買入日、勝率、期待リターン）
   - 期待リターン推移グラフ
   - 勝率の棒グラフ
   - 過去の勝ち負けトレード散布図
   - 詳細統計テーブル

### 4. ウォッチリストの活用

1. 気になる銘柄を右クリック → 「ウォッチリストに追加」
2. ウォッチリストタブで一覧表示
3. 最適買入日が近づくと自動通知

### 5. データのエクスポート

- **CSV出力**: 銘柄リストやシミュレーション結果をCSVファイルで保存
- **スクリーンショット**: 現在の画面を画像として保存
- **設定のエクスポート**: 設定をJSON形式で保存し、他のPCと共有

---

## 🏗️ プロジェクト構造

```
yuutai_event_investor/
├── main.py                          # エントリーポイント
├── requirements.txt                 # 依存パッケージ
├── README.md                        # 本ファイル
├── config/
│   ├── settings.json               # ユーザー設定
│   └── theme_config.json           # テーマ設定
├── data/
│   ├── yuutai.db                   # SQLiteデータベース
│   ├── create_tables.sql           # データベーススキーマ
│   └── optimize_database.sql       # DB最適化クエリ
├── docs/
│   ├── requirements.md             # 要求定義書
│   ├── database_schema.md          # DB設計書
│   ├── roadmap.md                  # 開発ロードマップ
│   ├── SCRAPING_ARCHITECTURE.md    # スクレイピング設計書
│   ├── SCRAPING_USAGE.md           # スクレイピング使用方法
│   └── YUUTAI_DATA_UPDATE.md       # データ更新ガイド
├── scripts/
│   ├── init_database.py            # DB初期化スクリプト
│   ├── fetch_all_yuutai_stocks.py  # 優待データ一括取得
│   ├── export_yuutai_to_csv.py     # CSV出力（DB保存なし）
│   ├── run_all_backtests.py        # 全銘柄バックテスト実行
│   └── test_backtest.py            # バックテストテスト
├── src/
│   ├── ui/                         # UI関連
│   │   ├── main_window_v3.py      # メインウィンドウ（現行版）
│   │   └── widgets/               # UIコンポーネント
│   ├── core/                       # コア機能
│   │   ├── calculator.py          # バックテスト計算エンジン
│   │   ├── database.py            # データベースマネージャー
│   │   └── data_fetcher.py        # 株価データ取得
│   ├── scrapers/                   # スクレイピングモジュール
│   │   ├── base_scraper.py        # 基底スクレイパークラス
│   │   ├── scraper_kabuyutai.py   # kabuyutai.com対応
│   │   ├── scraper_96ut.py        # 96ut.com対応
│   │   ├── scraper_yutai_net.py   # yutai.net-ir.ne.jp対応
│   │   ├── scraper_manager.py     # スクレイパー統合管理
│   │   └── selectors.json         # CSSセレクター設定
│   └── utils/                      # ユーティリティ
├── resources/                      # リソースファイル
└── tests/                          # テストコード
```

---

## 🛠️ 技術スタック

### フロントエンド
- **PySide6**: Qt6ベースのUIフレームワーク
- **QFluentWidgets**: モダンなUIコンポーネント
- **qdarktheme**: ダーク/ライトテーマの自動切替

### バックエンド
- **Python 3.10+**: プログラミング言語
- **SQLite3**: ローカルデータベース
- **pandas**: データ処理
- **yfinance**: 株価データ取得
- **BeautifulSoup4**: Webスクレイピング

### データ可視化
- **matplotlib**: チャート描画

### 配布
- **PyInstaller**: 実行ファイル作成（将来的にNuitkaへ移行予定）

---

## 📚 ドキュメント

詳細なドキュメントは `docs/` ディレクトリに格納されています：

### プロジェクト全般
- [要求定義書](docs/requirements.md) - プロジェクトの仕様と要件
- [データベース設計書](docs/database_schema.md) - DB構造とテーブル定義
- [開発ロードマップ](docs/roadmap.md) - 開発計画とマイルストーン

### データ取得・スクレイピング
- [データ更新ガイド](docs/YUUTAI_DATA_UPDATE.md) - 優待銘柄データの取得・更新方法
- [スクレイピング設計書](docs/SCRAPING_ARCHITECTURE.md) - スクレイピングシステムのアーキテクチャ
- [スクレイピング使用方法](docs/SCRAPING_USAGE.md) - 各スクレイパーの詳細な使い方とトラブルシューティング

---

## 🤝 コントリビューション

コントリビューションは大歓迎です！以下の手順でご参加ください：

1. このリポジトリをフォーク
2. フィーチャーブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add some amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

---

## ⚠️ 免責事項

本アプリケーションは教育・研究目的で提供されています。実際の投資判断においては、本アプリケーションの分析結果のみに依存せず、ご自身の責任で行ってください。本アプリケーションの使用によって生じたいかなる損失についても、開発者は一切の責任を負いません。

- 過去の実績は将来の結果を保証するものではありません
- 株式投資には元本割れのリスクがあります
- 投資判断は自己責任で行ってください

---

## 🔮 将来の拡張機能

現在は**株主優待銘柄**のみをサポートしていますが、**高配当銘柄**（配当利回り3%以上など）も同様のバックテスト手法で分析可能です。

詳細は [docs/FUTURE_FEATURES.md](docs/FUTURE_FEATURES.md) をご覧ください：
- データベーススキーマ拡張済み
- CSVインポート用テンプレート準備済み
- `kenrlast`設定による将来の制度変更対応

---

## 📄 ライセンス

本プロジェクトは MIT ライセンスの下で公開されています。詳細は [LICENSE](LICENSE) ファイルをご覧ください。

---

## 🙏 謝辞

本プロジェクトは以下のリソースを参考にしています：

- 優待データ提供: [kabuyutai.com](https://www.kabuyutai.com) （主要データソース）
- 優待データ提供: [yutai.net-ir.ne.jp](https://yutai.net-ir.ne.jp/)
- 優待データ提供: [96ut.com](https://96ut.com/yuutai/)
- 株価データ: [yfinance](https://github.com/ranaroussi/yfinance)

---

## 📬 お問い合わせ

質問や提案がある場合は、[Issues](https://github.com/yourusername/yuutai_event_investor/issues) にてお気軽にお知らせください。

---

## 🔄 更新履歴

### Version 1.1.0 (2025-11-07)
- スクレイピング機能の大幅強化
  - 3つの優待情報サイトに対応（kabuyutai.com、yutai.net-ir.ne.jp、96ut.com）
  - 抽象基底クラスによる拡張性の高い設計
  - 外部設定ファイル（selectors.json）によるメンテナンス性向上
  - フォールバック戦略による高い信頼性
  - CSV出力スクリプト追加（DB保存前にデータ確認可能）
- ドキュメント拡充
  - データ更新ガイド追加
  - スクレイピングアーキテクチャドキュメント追加
  - スクレイピング使用方法ガイド追加

### Version 1.0.0 (未リリース)
- 初回リリース
- 基本機能実装
  - 銘柄リスト表示・ソート
  - 最適買入日の自動計算
  - 詳細分析機能
  - フィルター機能
  - ウォッチリスト
  - 通知機能
  - データエクスポート

---

<div align="center">
  <p>Made with ❤️ for イベント投資家</p>
</div>
