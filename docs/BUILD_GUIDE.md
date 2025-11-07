# 🔨 ビルドガイド

Yuutai Event Investorを実行ファイル（.exe）にビルドする手順です。

---

## 前提条件

### 必要なソフトウェア
- Python 3.10以上
- pip（Pythonパッケージマネージャー）
- すべての依存パッケージ（requirements.txtに記載）

### 環境確認

```bash
# Pythonバージョン確認
python --version
# 出力例: Python 3.10.0

# pipバージョン確認
pip --version
```

---

## ビルド手順

### Step 1: 依存パッケージのインストール

```bash
# プロジェクトルートに移動
cd C:\Users\hartm\Desktop\yuutai_event_investor

# 依存パッケージをインストール
pip install -r requirements.txt

# PyInstallerをインストール（まだの場合）
pip install pyinstaller
```

### Step 2: ビルド前の準備

```bash
# データベースを初期化（まだの場合）
python scripts/init_database.py

# 動作確認（オプション）
python main.py
```

### Step 3: PyInstallerでビルド

```bash
# .specファイルを使用してビルド
pyinstaller YuutaiEventInvestor.spec

# または、初回ビルド時に.specファイルを生成する場合
pyinstaller --name YuutaiEventInvestor ^
    --onedir ^
    --windowed ^
    --add-data "data;data" ^
    --add-data "config;config" ^
    --hidden-import PySide6 ^
    --hidden-import matplotlib ^
    main.py
```

**オプション説明:**
- `--onedir`: 1つのフォルダにすべてのファイルを配置
- `--windowed`: コンソールウィンドウを非表示（GUIアプリ用）
- `--add-data`: データファイルを含める
- `--hidden-import`: 自動検出されないモジュールを明示的に含める

### Step 4: ビルド結果の確認

ビルドが成功すると、以下のディレクトリが作成されます：

```
dist/
└── YuutaiEventInvestor/
    ├── YuutaiEventInvestor.exe  ← 実行ファイル
    ├── data/
    │   ├── create_tables.sql
    │   └── sample_stocks.csv
    ├── config/
    │   └── scraping_config.json
    ├── _internal/  ← 依存ライブラリ
    │   ├── PySide6/
    │   ├── matplotlib/
    │   └── ...
    ├── README.md
    ├── docs/
    │   └── USER_MANUAL.md
    └── CHANGELOG.md
```

### Step 5: 動作テスト

```bash
# ビルドしたアプリを起動
cd dist\YuutaiEventInvestor
YuutaiEventInvestor.exe
```

**確認事項:**
- [ ] アプリが正常に起動する
- [ ] データベースが正しく読み込まれる
- [ ] 銘柄リストが表示される
- [ ] フィルター機能が動作する
- [ ] チャートが表示される
- [ ] ウォッチリスト機能が動作する
- [ ] エクスポート機能が動作する

---

## トラブルシューティング

### エラー1: `ModuleNotFoundError`

**原因:** 必要なモジュールが含まれていない

**解決策:**
1. `YuutaiEventInvestor.spec`の`hiddenimports`にモジュールを追加
2. 再ビルド

```python
hiddenimports = [
    'missing_module',  # 不足しているモジュールを追加
    # ...
]
```

### エラー2: データファイルが見つからない

**原因:** `datas`の設定が不正

**解決策:**
1. `YuutaiEventInvestor.spec`の`datas`を確認
2. ファイルパスが正しいか確認

```python
datas = [
    ('data/create_tables.sql', 'data'),  # (ソース, 配置先)
    # ...
]
```

### エラー3: アプリが起動しない

**原因1:** Visual C++ Redistributableが不足

**解決策:** Microsoft Visual C++ Redistributableをインストール
https://aka.ms/vs/17/release/vc_redist.x64.exe

**原因2:** .NET Frameworkが古い

**解決策:** Windows Updateを実行

### エラー4: ファイルサイズが大きすぎる

**原因:** 不要なモジュールが含まれている

**解決策:**
1. `YuutaiEventInvestor.spec`の`excludes`に追加
2. UPX圧縮を有効化（既に有効）

```python
excludes = [
    'tkinter',
    'test',
    'unittest',
    # 不要なモジュールを追加
]
```

### エラー5: ビルドが遅い

**原因:** すべてのファイルを再ビルドしている

