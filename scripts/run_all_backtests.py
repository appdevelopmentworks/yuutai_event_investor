"""
全銘柄のバックテストを一括実行

Usage:
    python scripts/run_all_backtests.py

Author: Yuutai Event Investor Team
Date: 2025-11-07
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.database import DatabaseManager
from src.core.calculator import Calculator
from src.core.data_fetcher import DataFetcher

def main():
    print("=" * 60)
    print("全銘柄バックテスト実行")
    print("=" * 60)
    print()

    # データベース接続
    db_path = project_root / "data" / "yuutai.db"
    db = DatabaseManager(db_path)

    # 銘柄一覧を取得
    stocks = db.get_all_stocks()
    print(f"対象銘柄数: {len(stocks)}件")
    print()

    # データフェッチャーと計算機
    fetcher = DataFetcher(db)
    calculator = Calculator()

    success_count = 0
    error_count = 0

    for i, stock in enumerate(stocks, 1):
        code = stock['code']
        name = stock['name']
        rights_month = stock['rights_month']

        print(f"[{i}/{len(stocks)}] {code} - {name} ({rights_month}月)")

        try:
            # 株価データ取得
            ticker = f"{code}.T"
            df = fetcher.update_stock_data(ticker, period="10y")

            if df is None or df.empty:
                print(f"  [WARN] 株価データ取得失敗")
                error_count += 1
                continue

            print(f"  [OK] データ取得: {len(df)}件")

            # バックテスト実行
            result = calculator.find_optimal_timing(
                ticker=ticker,
                rights_month=rights_month,
                max_days_before=120,
                kenrlast=2,
                df=df
            )

            if result is None:
                print(f"  [WARN] バックテスト失敗（データ不足の可能性）")
                error_count += 1
                continue

            # 結果をキャッシュに保存
            db.save_simulation_result(
                code=code,
                rights_month=rights_month,
                optimal_days=result['optimal_days'],
                win_rate=result['win_rate'],
                expected_return=result['expected_return'],
                total_trades=result['total_count'],
                win_count=result['win_count'],
                lose_count=result['lose_count'],
                avg_win_return=result['avg_win_return'],
                avg_lose_return=result['avg_lose_return'],
                max_win_return=result['max_win_return'],
                max_lose_return=result['max_lose_return'],
                all_results=result['all_results']
            )

            print(f"  [OK] 最適: {result['optimal_days']}日前, 勝率: {result['win_rate']*100:.1f}%, 期待: {result['expected_return']:.2f}%")
            success_count += 1

        except Exception as e:
            print(f"  [ERROR] エラー: {e}")
            error_count += 1

        print()

    print("=" * 60)
    print("バックテスト完了")
    print("=" * 60)
    print(f"成功: {success_count}件")
    print(f"失敗: {error_count}件")
    print()
    print("アプリを再起動すると結果が表示されます。")

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
