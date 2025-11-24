"""
Risk Analysis Module
リスク分析モジュール

Author: Yuutai Event Investor Team
Date: 2025-01-11
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import logging
from scipy import stats


class RiskAnalyzer:
    """リスク分析クラス"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def calculate_max_drawdown(self, returns: pd.Series) -> Dict:
        """
        最大ドローダウンを計算

        Args:
            returns: リターンのシリーズ（%表示）

        Returns:
            Dict: 最大ドローダウン情報
        """
        try:
            if returns.empty or len(returns) < 2:
                return {
                    'max_drawdown': 0.0,
                    'max_drawdown_duration': 0,
                    'current_drawdown': 0.0
                }

            # 累積リターンを計算
            cumulative_returns = (1 + returns / 100).cumprod()

            # 累積最大値を計算
            running_max = cumulative_returns.expanding().max()

            # ドローダウンを計算
            drawdown = (cumulative_returns - running_max) / running_max * 100

            # 最大ドローダウン
            max_drawdown = drawdown.min()

            # 最大ドローダウンのインデックス
            max_dd_idx = drawdown.idxmin()

            # ドローダウン期間を計算
            # 最大ドローダウンの開始点を探す
            peak_subset = running_max[:max_dd_idx]
            if peak_subset.empty or len(peak_subset) == 0:
                # データが不十分な場合
                return {
                    'max_drawdown': float(max_drawdown),
                    'max_drawdown_duration': 0,
                    'current_drawdown': float(drawdown.iloc[-1]) if len(drawdown) > 0 else 0.0
                }

            peak_idx = peak_subset.idxmax()
            drawdown_duration = (max_dd_idx - peak_idx).days if hasattr(max_dd_idx - peak_idx, 'days') else len(drawdown[peak_idx:max_dd_idx])

            # 現在のドローダウン
            current_drawdown = drawdown.iloc[-1] if len(drawdown) > 0 else 0.0

            return {
                'max_drawdown': float(max_drawdown),
                'max_drawdown_duration': int(drawdown_duration),
                'current_drawdown': float(current_drawdown),
                'peak_index': peak_idx,
                'trough_index': max_dd_idx
            }

        except Exception as e:
            self.logger.error(f"最大ドローダウン計算エラー: {e}", exc_info=True)
            return {
                'max_drawdown': 0.0,
                'max_drawdown_duration': 0,
                'current_drawdown': 0.0
            }

    def calculate_var(self, returns: pd.Series, confidence_level: float = 0.95) -> Dict:
        """
        Value at Risk (VaR)を計算

        Args:
            returns: リターンのシリーズ（%表示）
            confidence_level: 信頼水準（デフォルト: 95%）

        Returns:
            Dict: VaR情報
        """
        try:
            if returns.empty:
                return {
                    'var_95': 0.0,
                    'var_99': 0.0,
                    'cvar_95': 0.0,
                    'cvar_99': 0.0
                }

            # VaR計算（ヒストリカル法）
            var_95 = np.percentile(returns, (1 - 0.95) * 100)
            var_99 = np.percentile(returns, (1 - 0.99) * 100)

            # CVaR (Conditional VaR / Expected Shortfall) 計算
            # VaRを超える損失の平均
            cvar_95 = returns[returns <= var_95].mean() if any(returns <= var_95) else var_95
            cvar_99 = returns[returns <= var_99].mean() if any(returns <= var_99) else var_99

            return {
                'var_95': float(var_95),
                'var_99': float(var_99),
                'cvar_95': float(cvar_95),
                'cvar_99': float(cvar_99),
                'confidence_level': confidence_level
            }

        except Exception as e:
            self.logger.error(f"VaR計算エラー: {e}", exc_info=True)
            return {
                'var_95': 0.0,
                'var_99': 0.0,
                'cvar_95': 0.0,
                'cvar_99': 0.0
            }

    def calculate_return_distribution(self, returns: pd.Series) -> Dict:
        """
        リターン分布の統計情報を計算

        Args:
            returns: リターンのシリーズ（%表示）

        Returns:
            Dict: 分布統計情報
        """
        try:
            if returns.empty:
                return {
                    'mean': 0.0,
                    'median': 0.0,
                    'std': 0.0,
                    'skewness': 0.0,
                    'kurtosis': 0.0,
                    'min': 0.0,
                    'max': 0.0,
                    'percentile_25': 0.0,
                    'percentile_75': 0.0
                }

            return {
                'mean': float(returns.mean()),
                'median': float(returns.median()),
                'std': float(returns.std()),
                'skewness': float(stats.skew(returns)),
                'kurtosis': float(stats.kurtosis(returns)),
                'min': float(returns.min()),
                'max': float(returns.max()),
                'percentile_25': float(np.percentile(returns, 25)),
                'percentile_75': float(np.percentile(returns, 75))
            }

        except Exception as e:
            self.logger.error(f"分布統計計算エラー: {e}", exc_info=True)
            return {
                'mean': 0.0,
                'median': 0.0,
                'std': 0.0,
                'skewness': 0.0,
                'kurtosis': 0.0,
                'min': 0.0,
                'max': 0.0,
                'percentile_25': 0.0,
                'percentile_75': 0.0
            }

    def calculate_sortino_ratio(self, returns: pd.Series,
                                target_return: float = 0.0,
                                periods_per_year: int = 252) -> float:
        """
        ソルティノレシオを計算（下方リスクのみを考慮）

        Args:
            returns: リターンのシリーズ（%表示）
            target_return: 目標リターン（デフォルト: 0%）
            periods_per_year: 年間取引回数（デフォルト: 252日）

        Returns:
            float: ソルティノレシオ
        """
        try:
            if returns.empty:
                return 0.0

            # 目標リターンを下回るリターンのみを抽出
            downside_returns = returns[returns < target_return]

            if downside_returns.empty:
                return float('inf')  # 下方リスクがない場合

            # 下方偏差を計算
            downside_deviation = np.sqrt(np.mean((downside_returns - target_return) ** 2))

            if downside_deviation == 0:
                return 0.0

            # 平均リターン
            mean_return = returns.mean()

            # ソルティノレシオ = (平均リターン - 目標リターン) / 下方偏差
            sortino_ratio = (mean_return - target_return) / downside_deviation

            # 年率化
            sortino_ratio *= np.sqrt(periods_per_year)

            return float(sortino_ratio)

        except Exception as e:
            self.logger.error(f"ソルティノレシオ計算エラー: {e}", exc_info=True)
            return 0.0

    def calculate_calmar_ratio(self, returns: pd.Series,
                              periods_per_year: int = 252) -> float:
        """
        カルマーレシオを計算（リターン / 最大ドローダウン）

        Args:
            returns: リターンのシリーズ（%表示）
            periods_per_year: 年間取引回数（デフォルト: 252日）

        Returns:
            float: カルマーレシオ
        """
        try:
            if returns.empty:
                return 0.0

            # 年率リターン
            mean_return = returns.mean()
            annualized_return = mean_return * periods_per_year

            # 最大ドローダウン
            max_dd_info = self.calculate_max_drawdown(returns)
            max_drawdown = abs(max_dd_info['max_drawdown'])

            if max_drawdown == 0:
                return 0.0

            # カルマーレシオ = 年率リターン / |最大ドローダウン|
            calmar_ratio = annualized_return / max_drawdown

            return float(calmar_ratio)

        except Exception as e:
            self.logger.error(f"カルマーレシオ計算エラー: {e}", exc_info=True)
            return 0.0

    def analyze_trade_sequence(self, win_trades: pd.DataFrame,
                               lose_trades: pd.DataFrame) -> Dict:
        """
        トレードシーケンスを分析（連勝・連敗など）

        Args:
            win_trades: 勝ちトレードのDataFrame
            lose_trades: 負けトレードのDataFrame

        Returns:
            Dict: シーケンス分析結果
        """
        try:
            # 全トレードを日付順に結合
            all_trades = []

            for idx, trade in win_trades.iterrows():
                # DataFrameのインデックスが日付
                trade_date = idx if hasattr(idx, 'year') else trade.get('買入日', trade.get('Date'))
                all_trades.append({
                    'date': trade_date,
                    'result': 'win',
                    'return': trade.get('リターン(%)', trade.get('return', 0))
                })

            for idx, trade in lose_trades.iterrows():
                # DataFrameのインデックスが日付
                trade_date = idx if hasattr(idx, 'year') else trade.get('買入日', trade.get('Date'))
                all_trades.append({
                    'date': trade_date,
                    'result': 'lose',
                    'return': trade.get('リターン(%)', trade.get('return', 0))
                })

            if not all_trades:
                return {
                    'max_consecutive_wins': 0,
                    'max_consecutive_losses': 0,
                    'avg_consecutive_wins': 0.0,
                    'avg_consecutive_losses': 0.0,
                    'current_streak': 0
                }

            # 日付でソート
            all_trades.sort(key=lambda x: x['date'])

            # 連勝・連敗をカウント
            current_streak = 0
            current_type = None
            win_streaks = []
            lose_streaks = []

            for trade in all_trades:
                if trade['result'] == current_type:
                    current_streak += 1
                else:
                    if current_type == 'win' and current_streak > 0:
                        win_streaks.append(current_streak)
                    elif current_type == 'lose' and current_streak > 0:
                        lose_streaks.append(current_streak)

                    current_streak = 1
                    current_type = trade['result']

            # 最後のストリークを追加
            if current_type == 'win' and current_streak > 0:
                win_streaks.append(current_streak)
            elif current_type == 'lose' and current_streak > 0:
                lose_streaks.append(current_streak)

            return {
                'max_consecutive_wins': max(win_streaks) if win_streaks else 0,
                'max_consecutive_losses': max(lose_streaks) if lose_streaks else 0,
                'avg_consecutive_wins': float(np.mean(win_streaks)) if win_streaks else 0.0,
                'avg_consecutive_losses': float(np.mean(lose_streaks)) if lose_streaks else 0.0,
                'current_streak': current_streak,
                'current_streak_type': current_type
            }

        except Exception as e:
            self.logger.error(f"トレードシーケンス分析エラー: {e}", exc_info=True)
            return {
                'max_consecutive_wins': 0,
                'max_consecutive_losses': 0,
                'avg_consecutive_wins': 0.0,
                'avg_consecutive_losses': 0.0,
                'current_streak': 0
            }

    def calculate_comprehensive_risk_metrics(self,
                                            win_trades: pd.DataFrame,
                                            lose_trades: pd.DataFrame) -> Dict:
        """
        包括的なリスク指標を計算

        Args:
            win_trades: 勝ちトレードのDataFrame
            lose_trades: 負けトレードのDataFrame

        Returns:
            Dict: 全リスク指標
        """
        try:
            # 全リターンを取得（列名の違いに対応）
            win_returns = pd.Series()
            lose_returns = pd.Series()

            # win_tradesからリターンを取得
            if not win_trades.empty:
                if 'return' in win_trades.columns:
                    win_returns = win_trades['return']
                elif 'リターン(%)' in win_trades.columns:
                    win_returns = win_trades['リターン(%)']

            # lose_tradesからリターンを取得
            if not lose_trades.empty:
                if 'return' in lose_trades.columns:
                    lose_returns = lose_trades['return']
                elif 'リターン(%)' in lose_trades.columns:
                    lose_returns = lose_trades['リターン(%)']

            # 空のSeriesを除外してからconcat（FutureWarning回避）
            series_to_concat = [s for s in [win_returns, lose_returns] if not s.empty]
            if series_to_concat:
                all_returns = pd.concat(series_to_concat, ignore_index=True)
            else:
                all_returns = pd.Series(dtype=float)

            if all_returns.empty:
                return {
                    'max_drawdown': self.calculate_max_drawdown(pd.Series()),
                    'var': self.calculate_var(pd.Series()),
                    'distribution': self.calculate_return_distribution(pd.Series()),
                    'sortino_ratio': 0.0,
                    'calmar_ratio': 0.0,
                    'trade_sequence': self.analyze_trade_sequence(win_trades, lose_trades)
                }

            return {
                'max_drawdown': self.calculate_max_drawdown(all_returns),
                'var': self.calculate_var(all_returns),
                'distribution': self.calculate_return_distribution(all_returns),
                'sortino_ratio': self.calculate_sortino_ratio(all_returns),
                'calmar_ratio': self.calculate_calmar_ratio(all_returns),
                'trade_sequence': self.analyze_trade_sequence(win_trades, lose_trades)
            }

        except Exception as e:
            self.logger.error(f"包括的リスク指標計算エラー: {e}", exc_info=True)
            return {
                'max_drawdown': {},
                'var': {},
                'distribution': {},
                'sortino_ratio': 0.0,
                'calmar_ratio': 0.0,
                'trade_sequence': {}
            }
