"""
株主優待データの企業名を東証全銘柄データから正式名称に更新

Usage:
    python scripts/update_stock_names.py
    python scripts/update_stock_names.py --input data/test_kabuyutai.csv --output data/test_kabuyutai_fixed.csv
    python scripts/update_stock_names.py --tse data/東証全銘柄.csv

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


def setup_logging():
    """ログ設定"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def load_tse_names(tse_file: Path) -> dict:
    """
    東証全銘柄CSVから証券コードと企業名の辞書を作成

    Args:
        tse_file: 東証全銘柄CSVファイルのパス

    Returns:
        dict: {証券コード: 企業名} の辞書
    """
    logger = logging.getLogger(__name__)
    logger.info(f"東証全銘柄データ読み込み: {tse_file}")

    code_to_name = {}

    try:
        # Shift-JIS (CP932) でエンコードされていることを想定
        with open(tse_file, 'r', encoding='cp932') as f:
            reader = csv.DictReader(f)
            for row in reader:
                code = row.get('コード', '').strip()
                name = row.get('銘柄名', '').strip()

                if code and name:
                    code_to_name[code] = name

        logger.info(f"東証全銘柄データ読み込み完了: {len(code_to_name)}件")
        return code_to_name

    except Exception as e:
        logger.error(f"東証全銘柄データ読み込みエラー: {e}")
        import traceback
        traceback.print_exc()
        return {}


def update_stock_names(input_file: Path, output_file: Path, code_to_name: dict):
    """
    優待データの企業名を正式名称に更新

    Args:
        input_file: 入力CSVファイル（スクレイピングデータ）
        output_file: 出力CSVファイル（名称更新後）
        code_to_name: 証券コードと企業名の辞書
    """
    logger = logging.getLogger(__name__)
    logger.info(f"優待データ読み込み: {input_file}")

    updated_count = 0
    not_found_count = 0
    total_count = 0

    try:
        with open(input_file, 'r', encoding='utf-8-sig') as f_in:
            reader = csv.DictReader(f_in)
            rows = list(reader)
            total_count = len(rows)

        # 企業名を更新
        for row in rows:
            code = row.get('code', '').strip()
            original_name = row.get('name', '').strip()

            if code in code_to_name:
                new_name = code_to_name[code]
                if new_name != original_name:
                    row['name'] = new_name
                    updated_count += 1
                    logger.debug(f"{code}: {original_name} -> {new_name}")
            else:
                logger.warning(f"東証全銘柄に見つからない: {code} ({original_name})")
                not_found_count += 1

        # 更新したデータを出力
        fieldnames = ['code', 'name', 'rights_month', 'rights_date',
                      'yuutai_genre', 'yuutai_content', 'min_investment']

        with open(output_file, 'w', encoding='utf-8-sig', newline='') as f_out:
            writer = csv.DictWriter(f_out, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        logger.info(f"[OK] 企業名を正式名称に更新しました: {output_file}")
        logger.info(f"  総件数: {total_count}件")
        logger.info(f"  更新件数: {updated_count}件")
        logger.info(f"  未発見: {not_found_count}件")

        return True

    except Exception as e:
        logger.error(f"企業名更新エラー: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description='優待データの企業名を東証全銘柄データから正式名称に更新'
    )
    parser.add_argument('--input', '-i', type=str,
                       default='data/test_kabuyutai.csv',
                       help='入力CSVファイル（デフォルト: data/test_kabuyutai.csv）')
    parser.add_argument('--output', '-o', type=str,
                       help='出力CSVファイル（デフォルト: {input}_fixed.csv）')
    parser.add_argument('--tse', type=str,
                       default='data/東証全銘柄.csv',
                       help='東証全銘柄CSVファイル（デフォルト: data/東証全銘柄.csv）')

    args = parser.parse_args()

    setup_logging()
    logger = logging.getLogger(__name__)

    print("=" * 60)
    print("優待データ企業名更新スクリプト")
    print("=" * 60)
    print()

    # ファイルパスを決定
    input_file = project_root / args.input

    if args.output:
        output_file = project_root / args.output
    else:
        # デフォルト: 入力ファイル名に _fixed を追加
        stem = input_file.stem
        output_file = input_file.parent / f"{stem}_fixed.csv"

    tse_file = project_root / args.tse

    print(f"入力ファイル: {input_file}")
    print(f"出力ファイル: {output_file}")
    print(f"東証全銘柄: {tse_file}")
    print()

    # ファイル存在チェック
    if not input_file.exists():
        logger.error(f"入力ファイルが見つかりません: {input_file}")
        return 1

    if not tse_file.exists():
        logger.error(f"東証全銘柄ファイルが見つかりません: {tse_file}")
        return 1

    # 東証全銘柄データを読み込み
    code_to_name = load_tse_names(tse_file)

    if not code_to_name:
        logger.error("東証全銘柄データが読み込めませんでした")
        return 1

    # 企業名を更新
    success = update_stock_names(input_file, output_file, code_to_name)

    print()
    print("=" * 60)
    print("処理完了" if success else "処理失敗")
    print("=" * 60)

    if success:
        print(f"出力ファイル: {output_file}")
        print()
        print("このファイルをデータベースにインポートできます:")
        print(f"  python scripts/import_major_stocks.py")
        print()
        print("または、アプリのメニューから [ファイル] > [CSVインポート] で読み込めます。")

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
