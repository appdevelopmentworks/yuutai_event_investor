"""
Portfolio Calculator Module
ポートフォリオ計算モジュール

Author: Yuutai Event Investor Team
Date: 2025-01-11
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import logging
from scipy.optimize import minimize


class PortfolioCalculator:
    """ポートフォリオ分析計算クラス"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def calculate_portfolio_metrics(self, stocks: List[Dict], weights: List[float]) -> Dict:
        """
        ポートフォリオの指標を計算

        Args:
            stocks: 銘柄データのリスト
            weights: 各銘柄の投資比率（合計1.0）

        Returns:
            Dict: ポートフォリオ指標
        """
        try:
            if len(stocks) != len(weights):
                raise ValueError("銘柄数と投資比率の数が一致しません")

            if not np.isclose(sum(weights), 1.0):
                raise ValueError(f"投資比率の合計が1.0ではありません: {sum(weights)}")

            # 各銘柄の期待リターンと勝率
            expected_returns = np.array([s.get('expected_return', 0) / 100 for s in stocks])
            win_rates = np.array([s.get('win_rate', 0) for s in stocks])
            weights = np.array(weights)

            # ポートフォリオの期待リターン（加重平均）
            portfolio_return = np.dot(weights, expected_returns) * 100  # パーセント表示

            # ポートフォリオの勝率（加重平均）
            portfolio_win_rate = np.dot(weights, win_rates)

            # リスク計算（簡易版: 標準偏差の加重平均）
            # より正確にはリターンの共分散行列が必要だが、データがないため簡易計算
            avg_win_returns = np.array([s.get('avg_win_return', 0) for s in stocks])
            avg_lose_returns = np.array([s.get('avg_lose_return', 0) for s in stocks])

            # 各銘柄のリターンの分散を推定
            variances = []
            for i, stock in enumerate(stocks):
                win_rate = win_rates[i]
                avg_win = avg_win_returns[i]
                avg_lose = avg_lose_returns[i]
                expected = expected_returns[i] * 100

                # 分散 = 勝率 * (平均勝ち - 期待値)^2 + (1-勝率) * (平均負け - 期待値)^2
                variance = (win_rate * (avg_win - expected)**2 +
                           (1 - win_rate) * (avg_lose - expected)**2)
                variances.append(variance)

            variances = np.array(variances)

            # ポートフォリオのリスク（分散投資効果を考慮）
            # 相関係数を0.3と仮定（実際の相関は不明）
            correlation = 0.3
            portfolio_variance = 0
            for i in range(len(weights)):
                for j in range(len(weights)):
                    if i == j:
                        portfolio_variance += weights[i]**2 * variances[i]
                    else:
                        # 共分散 = 相関係数 * σi * σj
                        portfolio_variance += (weights[i] * weights[j] * correlation *
                                             np.sqrt(variances[i]) * np.sqrt(variances[j]))

            portfolio_risk = np.sqrt(portfolio_variance)

            # シャープレシオ（リスクフリーレートを0と仮定）
            sharpe_ratio = portfolio_return / portfolio_risk if portfolio_risk > 0 else 0

            # リスク削減効果（単純平均のリスクと比較）
            equal_weight_variance = np.mean(variances)
            risk_reduction = (1 - portfolio_risk / np.sqrt(equal_weight_variance)) * 100

            # 最悪ケースのリターン（VaR95相当）
            worst_case_return = portfolio_return - 1.645 * portfolio_risk  # 95%信頼区間

            # ソルティノレシオ（下方リスクのみ考慮）
            # 下方偏差を計算（目標リターン0とする）
            downside_variance = 0
            for i in range(len(weights)):
                avg_lose = avg_lose_returns[i]
                if avg_lose < 0:  # 負のリターンのみ
                    downside_variance += weights[i]**2 * (avg_lose ** 2)

            downside_risk = np.sqrt(downside_variance) if downside_variance > 0 else portfolio_risk
            sortino_ratio = portfolio_return / downside_risk if downside_risk > 0 else 0

            return {
                'expected_return': portfolio_return,
                'win_rate': portfolio_win_rate,
                'risk': portfolio_risk,
                'sharpe_ratio': sharpe_ratio,
                'sortino_ratio': sortino_ratio,
                'risk_reduction': risk_reduction,
                'worst_case_return': worst_case_return,
                'downside_risk': downside_risk,
                'weights': weights.tolist()
            }

        except Exception as e:
            self.logger.error(f"ポートフォリオ指標計算エラー: {e}", exc_info=True)
            return None

    def optimize_portfolio(self, stocks: List[Dict],
                          optimization_target: str = 'sharpe') -> Optional[Dict]:
        """
        ポートフォリオの最適化

        Args:
            stocks: 銘柄データのリスト
            optimization_target: 最適化目標 ('sharpe', 'return', 'risk')

        Returns:
            Dict: 最適化されたポートフォリオ
        """
        try:
            n_stocks = len(stocks)

            if n_stocks < 2:
                self.logger.warning("最適化には2銘柄以上必要です")
                return None

            # 期待リターンと分散を抽出
            expected_returns = np.array([s.get('expected_return', 0) / 100 for s in stocks])
            win_rates = np.array([s.get('win_rate', 0) for s in stocks])

            # 分散を計算
            variances = []
            for stock in stocks:
                win_rate = stock.get('win_rate', 0)
                avg_win = stock.get('avg_win_return', 0)
                avg_lose = stock.get('avg_lose_return', 0)
                expected = stock.get('expected_return', 0)

                variance = (win_rate * (avg_win - expected)**2 +
                           (1 - win_rate) * (avg_lose - expected)**2)
                variances.append(variance)

            variances = np.array(variances)

            # 最適化関数の定義
            def portfolio_metrics(weights):
                """ポートフォリオのリターン、リスク、シャープレシオを計算"""
                portfolio_return = np.dot(weights, expected_returns)

                # リスク計算（相関係数0.3を仮定）
                correlation = 0.3
                portfolio_variance = 0
                for i in range(len(weights)):
                    for j in range(len(weights)):
                        if i == j:
                            portfolio_variance += weights[i]**2 * variances[i]
                        else:
                            portfolio_variance += (weights[i] * weights[j] * correlation *
                                                 np.sqrt(variances[i]) * np.sqrt(variances[j]))

                portfolio_risk = np.sqrt(portfolio_variance)
                sharpe = portfolio_return / portfolio_risk if portfolio_risk > 0 else 0

                return portfolio_return, portfolio_risk, sharpe

            # 目的関数
            if optimization_target == 'sharpe':
                # シャープレシオを最大化（負の値を最小化）
                def objective(weights):
                    _, _, sharpe = portfolio_metrics(weights)
                    return -sharpe
            elif optimization_target == 'return':
                # リターンを最大化（負の値を最小化）
                def objective(weights):
                    ret, _, _ = portfolio_metrics(weights)
                    return -ret
            else:  # 'risk'
                # リスクを最小化
                def objective(weights):
                    _, risk, _ = portfolio_metrics(weights)
                    return risk

            # 制約条件
            constraints = [
                {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}  # 合計が1
            ]

            # 境界条件（各銘柄0%〜100%）
            bounds = tuple((0, 1) for _ in range(n_stocks))

            # 初期値（均等配分）
            initial_weights = np.array([1.0 / n_stocks] * n_stocks)

            # 最適化実行
            result = minimize(
                objective,
                initial_weights,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints,
                options={'maxiter': 1000}
            )

            if not result.success:
                self.logger.warning(f"最適化に失敗しました: {result.message}")
                return None

            optimal_weights = result.x

            # 最適化されたポートフォリオの指標を計算
            metrics = self.calculate_portfolio_metrics(stocks, optimal_weights.tolist())

            if metrics:
                metrics['optimization_target'] = optimization_target
                self.logger.info(f"最適化完了 - 目標: {optimization_target}, "
                               f"リターン: {metrics['expected_return']:.2f}%, "
                               f"リスク: {metrics['risk']:.2f}, "
                               f"シャープ: {metrics['sharpe_ratio']:.2f}")

            return metrics

        except Exception as e:
            self.logger.error(f"ポートフォリオ最適化エラー: {e}", exc_info=True)
            return None

    def calculate_efficient_frontier(self, stocks: List[Dict],
                                     num_portfolios: int = 50) -> List[Dict]:
        """
        効率的フロンティアを計算

        Args:
            stocks: 銘柄データのリスト
            num_portfolios: 生成するポートフォリオ数

        Returns:
            List[Dict]: 各ポートフォリオのリターンとリスク
        """
        try:
            n_stocks = len(stocks)

            if n_stocks < 2:
                return []

            frontier_portfolios = []

            # ランダムなポートフォリオを生成
            for _ in range(num_portfolios):
                # ランダムな重みを生成（合計が1になるように）
                weights = np.random.random(n_stocks)
                weights /= np.sum(weights)

                metrics = self.calculate_portfolio_metrics(stocks, weights.tolist())

                if metrics:
                    frontier_portfolios.append({
                        'return': metrics['expected_return'],
                        'risk': metrics['risk'],
                        'sharpe': metrics['sharpe_ratio'],
                        'weights': weights.tolist()
                    })

            # リスクでソート
            frontier_portfolios.sort(key=lambda x: x['risk'])

            return frontier_portfolios

        except Exception as e:
            self.logger.error(f"効率的フロンティア計算エラー: {e}", exc_info=True)
            return []

    def suggest_allocation(self, stocks: List[Dict],
                          total_investment: float,
                          risk_tolerance: str = 'medium') -> Dict:
        """
        投資金額の配分を提案

        Args:
            stocks: 銘柄データのリスト
            total_investment: 総投資金額（円）
            risk_tolerance: リスク許容度 ('low', 'medium', 'high')

        Returns:
            Dict: 推奨配分
        """
        try:
            # リスク許容度に応じて最適化目標を設定
            if risk_tolerance == 'low':
                optimization_target = 'risk'  # リスク最小化
            elif risk_tolerance == 'high':
                optimization_target = 'return'  # リターン最大化
            else:
                optimization_target = 'sharpe'  # シャープレシオ最大化

            # ポートフォリオ最適化
            optimal = self.optimize_portfolio(stocks, optimization_target)

            if not optimal:
                # 最適化に失敗した場合は均等配分
                n_stocks = len(stocks)
                equal_weights = [1.0 / n_stocks] * n_stocks
                optimal = self.calculate_portfolio_metrics(stocks, equal_weights)
                optimal['optimization_target'] = 'equal'

            # 金額配分を計算
            allocations = []
            for i, (stock, weight) in enumerate(zip(stocks, optimal['weights'])):
                amount = total_investment * weight
                allocations.append({
                    'code': stock.get('code'),
                    'name': stock.get('name'),
                    'weight': weight,
                    'amount': amount
                })

            return {
                'allocations': allocations,
                'portfolio_metrics': optimal,
                'total_investment': total_investment,
                'risk_tolerance': risk_tolerance
            }

        except Exception as e:
            self.logger.error(f"配分提案エラー: {e}", exc_info=True)
            return None
