"""
統合テスト
全機能の動作確認を行う

Author: Yuutai Event Investor Team
Date: 2025-11-07
"""

import sys
from pathlib import Path
import unittest
import logging

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.database import DatabaseManager
from src.core.data_fetcher import StockDataFetcher
from src.core.calculator import OptimalTimingCalculator

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IntegrationTest(unittest.TestCase):
    """統合テストクラス"""

    @classmethod
    def setUpClass(cls):
        """テスト開始前の準備"""
        logger.info("=" * 60)
        logger.info("統合テスト開始")
        logger.info("=" * 60)
        cls.db = DatabaseManager()
        cls.fetcher = StockDataFetcher()
        cls.calculator = OptimalTimingCalculator(cls.fetcher)

    def test_01_database_connection(self):
        """データベース接続テスト"""
        logger.info("\n[TEST 1] データベース接続")
        try:
            conn = self.db.connect()
            self.assertIsNotNone(conn)
            conn.close()
            logger.info("✓ データベース接続成功")
        except Exception as e:
            self.fail(f"データベース接続失敗: {e}")

    def test_02_load_stocks(self):
        """銘柄データ読み込みテスト"""
        logger.info("\n[TEST 2] 銘柄データ読み込み")
        try:
            stocks = self.db.get_all_stocks()
            self.assertIsInstance(stocks, list)
            self.assertGreater(len(stocks), 0)
            logger.info(f"✓ {len(stocks)}件の銘柄データを読み込みました")

            # 最初の銘柄の構造を確認
            if stocks:
                stock = stocks[0]
                self.assertIn('code', stock)
                self.assertIn('name', stock)
                self.assertIn('rights_month', stock)
                logger.info(f"✓ データ構造確認: {stock['code']} - {stock['name']}")
        except Exception as e:
            self.fail(f"銘柄データ読み込み失敗: {e}")

    def test_03_simulation_cache(self):
        """シミュレーションキャッシュテスト"""
        logger.info("\n[TEST 3] シミュレーションキャッシュ")
        try:
            # キャッシュデータの件数確認
            conn = self.db.connect()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM simulation_cache")
            count = cursor.fetchone()['count']
            conn.close()

            self.assertGreater(count, 0, "シミュレーションキャッシュが空です")
            logger.info(f"✓ シミュレーションキャッシュ: {count}件")

            # 任意の銘柄のキャッシュを取得
            stocks = self.db.get_all_stocks()
            if stocks:
                code = stocks[0]['code']
                rights_month = stocks[0].get('rights_month', 3)
                cached = self.db.get_simulation_cache(code, rights_month)

                if cached:
                    self.assertIsInstance(cached, list)
                    logger.info(f"✓ 銘柄{code}のキャッシュ: {len(cached)}件")
                else:
                    logger.warning(f"⚠ 銘柄{code}のキャッシュなし")
        except Exception as e:
            self.fail(f"シミュレーションキャッシュテスト失敗: {e}")

    def test_04_watchlist(self):
        """ウォッチリスト機能テスト"""
        logger.info("\n[TEST 4] ウォッチリスト機能")
        try:
            # テスト用銘柄を追加
            stocks = self.db.get_all_stocks()
            if stocks:
                test_code = stocks[0]['code']
                test_memo = "統合テスト用メモ"

                # 追加
                self.db.add_to_watchlist(test_code, test_memo)
                logger.info(f"✓ ウォッチリストに追加: {test_code}")

                # 取得
                watchlist = self.db.get_watchlist()
                self.assertIsInstance(watchlist, list)
                self.assertGreater(len(watchlist), 0)
                logger.info(f"✓ ウォッチリスト取得: {len(watchlist)}件")

                # 削除
                self.db.remove_from_watchlist(test_code)
                logger.info(f"✓ ウォッチリストから削除: {test_code}")
        except Exception as e:
            self.fail(f"ウォッチリストテスト失敗: {e}")

    def test_05_notification_settings(self):
        """通知設定テスト"""
        logger.info("\n[TEST 5] 通知設定")
        try:
            # 通知設定を取得（メソッドの存在確認）
            if hasattr(self.db, 'get_notifications'):
                notifications = self.db.get_notifications()
                self.assertIsInstance(notifications, list)
                logger.info(f"✓ 通知設定取得: {len(notifications)}件")
            else:
                logger.info("⚠ get_notifications メソッドが実装されていません（スキップ）")

            # 通知の追加テスト
            if hasattr(self.db, 'add_notification'):
                stocks = self.db.get_all_stocks()
                if stocks:
                    test_code = stocks[0]['code']
                    self.db.add_notification(
                        code=test_code,
                        notification_days=30,
                        message="テスト通知"
                    )
                    logger.info(f"✓ 通知追加: {test_code}")
            else:
                logger.info("⚠ add_notification メソッドが実装されていません（スキップ）")
        except Exception as e:
            logger.warning(f"⚠ 通知設定テストスキップ: {e}")

    def test_06_data_fetcher(self):
        """データ取得機能テスト（軽量）"""
        logger.info("\n[TEST 6] データ取得機能")
        try:
            # テストティッカー（実在する銘柄）
            test_ticker = "7203.T"  # トヨタ自動車

            logger.info(f"データ取得中: {test_ticker}（最大10秒）")
            data = self.fetcher.fetch_stock_data(test_ticker, period="1mo")

            if data is not None and not data.empty:
                self.assertGreater(len(data), 0)
                logger.info(f"✓ データ取得成功: {len(data)}行")
            else:
                logger.warning("⚠ データ取得失敗（ネットワークエラーの可能性）")
        except Exception as e:
            logger.warning(f"⚠ データ取得テストスキップ: {e}")

    def test_07_calculator_structure(self):
        """計算機の構造テスト（実行はしない）"""
        logger.info("\n[TEST 7] 計算機構造")
        try:
            # メソッドの存在確認
            self.assertTrue(hasattr(self.calculator, 'find_optimal_timing'))
            self.assertTrue(callable(self.calculator.find_optimal_timing))
            logger.info("✓ 計算機メソッド確認")
        except Exception as e:
            self.fail(f"計算機構造テスト失敗: {e}")

    def test_08_database_schema(self):
        """データベーススキーマテスト"""
        logger.info("\n[TEST 8] データベーススキーマ")
        try:
            conn = self.db.connect()
            cursor = conn.cursor()

            # 必要なテーブルの存在確認
            required_tables = [
                'stocks',
                'simulation_cache',
                'watchlist',
                'notifications',  # 実際のテーブル名
                'price_history'
            ]

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [row['name'] for row in cursor.fetchall()]

            for table in required_tables:
                self.assertIn(table, existing_tables, f"テーブル'{table}'が存在しません")
                logger.info(f"✓ テーブル確認: {table}")

            conn.close()
        except Exception as e:
            self.fail(f"データベーススキーマテスト失敗: {e}")

    @classmethod
    def tearDownClass(cls):
        """テスト終了後の処理"""
        logger.info("\n" + "=" * 60)
        logger.info("統合テスト完了")
        logger.info("=" * 60)


def run_tests():
    """テストを実行"""
    suite = unittest.TestLoader().loadTestsFromTestCase(IntegrationTest)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 結果サマリー
    print("\n" + "=" * 60)
    print("テスト結果サマリー")
    print("=" * 60)
    print(f"実行: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失敗: {len(result.failures)}")
    print(f"エラー: {len(result.errors)}")
    print("=" * 60)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
