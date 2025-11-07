"""
優待CSVデータをデータベースにインポート
既存データを全削除してからインポートするオプションあり

Usage:
    # 既存データを削除してからインポート（推奨）
    python scripts/import_yuutai_csv.py --input data/all_yuutai_stocks_fixed.csv --clear

    # 既存データに追加（重複は上書き）
    python scripts/import_yuutai_csv.py --input data/all_yuutai_stocks_fixed.csv

Author: Yuutai Event Investor Team
Date: 2025-11-07
"""

import sys
from pathlib import Path
import argparse
import csv
import logging

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.database import DatabaseManager


def setup_logging():
    """ログ設定"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def clear_database(db: DatabaseManager):
    """
    データベースの銘柄データを全削除

    Args:
        db: DatabaseManagerインスタンス
    """
    logger = logging.getLogger(__name__)
    logger.info("データベースのデータを削除中...")

    try:
        conn = db.connect()
        cursor = conn.cursor()

        # stocksテーブルのデータを削除
        cursor.execute("DELETE FROM stocks")
        stocks_deleted = cursor.rowcount

        # simulation_cacheテーブルのデータを削除
        cursor.execute("DELETE FROM simulation_cache")
        cache_deleted = cursor.rowcount

        # watchlistテーブルのデータを削除
        cursor.execute("DELETE FROM watchlist")
        watchlist_deleted = cursor.rowcount

        conn.commit()

        # VACUUMは別のコネクションで実行（トランザクション外）
        cursor.execute("VACUUM")

        conn.close()

        logger.info(f"[OK] データベースを空にしました")
        logger.info(f"  削除件数 - stocks: {stocks_deleted}件")
        logger.info(f"  削除件数 - simulation_cache: {cache_deleted}件")
        logger.info(f"  削除件数 - watchlist: {watchlist_deleted}件")

        return True

    except Exception as e:
        logger.error(f"データベースクリアエラー: {e}")
        import traceback
        traceback.print_exc()
        return False


def import_csv(csv_file: Path, db: DatabaseManager, batch_size: int = 100):
    """
    CSVファイルからデータベースにインポート

    Args:
        csv_file: CSVファイルパス
        db: DatabaseManagerインスタンス
        batch_size: バッチサイズ

    Returns:
        tuple: (成功件数, 失敗件数)
    """
    logger = logging.getLogger(__name__)
    logger.info(f"CSVファイル読み込み: {csv_file}")

    success_count = 0
    error_count = 0

    try:
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        total_count = len(rows)
        logger.info(f"総件数: {total_count}件")

        for i, row in enumerate(rows, 1):
            code = row.get('code', '').strip()
            name = row.get('name', '').strip()
            rights_month = row.get('rights_month', '').strip()
            rights_date = row.get('rights_date', '').strip()
            yuutai_genre = row.get('yuutai_genre', '').strip()
            yuutai_content = row.get('yuutai_content', '').strip()
            min_investment_str = row.get('min_investment', '0').strip()

            # 必須フィールドチェック
            if not code or not name:
                logger.warning(f"スキップ（必須フィールド不足）: {row}")
                error_count += 1
                continue

            # 権利確定月を整数に変換
            try:
                rights_month = int(rights_month) if rights_month else None
            except ValueError:
                logger.warning(f"スキップ（権利確定月が不正）: {code} - {rights_month}")
                error_count += 1
                continue

            # 最低投資金額を整数に変換
            try:
                min_investment = int(min_investment_str) if min_investment_str else 0
            except ValueError:
                min_investment = 0

            # データベースに挿入
            success = db.insert_stock(
                code=code,
                name=name,
                rights_month=rights_month,
                rights_date=rights_date if rights_date else None,
                yuutai_genre=yuutai_genre if yuutai_genre else None,
                yuutai_content=yuutai_content if yuutai_content else None
            )

            if success:
                success_count += 1
            else:
                error_count += 1
                logger.error(f"インポート失敗: {code} - {name}")

            # 進捗表示
            if i % batch_size == 0:
                logger.info(f"  {i}/{total_count}件処理中... (成功: {success_count}, 失敗: {error_count})")

        logger.info(f"[OK] インポート完了")
        logger.info(f"  成功: {success_count}件")
        logger.info(f"  失敗: {error_count}件")

        return success_count, error_count

    except Exception as e:
        logger.error(f"CSVインポートエラー: {e}")
        import traceback
        traceback.print_exc()
        return success_count, error_count


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description='優待CSVデータをデータベースにインポート'
    )
    parser.add_argument('--input', '-i', type=str,
                       default='data/all_yuutai_stocks_fixed.csv',
                       help='入力CSVファイル（デフォルト: data/all_yuutai_stocks_fixed.csv）')
    parser.add_argument('--clear', '-c', action='store_true',
                       help='既存データを全削除してからインポート')
    parser.add_argument('--batch-size', '-b', type=int, default=100,
                       help='バッチサイズ（デフォルト: 100）')

    args = parser.parse_args()

    setup_logging()
    logger = logging.getLogger(__name__)

    print("=" * 60)
    print("優待データCSVインポートスクリプト")
    print("=" * 60)
    print()

    csv_file = project_root / args.input

    print(f"入力ファイル: {csv_file}")
    print(f"既存データ削除: {'はい' if args.clear else 'いいえ（重複は上書き）'}")
    print()

    # ファイル存在チェック
    if not csv_file.exists():
        logger.error(f"入力ファイルが見つかりません: {csv_file}")
        return 1

    # データベース初期化
    db = DatabaseManager()

    # 既存データを削除（オプション）
    if args.clear:
        print("-" * 60)
        print("既存データを削除します...")
        print("-" * 60)
        print()

        if not clear_database(db):
            logger.error("データベースのクリアに失敗しました")
            return 1

        print()

    # CSVインポート
    print("-" * 60)
    print("CSVデータをインポートします...")
    print("-" * 60)
    print()

    success_count, error_count = import_csv(csv_file, db, args.batch_size)

    print()
    print("=" * 60)
    print("処理完了")
    print("=" * 60)
    print(f"成功: {success_count}件")
    print(f"失敗: {error_count}件")
    print()

    if success_count > 0:
        print("データベースへのインポートが完了しました。")
        print("アプリを起動して確認してください:")
        print("  python main.py")
        print()

    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n中断されました")
        sys.exit(1)
    except Exception as e:
        print(f"\nエラー: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
