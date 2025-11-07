# 📝 Changelog

All notable changes to the Yuutai Event Investor project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2025-11-07

### 🎉 初回リリース

株主優待イベント投資の最適タイミング分析ツール「Yuutai Event Investor」の最初のリリースです。

### ✨ 追加された機能

#### コア機能
- **バックテストエンジン**: 過去10年分のデータを使用した最適買入日の自動計算
- **期待値計算**: 勝率と平均リターンに基づく期待リターンの算出
- **権利付最終日判定**: 権利確定日から営業日ベースで自動計算
- **120日分シミュレーション**: 1日前～120日前までの全パターン分析

#### UI機能
- **3ペイン レイアウト**: フィルターパネル、銘柄リスト、詳細分析の効率的な配置
- **銘柄リスト表示**: ソート・フィルタリング対応の一覧表示
- **詳細分析パネル**: 銘柄情報、統計、チャートの統合表示
- **チャート表示**:
  - 期待値推移チャート（折れ線グラフ）
  - 勝率分布チャート（棒グラフ）
  - トレード履歴チャート（積み上げ棒グラフ）
- **ダークテーマ**: モダンなダークUI（qdarktheme使用）

#### フィルター機能
- **権利確定月フィルター**: 1月～12月の選択
- **勝率フィルター**: 0%～100%のスライダー
- **期待リターンフィルター**: -20%～+20%のスライダー
- **優待ジャンルフィルター**: 食品、金券、日用品など

#### データ管理
- **SQLiteデータベース**: 銘柄、シミュレーション結果、ウォッチリスト、通知設定の永続化
- **価格データキャッシュ**: yfinanceから取得したデータのローカル保存
- **シミュレーションキャッシュ**: バックテスト結果の保存による高速表示

#### ウォッチリスト
- **銘柄の登録/削除**: お気に入り銘柄の管理
- **メモ機能**: 各銘柄にメモを追加
- **専用タブ**: ウォッチリスト専用の表示タブ

#### 通知機能
- **デスクトップ通知**: Windows/macOS/Linux対応
  - Windows: winotify
  - macOS: pync/osascript
  - Linux: notify2/notify-send
  - フォールバック: QSystemTrayIcon
- **通知タイミング設定**: 権利付最終日の何日前に通知するか設定可能
- **バックグラウンドチェック**: 1時間ごとの自動チェック（設定で変更可能）

#### エクスポート機能
- **CSV出力**: 全分析データのCSV形式エクスポート
- **PDF出力**: レポート形式でのPDF生成（reportlab使用）
- **スクリーンショット**: 現在の画面をPNG形式で保存
- **設定エクスポート/インポート**: 設定のバックアップと復元

#### スクレイピング
- **96ut.com対応**: 株主優待データの自動取得
- **yutai.net-ir.ne.jp対応**: 優待情報の補完取得
- **フォールバックセレクター**: サイト変更に対応する複数のセレクター
- **データ検証**: 取得データの妥当性チェック
- **エラーハンドリング**: リトライ機能とエラーログ記録

#### バッチ処理
- **並列処理**: ThreadPoolExecutorによる高速バックテスト
- **進捗表示**: プログレスバーでの進捗確認
- **エラー回復**: 一部のエラーをスキップして処理継続

#### その他
- **キーボードショートカット**:
  - `Ctrl+E`: CSV出力
  - `Ctrl+P`: PDF出力
  - `F5`: データ更新
  - `Ctrl+D`: ウォッチリストに追加
- **ツールチップ**: 全UI要素に説明テキスト
- **設定ダイアログ**: テーマ、通知、データ更新などの設定UI
- **ステータスバー**: 現在の処理状況を表示

### 🗄️ データベーススキーマ

以下のテーブルを実装：
- `stocks`: 銘柄マスタ
- `simulation_cache`: バックテスト結果キャッシュ
- `watchlist`: ウォッチリスト
- `notification_settings`: 通知設定
- `price_history`: 株価データキャッシュ

### 📊 パフォーマンス最適化

- シミュレーション結果のキャッシュによる高速表示
- データベースインデックスの最適化
- 並列処理による高速バックテスト
- キャッシュ優先ロジックによるネットワーク負荷軽減

### 🔧 技術スタック

- **言語**: Python 3.10+
- **UIフレームワーク**: PySide6 (Qt6)
- **データ可視化**: matplotlib
- **データ処理**: pandas, numpy
- **データ取得**: yfinance
- **スクレイピング**: beautifulsoup4, requests
- **データベース**: SQLite3
- **テーマ**: qdarktheme
- **PDF生成**: reportlab
- **通知**: winotify (Windows), pync (macOS), notify2 (Linux)

### 📚 ドキュメント

- README.md: プロジェクト概要
- USER_MANUAL.md: ユーザーマニュアル
- CLAUDE.md: 開発者向けドキュメント
- docs/requirements.md: 要求定義書
- docs/database_schema.md: データベース設計
- docs/roadmap.md: 開発ロードマップ

### 🧪 テスト

- 単体テスト: `tests/test_database.py`, `tests/test_data_fetcher.py`
- 統合テスト: `tests/test_integration.py`
- 手動テスト: `scripts/test_backtest.py`, `scripts/test_setup.py`

### 📦 配布

- PyInstallerによる実行ファイル生成
- onefolder形式での配布
- 必要なリソースファイルの同梱

---

## [Unreleased]

### 🚀 今後の予定

#### 機能追加
- [ ] ポートフォリオ管理機能
- [ ] リスク分析（シャープレシオ、最大ドローダウン）
- [ ] 複数銘柄の比較機能
- [ ] バックテスト期間のカスタマイズ
- [ ] APIによる外部連携

#### 改善
- [ ] UI/UXの洗練
- [ ] パフォーマンスの更なる最適化
- [ ] エラーメッセージの改善
- [ ] 多言語対応（英語）

#### バグ修正
- [ ] 既知のバグはありません

---

## バージョニング規則

- **Major (X.0.0)**: 互換性のない大きな変更
- **Minor (0.X.0)**: 後方互換性のある機能追加
- **Patch (0.0.X)**: バグ修正

---

## サポート

バグ報告や機能要望は[GitHub Issues](https://github.com/yourusername/yuutai_event_investor/issues)でお願いします。

---

**Maintained by**: Yuutai Event Investor Team
**License**: MIT
