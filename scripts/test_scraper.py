"""
Scraper Test Script
スクレイパー機能のテスト

Usage:
    python scripts/test_scraper.py
    python scripts/test_scraper.py --source 96ut
    python scripts/test_scraper.py --source yutai_net --month 3
    python scripts/test_scraper.py --all

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

from src.scrapers import ScraperManager, Scraper96ut, ScraperYutaiNet


def setup_logging():
    """ログ設定"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def test_scraper_96ut(month: int = None):
    """96ut.com スクレイパーのテスト"""
    print("\n" + "=" * 60)
    print("96ut.com スクレイパーテスト")
    print("=" * 60)

    scraper = Scraper96ut()

    try:
        if month:
            term = f"{month}月末"
            print(f"\n対象: {term}")
            stocks = scraper.scrape_stocks(term=term)
        else:
            print("\n対象: 全月")
            stocks = scraper.scrape_stocks()

        print(f"\n取得件数: {len(stocks)}件")

        if stocks:
            print("\n最初の5件:")
            for i, stock in enumerate(stocks[:5], 1):
                print(f"\n[{i}] {stock['code']} - {stock['name']}")
                print(f"    権利確定: {stock['rights_month']}月 ({stock['rights_date']})")
                if stock.get('yuutai_content'):
                    print(f"    優待内容: {stock['yuutai_content'][:50]}...")

    except Exception as e:
        print(f"\nエラー: {e}")
        import traceback
        traceback.print_exc()

    finally:
        scraper.close()


def test_scraper_yutai_net(month: int = None):
    """yutai.net-ir.ne.jp スクレイパーのテスト"""
    print("\n" + "=" * 60)
    print("yutai.net-ir.ne.jp スクレイパーテスト")
    print("=" * 60)

    scraper = ScraperYutaiNet()

    try:
        if month:
            print(f"\n対象: {month}月")
            stocks = scraper.scrape_stocks(month=month)
        else:
            print("\n対象: 全月")
            stocks = scraper.scrape_stocks()

        print(f"\n取得件数: {len(stocks)}件")

        if stocks:
            print("\n最初の5件:")
            for i, stock in enumerate(stocks[:5], 1):
                print(f"\n[{i}] {stock['code']} - {stock['name']}")
                print(f"    権利確定: {stock['rights_month']}月 ({stock['rights_date']})")
                if stock.get('yuutai_content'):
                    print(f"    優待内容: {stock['yuutai_content'][:50]}...")
                if stock.get('min_investment'):
                    print(f"    最低投資: {stock['min_investment']:,}円")

    except Exception as e:
        print(f"\nエラー: {e}")
        import traceback
        traceback.print_exc()

    finally:
        scraper.close()


def test_scraper_manager(month: int = None, mode: str = 'fallback'):
    """スクレイパーマネージャーのテスト"""
    print("\n" + "=" * 60)
    print(f"スクレイパーマネージャーテスト (mode={mode})")
    print("=" * 60)

    manager = ScraperManager()

    try:
        if month:
            print(f"\n対象: {month}月")
        else:
            print("\n対象: 全月")

        if mode == 'all':
            stocks = manager.scrape_all(month=month)
        else:  # fallback
            stocks = manager.scrape_with_fallback(month=month)

        print(f"\n取得件数: {len(stocks)}件")

        if stocks:
            print("\n最初の5件:")
            for i, stock in enumerate(stocks[:5], 1):
                print(f"\n[{i}] {stock['code']} - {stock['name']}")
                print(f"    権利確定: {stock['rights_month']}月 ({stock['rights_date']})")
                if stock.get('yuutai_content'):
                    print(f"    優待内容: {stock['yuutai_content'][:50]}...")
                if stock.get('min_investment'):
                    print(f"    最低投資: {stock['min_investment']:,}円")

            # 月別の統計
            month_counts = {}
            for stock in stocks:
                m = stock.get('rights_month')
                month_counts[m] = month_counts.get(m, 0) + 1

            print("\n月別統計:")
            for m in sorted(month_counts.keys()):
                print(f"  {m}月: {month_counts[m]}件")

    except Exception as e:
        print(f"\nエラー: {e}")
        import traceback
        traceback.print_exc()

    finally:
        manager.close_all()


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='スクレイパーテストスクリプト')
    parser.add_argument('--source', choices=['96ut', 'yutai_net', 'manager'],
                       default='manager', help='テストするスクレイパー')
    parser.add_argument('--month', type=int, choices=range(1, 13),
                       help='権利確定月（1-12）')
    parser.add_argument('--all', action='store_true',
                       help='全スクレイパーからデータを取得（マネージャーのみ）')

    args = parser.parse_args()

    setup_logging()

    print("=" * 60)
    print("スクレイパーテストスクリプト")
    print("=" * 60)
    print(f"テスト対象: {args.source}")
    if args.month:
        print(f"対象月: {args.month}月")
    print()

    if args.source == '96ut':
        test_scraper_96ut(args.month)
    elif args.source == 'yutai_net':
        test_scraper_yutai_net(args.month)
    else:  # manager
        mode = 'all' if args.all else 'fallback'
        test_scraper_manager(args.month, mode)

    print("\n" + "=" * 60)
    print("テスト完了")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n中断されました")
        sys.exit(1)
    except Exception as e:
        print(f"\nエラー: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
