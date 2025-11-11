#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PyInstaller Build Script for Yuutai Event Investor
優待イベント投資家アプリケーション

このスクリプトはPyInstallerを使用してアプリケーションをビルドします。

使用方法:
    python build_pyinstaller.py

必要なパッケージ:
    pip install pyinstaller

ビルドオプション:
    - Windows: 実行ファイル (.exe) + リソース
    - macOS: アプリバンドル (.app)
    - Linux: 実行ファイル + リソース
"""

import sys
import platform
import subprocess
from pathlib import Path
import shutil

# アプリケーション情報
APP_NAME = 'YuutaiEventInvestor'
VERSION = '1.0.0'

# プロジェクトルート
ROOT_DIR = Path(__file__).parent.resolve()
SPEC_FILE = ROOT_DIR / 'yuutai_event_investor.spec'
ICON_PATH = ROOT_DIR / 'AppImg.ico'
DIST_DIR = ROOT_DIR / 'dist'
BUILD_DIR = ROOT_DIR / 'build'

def clean_build_directories():
    """以前のビルドファイルを削除"""
    print("🧹 以前のビルドファイルをクリーンアップ中...")

    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
        print(f"  ✓ {BUILD_DIR} を削除")

    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
        print(f"  ✓ {DIST_DIR} を削除")

    print()

def build_pyinstaller():
    """PyInstallerでビルドを実行"""

    print("=" * 60)
    print(f"PyInstallerビルド開始: {APP_NAME} v{VERSION}")
    print("=" * 60)
    print(f"プラットフォーム: {platform.system()}")
    print(f"アイコン: {ICON_PATH}")
    print(f"Specファイル: {SPEC_FILE}")
    print()
    print("=" * 60)
    print()

    # ビルドコマンド
    cmd = [
        'pyinstaller',
        '--clean',           # キャッシュをクリーン
        '--noconfirm',       # 確認なしで上書き
        str(SPEC_FILE),      # specファイルを使用
    ]

    print("ビルドコマンド:")
    print(" ".join(cmd))
    print()
    print("=" * 60)
    print()

    try:
        # PyInstaller実行
        result = subprocess.run(cmd, check=True, cwd=ROOT_DIR)

        print()
        print("=" * 60)
        print("✅ ビルド成功!")
        print("=" * 60)
        print()
        print(f"出力先: {DIST_DIR / APP_NAME}")

        if platform.system() == 'Windows':
            exe_path = DIST_DIR / APP_NAME / f'{APP_NAME}.exe'
            print(f"実行ファイル: {exe_path}")
        elif platform.system() == 'Darwin':
            app_path = DIST_DIR / f'{APP_NAME}.app'
            print(f"アプリバンドル: {app_path}")
        else:
            exe_path = DIST_DIR / APP_NAME / APP_NAME
            print(f"実行ファイル: {exe_path}")

        print()
        print("配布方法:")
        print(f"  1. {DIST_DIR / APP_NAME} フォルダ全体をZIP圧縮")
        print(f"  2. ユーザーに配布")
        print(f"  3. 解凍後、実行ファイルをダブルクリックで起動")
        print()

        return 0

    except subprocess.CalledProcessError as e:
        print()
        print("=" * 60)
        print("❌ ビルド失敗")
        print("=" * 60)
        print(f"エラーコード: {e.returncode}")
        print()
        print("トラブルシューティング:")
        print("  1. requirements.txtのパッケージが全てインストールされているか確認")
        print("  2. PyInstallerを再インストール: pip install --upgrade pyinstaller")
        print("  3. specファイルの内容を確認")
        return 1
    except FileNotFoundError:
        print()
        print("=" * 60)
        print("❌ PyInstallerが見つかりません")
        print("=" * 60)
        print()
        print("以下のコマンドでPyInstallerをインストールしてください:")
        print("  pip install pyinstaller")
        return 1

def check_requirements():
    """必要なパッケージがインストールされているか確認"""
    print("📋 要件チェック中...")
    print()

    # PyInstallerの確認
    try:
        result = subprocess.run(
            ['pyinstaller', '--version'],
            capture_output=True,
            text=True,
            check=True
        )
        version = result.stdout.strip()
        print(f"  ✓ PyInstaller {version} インストール済み")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("  ✗ PyInstallerがインストールされていません")
        print()
        print("以下のコマンドでインストールしてください:")
        print("  pip install pyinstaller")
        return False

    # アイコンファイルの確認
    if not ICON_PATH.exists():
        print(f"  ✗ アイコンファイルが見つかりません: {ICON_PATH}")
        return False
    print(f"  ✓ アイコンファイル確認: {ICON_PATH}")

    # Specファイルの確認
    if not SPEC_FILE.exists():
        print(f"  ✗ Specファイルが見つかりません: {SPEC_FILE}")
        return False
    print(f"  ✓ Specファイル確認: {SPEC_FILE}")

    print()
    return True

if __name__ == '__main__':
    print()
    print("=" * 60)
    print("Yuutai Event Investor - PyInstaller ビルドスクリプト")
    print("=" * 60)
    print()

    # 要件チェック
    if not check_requirements():
        sys.exit(1)

    # 以前のビルドをクリーンアップ
    clean_build_directories()

    # ビルド実行
    sys.exit(build_pyinstaller())
