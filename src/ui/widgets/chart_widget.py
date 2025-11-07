"""
Chart Widget
チャート表示ウィジェット

Author: Yuutai Event Investor Team
Date: 2024-11-07
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import logging
from typing import Dict, List, Optional
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np

# 日本語フォント設定
import platform
if platform.system() == 'Windows':
    matplotlib.rc('font', family='MS Gothic')
elif platform.system() == 'Darwin':  # macOS
    matplotlib.rc('font', family='Hiragino Sans')
else:  # Linux
    matplotlib.rc('font', family='Noto Sans CJK JP')


class ChartWidget(QWidget):
    """チャート表示ウィジェット"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.current_chart_type = "expected_return"  # デフォルトは期待値チャート

        self.init_ui()

    def init_ui(self):
        """UIを初期化"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # ========================================
        # チャートタイプ選択ボタン
        # ========================================
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)

        self.expected_btn = QPushButton("期待値推移")
        self.win_rate_btn = QPushButton("勝率")
        self.trades_btn = QPushButton("トレード履歴")

        for btn in [self.expected_btn, self.win_rate_btn, self.trades_btn]:
            btn.setFixedHeight(32)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2D2D2D;
                    color: #B0B0B0;
                    border: 1px solid #404040;
                    border-radius: 4px;
                    padding: 5px 15px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #3A3A3A;
                    color: #E0E0E0;
                }
                QPushButton:checked {
                    background-color: #1E90FF;
                    color: white;
                    border: 1px solid #1E90FF;
                }
            """)
            btn.setCheckable(True)

        self.expected_btn.setChecked(True)

        self.expected_btn.clicked.connect(lambda: self.change_chart_type("expected_return"))
        self.win_rate_btn.clicked.connect(lambda: self.change_chart_type("win_rate"))
        self.trades_btn.clicked.connect(lambda: self.change_chart_type("trades"))

        button_layout.addWidget(self.expected_btn)
        button_layout.addWidget(self.win_rate_btn)
        button_layout.addWidget(self.trades_btn)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        # ========================================
        # Matplotlibキャンバス
        # ========================================
        self.figure = Figure(figsize=(8, 6), facecolor='#1E1E1E')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background-color: #1E1E1E;")

        layout.addWidget(self.canvas)

        # プレースホルダーを表示
        self.show_placeholder()

    def change_chart_type(self, chart_type: str):
        """チャートタイプを変更"""
        self.current_chart_type = chart_type

        # ボタンの状態を更新
        self.expected_btn.setChecked(chart_type == "expected_return")
        self.win_rate_btn.setChecked(chart_type == "win_rate")
        self.trades_btn.setChecked(chart_type == "trades")

        self.logger.info(f"チャートタイプを変更: {chart_type}")

        # 現在のデータで再描画（データがあれば）
        if hasattr(self, 'current_data') and self.current_data:
            self.plot_data(self.current_data)

    def show_placeholder(self):
        """プレースホルダーを表示"""
        self.figure.clear()
        ax = self.figure.add_subplot(111, facecolor='#1E1E1E')

        ax.text(0.5, 0.5, '銘柄を選択してください',
                horizontalalignment='center',
                verticalalignment='center',
                fontsize=14,
                color='#B0B0B0',
                transform=ax.transAxes)

        ax.set_xticks([])
        ax.set_yticks([])
        ax.spines['top'].set_color('#404040')
        ax.spines['right'].set_color('#404040')
        ax.spines['left'].set_color('#404040')
        ax.spines['bottom'].set_color('#404040')

        self.canvas.draw()

    def plot_data(self, result_data: Dict):
        """
        分析結果をプロット

        Args:
            result_data: calculator.find_optimal_timing()の結果
        """
        self.current_data = result_data

        if not result_data or 'all_results' not in result_data:
            self.show_placeholder()
            return

        all_results = result_data['all_results']

        if not all_results:
            self.show_placeholder()
            return

        # チャートタイプに応じて描画
        if self.current_chart_type == "expected_return":
            self.plot_expected_return(all_results, result_data)
        elif self.current_chart_type == "win_rate":
            self.plot_win_rate(all_results, result_data)
        elif self.current_chart_type == "trades":
            self.plot_trades(all_results, result_data)

    def plot_expected_return(self, all_results: List[Dict], result_data: Dict):
        """期待値推移チャートを描画"""
        self.figure.clear()
        ax = self.figure.add_subplot(111, facecolor='#1E1E1E')

        # データ準備
        days = [r['days_before'] for r in all_results]
        expected_returns = [r['expected_return'] for r in all_results]
        optimal_days = result_data['optimal_days']

        # 折れ線グラフ
        ax.plot(days, expected_returns, color='#1E90FF', linewidth=2, label='期待リターン')

        # 最適ポイントをハイライト
        optimal_return = result_data['expected_return']
        ax.scatter([optimal_days], [optimal_return], color='#10B981', s=100, zorder=5, label=f'最適: {optimal_days}日前')

        # グリッド
        ax.grid(True, alpha=0.2, color='#404040')

        # ラベル
        ax.set_xlabel('買入日（権利付最終日の何日前）', fontsize=10, color='#E0E0E0')
        ax.set_ylabel('期待リターン (%)', fontsize=10, color='#E0E0E0')
        ax.set_title(f'{result_data.get("ticker", "")} - 期待リターン推移', fontsize=12, color='#E0E0E0', pad=15)

        # 軸の色
        ax.tick_params(colors='#B0B0B0', labelsize=9)
        ax.spines['top'].set_color('#404040')
        ax.spines['right'].set_color('#404040')
        ax.spines['left'].set_color('#404040')
        ax.spines['bottom'].set_color('#404040')

        # 凡例
        ax.legend(facecolor='#2D2D2D', edgecolor='#404040', labelcolor='#E0E0E0', fontsize=9)

        # 0ラインを引く
        ax.axhline(y=0, color='#404040', linestyle='--', linewidth=1, alpha=0.5)

        self.figure.tight_layout()
        self.canvas.draw()

    def plot_win_rate(self, all_results: List[Dict], result_data: Dict):
        """勝率チャートを描画"""
        self.figure.clear()
        ax = self.figure.add_subplot(111, facecolor='#1E1E1E')

        # データ準備
        days = [r['days_before'] for r in all_results]
        win_rates = [r['win_rate'] * 100 for r in all_results]  # パーセント表示
        optimal_days = result_data['optimal_days']

        # 棒グラフ
        colors = ['#10B981' if d == optimal_days else '#4682B4' for d in days]
        ax.bar(days, win_rates, color=colors, alpha=0.8, width=1.5)

        # グリッド
        ax.grid(True, alpha=0.2, color='#404040', axis='y')

        # ラベル
        ax.set_xlabel('買入日（権利付最終日の何日前）', fontsize=10, color='#E0E0E0')
        ax.set_ylabel('勝率 (%)', fontsize=10, color='#E0E0E0')
        ax.set_title(f'{result_data.get("ticker", "")} - 勝率分布', fontsize=12, color='#E0E0E0', pad=15)

        # 軸の色
        ax.tick_params(colors='#B0B0B0', labelsize=9)
        ax.spines['top'].set_color('#404040')
        ax.spines['right'].set_color('#404040')
        ax.spines['left'].set_color('#404040')
        ax.spines['bottom'].set_color('#404040')

        # 50%ラインを引く
        ax.axhline(y=50, color='#FACC15', linestyle='--', linewidth=1, alpha=0.5, label='50%')
        ax.legend(facecolor='#2D2D2D', edgecolor='#404040', labelcolor='#E0E0E0', fontsize=9)

        self.figure.tight_layout()
        self.canvas.draw()

    def plot_trades(self, all_results: List[Dict], result_data: Dict):
        """トレード履歴（勝ち/負け）を描画"""
        self.figure.clear()
        ax = self.figure.add_subplot(111, facecolor='#1E1E1E')

        # データ準備
        days = [r['days_before'] for r in all_results]
        win_counts = [r['win_count'] for r in all_results]
        lose_counts = [r['lose_count'] for r in all_results]

        # 棒の幅を自動調整（データ数に応じて）
        bar_width = max(0.8, min(2.0, 100 / len(days)))

        # 積み上げ棒グラフ
        ax.bar(days, win_counts, label='勝ち', color='#10B981', alpha=0.8, width=bar_width)
        ax.bar(days, lose_counts, bottom=win_counts, label='負け', color='#EF4444', alpha=0.8, width=bar_width)

        # 最適ポイントを強調
        optimal_days = result_data['optimal_days']
        optimal_idx = next((i for i, r in enumerate(all_results) if r['days_before'] == optimal_days), None)
        if optimal_idx is not None:
            total_height = win_counts[optimal_idx] + lose_counts[optimal_idx]
            ax.plot(optimal_days, total_height, marker='*', markersize=15, color='#FACC15', zorder=5)

        # グリッド
        ax.grid(True, alpha=0.2, color='#404040', axis='y')

        # ラベル
        ax.set_xlabel('買入日（権利付最終日の何日前）', fontsize=10, color='#E0E0E0')
        ax.set_ylabel('トレード数', fontsize=10, color='#E0E0E0')
        ax.set_title(f'{result_data.get("ticker", "")} - トレード履歴', fontsize=12, color='#E0E0E0', pad=15)

        # 軸の色
        ax.tick_params(colors='#B0B0B0', labelsize=9)
        ax.spines['top'].set_color('#404040')
        ax.spines['right'].set_color('#404040')
        ax.spines['left'].set_color('#404040')
        ax.spines['bottom'].set_color('#404040')

        # 凡例
        ax.legend(facecolor='#2D2D2D', edgecolor='#404040', labelcolor='#E0E0E0', fontsize=9)

        self.figure.tight_layout()
        self.canvas.draw()

    def clear(self):
        """チャートをクリア"""
        self.current_data = None
        self.show_placeholder()
