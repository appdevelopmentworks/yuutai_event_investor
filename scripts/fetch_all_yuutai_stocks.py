"""
全優待銘柄取得スクリプト
スクレイピングで全優待銘柄を取得してデータベースに保存

Usage:
    python scripts/fetch_all_yuutai_stocks.py
    python scripts/fetch_all_yuutai_stocks.py --source yutai_net
    python scripts/fetch_all_yuutai_stocks.py --month 3

Author: Yuutai Event Investor Team
Date: 2025-11-07
"""

import sys
from pathlib import Path
import argparse
import logging

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.scrapers import ScraperManager
from src.core.database import DatabaseManager


def setup_logging():
    """ログ設定"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def fetch_and_save_stocks(source: str = None, month: int = None, mode: str = 'fallback'):
    """
    優待銘柄を取得してデータベースに保存

    Args:
        source: スクレイパー名（'96ut', 'yutai_net', または None で全ソース）
        month: 権利確定月（1-12、または None で全月）
        mode: 'fallback'（フォールバック戦略）または 'all'（全ソース統合）

    Returns:
        Tuple[int, int]: (成功件数, エラー件数)
    """
    print("\n" + "=" * 60)
    print("優待銘柄データ取得")
    print("=" * 60)

    if source:
        print(f"ソース: {source}")
    else:
        print(f"モード: {mode}")

    if month:
        print(f"対象月: {month}月")
    else:
        print("対象月: 全月（1-12月）")

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
            return 0, 0

        # 月別の統計
        month_counts = {}
        for stock in stocks:
            m = stock.get('rights_month')
            month_counts[m] = month_counts.get(m, 0) + 1

        print("\n月別統計:")
        for m in sorted(month_counts.keys()):
            print(f"  {m}月: {month_counts[m]}件")

        # データベースに保存
        print("\nデータベースに保存中...")
        db = DatabaseManager()

        success_count = 0
        error_count = 0
        updated_count = 0
        inserted_count = 0

        for i, stock in enumerate(stocks, 1):
            try:
                # 既存のデータを確認
                existing = db.get_stock_by_code(stock['code'])

                # データベースに保存
                conn = db.connect()
                cursor = conn.cursor()

                if existing:
                    # 更新
                    cursor.execute("""
                        UPDATE stocks
                        SET name = ?, rights_month = ?, rights_date = ?,
                            yuutai_genre = ?, yuutai_content = ?, min_investment = ?
                        WHERE code = ?
                    """, (
                        stock['name'],
                        stock['rights_month'],
                        stock['rights_date'],
                        stock.get('yuutai_genre', ''),
                        stock.get('yuutai_content', ''),
                        stock.get('min_investment', 0),
                        stock['code']
                    ))
                    updated_count += 1
                else:
                    # 新規挿入
                    cursor.execute("""
                        INSERT INTO stocks (code, name, rights_month, rights_date,
                                          yuutai_genre, yuutai_content, min_investment)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        stock['code'],
                        stock['name'],
                        stock['rights_month'],
                        stock['rights_date'],
                        stock.get('yuutai_genre', ''),
                        stock.get('yuutai_content', ''),
                        stock.get('min_investment', 0)
                    ))
                    inserted_count += 1

                conn.commit()
                conn.close()
                success_count += 1

                # 進捗表示
                if i % 100 == 0:
                    print(f"  {i}/{len(stocks)}件処理中...")

            except Exception as e:
                print(f"  [ERROR] {stock['code']} - {e}")
                error_count += 1

        print(f"\n処理完了: {len(stocks)}件")
        print(f"  新規挿入: {inserted_count}件")
        print(f"  更新: {updated_count}件")
        print(f"  エラー: {error_count}件")

        return success_count, error_count

    except Exception as e:
        print(f"\nエラー: {e}")
        import traceback
        traceback.print_exc()
        return 0, 0

    finally:
        manager.close_all()


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='全優待銘柄取得スクリプト')
    parser.add_argument('--source', choices=['96ut', 'yutai_net'],
                       help='特定のソースから取得')
    parser.add_argument('--month', type=int, choices=range(1, 13),
                       help='特定の月のみ取得（1-12）')
    parser.add_argument('--all', action='store_true',
                       help='全ソースから取得して統合')

    args = parser.parse_args()

    setup_logging()

    print("=" * 60)
    print("全優待銘柄取得スクリプト")
    print("=" * 60)
    print()

    mode = 'all' if args.all else 'fallback'
    success, errors = fetch_and_save_stocks(
        source=args.source,
        month=args.month,
        mode=mode
    )

    print("\n" + "=" * 60)
    print("処理完了")
    print("=" * 60)
    print(f"成功: {success}件")
    print(f"失敗: {errors}件")
    print()

    if success > 0:
        print("アプリを再起動すると新しいデータが表示されます。")

    return 0 if errors == 0 else 1


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
