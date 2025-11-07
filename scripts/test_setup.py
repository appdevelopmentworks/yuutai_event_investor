"""
Quick Test Script
動作確認用スクリプト

このスクリプトは主要機能の動作確認を行います。
"""

import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_database():
    """データベース機能のテスト"""
    logger.info("=" * 60)
    logger.info("データベース機能のテスト")
    logger.info("=" * 60)
    
    try:
        from src.core.database import DatabaseManager
        
        db = DatabaseManager()
        
        # データベースの存在確認
        if not db.db_path.exists():
            logger.error("❌ データベースが見つかりません")
            logger.info("以下のコマンドでデータベースを初期化してください:")
            logger.info("  python scripts/init_database.py")
            return False
        
        # 銘柄数を取得
        stocks = db.get_all_stocks()
        logger.info(f"✅ 登録銘柄数: {len(stocks)} 件")
        
        # サンプルデータを表示
        if stocks:
            logger.info("\n最初の3銘柄:")
            for stock in stocks[:3]:
                logger.info(f"  {stock['code']} - {stock['name']} ({stock['rights_month']}月)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ エラー: {e}")
        return False


def test_ticker_utils():
    """ティッカーユーティリティのテスト"""
    logger.info("\n" + "=" * 60)
    logger.info("ティッカーユーティリティのテスト")
    logger.info("=" * 60)
    
    try:
        from src.utils.ticker_utils import (
            check_ticker,
            is_japanese_stock,
            normalize_ticker,
            extract_code
        )
        
        # テストケース
        test_cases = [
            ("9202", "9202.T"),
            ("AAPL", "AAPL"),
            (" 8591 ", "8591.T")
        ]
        
        logger.info("\nティッカー変換テスト:")
        for input_ticker, expected in test_cases:
            result = normalize_ticker(input_ticker)
            status = "✅" if result == expected else "❌"
            logger.info(f"{status} '{input_ticker}' -> '{result}' (期待値: '{expected}')")
        
        # 日本株判定テスト
        logger.info("\n日本株判定テスト:")
        assert is_japanese_stock("9202.T") is True
        logger.info("✅ 9202.T は日本株")
        assert is_japanese_stock("AAPL") is False
        logger.info("✅ AAPL は日本株ではない")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ エラー: {e}")
        return False


def test_calculator():
    """計算エンジンのテスト"""
    logger.info("\n" + "=" * 60)
    logger.info("計算エンジンのテスト")
    logger.info("=" * 60)
    
    try:
        from src.core.calculator import Calculator
        import pandas as pd
        import numpy as np
        
        calc = Calculator()
        
        # サンプルデータを作成
        logger.info("\nサンプルデータで統計計算をテスト...")
        
        # 勝ちトレードのサンプルデータ
        win_data = pd.DataFrame({
            'リターン(%)': [2.5, 3.8, 1.2, 4.5, 2.1]
        })
        
        # 負けトレードのサンプルデータ
        lose_data = pd.DataFrame({
            'リターン(%)': [-1.5, -2.3, -0.8]
        })
        
        # 統計計算
        stats = calc.calculate_statistics(win_data, lose_data)
        
        logger.info(f"✅ 勝ちトレード: {stats['win_count']} 回")
        logger.info(f"✅ 負けトレード: {stats['lose_count']} 回")
        logger.info(f"✅ 勝率: {stats['win_rate']*100:.1f}%")
        logger.info(f"✅ 期待リターン: {stats['expected_return']:.2f}%")
        logger.info(f"✅ 平均勝ちリターン: {stats['avg_win_return']:.2f}%")
        logger.info(f"✅ 平均負けリターン: {stats['avg_lose_return']:.2f}%")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ エラー: {e}")
        return False


def test_ui_imports():
    """UI関連のインポートテスト"""
    logger.info("\n" + "=" * 60)
    logger.info("UI関連のインポートテスト")
    logger.info("=" * 60)
    
    try:
        # PySide6のインポート
        from PySide6.QtWidgets import QApplication
        logger.info("✅ PySide6 インポート成功")
        
        # メインウィンドウのインポート
        from src.ui.main_window import MainWindow
        logger.info("✅ MainWindow インポート成功")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ インポートエラー: {e}")
        logger.error("以下のコマンドで依存パッケージをインストールしてください:")
        logger.error("  pip install -r requirements.txt")
        return False
    except Exception as e:
        logger.error(f"❌ エラー: {e}")
        return False


def main():
    """メイン処理"""
    logger.info("\n🚀 Yuutai Event Investor - 動作確認テスト\n")
    
    results = []
    
    # 各種テストを実行
    results.append(("データベース", test_database()))
    results.append(("ティッカーユーティリティ", test_ticker_utils()))
    results.append(("計算エンジン", test_calculator()))
    results.append(("UI関連", test_ui_imports()))
    
    # 結果サマリー
    logger.info("\n" + "=" * 60)
    logger.info("テスト結果サマリー")
    logger.info("=" * 60)
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} - {test_name}")
        if not result:
            all_passed = False
    
    logger.info("=" * 60)
    
    if all_passed:
        logger.info("\n✅ すべてのテストに合格しました！")
        logger.info("\nアプリケーションを起動するには:")
        logger.info("  python main.py")
    else:
        logger.error("\n❌ 一部のテストに失敗しました")
        logger.error("エラーメッセージを確認して修正してください")
    
    logger.info("")


if __name__ == "__main__":
    main()
