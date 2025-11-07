"""
優待銘柄データをCSVにエクスポート
スクレイピングで取得したデータをCSVに出力（DBには保存しない）

Usage:
    python scripts/export_yuutai_to_csv.py
    python scripts/export_yuutai_to_csv.py --output data/yuutai_export.csv
    python scripts/export_yuutai_to_csv.py --month 3
    python scripts/export_yuutai_to_csv.py --source yutai_net

Author: Yuutai Event Investor Team
Date: 2025-11-07
"""

import sys
from pathlib import Path
import argparse
import logging
import csv
from datetime import datetime

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.scrapers import ScraperManager


def setup_logging():
    """ログ設定"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def export_to_csv(stocks, output_path: Path):
    """
    銘柄データをCSVに出力

    Args:
        stocks: 銘柄データのリスト
        output_path: 出力先CSVファイルパス
    """
    if not stocks:
        print("警告: エクスポートするデータがありません")
        return

    print(f"\nCSVファイルに出力中: {output_path}")

    # CSVヘッダー
    fieldnames = [
        'code',
        'name',
        'rights_month',
        'rights_date',
        'yuutai_genre',
        'yuutai_content',
        'min_investment'
    ]

    try:
        with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for stock in stocks:
                # 必要なフィールドのみ抽出
                row = {
                    'code': stock.get('code', ''),
                    'name': stock.get('name', ''),
                    'rights_month': stock.get('rights_month', ''),
                    'rights_date': stock.get('rights_date', ''),
                    'yuutai_genre': stock.get('yuutai_genre', ''),
                    'yuutai_content': stock.get('yuutai_content', ''),
                    'min_investment': stock.get('min_investment', 0)
                }
                writer.writerow(row)

        print(f"[OK] CSVファイルを作成しました: {output_path}")
        print(f"  出力件数: {len(stocks)}件")

    except Exception as e:
        print(f"エラー: CSV出力に失敗しました - {e}")
        import traceback
        traceback.print_exc()


def fetch_and_export(source: str = None, month: int = None,
                     output_path: Path = None, mode: str = 'fallback'):
    """
    優待銘柄を取得してCSVにエクスポート

    Args:
        source: スクレイパー名（'96ut', 'yutai_net', または None で全ソース）
        month: 権利確定月（1-12、または None で全月）
        output_path: 出力先CSVファイルパス
        mode: 'fallback'（フォールバック戦略）または 'all'（全ソース統合）

    Returns:
        int: 取得件数
    """
    print("\n" + "=" * 60)
    print("優待銘柄データ取得・CSV出力")
    print("=" * 60)

    if source:
        print(f"ソース: {source}")
    else:
        print(f"モード: {mode}")

    if month:
        print(f"対象月: {month}月")
    else:
        print("対象月: 全月（1-12月）")

    print(f"出力先: {output_path}")
    print()

    # スクレイパーマネージャーを初期化
    manager = ScraperManager()

    try:
        # データ取得
        print("データ取得中...")

        if source:
            # 特定のソースから取得
            stocks = manager.scrape_by_source(source, month=month)
        elif mode == 'all':
            # 全ソースから取得して統合
            stocks = manager.scrape_all(month=month)
        else:
            # フォールバック戦略（デフォルト）
            stocks = manager.scrape_with_fallback(month=month)

        print(f"\n取得件数: {len(stocks)}件")

        if not stocks:
            print("\n警告: データが取得できませんでした")
            return 0

        # 月別の統計
        month_counts = {}
        for stock in stocks:
            m = stock.get('rights_month')
            month_counts[m] = month_counts.get(m, 0) + 1

        print("\n月別統計:")
        for m in sorted(month_counts.keys()):
            print(f"  {m}月: {month_counts[m]}件")

        # CSVに出力
        export_to_csv(stocks, output_path)

        return len(stocks)

    except Exception as e:
        print(f"\nエラー: {e}")
        import traceback
        traceback.print_exc()
        return 0

    finally:
        manager.close_all()


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='優待銘柄データCSVエクスポートスクリプト')
    parser.add_argument('--output', '-o', type=str,
                       help='出力先CSVファイルパス（デフォルト: data/yuutai_YYYYMMDD_HHMMSS.csv）')
    parser.add_argument('--source', choices=['96ut', 'yutai_net'],
                       help='特定のソースから取得')
    parser.add_argument('--month', type=int, choices=range(1, 13),
                       help='特定の月のみ取得（1-12）')
    parser.add_argument('--all', action='store_true',
                       help='全ソースから取得して統合')

    args = parser.parse_args()

    setup_logging()

    print("=" * 60)
    print("優待銘柄データCSVエクスポートスクリプト")
    print("=" * 60)
    print()

    # 出力先パスを決定
    if args.output:
        output_path = Path(args.output)
    else:
        # デフォルト: data/yuutai_YYYYMMDD_HHMMSS.csv
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = project_root / "data" / f"yuutai_{timestamp}.csv"

    # 出力先ディレクトリを作成
    output_path.parent.mkdir(parents=True, exist_ok=True)

    mode = 'all' if args.all else 'fallback'
    count = fetch_and_export(
        source=args.source,
        month=args.month,
        output_path=output_path,
        mode=mode
    )

    print("\n" + "=" * 60)
    print("処理完了")
    print("=" * 60)
    print(f"取得件数: {count}件")
    print(f"出力先: {output_path}")
    print()

    if count > 0:
        print("CSVファイルを確認してください。")
        print("問題なければ、以下のコマンドでデータベースにインポートできます:")
        print(f"  python scripts/import_major_stocks.py")
        print()
        print("または、アプリのメニューから [ファイル] > [CSVインポート] で読み込めます。")

    return 0 if count > 0 else 1


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