**解決策:**
```bash
# キャッシュをクリア
pyinstaller --clean YuutaiEventInvestor.spec
```

---

## 配布準備

### Step 1: 配布パッケージの作成

```bash
# distフォルダをZIP圧縮
cd dist
tar -a -c -f YuutaiEventInvestor_v1.0.0_Windows.zip YuutaiEventInvestor

# または、PowerShellで
Compress-Archive -Path YuutaiEventInvestor -DestinationPath YuutaiEventInvestor_v1.0.0_Windows.zip
```

### Step 2: リリースノートの作成

`RELEASE_NOTES.txt`を作成：

```
Yuutai Event Investor v1.0.0
=============================

リリース日: 2025-11-07

【新機能】
- 株主優待イベント投資の最適タイミング分析
- バックテスト機能
- チャート表示
- ウォッチリスト
- 通知機能
- CSV/PDFエクスポート

【動作環境】
- Windows 10/11 (64bit)
- メモリ: 4GB以上推奨
- ディスク: 500MB以上の空き容量

【インストール】
1. ZIPファイルを解凍
2. YuutaiEventInvestor.exeをダブルクリック

【サポート】
GitHub: https://github.com/yourusername/yuutai_event_investor
Issues: https://github.com/yourusername/yuutai_event_investor/issues

【ライセンス】
MIT License
```

### Step 3: チェックリスト

配布前の最終確認：

- [ ] ビルドが正常に完了
- [ ] クリーンな環境で動作テスト
- [ ] README.mdが最新
- [ ] USER_MANUAL.mdが完成
- [ ] CHANGELOG.mdが更新されている
- [ ] バージョン番号が正しい
- [ ] ライセンス表記が正しい
- [ ] リリースノートが作成されている

---

## 高度な設定

### アイコンの設定

```python
# YuutaiEventInvestor.spec
exe = EXE(
    # ...
    icon='icon.ico',  # アイコンファイルを指定
)
```

アイコンファイルの準備：
1. 256x256 PNG画像を作成
2. オンラインツールで.ico形式に変換
   - https://icoconvert.com/
   - https://convertio.co/png-ico/

### 圧縮の最適化

```python
# YuutaiEventInvestor.spec
exe = EXE(
    # ...
    upx=True,  # UPX圧縮を有効化
    upx_exclude=['PySide6'],  # 圧縮しないモジュール
)
```

### デバッグビルド

開発時のデバッグ用ビルド：

```bash
pyinstaller --debug=all YuutaiEventInvestor.spec
```

これにより、コンソールにデバッグ情報が出力されます。

---

## ビルド自動化

### バッチファイルの作成

`build.bat`:

```batch
@echo off
echo ========================================
echo Yuutai Event Investor Build Script
echo ========================================
echo.

echo [1/4] Cleaning old builds...
rmdir /s /q dist 2>nul
rmdir /s /q build 2>nul
del /f /q *.spec 2>nul

echo [2/4] Installing dependencies...
pip install -r requirements.txt

echo [3/4] Building application...
pyinstaller YuutaiEventInvestor.spec

echo [4/4] Creating distribution package...
cd dist
tar -a -c -f YuutaiEventInvestor_v1.0.0_Windows.zip YuutaiEventInvestor
cd ..

echo.
echo ========================================
echo Build completed!
echo Output: dist\YuutaiEventInvestor_v1.0.0_Windows.zip
echo ========================================
pause
```

実行：
```bash
build.bat
```

---

## CI/CD（GitHub Actions）

`.github/workflows/build.yml`の例：

```yaml
name: Build

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Build with PyInstaller
        run: pyinstaller YuutaiEventInvestor.spec
      - name: Create ZIP
        run: Compress-Archive -Path dist/YuutaiEventInvestor -DestinationPath YuutaiEventInvestor.zip
      - name: Upload artifact
        uses: actions/upload-artifact@v3
        with:
          name: YuutaiEventInvestor
          path: YuutaiEventInvestor.zip
```

---

## 参考リンク

- [PyInstaller公式ドキュメント](https://pyinstaller.org/en/stable/)
- [PySide6ドキュメント](https://doc.qt.io/qtforpython/)
- [UPX圧縮ツール](https://upx.github.io/)

---

**最終更新:** 2025-11-07
**対象バージョン:** 1.0.0
