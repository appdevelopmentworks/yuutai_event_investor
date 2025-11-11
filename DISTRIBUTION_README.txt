========================================
  Yuutai Event Investor v1.0.0
  株主優待イベント投資分析ツール
========================================

本アプリケーションをダウンロードいただき、ありがとうございます。

■ 初めての方へ

1. このフォルダ内の「YuutaiEventInvestor.exe」をダブルクリックしてください
   （Windows以外の場合は「YuutaiEventInvestor」を実行）

2. 初回起動時、約2224件の銘柄データが表示されます
   （データは2025年11月時点のものです）

3. 銘柄をクリックすると、最適な買入タイミングが自動計算されます

■ 詳細な使い方

- INSTALL.md      : インストール・初期設定ガイド
- README.md       : 機能の詳細説明
- BUILD.md        : ビルド方法（開発者向け）

■ データの更新方法

最新の銘柄データを取得したい場合：

1. アプリを起動
2. メニューバー → 「ファイル」 → 「データ更新」
3. 約5-10分で完了（インターネット接続が必要です）

■ 含まれるファイル

📂 YuutaiEventInvestor/
  ├─ YuutaiEventInvestor.exe  実行ファイル
  ├─ config/                  設定ファイル
  ├─ data/
  │   └─ yuutai.db           初期データベース（2224件）
  ├─ AppImg.ico               アイコン
  ├─ README.md                詳細ガイド
  ├─ INSTALL.md               インストールガイド
  ├─ LICENSE                  ライセンス情報
  └─ その他依存ファイル

■ 動作環境

- Windows 10/11（64bit）
- macOS 10.14以降
- Linux（Ubuntu 20.04以降）

■ トラブルシューティング

◆ 起動しない場合

  Windows:
    - Microsoft Visual C++ 再頒布可能パッケージをインストール
      https://aka.ms/vs/17/release/vc_redist.x64.exe

  macOS:
    - 右クリック → 「開く」で起動してください
    - システム環境設定 → セキュリティ → 「このまま開く」

  Linux:
    - sudo apt-get install libxcb-xinerama0 libxcb-cursor0

◆ 銘柄が表示されない場合

  1. data/yuutai.db ファイルがあるか確認
  2. ない場合は、ZIPファイルを再度解凍してください

◆ データ更新ができない場合

  - インターネット接続を確認してください
  - ファイアウォールがブロックしていないか確認してください

■ サポート・お問い合わせ

GitHub Issues:
  https://github.com/yourusername/yuutai_event_investor/issues

詳細なドキュメント:
  INSTALL.md および README.md をご覧ください

■ 免責事項

本アプリケーションは教育・研究目的で提供されています。
投資判断は自己責任で行ってください。
本アプリケーションの使用によって生じた損失について、
開発者は一切の責任を負いません。

■ ライセンス

MIT License
詳細は LICENSE ファイルをご覧ください。

========================================
  Yuutai Event Investor Team
  2025-01-11
========================================
