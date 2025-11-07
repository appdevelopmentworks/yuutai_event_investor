"""
Unit Tests for Database Module
データベースモジュールのテスト

Author: Yuutai Event Investor Team
Date: 2024-11-07
Version: 1.0.0
"""

import pytest
import sqlite3
from pathlib import Path
import tempfile
import sys

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.database import DatabaseManager


@pytest.fixture
def temp_db():
    """テスト用の一時データベースを作成"""
    # 一時ファイルを作成
    with tempfile.NamedTemporaryFile(mode='w', suffix='.db', delete=False) as f:
        db_path = Path(f.name)
    
    # DatabaseManagerを作成
    db = DatabaseManager(db_path)
    
    # スキーマを初期化
    db.initialize_database()
    
    yield db
    
    # テスト後にクリーンアップ
    if db_path.exists():
        db_path.unlink()


class TestDatabaseManager:
    """DatabaseManagerクラスのテスト"""
    
    def test_initialize_database(self, temp_db):
        """データベース初期化のテスト"""
        # スキーマバージョンを確認
        version = temp_db.get_schema_version()
        assert version == 1
        
        # テーブルが作成されているか確認
        conn = temp_db.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            ORDER BY name
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        expected_tables = [
            'notifications',
            'price_history',
            'schema_version',
            'simulation_cache',
            'stocks',
            'watchlist'
        ]
        
        for table in expected_tables:
            assert table in tables
    
    def test_insert_and_get_stock(self, temp_db):
        """銘柄の追加と取得のテスト"""
        # 銘柄を追加
        result = temp_db.insert_stock(
            code="9202",
            name="ANAホールディングス",
            rights_month=3,
            yuutai_genre="優待券",
            yuutai_content="国内線50%割引券",
            min_shares=100
        )
        
        assert result is True
        
        # 銘柄を取得
        stock = temp_db.get_stock("9202")
        
        assert stock is not None
        assert stock['code'] == "9202"
        assert stock['name'] == "ANAホールディングス"
        assert stock['rights_month'] == 3
        assert stock['yuutai_genre'] == "優待券"
    
    def test_get_all_stocks(self, temp_db):
        """全銘柄取得のテスト"""
        # 複数の銘柄を追加
        stocks_data = [
            ("9202", "ANAホールディングス", 3),
            ("8591", "オリックス", 3),
            ("2914", "日本たばこ産業", 12)
        ]
        
        for code, name, month in stocks_data:
            temp_db.insert_stock(code=code, name=name, rights_month=month)
        
        # 全銘柄を取得
        all_stocks = temp_db.get_all_stocks()
        assert len(all_stocks) == 3
        
        # 3月銘柄のみ取得
        march_stocks = temp_db.get_all_stocks(rights_month=3)
        assert len(march_stocks) == 2
        
        # 12月銘柄のみ取得
        december_stocks = temp_db.get_all_stocks(rights_month=12)
        assert len(december_stocks) == 1
    
    def test_insert_price_history(self, temp_db):
        """株価履歴追加のテスト"""
        # 先に銘柄を追加
        temp_db.insert_stock(code="9202", name="ANAホールディングス", rights_month=3)
        
        # 株価履歴を追加
        result = temp_db.insert_price_history(
            code="9202",
            date="2024-01-15",
            open_price=3500.0,
            high=3600.0,
            low=3450.0,
            close=3550.0,
            volume=1000000
        )
        
        assert result is True
        
        # 株価履歴を取得
        history = temp_db.get_price_history("9202")
        
        assert len(history) == 1
        assert history[0]['code'] == "9202"
        assert history[0]['close'] == 3550.0
    
    def test_watchlist(self, temp_db):
        """ウォッチリスト機能のテスト"""
        # 銘柄を追加
        temp_db.insert_stock(code="9202", name="ANAホールディングス", rights_month=3)
        
        # ウォッチリストに追加
        result = temp_db.add_to_watchlist("9202", memo="注目銘柄")
        assert result is True
        
        # ウォッチリストを取得
        watchlist = temp_db.get_watchlist()
        assert len(watchlist) == 1
        assert watchlist[0]['code'] == "9202"
        assert watchlist[0]['memo'] == "注目銘柄"
        
        # ウォッチリストから削除
        result = temp_db.remove_from_watchlist("9202")
        assert result is True
        
        # 削除確認
        watchlist = temp_db.get_watchlist()
        assert len(watchlist) == 0
    
    def test_simulation_cache(self, temp_db):
        """シミュレーションキャッシュのテスト"""
        # 銘柄を追加
        temp_db.insert_stock(code="9202", name="ANAホールディングス", rights_month=3)
        
        # シミュレーション結果を保存
        result = temp_db.insert_simulation_cache(
            code="9202",
            rights_month=3,
            buy_days_before=5,
            win_count=7,
            lose_count=3,
            win_rate=0.7,
            expected_return=2.5,
            avg_win_return=4.0,
            max_win_return=8.5,
            avg_lose_return=-1.5,
            max_lose_return=-3.2
        )
        
        assert result is True
        
        # シミュレーション結果を取得
        cache = temp_db.get_simulation_cache("9202", 3)
        
        assert len(cache) == 1
        assert cache[0]['buy_days_before'] == 5
        assert cache[0]['win_rate'] == 0.7
        assert cache[0]['expected_return'] == 2.5


class TestTickerUtils:
    """ticker_utilsモジュールのテスト"""
    
    def test_check_ticker(self):
        """ティッカーコードチェックのテスト"""
        from src.utils.ticker_utils import check_ticker
        
        # 日本株
        assert check_ticker("9202") == "9202.T"
        assert check_ticker("8591") == "8591.T"
        
        # 米国株（変更されないはず）
        assert check_ticker("AAPL") == "AAPL"
        assert check_ticker("TSLA") == "TSLA"
    
    def test_is_japanese_stock(self):
        """日本株判定のテスト"""
        from src.utils.ticker_utils import is_japanese_stock
        
        assert is_japanese_stock("9202.T") is True
        assert is_japanese_stock("9202") is True
        assert is_japanese_stock("AAPL") is False
    
    def test_normalize_ticker(self):
        """ティッカー正規化のテスト"""
        from src.utils.ticker_utils import normalize_ticker
        
        assert normalize_ticker(" 9202 ") == "9202.T"
        assert normalize_ticker("aapl") == "AAPL"
        assert normalize_ticker("  TSLA  ") == "TSLA"
    
    def test_extract_code(self):
        """証券コード抽出のテスト"""
        from src.utils.ticker_utils import extract_code
        
        assert extract_code("9202.T") == "9202"
        assert extract_code("AAPL") == "AAPL"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
