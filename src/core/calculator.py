"""
Calculator Module
期待値・統計計算モジュール

Author: Yuutai Event Investor Team
Date: 2024-11-07
Version: 1.0.0
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
import json
from pathlib import Path


class Calculator:
    """期待値と統計情報を計算するクラス"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def _load_settings(self) -> Dict:
        """設定ファイルから設定を読み込む"""
        try:
            config_path = Path(__file__).parent.parent.parent / "config" / "settings.json"
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"設定ファイル読み込み失敗: {e}")

        # デフォルト設定
        return {'data_period': '10y', 'max_days_before': 120, 'min_trade_count': 3}
    
    def calculate_returns(self, df: pd.DataFrame, buy_days_before: int,
                         kenrlast: int, rights_month: int) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        指定した買入日でのリターンを計算し、勝ちトレードと負けトレードに分類
        
        Args:
            df: 株価データフレーム（yfinanceから取得したもの）
            buy_days_before: 何営業日前に購入するか
            kenrlast: 権利付最終日（1=米国株、2=日本株）
            rights_month: 権利確定月
            
        Returns:
            Tuple[pd.DataFrame, pd.DataFrame]: (勝ちトレード, 負けトレード)
        """
        try:
            # データフレームのコピーを作成
            data = df.copy()
            
            # 月情報を追加
            data["Month"] = data.index.month
            data["MonthSft"] = data["Month"].shift(-1)
            data.dropna(inplace=True)
            data["MonthSft"] = data["MonthSft"].astype(int)
            
            # 権利確定日のフラグを立てる
            data["権利確定日"] = data["Month"] != data["MonthSft"]

            # 権利付最終日のフラグを立てる（FutureWarning回避のため型変換を明示）
            data["権利付最終日"] = data["権利確定日"].shift(-kenrlast)
            data.loc[data["権利付最終日"].isna(), "権利付最終日"] = False
            data["権利付最終日"] = data["権利付最終日"].astype(bool)
            
            # 買入日の終値を取得
            data["買入日終値"] = data["Close"].shift(buy_days_before)
            
            # リターンを計算
            data["リターン(%)"] = (data["Close"] - data["買入日終値"]) / data["買入日終値"] * 100
            
            # 権利付最終日で指定月のデータのみを抽出
            filtered = data[data["権利付最終日"] & (data["Month"] == rights_month)]
            
            # 勝ちトレードと負けトレードに分類
            win_trades = filtered[filtered["リターン(%)"] > 0].copy()
            lose_trades = filtered[filtered["リターン(%)"] <= 0].copy()
            
            return win_trades, lose_trades
            
        except Exception as e:
            self.logger.error(f"リターン計算エラー: {e}")
            return pd.DataFrame(), pd.DataFrame()
    
    def calculate_statistics(self, win_trades: pd.DataFrame,
                            lose_trades: pd.DataFrame) -> Dict[str, float]:
        """
        勝ち/負けトレードの統計情報を計算
        
        Args:
            win_trades: 勝ちトレードのDataFrame
            lose_trades: 負けトレードのDataFrame
            
        Returns:
            Dict: 統計情報
        """
        try:
            win_count = len(win_trades)
            lose_count = len(lose_trades)
            total_count = win_count + lose_count
            
            # 勝率
            win_rate = win_count / total_count if total_count > 0 else 0.0
            
            # 勝ちトレードの統計
            if win_count > 0:
                avg_win = round(win_trades["リターン(%)"].mean(), 2)
                max_win = round(win_trades["リターン(%)"].max(), 2)
            else:
                avg_win = 0.0
                max_win = 0.0
            
            # 負けトレードの統計
            if lose_count > 0:
                avg_lose = round(lose_trades["リターン(%)"].mean(), 2)
                max_lose = round(lose_trades["リターン(%)"].min(), 2)
            else:
                avg_lose = 0.0
                max_lose = 0.0
            
            # 期待値
            expected_value = (avg_win * win_rate) + (avg_lose * (1 - win_rate))
            
            return {
                "win_count": win_count,
                "lose_count": lose_count,
                "total_count": total_count,
                "win_rate": round(win_rate, 4),
                "avg_win_return": avg_win,
                "max_win_return": max_win,
                "avg_lose_return": avg_lose,
                "max_lose_return": max_lose,
                "expected_return": round(expected_value, 2)
            }
            
        except Exception as e:
            self.logger.error(f"統計計算エラー: {e}")
            return {
                "win_count": 0,
                "lose_count": 0,
                "total_count": 0,
                "win_rate": 0.0,
                "avg_win_return": 0.0,
                "max_win_return": 0.0,
                "avg_lose_return": 0.0,
                "max_lose_return": 0.0,
                "expected_return": 0.0
            }
    
    def find_optimal_timing(self, ticker: str, rights_month: int,
                           max_days_before: int = 120,
                           kenrlast: int = 2,
                           df: Optional[pd.DataFrame] = None) -> Optional[Dict]:
        """
        最適な買入タイミングを見つける

        Args:
            ticker: ティッカーコード
            rights_month: 権利確定月
            max_days_before: 最大何日前まで検証するか
            kenrlast: 権利付最終日
            df: 株価データ（オプション、指定しない場合はdata_fetcherで取得）

        Returns:
            Dict: 最適なタイミング情報
            {
                'ticker': ティッカーコード,
                'rights_month': 権利確定月,
                'optimal_days': 最適な買入日数,
                'win_rate': 勝率,
                'expected_return': 期待リターン,
                'all_results': 全日数の結果リスト
            }
        """
        try:
            # 設定を読み込む
            settings = self._load_settings()
            data_period = settings.get('data_period', '10y')

            # 株価データが指定されていない場合はdata_fetcherで取得
            if df is None:
                from src.core.data_fetcher import DataFetcher
                fetcher = DataFetcher()
                df = fetcher.update_stock_data(ticker, period=data_period)

                if df is None or df.empty:
                    self.logger.error(f"株価データが取得できません: {ticker}")
                    return None

            # カラム名を統一（yfinance形式）
            if 'close' in df.columns:
                df = df.rename(columns={
                    'open': 'Open',
                    'high': 'High',
                    'low': 'Low',
                    'close': 'Close',
                    'volume': 'Volume'
                })

            all_results = []

            # 1日前から max_days_before 日前までスキャン
            for days_before in range(1, max_days_before + 1):
                # リターンを計算
                win_trades, lose_trades = self.calculate_returns(
                    df=df,
                    buy_days_before=days_before,
                    kenrlast=kenrlast,
                    rights_month=rights_month
                )

                # 統計情報を計算
                stats = self.calculate_statistics(win_trades, lose_trades)

                # データが少ない場合はスキップ
                if stats['total_count'] < 3:
                    continue

                all_results.append({
                    'days_before': days_before,
                    'win_count': stats['win_count'],
                    'lose_count': stats['lose_count'],
                    'total_count': stats['total_count'],
                    'win_rate': stats['win_rate'],
                    'expected_return': stats['expected_return'],
                    'avg_win_return': stats['avg_win_return'],
                    'max_win_return': stats['max_win_return'],
                    'avg_lose_return': stats['avg_lose_return'],
                    'max_lose_return': stats['max_lose_return']
                })

            # 結果がない場合
            if not all_results:
                self.logger.warning(f"有効なデータが見つかりません: {ticker}")
                return None

            # 期待値が最も高いタイミングを見つける
            # 期待値と勝率の両方を考慮（期待値 * 勝率のスコア）
            for result in all_results:
                result['score'] = result['expected_return'] * result['win_rate']

            # スコアでソート
            all_results.sort(key=lambda x: x['score'], reverse=True)
            optimal = all_results[0]

            self.logger.info(
                f"最適タイミング発見: {ticker} - "
                f"{optimal['days_before']}日前 "
                f"(期待値: {optimal['expected_return']}%, 勝率: {optimal['win_rate']*100:.1f}%)"
            )

            return {
                'ticker': ticker,
                'rights_month': rights_month,
                'optimal_days': optimal['days_before'],
                'win_rate': optimal['win_rate'],
                'expected_return': optimal['expected_return'],
                'win_count': optimal['win_count'],
                'lose_count': optimal['lose_count'],
                'total_count': optimal['total_count'],
                'avg_win_return': optimal['avg_win_return'],
                'max_win_return': optimal['max_win_return'],
                'avg_lose_return': optimal['avg_lose_return'],
                'max_lose_return': optimal['max_lose_return'],
                'all_results': all_results
            }

        except Exception as e:
            self.logger.error(f"最適タイミング検索エラー: {ticker} - {e}")
            return None


class OptimalTimingCalculator:
    """
    最適な買入タイミングを計算するクラス
    data_fetcherと連携してバックテストを実行
    """

    def __init__(self, data_fetcher=None):
        """
        Args:
            data_fetcher: StockDataFetcherインスタンス
        """
        self.logger = logging.getLogger(__name__)
        self.calculator = Calculator()
        self.data_fetcher = data_fetcher

    def find_optimal_timing(self, ticker: str, rights_date: str,
                           max_days_before: int = 120,
                           kenrlast: int = 2) -> Optional[Dict]:
        """
        最適な買入タイミングを見つける

        Args:
            ticker: ティッカーコード
            rights_date: 権利確定日（YYYY-MM-DD形式）
            max_days_before: 最大何日前まで検証するか
            kenrlast: 権利付最終日（1=米国株、2=日本株）

        Returns:
            Dict: 最適なタイミング情報
        """
        try:
            # 権利確定月を抽出
            from datetime import datetime
            rights_month = datetime.strptime(rights_date, '%Y-%m-%d').month

            # 設定を読み込む
            settings = self.calculator._load_settings()
            data_period = settings.get('data_period', '10y')

            # 株価データを取得
            if self.data_fetcher is None:
                self.logger.error("data_fetcherが設定されていません")
                return None

            df = self.data_fetcher.fetch_stock_data(ticker, period=data_period)

            if df is None or df.empty:
                self.logger.error(f"株価データが取得できません: {ticker}")
                return None

            # calculatorのメソッドを呼び出し
            result = self.calculator.find_optimal_timing(
                ticker=ticker,
                rights_month=rights_month,
                max_days_before=max_days_before,
                kenrlast=kenrlast,
                df=df
            )

            return result

        except Exception as e:
            self.logger.error(f"最適タイミング計算エラー: {ticker} - {e}", exc_info=True)
            return None
