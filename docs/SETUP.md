# 🚀 セットアップガイド

## プロジェクト構造が完成しました！

プロジェクトの基本構造とすべての設定ファイルが作成されました。

---

## 📂 作成されたファイル・ディレクトリ

```
yuutai_event_investor/
├── .gitignore                       ✅ Git管理除外ファイル
├── README.md                        ✅ プロジェクト説明書
├── main.py                          ✅ メインエントリーポイント
├── requirements.txt                 ✅ 依存パッケージリスト
│
├── config/                          ✅ 設定ファイル
│   ├── settings_default.json       ✅ デフォルト設定
│   ├── scraping_config.json        ✅ スクレイピング設定
│   └── theme_config.json           ✅ テーマ設定
│
├── data/                            ✅ データベース・キャッシュ
│   ├── create_tables.sql           ✅ DB初期化スクリプト
│   └── cache/                      ✅ キャッシュディレクトリ
│       └── .gitkeep
│
├── docs/                            ✅ ドキュメント
│   ├── requirements.md             ✅ 要求定義書
│   ├── database_schema.md          ✅ DB設計書
│   └── roadmap.md                  ✅ 開発ロードマップ
│
├── src/                             ✅ ソースコード
│   ├── __init__.py
│   ├── ui/                         ✅ UI関連
│   │   └── __init__.py
│   ├── core/                       ✅ コア機能
│   │   └── __init__.py
│   ├── scraping/                   ✅ スクレイピング
│   │   └── __init__.py
│   └── utils/                      ✅ ユーティリティ
│       └── __init__.py
│
├── resources/                       ✅ リソースファイル
│   ├── icons/                      ✅ アイコン
│   ├── themes/                     ✅ テーマファイル
│   └── images/                     ✅ 画像
│
└── tests/                           ✅ テストコード
    └── __init__.py
```

---

## 🔧 次のステップ: 環境セットアップ

### 1. Python仮想環境の作成

```bash
# プロジェクトディレクトリに移動
cd /mnt/c/Users/hartm/Desktop/yuutai_event_investor

# 仮想環境を作成
python -m venv venv

# 仮想環境をアクティベート
# Windows (PowerShell)
venv\Scripts\Activate.ps1

# Windows (Command Prompt)
venv\Scripts\activate.bat

# macOS/Linux
source venv/bin/activate
```

### 2. 依存パッケージのインストール

```bash
# requirements.txtから一括インストール
pip install -r requirements.txt

# または、段階的にインストール（推奨）
# まずはコア依存関係のみ
pip install PySide6 pandas numpy yfinance

# UI関連
pip install qfluentwidgets qdarktheme

# スクレイピング関連
pip install beautifulsoup4 requests lxml

# データ可視化
pip install matplotlib

# その他
pip install plyer python-dotenv colorlog
```

### 3. データベースの初期化

```bash
# SQLite3でデータベースを作成
cd data
sqlite3 yuutai.db < create_tables.sql

# 確認
sqlite3 yuutai.db "SELECT * FROM schema_version;"
```

または、Pythonスクリプトで初期化：

```python
import sqlite3
from pathlib import Path

# データベースファイルのパス
db_path = Path(__file__).parent / "data" / "yuutai.db"
sql_path = Path(__file__).parent / "data" / "create_tables.sql"

# データベースを作成
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# SQLスクリプトを実行
with open(sql_path, 'r', encoding='utf-8') as f:
    cursor.executescript(f.read())

conn.commit()
conn.close()

print("✅ データベースの初期化が完了しました！")
```

### 4. 動作確認

```bash
# メインスクリプトを実行
python main.py
```

期待される出力：
```
Yuutai Event Investor
==================================================
株主優待イベント投資分析ツール v1.0.0
==================================================

開発中...

次のステップ:
1. データベースの初期化
2. UIの実装
3. 計算エンジンの実装
```

---

## 📋 開発の優先順位

ロードマップ（docs/roadmap.md）に従って、以下の順序で開発を進めます：

### Phase 1: 基盤構築（Week 1-2）
- [x] ✅ プロジェクト構造作成
- [x] ✅ requirements.txt作成
- [x] ✅ 設定ファイル作成
- [ ] ⏳ データベース実装
- [ ] ⏳ 既存コードの移植

### Phase 2: コア機能実装（Week 3-4）
- [ ] 計算エンジン実装
- [ ] バックテストエンジン
- [ ] yfinanceデータ取得

### Phase 3: UI実装（Week 5-6）
- [ ] メインウィンドウ
- [ ] 銘柄リスト
- [ ] チャート表示

---

## 🛠️ 開発ツールの設定（オプション）

### VSCodeの設定

`.vscode/settings.json` を作成（推奨）：

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/Scripts/python.exe",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "editor.formatOnSave": true,
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true
  }
}
```

### Git初期化

```bash
cd /mnt/c/Users/hartm/Desktop/yuutai_event_investor

# Gitリポジトリを初期化
git init

# 初回コミット
git add .
git commit -m "Initial project setup: directory structure, config files, and documentation"
```

---

## 📝 重要な設定ファイルの説明

### 1. `config/settings_default.json`
- アプリケーションのデフォルト設定
- 初回起動時にコピーされ、`settings.json`として使用される
- ユーザーがカスタマイズ可能

### 2. `config/scraping_config.json`
- スクレイピング対象サイトの設定
- セレクターの定義とフォールバック設定
- サイト仕様変更時に修正が必要

### 3. `config/theme_config.json`
- ダーク/ライトテーマの色設定
- フォント、スペーシング、ボーダー半径の定義
- チャートの色設定

---

## ❓ トラブルシューティング

### Q: `pip install qfluentwidgets` でエラーが出る

A: 以下を試してください：
```bash
# pipをアップグレード
python -m pip install --upgrade pip

# 再度インストール
pip install qfluentwidgets
```

### Q: SQLite3が見つからない

A: Pythonには標準で組み込まれていますが、以下で確認：
```bash
python -c "import sqlite3; print(sqlite3.version)"
```

### Q: 仮想環境が作成できない

A: Pythonバージョンを確認：
```bash
python --version  # 3.10以上必要
```

---

## 🎯 次のアクション

1. **仮想環境のセットアップ** - 上記手順に従って実行
2. **パッケージのインストール** - `pip install -r requirements.txt`
3. **データベースの初期化** - SQLスクリプトを実行
4. **既存コードの移植** - Streamlitアプリから関数を移植

準備が整ったら、Phase 2「コア機能実装」に進みましょう！

---

## 📚 参考資料

- [要求定義書](docs/requirements.md)
- [データベース設計書](docs/database_schema.md)
- [開発ロードマップ](docs/roadmap.md)
- [PySide6ドキュメント](https://doc.qt.io/qtforpython/)
- [QFluentWidgets](https://qfluentwidgets.com/)

---

🎉 **プロジェクト構造の作成が完了しました！**

次は実装フェーズに入ります。頑張りましょう！
