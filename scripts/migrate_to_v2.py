"""
データベースをv2スキーマにマイグレーション
主キーを code から (code, rights_month) の複合キーに変更

Usage:
    python scripts/migrate_to_v2.py
    python scripts/migrate_to_v2.py --backup data/yuutai_backup.db

Author: Yuutai Event Investor Team
Date: 2025-11-07
"""

import sys
from pathlib import Path
import argparse
import logging
import shutil
import sqlite3

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def setup_logging():
    """ログ設定"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def backup_database(db_path: Path, backup_path: Path):
    """
    データベースをバックアップ

    Args:
        db_path: 元のデータベースパス
        backup_path: バックアップ先パス
    """
    logger = logging.getLogger(__name__)
    logger.info(f"データベースをバックアップ: {backup_path}")

    try:
        shutil.copy2(db_path, backup_path)
        logger.info(f"[OK] バックアップ完了: {backup_path}")
        return True
    except Exception as e:
        logger.error(f"バックアップエラー: {e}")
        return False


def get_schema_version(db_path: Path) -> int:
    """
    現在のスキーマバージョンを取得

    Args:
        db_path: データベースパス

    Returns:
        int: スキーマバージョン
    """
    logger = logging.getLogger(__name__)

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT MAX(version) FROM schema_version")
        result = cursor.fetchone()
        conn.close()

        version = result[0] if result and result[0] else 0
        logger.info(f"現在のスキーマバージョン: {version}")
        return version

    except Exception as e:
        logger.warning(f"スキーマバージョン取得エラー（v1以前の可能性）: {e}")
        return 0


def migrate_to_v2(db_path: Path, sql_file: Path):
    """
    v2スキーマにマイグレーション

    Args:
        db_path: データベースパス
        sql_file: 新しいスキーマSQLファイル

    Returns:
        bool: 成功した場合True
    """
    logger = logging.getLogger(__name__)
    logger.info("v2スキーマへのマイグレーション開始")

    try:
        # SQLファイルを読み込み
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_script = f.read()

        # データベース接続
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # トランザクション開始
        cursor.execute("BEGIN TRANSACTION")

        # 既存データを一時テーブルに退避
        logger.info("既存データを退避中...")

        # stocksテーブルのデータを確認
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stocks'")
        stocks_exists = cursor.fetchone()

        old_stocks = []
        if stocks_exists:
            cursor.execute("SELECT * FROM stocks")
            old_stocks = cursor.fetchall()
            logger.info(f"  stocks: {len(old_stocks)}件")

        # スキーマを再作成
        logger.info("新しいスキーマを適用中...")
        cursor.executescript(sql_script)

        logger.info("[OK] マイグレーション完了")
        conn.commit()
        conn.close()

        return True

    except Exception as e:
        logger.error(f"マイグレーションエラー: {e}")
        import traceback
        traceback.print_exc()

        try:
            conn.rollback()
            conn.close()
        except:
            pass

        return False


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description='データベースをv2スキーマにマイグレーション'
    )
    parser.add_argument('--db', type=str,
                       default='data/yuutai.db',
                       help='データベースファイル（デフォルト: data/yuutai.db）')
    parser.add_argument('--backup', type=str,
                       help='バックアップ先（デフォルト: data/yuutai_backup_{timestamp}.db）')
    parser.add_argument('--sql', type=str,
                       default='data/create_tables_v2.sql',
                       help='新スキーマSQLファイル（デフォルト: data/create_tables_v2.sql）')

    args = parser.parse_args()

    setup_logging()
    logger = logging.getLogger(__name__)

    print("=" * 60)
    print("データベースマイグレーション - v1 → v2")
    print("=" * 60)
    print()
    print("変更内容:")
    print("  - stocksテーブルの主キーを(code, rights_month)の複合キーに変更")
    print("  - 同じ銘柄が複数の月に優待を実施する場合に対応")
    print()

    db_path = project_root / args.db
    sql_file = project_root / args.sql

    # ファイル存在チェック
    if not db_path.exists():
        logger.error(f"データベースファイルが見つかりません: {db_path}")
        return 1

    if not sql_file.exists():
        logger.error(f"SQLファイルが見つかりません: {sql_file}")
        return 1

    # 現在のスキーマバージョンを確認
    current_version = get_schema_version(db_path)

    if current_version >= 2:
        logger.warning(f"既にv{current_version}です。マイグレーション不要。")
        print()
        print("既に最新バージョンです。")
        return 0

    # バックアップ
    if args.backup:
        backup_path = project_root / args.backup
    else:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = project_root / "data" / f"yuutai_backup_{timestamp}.db"

    print("-" * 60)
    print("バックアップを作成します...")
    print("-" * 60)
    print()

    if not backup_database(db_path, backup_path):
        logger.error("バックアップに失敗しました")
        return 1

    print()

    # ユーザー確認
    print("-" * 60)
    print("警告: この操作は既存データを削除します")
    print("-" * 60)
    print()
    print("マイグレーション後、CSVから再インポートする必要があります:")
    print("  python scripts/import_yuutai_csv.py --input data/all_yuutai_stocks_fixed.csv --clear")
    print()
    response = input("続行しますか？ (yes/no): ")

    if response.lower() not in ['yes', 'y']:
        print("中断されました")
        return 0

    print()

    # マイグレーション実行
    print("-" * 60)
    print("マイグレーションを実行します...")
    print("-" * 60)
    print()

    success = migrate_to_v2(db_path, sql_file)

    print()
    print("=" * 60)
    print("処理完了" if success else "処理失敗")
    print("=" * 60)

    if success:
        print()
        print("マイグレーションが完了しました。")
        print()
        print("次のステップ:")
        print("  1. データを再インポート:")
        print("     python scripts/import_yuutai_csv.py --input data/all_yuutai_stocks_fixed.csv --clear")
        print()
        print("  2. アプリを起動:")
        print("     python main.py")
        print()
        print(f"問題が発生した場合は、バックアップから復元できます:")
        print(f"  cp {backup_path} {db_path}")

    return 0 if success else 1


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
