"""
Test Data Fetcher Module
data_fetcherのテストコード

Author: Yuutai Event Investor Team
Date: 2024-11-07
"""

import pytest
import pandas as pd
from pathlib import Path
import sys

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.data_fetcher import DataFetcher
from src.core.database import DatabaseManager


class TestDataFetcher:
    """DataFetcherクラスのテスト"""

    @pytest.fixture
    def temp_db(self, tmp_path):
        """テスト用の一時データベースを作成"""
        db_path = tmp_path / "test_yuutai.db"
        db_manager = DatabaseManager(db_path)

        # データベース初期化
        sql_path = project_root / "data" / "create_tables.sql"
        if sql_path.exists():
            with open(sql_path, 'r', encoding='utf-8') as f:
                sql_script = f.read()
            conn = db_manager.connect()
            cursor = conn.cursor()
            cursor.executescript(sql_script)
            conn.commit()
            conn.close()

        return db_manager

    @pytest.fixture
    def fetcher(self, temp_db):
        """DataFetcherインスタンスを作成"""
        return DataFetcher(db_manager=temp_db)

    def test_fetch_stock_data_japanese_stock(self, fetcher):
        """日本株の株価データ取得テスト"""
        # 実際のAPIを呼び出すため、ネットワーク接続が必要
        df = fetcher.fetch_stock_data("9202", period="1mo")

        assert df is not None, "データが取得できませんでした"
        assert not df.empty, "データが空です"
        assert 'close' in df.columns, "close列が存在しません"
        assert len(df) > 0, "データが0件です"

    def test_fetch_stock_data_us_stock(self, fetcher):
        """米国株の株価データ取得テスト"""
        df = fetcher.fetch_stock_data("AAPL", period="1mo")

        assert df is not None, "データが取得できませんでした"
        assert not df.empty, "データが空です"
        assert 'close' in df.columns, "close列が存在しません"

    def test_save_to_database(self, fetcher):
        """データベースへの保存テスト"""
        # テストデータを作成
        dates = pd.date_range(start='2024-01-01', periods=5, freq='D')
        test_df = pd.DataFrame({
            'open': [100.0, 101.0, 102.0, 103.0, 104.0],
            'high': [105.0, 106.0, 107.0, 108.0, 109.0],
            'low': [95.0, 96.0, 97.0, 98.0, 99.0],
            'close': [102.0, 103.0, 104.0, 105.0, 106.0],
            'volume': [1000000, 1100000, 1200000, 1300000, 1400000]
        }, index=dates)

        # データベースに保存
        result = fetcher.save_to_database("9202", test_df)

        assert result is True, "データベース保存に失敗しました"

        # 保存されたデータを確認
        price_history = fetcher.db_manager.get_price_history("9202")
        assert len(price_history) == 5, "保存されたデータ件数が不正です"

    def test_get_cached_data(self, fetcher):
        """キャッシュデータ取得テスト"""
        # まずデータを保存
        dates = pd.date_range(start='2024-01-01', periods=3, freq='D')
        test_df = pd.DataFrame({
            'open': [100.0, 101.0, 102.0],
            'high': [105.0, 106.0, 107.0],
            'low': [95.0, 96.0, 97.0],
            'close': [102.0, 103.0, 104.0],
            'volume': [1000000, 1100000, 1200000]
        }, index=dates)

        fetcher.save_to_database("8151", test_df)

        # キャッシュから取得
        cached_df = fetcher.get_cached_data("8151")

        assert cached_df is not None, "キャッシュデータが取得できません"
        assert not cached_df.empty, "キャッシュデータが空です"
        assert len(cached_df) == 3, "キャッシュデータ件数が不正です"
        assert 'Close' in cached_df.columns, "Close列が存在しません"

    def test_get_cached_data_with_limit(self, fetcher):
        """キャッシュデータ取得（件数制限）テスト"""
        # データを保存
        dates = pd.date_range(start='2024-01-01', periods=10, freq='D')
        test_df = pd.DataFrame({
            'open': [100.0 + i for i in range(10)],
            'high': [105.0 + i for i in range(10)],
            'low': [95.0 + i for i in range(10)],
            'close': [102.0 + i for i in range(10)],
            'volume': [1000000 + i * 100000 for i in range(10)]
        }, index=dates)

        fetcher.save_to_database("7201", test_df)

        # 5件のみ取得
        cached_df = fetcher.get_cached_data("7201", limit=5)

        assert cached_df is not None, "キャッシュデータが取得できません"
        assert len(cached_df) == 5, f"キャッシュデータ件数が不正です（期待: 5件, 実際: {len(cached_df)}件）"

    def test_update_stock_data_no_cache(self, fetcher):
        """株価データ更新テスト（キャッシュなし）"""
        # キャッシュがない状態で更新
        df = fetcher.update_stock_data("9202", period="1mo", force_update=True)

        assert df is not None, "データ更新に失敗しました"
        assert not df.empty, "データが空です"

        # データベースに保存されているか確認
        cached_df = fetcher.get_cached_data("9202")
        assert cached_df is not None, "データベースに保存されていません"

    def test_get_latest_price(self, fetcher):
        """最新株価取得テスト"""
        # テストデータを保存
        dates = pd.date_range(start='2024-01-01', periods=3, freq='D')
        test_df = pd.DataFrame({
            'open': [100.0, 101.0, 102.0],
            'high': [105.0, 106.0, 107.0],
            'low': [95.0, 96.0, 97.0],
            'close': [102.0, 103.0, 104.0],
            'volume': [1000000, 1100000, 1200000]
        }, index=dates)

        fetcher.save_to_database("8151", test_df)

        # 最新株価を取得
        latest_price = fetcher.get_latest_price("8151")

        assert latest_price is not None, "最新株価が取得できません"
        assert latest_price == 104.0, f"最新株価が不正です（期待: 104.0, 実際: {latest_price}）"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
