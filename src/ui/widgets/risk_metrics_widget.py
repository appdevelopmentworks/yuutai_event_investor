"""
Risk Metrics Widget
リスク指標ウィジェット

Author: Yuutai Event Investor Team
Date: 2025-01-11
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QLabel, QFrame, QTabWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
import logging
from typing import Dict, Optional
import pandas as pd
from ...core.risk_analyzer import RiskAnalyzer


class RiskMetricsWidget(QWidget):
    """リスク指標表示ウィジェット"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.risk_analyzer = RiskAnalyzer()
        self.init_ui()

    def init_ui(self):
        """UIを初期化"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # ========================================
        # ヘッダー
        # ========================================
        header = QLabel("📊 リスク分析指標")
        header.setFont(QFont("Meiryo", 11, QFont.Bold))
        header.setStyleSheet("color: #1E90FF; padding: 5px;")
        layout.addWidget(header)

        # 区切り線
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #404040;")
        layout.addWidget(line)

        # ========================================
        # タブウィジェット
        # ========================================
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #404040;
                background-color: #1E1E1E;
            }
            QTabBar::tab {
                background-color: #2D2D2D;
                color: #B0B0B0;
                padding: 6px 12px;
                border: none;
                border-bottom: 2px solid transparent;
            }
            QTabBar::tab:selected {
                background-color: #1E1E1E;
                color: #1E90FF;
                border-bottom: 2px solid #1E90FF;
            }
            QTabBar::tab:hover {
                color: #E0E0E0;
            }
        """)

        # ドローダウン分析タブ
        self.drawdown_table = self.create_metrics_table()
        self.tab_widget.addTab(self.drawdown_table, "ドローダウン")

        # VaR分析タブ
        self.var_table = self.create_metrics_table()
        self.tab_widget.addTab(self.var_table, "VaR")

        # 分布統計タブ
        self.distribution_table = self.create_metrics_table()
        self.tab_widget.addTab(self.distribution_table, "分布統計")

        # その他の指標タブ
        self.other_metrics_table = self.create_metrics_table()
        self.tab_widget.addTab(self.other_metrics_table, "その他")

        layout.addWidget(self.tab_widget)

    def create_metrics_table(self) -> QTableWidget:
        """メトリクステーブルを作成"""
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["指標", "値"])

        # テーブルスタイル
        table.setStyleSheet("""
            QTableWidget {
                background-color: #1E1E1E;
                color: #E0E0E0;
                border: none;
                gridline-color: #404040;
            }
            QTableWidget::item {
                padding: 6px;
                border-bottom: 1px solid #2D2D2D;
            }
            QTableWidget::item:selected {
                background-color: #1E90FF;
                color: white;
            }
            QHeaderView::section {
                background-color: #2D2D2D;
                color: #E0E0E0;
                padding: 6px;
                border: none;
                border-bottom: 2px solid #1E90FF;
                font-weight: bold;
            }
        """)

        # ヘッダー設定
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)

        table.setMaximumHeight(300)
        table.verticalHeader().setVisible(False)

        return table

    def load_risk_metrics(self, win_trades: pd.DataFrame, lose_trades: pd.DataFrame):
        """
        リスク指標をロードして表示

        Args:
            win_trades: 勝ちトレードのDataFrame
            lose_trades: 負けトレードのDataFrame
        """
        try:
            # 包括的なリスク指標を計算
            risk_metrics = self.risk_analyzer.calculate_comprehensive_risk_metrics(
                win_trades, lose_trades
            )

            # 各タブにデータを表示
            self.update_drawdown_tab(risk_metrics.get('max_drawdown', {}))
            self.update_var_tab(risk_metrics.get('var', {}))
            self.update_distribution_tab(risk_metrics.get('distribution', {}))
            self.update_other_metrics_tab(risk_metrics)

        except Exception as e:
            self.logger.error(f"リスク指標ロードエラー: {e}", exc_info=True)

    def update_drawdown_tab(self, drawdown_data: Dict):
        """ドローダウンタブを更新"""
        self.drawdown_table.setRowCount(0)

        metrics = [
            ("最大ドローダウン", f"{drawdown_data.get('max_drawdown', 0):.2f}%",
             drawdown_data.get('max_drawdown', 0) < -10),
            ("ドローダウン期間", f"{drawdown_data.get('max_drawdown_duration', 0)}回", False),
            ("現在のドローダウン", f"{drawdown_data.get('current_drawdown', 0):.2f}%",
             drawdown_data.get('current_drawdown', 0) < -5),
        ]

        for label, value, is_warning in metrics:
            row = self.drawdown_table.rowCount()
            self.drawdown_table.insertRow(row)

            label_item = QTableWidgetItem(label)
            label_item.setFont(QFont("Meiryo", 9))
            self.drawdown_table.setItem(row, 0, label_item)

            value_item = QTableWidgetItem(value)
            value_item.setFont(QFont("Meiryo", 9, QFont.Bold))
            value_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if is_warning:
                value_item.setForeground(QColor(239, 68, 68))  # 赤色
            self.drawdown_table.setItem(row, 1, value_item)

    def update_var_tab(self, var_data: Dict):
        """VaRタブを更新"""
        self.var_table.setRowCount(0)

        metrics = [
            ("VaR (95%)", f"{var_data.get('var_95', 0):.2f}%"),
            ("VaR (99%)", f"{var_data.get('var_99', 0):.2f}%"),
            ("CVaR (95%)", f"{var_data.get('cvar_95', 0):.2f}%"),
            ("CVaR (99%)", f"{var_data.get('cvar_99', 0):.2f}%"),
        ]

        for label, value in metrics:
            row = self.var_table.rowCount()
            self.var_table.insertRow(row)

            label_item = QTableWidgetItem(label)
            label_item.setFont(QFont("Meiryo", 9))
            self.var_table.setItem(row, 0, label_item)

            value_item = QTableWidgetItem(value)
            value_item.setFont(QFont("Meiryo", 9, QFont.Bold))
            value_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            # 負の値は赤色で表示
            if var_data.get(label.split()[0].lower().replace('(', '').replace(')', '').replace('%', ''), 0) < 0:
                value_item.setForeground(QColor(239, 68, 68))
            self.var_table.setItem(row, 1, value_item)

    def update_distribution_tab(self, dist_data: Dict):
        """分布統計タブを更新"""
        self.distribution_table.setRowCount(0)

        metrics = [
            ("平均リターン", f"{dist_data.get('mean', 0):.2f}%"),
            ("中央値", f"{dist_data.get('median', 0):.2f}%"),
            ("標準偏差", f"{dist_data.get('std', 0):.2f}%"),
            ("歪度 (Skewness)", f"{dist_data.get('skewness', 0):.3f}"),
            ("尖度 (Kurtosis)", f"{dist_data.get('kurtosis', 0):.3f}"),
            ("最小値", f"{dist_data.get('min', 0):.2f}%"),
            ("25パーセンタイル", f"{dist_data.get('percentile_25', 0):.2f}%"),
            ("75パーセンタイル", f"{dist_data.get('percentile_75', 0):.2f}%"),
            ("最大値", f"{dist_data.get('max', 0):.2f}%"),
        ]

        for label, value in metrics:
            row = self.distribution_table.rowCount()
            self.distribution_table.insertRow(row)

            label_item = QTableWidgetItem(label)
            label_item.setFont(QFont("Meiryo", 9))
            self.distribution_table.setItem(row, 0, label_item)

            value_item = QTableWidgetItem(value)
            value_item.setFont(QFont("Meiryo", 9, QFont.Bold))
            value_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.distribution_table.setItem(row, 1, value_item)

    def update_other_metrics_tab(self, risk_metrics: Dict):
        """その他の指標タブを更新"""
        self.other_metrics_table.setRowCount(0)

        sequence = risk_metrics.get('trade_sequence', {})

        metrics = [
            ("ソルティノレシオ", f"{risk_metrics.get('sortino_ratio', 0):.3f}"),
            ("カルマーレシオ", f"{risk_metrics.get('calmar_ratio', 0):.3f}"),
            ("最大連勝回数", f"{sequence.get('max_consecutive_wins', 0)}回"),
            ("最大連敗回数", f"{sequence.get('max_consecutive_losses', 0)}回"),
            ("平均連勝回数", f"{sequence.get('avg_consecutive_wins', 0):.1f}回"),
            ("平均連敗回数", f"{sequence.get('avg_consecutive_losses', 0):.1f}回"),
        ]

        for label, value in metrics:
            row = self.other_metrics_table.rowCount()
            self.other_metrics_table.insertRow(row)

            label_item = QTableWidgetItem(label)
            label_item.setFont(QFont("Meiryo", 9))
            self.other_metrics_table.setItem(row, 0, label_item)

            value_item = QTableWidgetItem(value)
            value_item.setFont(QFont("Meiryo", 9, QFont.Bold))
            value_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            # ソルティノ/カルマーレシオは高いほど良い
            if "レシオ" in label and risk_metrics.get(label.replace("レシオ", "ratio").lower().replace("ソルティノ", "sortino").replace("カルマー", "calmar"), 0) > 1.0:
                value_item.setForeground(QColor(16, 185, 129))

            self.other_metrics_table.setItem(row, 1, value_item)

    def clear(self):
        """全てのテーブルをクリア"""
        self.drawdown_table.setRowCount(0)
        self.var_table.setRowCount(0)
        self.distribution_table.setRowCount(0)
        self.other_metrics_table.setRowCount(0)
