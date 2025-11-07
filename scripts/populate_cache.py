"""
Populate simulation_cache with sample data
サンプルデータでシミュレーションキャッシュを埋める
"""

import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging
from src.core.database import DatabaseManager
from src.core.calculator import OptimalTimingCalculator
from src.core.data_fetcher import StockDataFetcher

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """メイン処理"""
    logger.info("シミュレーションキャッシュデータ生成開始...")

    # データベースとフェッチャー初期化
    db = DatabaseManager()
    fetcher = StockDataFetcher()
    calculator = OptimalTimingCalculator(fetcher)

    # 全銘柄を取得
    stocks = db.get_all_stocks()
    logger.info(f"{len(stocks)}件の銘柄を取得しました")

    success_count = 0
    error_count = 0

    for i, stock in enumerate(stocks, 1):
        code = stock['code']
        name = stock['name']
        rights_month = stock.get('rights_month')
        rights_date = stock.get('rights_date')

        if not rights_date:
            logger.warning(f"[{i}/{len(stocks)}] {code} ({name}): 権利確定日が設定されていません。スキップします。")
            error_count += 1
            continue

        logger.info(f"[{i}/{len(stocks)}] {code} ({name}): バックテスト実行中...")

        try:
            # バックテストを実行
            result = calculator.find_optimal_timing(
                ticker=code,
                rights_date=rights_date
            )

            if result and result.get('all_results'):
                # 全結果をキャッシュに保存
                for day_result in result['all_results']:
                    db.save_simulation_cache(
                        code=code,
                        rights_month=rights_month,
                        buy_days_before=day_result['days_before'],
                        win_count=day_result['win_count'],
                        lose_count=day_result['lose_count'],
                        win_rate=day_result['win_rate'],
                        expected_return=day_result['expected_return'],
                        avg_win_return=day_result['avg_win_return'],
                        max_win_return=day_result['max_win_return'],
                        avg_lose_return=day_result['avg_lose_return'],
                        max_lose_return=day_result['max_lose_return']
                    )

                logger.info(f"  ✓ 成功: {len(result['all_results'])}件のデータを保存しました")
                logger.info(f"    最適日数: {result['optimal_days']}日前, "
                          f"勝率: {result['win_rate']*100:.1f}%, "
                          f"期待リターン: {result['expected_return']:+.2f}%")
                success_count += 1
            else:
                logger.warning(f"  ✗ データが取得できませんでした")
                error_count += 1

        except Exception as e:
            logger.error(f"  ✗ エラー: {e}")
            error_count += 1

    logger.info(f"\n完了: 成功 {success_count}件, エラー {error_count}件")

if __name__ == "__main__":
    main()
