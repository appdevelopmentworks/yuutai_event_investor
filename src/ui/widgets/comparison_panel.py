"""
Comparison Panel Widget
複数銘柄比較パネル

Author: Yuutai Event Investor Team
Date: 2025-01-11
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QLabel, QPushButton,
    QMessageBox, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
import logging
from typing import Dict, List, Optional
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import platform


class ComparisonChartWidget(QWidget):
    """比較チャートウィジェット"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.init_ui()

        # フォント設定
        if platform.system() == 'Windows':
            plt.rcParams['font.family'] = 'MS Gothic'
        elif platform.system() == 'Darwin':
            plt.rcParams['font.family'] = 'Hiragino Sans'
        else:
            plt.rcParams['font.family'] = 'Noto Sans CJK JP'

    def init_ui(self):
        """UIを初期化"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Matplotlibのfigureを作成
        self.figure = Figure(figsize=(10, 6), facecolor='#1E1E1E')
        self.canvas = FigureCanvasQTAgg(self.figure)
        layout.addWidget(self.canvas)

    def plot_comparison(self, stocks_data: List[Dict]):
        """
        比較チャートをプロット

        Args:
            stocks_data: 銘柄データのリスト
        """
        try:
            self.figure.clear()

            if not stocks_data:
                return

            # 2つのサブプロット: 期待リターン比較と勝率比較
            ax1 = self.figure.add_subplot(1, 2, 1, facecolor='#1E1E1E')
            ax2 = self.figure.add_subplot(1, 2, 2, facecolor='#1E1E1E')

            stock_names = []
            expected_returns = []
            win_rates = []
            colors = ['#1E90FF', '#10B981', '#FACC15', '#EF4444', '#8B5CF6']

            for i, stock in enumerate(stocks_data):
                name = stock.get('name', stock.get('code', ''))
                stock_names.append(name[:6] + '...' if len(name) > 6 else name)
                expected_returns.append(stock.get('expected_return', 0))
                win_rates.append(stock.get('win_rate', 0) * 100)

            # 期待リターン比較
            bars1 = ax1.bar(range(len(stock_names)), expected_returns,
                           color=[colors[i % len(colors)] for i in range(len(stock_names))])
            ax1.set_ylabel('期待リターン (%)', color='#E0E0E0', fontsize=10)
            ax1.set_title('期待リターン比較', color='#E0E0E0', fontsize=12, fontweight='bold')
            ax1.set_xticks(range(len(stock_names)))
            ax1.set_xticklabels(stock_names, rotation=45, ha='right', color='#E0E0E0')
            ax1.tick_params(colors='#E0E0E0')
            ax1.spines['bottom'].set_color('#404040')
            ax1.spines['top'].set_color('#404040')
            ax1.spines['left'].set_color('#404040')
            ax1.spines['right'].set_color('#404040')
            ax1.grid(True, alpha=0.2, color='#404040')
            ax1.axhline(y=0, color='#666666', linestyle='--', linewidth=1)

            # 値をバーの上に表示
            for i, (bar, val) in enumerate(zip(bars1, expected_returns)):
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height,
                        f'{val:+.2f}%',
                        ha='center', va='bottom' if height > 0 else 'top',
                        color='#E0E0E0', fontsize=9)

            # 勝率比較
            bars2 = ax2.bar(range(len(stock_names)), win_rates,
                           color=[colors[i % len(colors)] for i in range(len(stock_names))])
            ax2.set_ylabel('勝率 (%)', color='#E0E0E0', fontsize=10)
            ax2.set_title('勝率比較', color='#E0E0E0', fontsize=12, fontweight='bold')
            ax2.set_xticks(range(len(stock_names)))
            ax2.set_xticklabels(stock_names, rotation=45, ha='right', color='#E0E0E0')
            ax2.tick_params(colors='#E0E0E0')
            ax2.spines['bottom'].set_color('#404040')
            ax2.spines['top'].set_color('#404040')
            ax2.spines['left'].set_color('#404040')
            ax2.spines['right'].set_color('#404040')
            ax2.grid(True, alpha=0.2, color='#404040')
            ax2.set_ylim(0, 100)

            # 50%のライン
            ax2.axhline(y=50, color='#666666', linestyle='--', linewidth=1)

            # 値をバーの上に表示
            for i, (bar, val) in enumerate(zip(bars2, win_rates)):
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height,
                        f'{val:.1f}%',
                        ha='center', va='bottom',
                        color='#E0E0E0', fontsize=9)

            self.figure.tight_layout()
            self.canvas.draw()

        except Exception as e:
            self.logger.error(f"比較チャート描画エラー: {e}", exc_info=True)

    def clear(self):
        """チャートをクリア"""
        self.figure.clear()
        self.canvas.draw()


class ComparisonPanel(QWidget):
    """複数銘柄比較パネル"""

    # シグナル定義
    stock_removed = Signal(str)  # 銘柄が削除されたときのシグナル
    send_to_portfolio = Signal(list)  # ポートフォリオに送信するシグナル

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.compared_stocks = []  # 比較中の銘柄リスト
        self.max_stocks = 5  # 最大比較銘柄数
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

        title = QLabel("📊 銘柄比較")
        title.setFont(QFont("Meiryo", 14, QFont.Bold))
        title.setStyleSheet("color: #E0E0E0;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # 銘柄数表示
        self.count_label = QLabel("0 / 5 銘柄")
        self.count_label.setStyleSheet("color: #B0B0B0; font-size: 11px;")
        header_layout.addWidget(self.count_label)

        # ポートフォリオに送信ボタン
        send_portfolio_btn = QPushButton("💼 ポートフォリオへ送る")
        send_portfolio_btn.setFixedSize(150, 30)
        send_portfolio_btn.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        send_portfolio_btn.clicked.connect(self.send_stocks_to_portfolio)
        header_layout.addWidget(send_portfolio_btn)

        # クリアボタン
        clear_btn = QPushButton("🗑 全てクリア")
        clear_btn.setFixedSize(100, 30)
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
        # 比較テーブル
        # ========================================
        table_label = QLabel("比較テーブル")
        table_label.setFont(QFont("Meiryo", 11, QFont.Bold))
        table_label.setStyleSheet("color: #E0E0E0;")
        layout.addWidget(table_label)

        self.comparison_table = self.create_comparison_table()
        layout.addWidget(self.comparison_table)

        # ========================================
        # 比較チャート
        # ========================================
        chart_label = QLabel("比較チャート")
        chart_label.setFont(QFont("Meiryo", 11, QFont.Bold))
        chart_label.setStyleSheet("color: #E0E0E0;")
        layout.addWidget(chart_label)

        self.chart_widget = ComparisonChartWidget()
        self.chart_widget.setMinimumHeight(300)
        layout.addWidget(self.chart_widget)

    def create_comparison_table(self) -> QTableWidget:
        """比較テーブルを作成"""
        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels([
            "銘柄名", "コード", "最適日数", "勝率(%)", "期待リターン(%)",
            "総トレード", "操作"
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
                border-bottom: 1px solid #2D2D2D;
            }
            QTableWidget::item:selected {
                background-color: #1E90FF;
                color: white;
            }
            QTableWidget::item:hover {
                background-color: #2D2D2D;
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
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # 銘柄名
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # コード
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # 最適日数
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # 勝率
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # 期待リターン
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # 総トレード
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # 操作

        table.setMaximumHeight(250)

        return table

    def add_stock(self, stock_data: Dict) -> bool:
        """
        銘柄を比較リストに追加

        Args:
            stock_data: 銘柄データ

        Returns:
            bool: 追加に成功した場合True
        """
        try:
            code = stock_data.get('code')

            # 重複チェック
            if any(s.get('code') == code and s.get('rights_month') == stock_data.get('rights_month')
                   for s in self.compared_stocks):
                QMessageBox.warning(self, "警告", "この銘柄は既に比較リストに追加されています。")
                return False

            # 最大数チェック
            if len(self.compared_stocks) >= self.max_stocks:
                QMessageBox.warning(
                    self, "警告",
                    f"最大{self.max_stocks}銘柄まで比較できます。\n既存の銘柄を削除してから追加してください。"
                )
                return False

            # 必要なデータの確認
            if not stock_data.get('optimal_days'):
                QMessageBox.warning(
                    self, "警告",
                    "この銘柄はまだバックテストが実行されていません。\n先にバックテストを実行してください。"
                )
                return False

            # 追加
            self.compared_stocks.append(stock_data)
            self.update_display()

            self.logger.info(f"比較リストに追加: {code} - {stock_data.get('name')}")
            return True

        except Exception as e:
            self.logger.error(f"銘柄追加エラー: {e}", exc_info=True)
            return False

    def remove_stock(self, code: str, rights_month: int):
        """
        銘柄を比較リストから削除

        Args:
            code: 銘柄コード
            rights_month: 権利確定月
        """
        try:
            self.compared_stocks = [
                s for s in self.compared_stocks
                if not (s.get('code') == code and s.get('rights_month') == rights_month)
            ]
            self.update_display()
            self.stock_removed.emit(code)
            self.logger.info(f"比較リストから削除: {code}")

        except Exception as e:
            self.logger.error(f"銘柄削除エラー: {e}", exc_info=True)

    def clear_all(self):
        """全ての銘柄をクリア"""
        if not self.compared_stocks:
            return

        reply = QMessageBox.question(
            self, "確認",
            "比較リストを全てクリアしますか？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.compared_stocks.clear()
            self.update_display()
            self.logger.info("比較リストをクリアしました")

    def send_stocks_to_portfolio(self):
        """比較中の銘柄をポートフォリオパネルに送信"""
        if not self.compared_stocks:
            QMessageBox.warning(self, "警告", "比較リストに銘柄がありません。")
            return

        if len(self.compared_stocks) < 2:
            QMessageBox.warning(
                self, "警告",
                "ポートフォリオシミュレーションには2銘柄以上必要です。"
            )
            return

        # ポートフォリオに送信するシグナルを発行
        self.send_to_portfolio.emit(self.compared_stocks.copy())
        self.logger.info(f"{len(self.compared_stocks)}銘柄をポートフォリオに送信")

        QMessageBox.information(
            self, "送信完了",
            f"{len(self.compared_stocks)}銘柄をポートフォリオタブに送信しました。"
        )

    def update_display(self):
        """表示を更新"""
        # 銘柄数更新
        self.count_label.setText(f"{len(self.compared_stocks)} / {self.max_stocks} 銘柄")

        # テーブル更新
        self.update_table()

        # チャート更新
        self.chart_widget.plot_comparison(self.compared_stocks)

    def update_table(self):
        """テーブルを更新"""
        self.comparison_table.setRowCount(0)

        for stock in self.compared_stocks:
            row = self.comparison_table.rowCount()
            self.comparison_table.insertRow(row)

            # 銘柄名
            name_item = QTableWidgetItem(stock.get('name', ''))
            self.comparison_table.setItem(row, 0, name_item)

            # コード
            code = stock.get('code', '')
            rights_month = stock.get('rights_month', 0)
            code_item = QTableWidgetItem(f"{code} ({rights_month}月)")
            code_item.setTextAlignment(Qt.AlignCenter)
            self.comparison_table.setItem(row, 1, code_item)

            # 最適日数
            optimal_days = stock.get('optimal_days', 0)
            days_item = QTableWidgetItem(f"{optimal_days}日前")
            days_item.setTextAlignment(Qt.AlignCenter)
            self.comparison_table.setItem(row, 2, days_item)

            # 勝率
            win_rate = stock.get('win_rate', 0)
            win_rate_item = QTableWidgetItem(f"{win_rate*100:.1f}%")
            win_rate_item.setTextAlignment(Qt.AlignCenter)
            if win_rate >= 0.7:
                win_rate_item.setForeground(QColor(16, 185, 129))
            elif win_rate >= 0.5:
                win_rate_item.setForeground(QColor(250, 204, 21))
            else:
                win_rate_item.setForeground(QColor(239, 68, 68))
            self.comparison_table.setItem(row, 3, win_rate_item)

            # 期待リターン
            expected_return = stock.get('expected_return', 0)
            return_item = QTableWidgetItem(f"{expected_return:+.2f}%")
            return_item.setTextAlignment(Qt.AlignCenter)
            if expected_return > 0:
                return_item.setForeground(QColor(16, 185, 129))
            else:
                return_item.setForeground(QColor(239, 68, 68))
            self.comparison_table.setItem(row, 4, return_item)

            # 総トレード
            total_count = stock.get('total_count', 0)
            count_item = QTableWidgetItem(str(total_count))
            count_item.setTextAlignment(Qt.AlignCenter)
            self.comparison_table.setItem(row, 5, count_item)

            # 削除ボタン
            remove_btn = QPushButton("削除")
            remove_btn.setStyleSheet("""
                QPushButton {
                    background-color: #EF4444;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    padding: 3px 8px;
                }
                QPushButton:hover {
                    background-color: #DC2626;
                }
            """)
            remove_btn.clicked.connect(
                lambda checked, c=code, rm=rights_month: self.remove_stock(c, rm)
            )
            self.comparison_table.setCellWidget(row, 6, remove_btn)

    def get_compared_stocks(self) -> List[Dict]:
        """比較中の銘柄リストを取得"""
        return self.compared_stocks.copy()

    def is_stock_compared(self, code: str, rights_month: int) -> bool:
        """銘柄が比較リストに含まれているかチェック"""
        return any(
            s.get('code') == code and s.get('rights_month') == rights_month
            for s in self.compared_stocks
        )
