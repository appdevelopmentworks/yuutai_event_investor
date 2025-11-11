#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Nuitka Build Script for Yuutai Event Investor
優待イベント投資家アプリケーション

このスクリプトはNuitkaを使用してアプリケーションをコンパイルします。

使用方法:
    python build_nuitka.py

必要なパッケージ:
    pip install nuitka ordered-set

ビルドオプション:
    - Windows: 実行ファイル (.exe) + リソース
    - macOS: アプリバンドル (.app)
    - Linux: 実行ファイル + リソース
"""

import sys
import platform
import subprocess
from pathlib import Path

# アプリケーション情報
APP_NAME = 'YuutaiEventInvestor'
VERSION = '1.0.0'
AUTHOR = 'Yuutai Event Investor Team'

# プロジェクトルート
ROOT_DIR = Path(__file__).parent.resolve()
ICON_PATH = ROOT_DIR / 'AppImg.ico'

def build_nuitka():
    """Nuitkaでビルドを実行"""

    # データベースファイルのパス
    DB_PATH = ROOT_DIR / 'data' / 'yuutai.db'

    # 基本的なNuitkaコマンド
    cmd = [
        sys.executable,
        '-m', 'nuitka',
        '--standalone',                          # スタンドアロン実行ファイル
        '--onefile',                             # 単一実行ファイル化
        '--enable-plugin=pyside6',               # PySide6プラグイン
        '--include-data-dir=config=config',      # configフォルダを含める
        '--include-data-files=data/*.sql=data/', # SQLファイルを含める
        f'--include-data-files={DB_PATH}=data/', # データベースファイル（2224件の銘柄データ入り）
        f'--include-data-files={ICON_PATH}=.',   # アイコンファイルを含める
        '--follow-imports',                      # インポートを追跡
        '--assume-yes-for-downloads',            # 依存関係の自動ダウンロード
    ]

    # プラットフォーム固有の設定
    if platform.system() == 'Windows':
        cmd.extend([
            '--windows-disable-console',         # コンソールウィンドウを非表示
            f'--windows-icon-from-ico={ICON_PATH}',  # Windowsアイコン
            '--windows-company-name=Yuutai Event Investor Team',
            f'--windows-product-name={APP_NAME}',
            f'--windows-file-version={VERSION}',
            f'--windows-product-version={VERSION}',
            '--windows-file-description=株主優待イベント投資分析ツール',
        ])
    elif platform.system() == 'Darwin':  # macOS
        cmd.extend([
            '--macos-create-app-bundle',         # .appバンドル作成
            f'--macos-app-icon={ICON_PATH}',     # macOSアイコン
            '--macos-app-name=YuutaiEventInvestor',
            '--macos-app-version={VERSION}',
        ])
    elif platform.system() == 'Linux':
        cmd.extend([
            f'--linux-icon={ICON_PATH}',         # Linuxアイコン
        ])

    # 出力設定
    cmd.extend([
        f'--output-dir=dist',                    # 出力ディレクトリ
        '--remove-output',                       # 既存のビルドを削除
        'main.py',                               # エントリーポイント
    ])

    print("=" * 60)
    print(f"Nuitkaビルド開始: {APP_NAME} v{VERSION}")
    print("=" * 60)
    print(f"プラットフォーム: {platform.system()}")
    print(f"アイコン: {ICON_PATH}")
    print()
    print("ビルドコマンド:")
    print(" ".join(cmd))
    print()
    print("=" * 60)
    print()

    try:
        # Nuitka実行
        result = subprocess.run(cmd, check=True, cwd=ROOT_DIR)

        print()
        print("=" * 60)
        print("✅ ビルド成功!")
        print("=" * 60)
        print()
        print(f"出力先: {ROOT_DIR / 'dist'}")

        if platform.system() == 'Windows':
            print(f"実行ファイル: dist/{APP_NAME}.exe")
        elif platform.system() == 'Darwin':
            print(f"アプリバンドル: dist/{APP_NAME}.app")
        else:
            print(f"実行ファイル: dist/{APP_NAME}")

        return 0

    except subprocess.CalledProcessError as e:
        print()
        print("=" * 60)
        print("❌ ビルド失敗")
        print("=" * 60)
        print(f"エラーコード: {e.returncode}")
        return 1
    except FileNotFoundError:
        print()
        print("=" * 60)
        print("❌ Nuitkaが見つかりません")
        print("=" * 60)
        print()
        print("以下のコマンドでNuitkaをインストールしてください:")
        print("  pip install nuitka ordered-set")
        return 1

def check_requirements():
    """必要なパッケージがインストールされているか確認"""
    try:
        import nuitka
        print(f"✓ Nuitka {nuitka.__version__} インストール済み")
        return True
    except ImportError:
        print("✗ Nuitkaがインストールされていません")
        print()
        print("以下のコマンドでインストールしてください:")
        print("  pip install nuitka ordered-set")
        return False

if __name__ == '__main__':
    print()
    print("=" * 60)
    print("Yuutai Event Investor - Nuitka ビルドスクリプト")
    print("=" * 60)
    print()

    # 要件チェック
    if not check_requirements():
        sys.exit(1)

    # アイコンファイルの存在確認
    if not ICON_PATH.exists():
        print(f"❌ アイコンファイルが見つかりません: {ICON_PATH}")
        sys.exit(1)

    print(f"✓ アイコンファイル確認: {ICON_PATH}")
    print()

    # ビルド実行
    sys.exit(build_nuitka())
