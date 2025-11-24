"""
Data Fetcher Module
yfinanceを使った株価データ取得モジュール

Author: Yuutai Event Investor Team
Date: 2024-11-07
Version: 1.0.0
"""

import yfinance as yf
import pandas as pd
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging
from pathlib import Path

from src.core.database import DatabaseManager
from src.utils.ticker_utils import normalize_ticker, extract_code


class DataFetcher:
    """株価データを取得してデータベースに保存するクラス"""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """
        DataFetcherを初期化

        Args:
            db_manager: DatabaseManagerインスタンス（オプション）
        """
        self.db_manager = db_manager or DatabaseManager()
        self.logger = logging.getLogger(__name__)

    def fetch_stock_data(self, ticker: str, period: str = "5y") -> Optional[pd.DataFrame]:
        """
        yfinanceから株価データを取得

        Args:
            ticker: ティッカーコード（例: "9202", "AAPL"）
            period: 取得期間（"1y", "5y", "10y", "max"）

        Returns:
            pd.DataFrame: 株価データ、取得失敗時はNone

        Examples:
            >>> fetcher = DataFetcher()
            >>> df = fetcher.fetch_stock_data("9202", period="5y")
            >>> print(df.head())
        """
        try:
            # ティッカーコードを正規化（日本株の場合は.Tを追加）
            normalized_ticker = normalize_ticker(ticker)

            self.logger.info(f"株価データ取得開始: {normalized_ticker} (期間: {period})")

            # yfinanceでデータ取得
            stock = yf.Ticker(normalized_ticker)
            df = stock.history(period=period)

            # データが空の場合
            if df.empty:
                self.logger.warning(f"株価データが見つかりません: {normalized_ticker}")
                return None

            # カラム名を日本語化（オプション）
            df = df.rename(columns={
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })

            self.logger.info(f"株価データ取得完了: {normalized_ticker} ({len(df)}件)")
            return df

        except Exception as e:
            self.logger.error(f"株価データ取得エラー: {ticker} - {e}")
            return None

    def save_to_database(self, ticker: str, df: pd.DataFrame) -> bool:
        """
        株価データをデータベースに保存

        Args:
            ticker: ティッカーコード
            df: 株価データフレーム

        Returns:
            bool: 成功した場合True
        """
        try:
            # 証券コードを抽出（.Tを削除）
            code = extract_code(normalize_ticker(ticker))

            self.logger.info(f"データベースに保存開始: {code} ({len(df)}件)")

            success_count = 0
            error_count = 0

            # 1行ずつデータベースに挿入
            for date, row in df.iterrows():
                # 日付をYYYY-MM-DD形式に変換
                date_str = date.strftime('%Y-%m-%d')

                # データベースに保存
                result = self.db_manager.insert_price_history(
                    code=code,
                    date=date_str,
                    open_price=float(row['open']),
                    high=float(row['high']),
                    low=float(row['low']),
                    close=float(row['close']),
                    volume=int(row['volume'])
                )

                if result:
                    success_count += 1
                else:
                    error_count += 1

            self.logger.info(f"データベース保存完了: {code} (成功: {success_count}件, エラー: {error_count}件)")
            return error_count == 0

        except Exception as e:
            self.logger.error(f"データベース保存エラー: {ticker} - {e}")
            return False

    def get_cached_data(self, ticker: str, limit: Optional[int] = None) -> Optional[pd.DataFrame]:
        """
        データベースからキャッシュされた株価データを取得

        Args:
            ticker: ティッカーコード
            limit: 取得件数制限（オプション）

        Returns:
            pd.DataFrame: 株価データ、データがない場合はNone
        """
        try:
            # 証券コードを抽出
            code = extract_code(normalize_ticker(ticker))

            # データベースから取得
            price_history = self.db_manager.get_price_history(code, limit=limit)

            if not price_history:
                self.logger.info(f"キャッシュデータが見つかりません: {code}")
                return None

            # DataFrameに変換
            df = pd.DataFrame(price_history)

            # date列をインデックスに設定
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)

            # 不要な列を削除
            df.drop(['id', 'code'], axis=1, inplace=True, errors='ignore')

            # カラム名をyfinance形式に統一（大文字化）
            df = df.rename(columns={
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume'
            })

            # 日付の降順でソート（最新が上）
            df.sort_index(ascending=False, inplace=True)

            self.logger.info(f"キャッシュデータ取得完了: {code} ({len(df)}件)")
            return df

        except Exception as e:
            self.logger.error(f"キャッシュデータ取得エラー: {ticker} - {e}")
            return None

    def update_stock_data(self, ticker: str, period: str = "5y",
                          force_update: bool = False) -> Optional[pd.DataFrame]:
        """
        株価データを更新（キャッシュがあれば使用、なければ取得）

        Args:
            ticker: ティッカーコード
            period: 取得期間
            force_update: True の場合、キャッシュを無視して強制的に更新

        Returns:
            pd.DataFrame: 株価データ
        """
        try:
            # キャッシュをチェック
            if not force_update:
                cached_df = self.get_cached_data(ticker)

                if cached_df is not None and not cached_df.empty:
                    # キャッシュの最新日付を確認
                    latest_date = cached_df.index.max()
                    days_old = (datetime.now() - latest_date).days

                    # 7日以内のデータならキャッシュを使用
                    if days_old <= 7:
                        self.logger.info(f"キャッシュを使用: {ticker} (最終更新: {days_old}日前)")
                        return cached_df
                    else:
                        self.logger.info(f"キャッシュが古いため更新: {ticker} (最終更新: {days_old}日前)")

            # 新しいデータを取得
            df = self.fetch_stock_data(ticker, period=period)

            if df is None:
                self.logger.warning(f"データ取得失敗、キャッシュを使用: {ticker}")
                return self.get_cached_data(ticker)

            # データベースに保存
            self.save_to_database(ticker, df)

            return df

        except Exception as e:
            self.logger.error(f"株価データ更新エラー: {ticker} - {e}")
            return None

    def bulk_update(self, tickers: list, period: str = "5y") -> Dict[str, bool]:
        """
        複数銘柄の株価データを一括更新

        Args:
            tickers: ティッカーコードのリスト
            period: 取得期間

        Returns:
            Dict[str, bool]: ティッカーごとの成功/失敗
        """
        results = {}

        self.logger.info(f"一括更新開始: {len(tickers)}銘柄")

        for i, ticker in enumerate(tickers, 1):
            self.logger.info(f"進捗: {i}/{len(tickers)} - {ticker}")

            df = self.update_stock_data(ticker, period=period, force_update=True)
            results[ticker] = df is not None

        success_count = sum(1 for v in results.values() if v)
        self.logger.info(f"一括更新完了: 成功 {success_count}/{len(tickers)}銘柄")

        return results

    def get_latest_price(self, ticker: str) -> Optional[float]:
        """
        最新の株価（終値）を取得

        Args:
            ticker: ティッカーコード

        Returns:
            float: 最新の終値、取得失敗時はNone
        """
        try:
            df = self.get_cached_data(ticker, limit=1)

            if df is not None and not df.empty:
                return float(df['Close'].iloc[0])

            # キャッシュになければ最新データを取得
            df = self.fetch_stock_data(ticker, period="5d")

            if df is not None and not df.empty:
                return float(df['Close'].iloc[-1])

            return None

        except Exception as e:
            self.logger.error(f"最新株価取得エラー: {ticker} - {e}")
            return None

    def close(self):
        """
        リソースをクリーンアップ

        Note: macOSでのSQLite接続リークを防ぐため、
        スレッド終了時に呼び出すことを推奨
        """
        try:
            if self.db_manager:
                self.db_manager.close()
                self.logger.debug("DataFetcher リソースをクリーンアップしました")
        except Exception as e:
            self.logger.error(f"DataFetcher クリーンアップエラー: {e}")


# エイリアス（互換性のため）
StockDataFetcher = DataFetcher
