"""
Batch Processor Module
バッチ処理・マルチスレッド処理モジュール

Author: Yuutai Event Investor Team
Date: 2024-11-07
"""

import logging
from typing import List, Dict, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from PySide6.QtCore import QObject, Signal
import time
import threading


class BatchCalculationWorkerSignals(QObject):
    """BatchCalculationWorker用のシグナル"""
    progress_updated = Signal(int, int)  # 現在の進捗, 全体数
    stock_completed = Signal(str, dict)  # 銘柄コード, 結果
    batch_completed = Signal(list)  # 全結果のリスト
    error_occurred = Signal(str, str)  # 銘柄コード, エラーメッセージ


class BatchCalculationWorker:
    """
    複数銘柄のバックテストを並列処理するワーカー

    Note: macOSでQThread + SQLiteの競合によるSIGSEGVクラッシュを回避するため、
    QThreadではなくthreading.Threadを使用
    """

    def __init__(
        self,
        stocks: List[Dict[str, Any]],
        calculator,
        max_workers: int = 4
    ):
        """
        Args:
            stocks: 処理する銘柄リスト
            calculator: OptimalTimingCalculatorインスタンス
            max_workers: 同時実行スレッド数
        """
        self.logger = logging.getLogger(__name__)
        self.stocks = stocks
        self.calculator = calculator
        self.max_workers = max_workers
        self.running = False
        self.results = []
        self.signals = BatchCalculationWorkerSignals()
        self._thread = None

    @property
    def progress_updated(self):
        return self.signals.progress_updated

    @property
    def stock_completed(self):
        return self.signals.stock_completed

    @property
    def batch_completed(self):
        return self.signals.batch_completed

    @property
    def error_occurred(self):
        return self.signals.error_occurred

    def start(self):
        """ワーカースレッドを開始"""
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def isRunning(self):
        """スレッドが実行中かどうか"""
        return self._thread is not None and self._thread.is_alive()

    def _run(self):
        """スレッドのメイン処理"""
        self.logger.info(f"バッチ計算開始: {len(self.stocks)}銘柄, {self.max_workers}スレッド")
        self.running = True
        self.results = []

        total_stocks = len(self.stocks)
        completed_count = 0

        try:
            # ThreadPoolExecutorで並列処理
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # 全銘柄の処理をsubmit
                future_to_stock = {
                    executor.submit(self._calculate_stock, stock): stock
                    for stock in self.stocks
                }

                # 完了した順に処理
                for future in as_completed(future_to_stock):
                    if not self.running:
                        self.logger.info("バッチ処理が中断されました")
                        break

                    stock = future_to_stock[future]
                    code = stock.get('code', '不明')

                    try:
                        result = future.result()
                        if result:
                            self.results.append(result)
                            self.stock_completed.emit(code, result)
                        completed_count += 1
                        self.progress_updated.emit(completed_count, total_stocks)

                    except Exception as e:
                        error_msg = f"計算エラー: {e}"
                        self.logger.error(f"{code}: {error_msg}", exc_info=True)
                        self.error_occurred.emit(code, error_msg)
                        completed_count += 1
                        self.progress_updated.emit(completed_count, total_stocks)

            self.logger.info(f"バッチ計算完了: {len(self.results)}件成功")
            self.batch_completed.emit(self.results)

        except Exception as e:
            self.logger.error(f"バッチ処理エラー: {e}", exc_info=True)
            self.error_occurred.emit("BATCH", str(e))

        finally:
            self.running = False

    def _calculate_stock(self, stock: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        1銘柄の計算を実行

        Args:
            stock: 銘柄データ

        Returns:
            Dict: 計算結果、失敗時はNone
        """
        code = stock.get('code')
        rights_date = stock.get('rights_date')

        if not code or not rights_date:
            self.logger.warning(f"銘柄情報が不足しています: {code}")
            return None

        try:
            # 最適タイミングを計算
            result = self.calculator.find_optimal_timing(
                ticker=code,
                rights_date=rights_date
            )

            if result:
                # 銘柄情報をマージ
                result.update({
                    'code': code,
                    'name': stock.get('name', ''),
                    'rights_month': stock.get('rights_month'),
                    'rights_date': rights_date,
                    'yuutai_genre': stock.get('yuutai_genre', ''),
                    'yuutai_content': stock.get('yuutai_content', '')
                })

            return result

        except Exception as e:
            self.logger.error(f"{code} の計算エラー: {e}")
            return None

    def stop(self):
        """処理を停止"""
        self.logger.info("バッチ処理停止要求")
        self.running = False


class ParallelDataFetcher:
    """
    複数銘柄の株価データを並列取得するクラス
    """

    def __init__(self, data_fetcher, max_workers: int = 4):
        """
        Args:
            data_fetcher: DataFetcherインスタンス
            max_workers: 同時実行スレッド数
        """
        self.logger = logging.getLogger(__name__)
        self.data_fetcher = data_fetcher
        self.max_workers = max_workers

    def fetch_multiple_stocks(
        self,
        ticker_list: List[str],
        period: str = '10y',
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Dict[str, Any]:
        """
        複数銘柄の株価データを並列取得

        Args:
            ticker_list: ティッカーコードのリスト
            period: 取得期間
            progress_callback: 進捗コールバック関数(current, total)

        Returns:
            Dict: {ticker: dataframe} の辞書
        """
        self.logger.info(f"並列データ取得開始: {len(ticker_list)}銘柄")

        results = {}
        total = len(ticker_list)
        completed = 0

        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_ticker = {
                    executor.submit(
                        self.data_fetcher.fetch_stock_data,
                        ticker,
                        period
                    ): ticker
                    for ticker in ticker_list
                }

                for future in as_completed(future_to_ticker):
                    ticker = future_to_ticker[future]

                    try:
                        df = future.result()
                        if df is not None and not df.empty:
                            results[ticker] = df
                        completed += 1

                        if progress_callback:
                            progress_callback(completed, total)

                    except Exception as e:
                        self.logger.error(f"{ticker} のデータ取得エラー: {e}")
                        completed += 1

                        if progress_callback:
                            progress_callback(completed, total)

            self.logger.info(f"並列データ取得完了: {len(results)}件成功")
            return results

        except Exception as e:
            self.logger.error(f"並列データ取得エラー: {e}", exc_info=True)
            return results


class ProgressTracker:
    """
    進捗状況を追跡するクラス
    """

    def __init__(self, total: int):
        """
        Args:
            total: 総タスク数
        """
        self.total = total
        self.completed = 0
        self.failed = 0
        self.start_time = time.time()

    def increment_completed(self):
        """完了カウントを増やす"""
        self.completed += 1

    def increment_failed(self):
        """失敗カウントを増やす"""
        self.failed += 1

    def get_progress_percentage(self) -> float:
        """
        進捗率を取得

        Returns:
            float: 進捗率（0.0-100.0）
        """
        if self.total == 0:
            return 0.0
        return (self.completed + self.failed) / self.total * 100.0

    def get_elapsed_time(self) -> float:
        """
        経過時間を取得

        Returns:
            float: 経過時間（秒）
        """
        return time.time() - self.start_time

    def get_estimated_remaining_time(self) -> Optional[float]:
        """
        推定残り時間を取得

        Returns:
            float: 推定残り時間（秒）、計算不可の場合はNone
        """
        processed = self.completed + self.failed
        if processed == 0:
            return None

        elapsed = self.get_elapsed_time()
        avg_time_per_task = elapsed / processed
        remaining_tasks = self.total - processed

        return avg_time_per_task * remaining_tasks

    def get_summary(self) -> Dict[str, Any]:
        """
        進捗サマリーを取得

        Returns:
            Dict: 進捗サマリー
        """
        return {
            'total': self.total,
            'completed': self.completed,
            'failed': self.failed,
            'progress_percentage': self.get_progress_percentage(),
            'elapsed_time': self.get_elapsed_time(),
            'estimated_remaining_time': self.get_estimated_remaining_time()
        }
