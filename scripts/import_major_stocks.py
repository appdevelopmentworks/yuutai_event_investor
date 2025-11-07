"""
主要優待銘柄をデータベースにインポート

Usage:
    python scripts/import_major_stocks.py

Author: Yuutai Event Investor Team
Date: 2025-11-07
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.database import DatabaseManager
from src.utils.csv_importer import CSVImporter

def main():
    print("=" * 60)
    print("主要優待銘柄インポート")
    print("=" * 60)
    print()

    # データベース接続
    db_path = project_root / "data" / "yuutai.db"
    db = DatabaseManager(db_path)

    # CSVインポーター
    importer = CSVImporter(db)

    # CSVファイルパス
    csv_path = project_root / "data" / "major_yuutai_stocks.csv"

    if not csv_path.exists():
        print(f"エラー: CSVファイルが見つかりません: {csv_path}")
        return 1

    print(f"CSVファイル: {csv_path}")
    print()

    # インポート前の件数
    stocks_before = db.get_all_stocks()
    print(f"インポート前の銘柄数: {len(stocks_before)}件")
    print()

    # インポート実行
    print("インポート中...")
    success, skipped, errors = importer.import_stocks(str(csv_path), overwrite=True)

    print()
    print("=" * 60)
    print("インポート結果")
    print("=" * 60)
    print(f"成功: {success}件")
    print(f"スキップ: {skipped}件")
    print(f"エラー: {len(errors)}件")

    if errors:
        print("\nエラー詳細:")
        for error in errors[:5]:  # 最初の5件のみ表示
            print(f"  - {error}")

    # インポート後の件数
    stocks_after = db.get_all_stocks()
    print(f"\nインポート後の銘柄数: {len(stocks_after)}件")

    print()
    print("=" * 60)
    print()

    # 銘柄一覧を表示
    print("登録された銘柄:")
    for stock in stocks_after:
        print(f"  {stock['code']} - {stock['name']} ({stock['rights_month']}月)")

    print()
    print("インポート完了！")
    print("アプリを起動すると新しいデータが表示されます。")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n中断されました")
        sys.exit(1)
    except Exception as e:
        print(f"エラー: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
