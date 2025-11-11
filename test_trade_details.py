"""
トレード詳細取得のテストスクリプト
"""
import sys
import logging
from src.core.data_fetcher import StockDataFetcher
from src.core.calculator import OptimalTimingCalculator

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_trade_details():
    """トレード詳細取得をテスト"""
    # テスト用の銘柄（実際のコードに置き換えてください）
    ticker = "2914.T"  # JT
    rights_month = 12   # 12月
    buy_days_before = 30  # 30日前

    print(f"\n=== トレード詳細取得テスト ===")
    print(f"銘柄コード: {ticker}")
    print(f"権利確定月: {rights_month}月")
    print(f"買入日数: {buy_days_before}日前")
    print("=" * 50)

    try:
        # データ取得
        fetcher = StockDataFetcher()
        calculator = OptimalTimingCalculator(fetcher)

        print("\n株価データを取得中...")
        trade_details = calculator.get_trade_details(
            ticker,
            rights_month,
            buy_days_before
        )

        if trade_details:
            win_trades = trade_details.get('win_trades')
            lose_trades = trade_details.get('lose_trades')

            print(f"\n[OK] 取得成功!")
            print(f"  勝ちトレード数: {len(win_trades)}")
            print(f"  負けトレード数: {len(lose_trades)}")

            if not win_trades.empty:
                print(f"\n  win_trades列: {list(win_trades.columns)}")
                print(f"  リターン列チェック: 'リターン(%)' in columns = {'リターン(%)' in win_trades.columns}")
                print(f"  買入日列チェック: '買入日' in columns = {'買入日' in win_trades.columns}")

                # 最初の1件の買入日を表示
                first_row = win_trades.iloc[0]
                print(f"  サンプル - 権利付最終日: {win_trades.index[0]}, 買入日: {first_row.get('買入日', 'N/A')}")

            if not lose_trades.empty:
                print(f"\n  lose_trades列: {list(lose_trades.columns)}")
                print(f"  リターン列チェック: 'リターン(%)' in columns = {'リターン(%)' in lose_trades.columns}")
                print(f"  買入日列チェック: '買入日' in columns = {'買入日' in lose_trades.columns}")

            # リスク分析をテスト
            print("\n--- リスク分析テスト ---")
            from src.core.risk_analyzer import RiskAnalyzer

            analyzer = RiskAnalyzer()
            risk_metrics = analyzer.calculate_comprehensive_risk_metrics(
                win_trades,
                lose_trades
            )

            print(f"\nリスク指標:")
            print(f"  最大ドローダウン: {risk_metrics.get('max_drawdown', {})}")
            print(f"  VaR: {risk_metrics.get('var', {})}")
            print(f"  分布統計: {risk_metrics.get('distribution', {})}")
            print(f"  ソルティノレシオ: {risk_metrics.get('sortino_ratio', 0):.3f}")
            print(f"  カルマーレシオ: {risk_metrics.get('calmar_ratio', 0):.3f}")
            print(f"  トレードシーケンス: {risk_metrics.get('trade_sequence', {})}")

        else:
            print("\n[NG] 取得失敗: trade_detailsがNone")

    except Exception as e:
        print(f"\n[ERROR] エラー発生: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_trade_details()
