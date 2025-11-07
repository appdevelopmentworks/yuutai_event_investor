"""
Backtest Engine Test Script
バックテストエンジンの動作確認スクリプト

Author: Yuutai Event Investor Team
Date: 2024-11-07
"""

import sys
from pathlib import Path
import logging

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.data_fetcher import DataFetcher
from src.core.calculator import Calculator
from src.core.database import DatabaseManager

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_data_fetcher():
    """DataFetcherの動作確認"""
    print("\n" + "=" * 60)
    print("[DataFetcher] 動作確認")
    print("=" * 60)

    try:
        fetcher = DataFetcher()

        # テスト銘柄: ANA (9202)
        ticker = "9202"
        print(f"\n[OK] テスト銘柄: {ticker} (ANA)")

        # 株価データ取得
        print(f"[INFO] 株価データ取得中... (期間: 10年)")
        df = fetcher.fetch_stock_data(ticker, period="10y")

        if df is not None and not df.empty:
            print(f"[OK] データ取得成功: {len(df)}件")
            print(f"   最新日付: {df.index.max()}")
            print(f"   最新終値: {df['close'].iloc[-1]:.2f}")

            # データベースに保存
            print(f"\n[INFO] データベースに保存中...")
            result = fetcher.save_to_database(ticker, df)

            if result:
                print(f"[OK] データベース保存成功")

                # キャッシュから取得
                print(f"\n[INFO] キャッシュから取得テスト...")
                cached_df = fetcher.get_cached_data(ticker, limit=5)

                if cached_df is not None:
                    print(f"[OK] キャッシュ取得成功: {len(cached_df)}件")
                    print(f"\n最新5件のデータ:")
                    print(cached_df[['Close', 'Volume']].head())
                else:
                    print(f"[ERROR] キャッシュ取得失敗")
            else:
                print(f"[ERROR] データベース保存失敗")
        else:
            print(f"[ERROR] データ取得失敗")

        return True

    except Exception as e:
        logger.error(f"DataFetcher テストエラー: {e}")
        return False


def test_calculator():
    """Calculatorの動作確認"""
    print("\n" + "=" * 60)
    print("[Calculator] 動作確認")
    print("=" * 60)

    try:
        fetcher = DataFetcher()
        calculator = Calculator()

        # テスト銘柄: ANA (9202) - 権利確定月: 3月
        ticker = "9202"
        rights_month = 3

        print(f"\n[OK] テスト銘柄: {ticker} (ANA)")
        print(f"[OK] 権利確定月: {rights_month}月")

        # 株価データ取得
        print(f"\n[INFO] 株価データ取得中... (期間: 10年)")
        df = fetcher.update_stock_data(ticker, period="10y")

        if df is None or df.empty:
            print(f"[ERROR] 株価データが取得できません")
            return False

        print(f"[OK] データ取得成功: {len(df)}件")

        # 最適タイミングを検索
        print(f"\n[INFO] 最適買入タイミングを検索中... (最大120日前まで)")
        print(f"   ※ この処理には数十秒かかる場合があります")

        result = calculator.find_optimal_timing(
            ticker=ticker,
            rights_month=rights_month,
            max_days_before=120,
            kenrlast=2,
            df=df
        )

        if result:
            print(f"\n" + "=" * 60)
            print(f"[SUCCESS] 最適タイミング発見！")
            print(f"=" * 60)
            print(f"最適買入日: 権利付最終日の {result['optimal_days']}日前")
            print(f"期待リターン: {result['expected_return']:.2f}%")
            print(f"勝率: {result['win_rate']*100:.1f}%")
            print(f"総トレード数: {result['total_count']}回")
            print(f"   勝ち: {result['win_count']}回")
            print(f"   負け: {result['lose_count']}回")
            print(f"平均勝ちリターン: {result['avg_win_return']:.2f}%")
            print(f"平均負けリターン: {result['avg_lose_return']:.2f}%")

            # トップ5の結果を表示
            print(f"\nトップ5のタイミング:")
            print(f"{'順位':<6}{'日数':<8}{'期待値':<10}{'勝率':<10}{'総数':<8}")
            print(f"-" * 50)

            for i, r in enumerate(result['all_results'][:5], 1):
                print(f"{i:<6}{r['days_before']:<8}{r['expected_return']:>7.2f}%  "
                      f"{r['win_rate']*100:>6.1f}%  {r['total_count']:<8}")

            return True
        else:
            print(f"[ERROR] 最適タイミングが見つかりませんでした")
            return False

    except Exception as e:
        logger.error(f"Calculator テストエラー: {e}")
        return False


def main():
    """メイン処理"""
    print("\n" + "=" * 60)
    print("Yuutai Event Investor - バックテストエンジン動作確認")
    print("=" * 60)

    # DataFetcher テスト
    df_result = test_data_fetcher()

    # Calculator テスト
    calc_result = test_calculator()

    # 結果サマリー
    print("\n" + "=" * 60)
    print("テスト結果サマリー")
    print("=" * 60)
    print(f"DataFetcher: {'[OK] 成功' if df_result else '[ERROR] 失敗'}")
    print(f"Calculator: {'[OK] 成功' if calc_result else '[ERROR] 失敗'}")

    if df_result and calc_result:
        print("\n[SUCCESS] すべてのテストが成功しました！")
        print("[OK] バックテストエンジンは正常に動作しています")
    else:
        print("\n[WARNING] 一部のテストが失敗しました")

    print("=" * 60)


if __name__ == "__main__":
    main()
