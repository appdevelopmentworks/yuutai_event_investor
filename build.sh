#!/bin/bash
# macOS/Linux用ビルドスクリプト
# 使用方法: ./build.sh [pyinstaller|nuitka]

set -e

echo ""
echo "========================================"
echo "Yuutai Event Investor ビルドスクリプト"
echo "========================================"
echo ""

# 引数チェック
if [ $# -eq 0 ]; then
    echo "使用方法: ./build.sh [pyinstaller|nuitka]"
    echo ""
    echo "例:"
    echo "  ./build.sh pyinstaller  - PyInstallerでビルド"
    echo "  ./build.sh nuitka       - Nuitkaでビルド"
    echo ""
    exit 1
fi

# ビルド方法に応じて実行
case "$1" in
    pyinstaller)
        echo "PyInstallerでビルドします..."
        echo ""
        python3 build_pyinstaller.py
        ;;
    nuitka)
        echo "Nuitkaでビルドします..."
        echo ""
        python3 build_nuitka.py
        ;;
    *)
        echo "エラー: 不明なビルド方法 '$1'"
        echo ""
        echo "有効なオプション: pyinstaller, nuitka"
        echo ""
        exit 1
        ;;
esac

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================"
    echo "✅ ビルド完了!"
    echo "========================================"
    echo ""
    echo "出力先: dist/YuutaiEventInvestor"
    echo ""
else
    echo ""
    echo "========================================"
    echo "❌ ビルド失敗"
    echo "========================================"
    echo ""
    exit 1
fi
