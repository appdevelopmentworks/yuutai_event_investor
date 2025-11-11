# ビルドガイド - Yuutai Event Investor

このドキュメントでは、Yuutai Event Investorアプリケーションを配布可能な実行ファイルにビルドする方法を説明します。

## 📋 前提条件

### 必須パッケージ

```bash
# 基本パッケージ（requirements.txtから）
pip install -r requirements.txt

# PyInstallerを使用する場合
pip install pyinstaller

# Nuitkaを使用する場合
pip install nuitka ordered-set
```

### システム要件

- **Windows**: Windows 10以降
- **macOS**: macOS 10.14 (Mojave)以降
- **Linux**: Ubuntu 20.04以降、または同等のディストリビューション

## 🏗️ ビルド方法

### 方法1: PyInstaller（推奨）

PyInstallerは最も簡単で安定したビルド方法です。

#### Windows

```batch
# バッチファイルを使用
build.bat pyinstaller

# または直接実行
python build_pyinstaller.py
```

#### macOS / Linux

```bash
# シェルスクリプトを使用
./build.sh pyinstaller

# または直接実行
python3 build_pyinstaller.py
```

#### 手動でspecファイルから実行

```bash
pyinstaller --clean --noconfirm yuutai_event_investor.spec
```

### 方法2: Nuitka（高速実行）

Nuitkaはコンパイルに時間がかかりますが、実行速度が速くなります。

#### Windows

```batch
# バッチファイルを使用
build.bat nuitka

# または直接実行
python build_nuitka.py
```

#### macOS / Linux

```bash
# シェルスクリプトを使用
./build.sh nuitka

# または直接実行
python3 build_nuitka.py
```

## 📦 ビルド出力

### ディレクトリ構造

```
dist/
└── YuutaiEventInvestor/          # 配布フォルダ
    ├── YuutaiEventInvestor.exe   # 実行ファイル (Windows)
    ├── YuutaiEventInvestor        # 実行ファイル (macOS/Linux)
    ├── YuutaiEventInvestor.app    # アプリバンドル (macOS Nuitka)
    ├── config/                    # 設定ファイル
    ├── data/                      # データファイル
    ├── AppImg.ico                 # アイコン
    └── その他の依存ファイル
```

### ファイルサイズ目安

- **PyInstaller**: 約150-250MB
- **Nuitka (onefile)**: 約80-150MB
- **Nuitka (standalone)**: 約100-200MB

## 🚀 配布方法

### 1. ZIPファイルの作成

```bash
# Windows
cd dist
powershell Compress-Archive -Path YuutaiEventInvestor -DestinationPath YuutaiEventInvestor-v1.0.0-Windows.zip

# macOS
cd dist
zip -r YuutaiEventInvestor-v1.0.0-macOS.zip YuutaiEventInvestor.app

# Linux
cd dist
tar -czf YuutaiEventInvestor-v1.0.0-Linux.tar.gz YuutaiEventInvestor/
```

### 2. 配布パッケージの内容

配布時には以下を含めてください：

- ✅ 実行ファイル（`dist/YuutaiEventInvestor/`フォルダ全体）
- ✅ README.md（使い方ガイド）
- ✅ LICENSE（ライセンス情報）
- ✅ data/yuutai.db（初期データベース）

### 3. ユーザーへの使用方法

**Windows:**
1. ZIPファイルを解凍
2. `YuutaiEventInvestor`フォルダ内の`YuutaiEventInvestor.exe`をダブルクリック

**macOS:**
1. ZIPファイルを解凍
2. `YuutaiEventInvestor.app`を「アプリケーション」フォルダにドラッグ
3. 初回起動時に「開発元を確認できません」と表示された場合：
   - システム環境設定 → セキュリティとプライバシー → 「このまま開く」

**Linux:**
1. tar.gzファイルを解凍
2. ターミナルで`./YuutaiEventInvestor`を実行

## 🔧 トラブルシューティング

### PyInstallerのビルドエラー

#### エラー: "ModuleNotFoundError"

```bash
# specファイルのhiddenimportsに追加
hiddenimports = [
    'モジュール名',
]
```

#### エラー: "Failed to execute script"

```bash
# デバッグモードで実行
pyinstaller --debug=all yuutai_event_investor.spec
```

### Nuitkaのビルドエラー

#### エラー: "Could not find compiler"

**Windows:** Microsoft Visual Studio Build Tools をインストール

```bash
# C++コンパイラが必要
# https://visualstudio.microsoft.com/downloads/
```

**macOS:** Xcodeコマンドラインツールをインストール

```bash
xcode-select --install
```

**Linux:** GCCをインストール

```bash
sudo apt-get install gcc g++ python3-dev
```

#### エラー: ビルドが非常に遅い

```bash
# --onefile オプションを外して standalone モードで実行
# build_nuitka.py の '--onefile' 行をコメントアウト
```

### アイコンが表示されない

- `AppImg.ico`ファイルが正しい場所にあることを確認
- アイコンファイルが破損していないか確認
- Windows: .icoフォーマット、macOS: .icnsフォーマットに変換が必要な場合あり

### 実行ファイルが大きすぎる

```bash
# PyInstallerの場合: UPX圧縮を有効化
# specファイルで upx=True に設定（既に有効）

# Nuitkaの場合: プラグインを最小限に
# 不要な --enable-plugin オプションを削除
```

## 📝 ビルド設定のカスタマイズ

### PyInstaller (yuutai_event_investor.spec)

```python
# コンソールウィンドウを表示したい場合
console=True

# アイコンを変更
icon='別のアイコンファイル.ico'

# 除外するモジュールを追加
excludes=['不要なモジュール']
```

### Nuitka (build_nuitka.py)

```python
# Onefileモードを無効化（起動が速くなる）
# '--onefile', の行を削除

# コンパイル最適化レベルを変更
cmd.append('--lto=yes')  # Link Time Optimization
```

## 🎯 推奨ビルド方法

### 開発・テスト用
- **PyInstaller**: 高速なビルド、デバッグが容易

### 本番配布用
- **Nuitka**: 実行速度が速い、ファイルサイズが小さい

### クロスプラットフォーム配布
- 各プラットフォームで個別にビルド
- GitHubのマトリックスビルド（CI/CD）を使用

## 📚 参考リソース

- [PyInstaller公式ドキュメント](https://pyinstaller.org/)
- [Nuitka公式ドキュメント](https://nuitka.net/)
- [PySide6ドキュメント](https://doc.qt.io/qtforpython/)

## ❓ サポート

ビルドに関する問題が発生した場合：

1. このドキュメントのトラブルシューティングセクションを確認
2. GitHubのIssuesで報告
3. ビルドログを添付して質問

---

**最終更新**: 2025-01-11
**バージョン**: 1.0.0
