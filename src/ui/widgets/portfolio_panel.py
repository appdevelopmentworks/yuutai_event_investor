"""
Portfolio Panel Widget
ポートフォリオシミュレーションパネル

Author: Yuutai Event Investor Team
Date: 2025-01-11
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QLabel, QPushButton,
    QSpinBox, QComboBox, QMessageBox, QFrame, QSlider, QDoubleSpinBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
import logging
from typing import Dict, List, Optional
from ...core.portfolio_calculator import PortfolioCalculator


class PortfolioPanel(QWidget):
    """ポートフォリオシミュレーションパネル"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.portfolio_stocks = []  # ポートフォリオに含まれる銘柄
        self.calculator = PortfolioCalculator()
        self.init_ui()

    def init_ui(self):
        """UIを初期化"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # ========================================
        # ヘッダー
        # ========================================
        header_layout = QHBoxLayout()

        title = QLabel("💼 ポートフォリオシミュレーション")
        title.setFont(QFont("Meiryo", 14, QFont.Bold))
        title.setStyleSheet("color: #E0E0E0;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # クリアボタン
        clear_btn = QPushButton("🗑 クリア")
        clear_btn.setFixedSize(80, 30)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #EF4444;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #DC2626;
            }
        """)
        clear_btn.clicked.connect(self.clear_all)
        header_layout.addWidget(clear_btn)

        layout.addLayout(header_layout)

        # 区切り線
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #404040;")
        layout.addWidget(line)

        # ========================================
        # 設定パネル
        # ========================================
        settings_label = QLabel("投資設定")
        settings_label.setFont(QFont("Meiryo", 11, QFont.Bold))
        settings_label.setStyleSheet("color: #E0E0E0;")
        layout.addWidget(settings_label)

        settings_layout = QHBoxLayout()

        # 総投資金額
        amount_label = QLabel("総投資金額:")
        amount_label.setStyleSheet("color: #B0B0B0;")
        settings_layout.addWidget(amount_label)

        self.investment_amount = QSpinBox()
        self.investment_amount.setMinimum(10)
        self.investment_amount.setMaximum(100000)
        self.investment_amount.setValue(1000)
        self.investment_amount.setSingleStep(10)
        self.investment_amount.setSuffix(" 万円")
        self.investment_amount.setStyleSheet("""
            QSpinBox {
                background-color: #2D2D2D;
                color: #E0E0E0;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 5px;
                min-width: 120px;
            }
        """)
        settings_layout.addWidget(self.investment_amount)

        settings_layout.addSpacing(20)

        # リスク許容度
        risk_label = QLabel("リスク許容度:")
        risk_label.setStyleSheet("color: #B0B0B0;")
        settings_layout.addWidget(risk_label)

        self.risk_tolerance = QComboBox()
        self.risk_tolerance.addItems(["低リスク", "中リスク", "高リスク"])
        self.risk_tolerance.setCurrentIndex(1)
        self.risk_tolerance.setStyleSheet("""
            QComboBox {
                background-color: #2D2D2D;
                color: #E0E0E0;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 5px;
                min-width: 100px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #2D2D2D;
                color: #E0E0E0;
                selection-background-color: #1E90FF;
            }
        """)
        settings_layout.addWidget(self.risk_tolerance)

        settings_layout.addStretch()

        # 最適化ボタン
        optimize_btn = QPushButton("🎯 最適配分を計算")
        optimize_btn.setFixedSize(150, 35)
        optimize_btn.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        optimize_btn.clicked.connect(self.optimize_portfolio)
        settings_layout.addWidget(optimize_btn)

        layout.addLayout(settings_layout)

        # ========================================
        # 銘柄配分テーブル
        # ========================================
        allocation_label = QLabel("銘柄配分")
        allocation_label.setFont(QFont("Meiryo", 11, QFont.Bold))
        allocation_label.setStyleSheet("color: #E0E0E0;")
        layout.addWidget(allocation_label)

        self.allocation_table = self.create_allocation_table()
        layout.addWidget(self.allocation_table)

        # ========================================
        # ポートフォリオ指標
        # ========================================
        metrics_label = QLabel("ポートフォリオ指標")
        metrics_label.setFont(QFont("Meiryo", 11, QFont.Bold))
        metrics_label.setStyleSheet("color: #E0E0E0;")
        layout.addWidget(metrics_label)

        self.metrics_widget = self.create_metrics_widget()
        layout.addWidget(self.metrics_widget)

    def create_allocation_table(self) -> QTableWidget:
        """配分テーブルを作成"""
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels([
            "銘柄名", "コード", "配分比率(%)", "投資金額(万円)", "期待リターン(%)"
        ])

        # テーブルスタイル
        table.setStyleSheet("""
            QTableWidget {
                background-color: #1E1E1E;
                color: #E0E0E0;
                border: 1px solid #404040;
                gridline-color: #404040;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #1E90FF;
            }
            QHeaderView::section {
                background-color: #2D2D2D;
                color: #E0E0E0;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #1E90FF;
                font-weight: bold;
            }
        """)

        # ヘッダー設定
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)

        table.setMaximumHeight(300)

        return table

    def create_metrics_widget(self) -> QWidget:
        """指標ウィジェットを作成"""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #2D2D2D;
                border-radius: 8px;
                border: 1px solid #404040;
            }
        """)

        layout = QHBoxLayout(widget)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(30)

        # 期待リターン
        self.portfolio_return_label = self._create_metric_widget(
            "ポートフォリオ期待リターン", "-", "#10B981"
        )
        layout.addWidget(self.portfolio_return_label)

        # 勝率
        self.portfolio_winrate_label = self._create_metric_widget(
            "ポートフォリオ勝率", "-", "#1E90FF"
        )
        layout.addWidget(self.portfolio_winrate_label)

        # リスク
        self.portfolio_risk_label = self._create_metric_widget(
            "ポートフォリオリスク", "-", "#FACC15"
        )
        layout.addWidget(self.portfolio_risk_label)

        # シャープレシオ
        self.sharpe_ratio_label = self._create_metric_widget(
            "シャープレシオ", "-", "#8B5CF6"
        )
        layout.addWidget(self.sharpe_ratio_label)

        # ソルティノレシオ
        self.sortino_ratio_label = self._create_metric_widget(
            "ソルティノレシオ", "-", "#A78BFA"
        )
        layout.addWidget(self.sortino_ratio_label)

        # リスク削減効果
        self.risk_reduction_label = self._create_metric_widget(
            "リスク削減効果", "-", "#10B981"
        )
        layout.addWidget(self.risk_reduction_label)

        # 最悪ケースリターン
        self.worst_case_label = self._create_metric_widget(
            "最悪ケース(95%)", "-", "#EF4444"
        )
        layout.addWidget(self.worst_case_label)

        return widget

    def _create_metric_widget(self, title: str, value: str, color: str) -> QWidget:
        """指標ウィジェットを作成"""
        widget = QWidget()
        widget.setStyleSheet("border: none;")

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        title_label = QLabel(title)
        title_label.setFont(QFont("Meiryo", 9))
        title_label.setStyleSheet("color: #B0B0B0;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setFont(QFont("Meiryo", 14, QFont.Bold))
        value_label.setStyleSheet(f"color: {color};")
        value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(value_label)

        # value_labelを後で更新できるように保存
        widget.value_label = value_label

        return widget

    def add_stock(self, stock_data: Dict) -> bool:
        """
        ポートフォリオに銘柄を追加

        Args:
            stock_data: 銘柄データ

        Returns:
            bool: 追加成功時True
        """
        # 同じ銘柄(コード+権利月)が既に存在するかチェック
        code = stock_data.get('code')
        rights_month = stock_data.get('rights_month')

        for stock in self.portfolio_stocks:
            if stock.get('code') == code and stock.get('rights_month') == rights_month:
                return False  # 既に存在

        self.portfolio_stocks.append(stock_data)
        self.update_table()
        self.calculate_equal_weight_portfolio()
        return True

    def set_stocks(self, stocks: List[Dict]):
        """
        ポートフォリオに銘柄を設定

        Args:
            stocks: 銘柄データのリスト
        """
        self.portfolio_stocks = stocks
        self.update_table()
        self.calculate_equal_weight_portfolio()

    def update_table(self):
        """テーブルを更新（均等配分）"""
        self.allocation_table.setRowCount(0)

        if not self.portfolio_stocks:
            return

        n_stocks = len(self.portfolio_stocks)
        equal_weight = 100.0 / n_stocks
        total_investment = self.investment_amount.value()

        for stock in self.portfolio_stocks:
            row = self.allocation_table.rowCount()
            self.allocation_table.insertRow(row)

            # 銘柄名
            name_item = QTableWidgetItem(stock.get('name', ''))
            self.allocation_table.setItem(row, 0, name_item)

            # コード
            code = stock.get('code', '')
            rights_month = stock.get('rights_month', 0)
            code_item = QTableWidgetItem(f"{code} ({rights_month}月)")
            code_item.setTextAlignment(Qt.AlignCenter)
            self.allocation_table.setItem(row, 1, code_item)

            # 配分比率
            weight_item = QTableWidgetItem(f"{equal_weight:.1f}%")
            weight_item.setTextAlignment(Qt.AlignCenter)
            self.allocation_table.setItem(row, 2, weight_item)

            # 投資金額
            amount = total_investment * equal_weight / 100
            amount_item = QTableWidgetItem(f"{amount:.1f}")
            amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.allocation_table.setItem(row, 3, amount_item)

            # 期待リターン
            expected_return = stock.get('expected_return', 0)
            return_item = QTableWidgetItem(f"{expected_return:+.2f}%")
            return_item.setTextAlignment(Qt.AlignCenter)
            if expected_return > 0:
                return_item.setForeground(QColor(16, 185, 129))
            else:
                return_item.setForeground(QColor(239, 68, 68))
            self.allocation_table.setItem(row, 4, return_item)

    def calculate_equal_weight_portfolio(self):
        """均等配分ポートフォリオを計算"""
        if not self.portfolio_stocks:
            return

        n_stocks = len(self.portfolio_stocks)
        equal_weights = [1.0 / n_stocks] * n_stocks

        metrics = self.calculator.calculate_portfolio_metrics(
            self.portfolio_stocks,
            equal_weights
        )

        if metrics:
            self.update_metrics_display(metrics)

    def optimize_portfolio(self):
        """ポートフォリオを最適化"""
        if not self.portfolio_stocks:
            QMessageBox.warning(
                self, "警告",
                "ポートフォリオに銘柄がありません。\n比較パネルから銘柄を追加してください。"
            )
            return

        if len(self.portfolio_stocks) < 2:
            QMessageBox.warning(
                self, "警告",
                "最適化には2銘柄以上必要です。"
            )
            return

        # リスク許容度を取得
        risk_map = {0: 'low', 1: 'medium', 2: 'high'}
        risk_tolerance = risk_map[self.risk_tolerance.currentIndex()]

        # 最適化実行
        result = self.calculator.suggest_allocation(
            self.portfolio_stocks,
            self.investment_amount.value() * 10000,  # 万円を円に変換
            risk_tolerance
        )

        if not result:
            QMessageBox.critical(
                self, "エラー",
                "最適化に失敗しました。"
            )
            return

        # テーブルを更新
        self.update_table_with_optimization(result['allocations'])

        # 指標を更新
        self.update_metrics_display(result['portfolio_metrics'])

        self.logger.info(f"ポートフォリオ最適化完了 - リスク許容度: {risk_tolerance}")

    def update_table_with_optimization(self, allocations: List[Dict]):
        """最適化結果でテーブルを更新"""
        self.allocation_table.setRowCount(0)

        for allocation in allocations:
            row = self.allocation_table.rowCount()
            self.allocation_table.insertRow(row)

            # 対応する銘柄データを取得
            stock = next((s for s in self.portfolio_stocks
                         if s.get('code') == allocation['code']), None)

            if not stock:
                continue

            # 銘柄名
            name_item = QTableWidgetItem(allocation['name'])
            self.allocation_table.setItem(row, 0, name_item)

            # コード
            rights_month = stock.get('rights_month', 0)
            code_item = QTableWidgetItem(f"{allocation['code']} ({rights_month}月)")
            code_item.setTextAlignment(Qt.AlignCenter)
            self.allocation_table.setItem(row, 1, code_item)

            # 配分比率
            weight = allocation['weight'] * 100
            weight_item = QTableWidgetItem(f"{weight:.1f}%")
            weight_item.setTextAlignment(Qt.AlignCenter)
            # 推奨配分は背景色を変更
            weight_item.setBackground(QColor(30, 144, 255, 30))
            self.allocation_table.setItem(row, 2, weight_item)

            # 投資金額
            amount = allocation['amount'] / 10000  # 円を万円に変換
            amount_item = QTableWidgetItem(f"{amount:.1f}")
            amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            amount_item.setBackground(QColor(30, 144, 255, 30))
            self.allocation_table.setItem(row, 3, amount_item)

            # 期待リターン
            expected_return = stock.get('expected_return', 0)
            return_item = QTableWidgetItem(f"{expected_return:+.2f}%")
            return_item.setTextAlignment(Qt.AlignCenter)
            if expected_return > 0:
                return_item.setForeground(QColor(16, 185, 129))
            else:
                return_item.setForeground(QColor(239, 68, 68))
            self.allocation_table.setItem(row, 4, return_item)

    def update_metrics_display(self, metrics: Dict):
        """指標表示を更新"""
        # ポートフォリオ期待リターン
        self.portfolio_return_label.value_label.setText(
            f"{metrics['expected_return']:+.2f}%"
        )

        # ポートフォリオ勝率
        self.portfolio_winrate_label.value_label.setText(
            f"{metrics['win_rate']*100:.1f}%"
        )

        # リスク
        self.portfolio_risk_label.value_label.setText(
            f"{metrics['risk']:.2f}"
        )

        # シャープレシオ
        self.sharpe_ratio_label.value_label.setText(
            f"{metrics['sharpe_ratio']:.2f}"
        )

        # ソルティノレシオ
        self.sortino_ratio_label.value_label.setText(
            f"{metrics.get('sortino_ratio', 0):.2f}"
        )

        # リスク削減効果
        self.risk_reduction_label.value_label.setText(
            f"{metrics['risk_reduction']:+.1f}%"
        )

        # 最悪ケースリターン
        self.worst_case_label.value_label.setText(
            f"{metrics.get('worst_case_return', 0):+.2f}%"
        )

    def clear_all(self):
        """全てクリア"""
        if not self.portfolio_stocks:
            return

        reply = QMessageBox.question(
            self, "確認",
            "ポートフォリオをクリアしますか？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.portfolio_stocks.clear()
            self.allocation_table.setRowCount(0)

            # 指標をリセット
            self.portfolio_return_label.value_label.setText("-")
            self.portfolio_winrate_label.value_label.setText("-")
            self.portfolio_risk_label.value_label.setText("-")
            self.sharpe_ratio_label.value_label.setText("-")
            self.sortino_ratio_label.value_label.setText("-")
            self.risk_reduction_label.value_label.setText("-")
            self.worst_case_label.value_label.setText("-")

            self.logger.info("ポートフォリオをクリアしました")
