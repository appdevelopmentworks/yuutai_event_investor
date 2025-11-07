"""
Database Manager Module
データベース操作を管理するモジュール

Author: Yuutai Event Investor Team
Date: 2024-11-07
Version: 1.0.0
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
import logging


class DatabaseManager:
    """データベース操作を管理するクラス"""
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        データベースマネージャーを初期化
        
        Args:
            db_path: データベースファイルのパス（デフォルト: data/yuutai.db）
        """
        if db_path is None:
            project_root = Path(__file__).parent.parent.parent
            db_path = project_root / "data" / "yuutai.db"
        
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        # データベースディレクトリが存在しない場合は作成
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
    def connect(self) -> sqlite3.Connection:
        """データベース接続を取得"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 結果を辞書形式で取得
        return conn
    
    def initialize_database(self) -> bool:
        """
        データベースを初期化（テーブル作成）
        
        Returns:
            bool: 成功した場合True
        """
        try:
            sql_path = self.db_path.parent / "create_tables.sql"
            
            if not sql_path.exists():
                self.logger.error(f"SQLファイルが見つかりません: {sql_path}")
                return False
            
            with open(sql_path, 'r', encoding='utf-8') as f:
                sql_script = f.read()
            
            conn = self.connect()
            cursor = conn.cursor()
            cursor.executescript(sql_script)
            conn.commit()
            conn.close()
            
            self.logger.info("データベースの初期化が完了しました")
            return True
            
        except Exception as e:
            self.logger.error(f"データベース初期化エラー: {e}")
            return False
    
    # ==========================================
    # 銘柄マスタ操作
    # ==========================================
    
    def insert_stock(self, code: str, name: str, rights_month: int,
                     rights_date: Optional[str] = None,
                     yuutai_genre: Optional[str] = None,
                     yuutai_content: Optional[str] = None,
                     yuutai_detail: Optional[str] = None,
                     min_shares: Optional[int] = None,
                     data_source: Optional[str] = None) -> bool:
        """
        銘柄を追加

        Args:
            code: 証券コード
            name: 銘柄名
            rights_month: 権利確定月
            rights_date: 権利確定日（YYYY-MM-DD形式）
            yuutai_genre: 優待ジャンル
            yuutai_content: 優待内容（簡易）
            yuutai_detail: 優待内容（詳細）
            min_shares: 最低必要株数
            data_source: データソース

        Returns:
            bool: 成功した場合True
        """
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO stocks
                (code, name, rights_month, rights_date, yuutai_genre, yuutai_content,
                 yuutai_detail, min_shares, data_source, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (code, name, rights_month, rights_date, yuutai_genre, yuutai_content,
                  yuutai_detail, min_shares, data_source))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            self.logger.error(f"銘柄追加エラー: {e}")
            return False
    
    def get_stock(self, code: str, rights_month: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        銘柄情報を取得（複合主キー対応）

        Args:
            code: 証券コード
            rights_month: 権利確定月（指定時は特定の月のレコードを取得、未指定時は最初のレコード）

        Returns:
            Dict: 銘柄情報、存在しない場合None
        """
        try:
            conn = self.connect()
            cursor = conn.cursor()

            if rights_month is not None:
                # 権利確定月を指定した場合
                cursor.execute(
                    "SELECT * FROM stocks WHERE code = ? AND rights_month = ?",
                    (code, rights_month)
                )
            else:
                # 権利確定月を指定しない場合は最初のレコード
                cursor.execute("SELECT * FROM stocks WHERE code = ?", (code,))

            row = cursor.fetchone()
            conn.close()

            if row:
                return dict(row)
            return None

        except Exception as e:
            self.logger.error(f"銘柄取得エラー: {e}")
            return None

    def get_stocks_by_code(self, code: str) -> List[Dict[str, Any]]:
        """
        同じ証券コードの全銘柄を取得（複数月の優待に対応）

        Args:
            code: 証券コード

        Returns:
            List[Dict]: 銘柄情報のリスト
        """
        try:
            conn = self.connect()
            cursor = conn.cursor()

            cursor.execute(
                "SELECT * FROM stocks WHERE code = ? ORDER BY rights_month",
                (code,)
            )
            rows = cursor.fetchall()
            conn.close()

            return [dict(row) for row in rows]

        except Exception as e:
            self.logger.error(f"銘柄一覧取得エラー: {e}")
            return []
    
    def get_all_stocks(self, rights_month: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        全銘柄を取得
        
        Args:
            rights_month: 権利確定月でフィルター（オプション）
            
        Returns:
            List[Dict]: 銘柄情報のリスト
        """
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            if rights_month:
                cursor.execute(
                    "SELECT * FROM stocks WHERE rights_month = ? ORDER BY code",
                    (rights_month,)
                )
            else:
                cursor.execute("SELECT * FROM stocks ORDER BY code")
            
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            self.logger.error(f"銘柄一覧取得エラー: {e}")
            return []
    
    # ==========================================
    # 株価履歴操作
    # ==========================================
    
    def insert_price_history(self, code: str, date: str, open_price: float,
                            high: float, low: float, close: float,
                            volume: int) -> bool:
        """
        株価履歴を追加
        
        Args:
            code: 証券コード
            date: 日付（YYYY-MM-DD形式）
            open_price: 始値
            high: 高値
            low: 安値
            close: 終値
            volume: 出来高
            
        Returns:
            bool: 成功した場合True
        """
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO price_history 
                (code, date, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (code, date, open_price, high, low, close, volume))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            self.logger.error(f"株価履歴追加エラー: {e}")
            return False
    
    def get_price_history(self, code: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        株価履歴を取得
        
        Args:
            code: 証券コード
            limit: 取得件数制限（オプション）
            
        Returns:
            List[Dict]: 株価履歴のリスト
        """
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            if limit:
                cursor.execute("""
                    SELECT * FROM price_history 
                    WHERE code = ? 
                    ORDER BY date DESC 
                    LIMIT ?
                """, (code, limit))
            else:
                cursor.execute("""
                    SELECT * FROM price_history 
                    WHERE code = ? 
                    ORDER BY date DESC
                """, (code,))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            self.logger.error(f"株価履歴取得エラー: {e}")
            return []
    
    # ==========================================
    # シミュレーションキャッシュ操作
    # ==========================================
    
    def insert_simulation_cache(self, code: str, rights_month: int,
                                buy_days_before: int, win_count: int,
                                lose_count: int, win_rate: float,
                                expected_return: float, avg_win_return: float,
                                max_win_return: float, avg_lose_return: float,
                                max_lose_return: float) -> bool:
        """
        シミュレーション結果をキャッシュに保存
        
        Returns:
            bool: 成功した場合True
        """
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO simulation_cache 
                (code, rights_month, buy_days_before, win_count, lose_count,
                 win_rate, expected_return, avg_win_return, max_win_return,
                 avg_lose_return, max_lose_return, calculated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (code, rights_month, buy_days_before, win_count, lose_count,
                  win_rate, expected_return, avg_win_return, max_win_return,
                  avg_lose_return, max_lose_return))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            self.logger.error(f"シミュレーションキャッシュ保存エラー: {e}")
            return False
    
    def get_simulation_cache(self, code: str, rights_month: int) -> List[Dict[str, Any]]:
        """
        シミュレーション結果を取得

        Args:
            code: 証券コード
            rights_month: 権利確定月

        Returns:
            List[Dict]: シミュレーション結果のリスト
        """
        try:
            conn = self.connect()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM simulation_cache
                WHERE code = ? AND rights_month = ?
                ORDER BY buy_days_before
            """, (code, rights_month))

            rows = cursor.fetchall()
            conn.close()

            return [dict(row) for row in rows]

        except Exception as e:
            self.logger.error(f"シミュレーションキャッシュ取得エラー: {e}")
            return []

    def get_best_simulation_result(self, code: str) -> Optional[Dict[str, Any]]:
        """
        最適なシミュレーション結果を取得（期待リターン×勝率が最高のもの）

        Args:
            code: 証券コード

        Returns:
            Dict: 最適なシミュレーション結果、存在しない場合はNone
        """
        try:
            conn = self.connect()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM simulation_cache
                WHERE code = ?
                ORDER BY (expected_return * win_rate) DESC
                LIMIT 1
            """, (code,))

            row = cursor.fetchone()
            conn.close()

            return dict(row) if row else None

        except Exception as e:
            self.logger.error(f"最適シミュレーション結果取得エラー: {e}")
            return None
    
    # ==========================================
    # ウォッチリスト操作
    # ==========================================
    
    def add_to_watchlist(self, code: str, memo: Optional[str] = None) -> bool:
        """ウォッチリストに追加"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO watchlist (code, memo, added_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (code, memo))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            self.logger.error(f"ウォッチリスト追加エラー: {e}")
            return False
    
    def remove_from_watchlist(self, code: str) -> bool:
        """ウォッチリストから削除"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM watchlist WHERE code = ?", (code,))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            self.logger.error(f"ウォッチリスト削除エラー: {e}")
            return False
    
    def get_watchlist(self) -> List[Dict[str, Any]]:
        """ウォッチリストを取得"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT w.*, s.name, s.rights_month 
                FROM watchlist w
                JOIN stocks s ON w.code = s.code
                ORDER BY w.added_at DESC
            """)
            
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            self.logger.error(f"ウォッチリスト取得エラー: {e}")
            return []
    
    # ==========================================
    # ユーティリティ
    # ==========================================
    
    def get_schema_version(self) -> Optional[int]:
        """スキーマバージョンを取得"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            cursor.execute("SELECT MAX(version) as version FROM schema_version")
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return row['version']
            return None
            
        except Exception as e:
            self.logger.error(f"スキーマバージョン取得エラー: {e}")
            return None

    # ==========================================
    # 銘柄データ操作（CSVインポート用）
    # ==========================================

    def get_stock_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """
        銘柄コードで銘柄を取得

        Args:
            code: 銘柄コード

        Returns:
            Dict: 銘柄データ、存在しない場合はNone
        """
        try:
            conn = self.connect()
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM stocks WHERE code = ?", (code,))
            row = cursor.fetchone()
            conn.close()

            return dict(row) if row else None

        except Exception as e:
            self.logger.error(f"銘柄取得エラー: {e}")
            return None

    def add_stock(self, code: str, name: str, rights_month: Optional[int],
                  rights_date: str, yuutai_genre: str = '',
                  yuutai_content: str = '', min_investment: int = 0) -> bool:
        """
        新規銘柄を追加

        Args:
            code: 銘柄コード
            name: 銘柄名
            rights_month: 権利確定月
            rights_date: 権利確定日
            yuutai_genre: 優待ジャンル
            yuutai_content: 優待内容
            min_investment: 最低投資金額

        Returns:
            bool: 成功時True
        """
        try:
            conn = self.connect()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO stocks (code, name, rights_month, rights_date,
                                  yuutai_genre, yuutai_content, min_investment)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (code, name, rights_month, rights_date, yuutai_genre,
                  yuutai_content, min_investment))

            conn.commit()
            conn.close()

            self.logger.info(f"銘柄追加成功: {code} - {name}")
            return True

        except Exception as e:
            self.logger.error(f"銘柄追加エラー: {e}")
            return False

    def update_stock(self, code: str, name: str, rights_month: Optional[int],
                    rights_date: str, yuutai_genre: str = '',
                    yuutai_content: str = '', min_investment: int = 0) -> bool:
        """
        既存銘柄を更新

        Args:
            code: 銘柄コード
            name: 銘柄名
            rights_month: 権利確定月
            rights_date: 権利確定日
            yuutai_genre: 優待ジャンル
            yuutai_content: 優待内容
            min_investment: 最低投資金額

        Returns:
            bool: 成功時True
        """
        try:
            conn = self.connect()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE stocks
                SET name = ?, rights_month = ?, rights_date = ?,
                    yuutai_genre = ?, yuutai_content = ?, min_investment = ?
                WHERE code = ?
            """, (name, rights_month, rights_date, yuutai_genre,
                  yuutai_content, min_investment, code))

            conn.commit()
            conn.close()

            self.logger.info(f"銘柄更新成功: {code} - {name}")
            return True

        except Exception as e:
            self.logger.error(f"銘柄更新エラー: {e}")
            return False
