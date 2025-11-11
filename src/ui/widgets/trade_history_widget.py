"""
Trade History Widget
トレード履歴表示ウィジェット

Author: Yuutai Event Investor Team
Date: 2025-01-11
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QLabel, QPushButton,
    QComboBox, QTabWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
import logging
from typing import Dict, List, Optional
import pandas as pd


class TradeHistoryWidget(QWidget):
    """トレード履歴表示ウィジェット"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.current_trades = None
        self.init_ui()

    def init_ui(self):
        """UIを初期化"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # ========================================
        # ヘッダー
        # ========================================
        header_layout = QHBoxLayout()

        title = QLabel("📊 トレード履歴詳細")
        title.setFont(QFont("Meiryo", 13, QFont.Bold))
        title.setStyleSheet("color: #1E90FF;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # フィルター
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["全て", "勝ちトレードのみ", "負けトレードのみ"])
        self.filter_combo.setStyleSheet("""
            QComboBox {
                background-color: #2D2D2D;
                color: #E0E0E0;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 5px 10px;
                min-width: 120px;
            }
            QComboBox:hover {
                border: 1px solid #1E90FF;
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
        self.filter_combo.currentIndexChanged.connect(self.on_filter_changed)
        header_layout.addWidget(self.filter_combo)

        # エクスポートボタン
        export_btn = QPushButton("💾 CSV出力")
        export_btn.setFixedSize(100, 30)
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #4682B4;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #1E90FF;
            }
        """)
        export_btn.clicked.connect(self.export_to_csv)
        header_layout.addWidget(export_btn)

        layout.addLayout(header_layout)

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
                padding: 8px 16px;
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

        # タブ1: 全トレード履歴
        self.all_trades_table = self.create_trades_table()
        self.tab_widget.addTab(self.all_trades_table, "全トレード")

        # タブ2: 年別パフォーマンス
        self.yearly_performance_widget = self.create_yearly_performance_widget()
        self.tab_widget.addTab(self.yearly_performance_widget, "年別分析")

        layout.addWidget(self.tab_widget)

    def create_trades_table(self) -> QTableWidget:
        """トレード履歴テーブルを作成"""
        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels([
            "取引年", "権利確定日", "買入日", "買値", "売値", "リターン(%)", "結果"
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
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # 取引年
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # 権利確定日
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # 買入日
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # 買値
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # 売値
        header.setSectionResizeMode(5, QHeaderView.Stretch)  # リターン
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # 結果

        # 行選択モード
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)

        # ソート有効化
        table.setSortingEnabled(True)

        return table

    def create_yearly_performance_widget(self) -> QWidget:
        """年別パフォーマンスウィジェットを作成"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)

        # 説明ラベル
        desc = QLabel("各年のパフォーマンスサマリー")
        desc.setStyleSheet("color: #B0B0B0; font-size: 11px;")
        layout.addWidget(desc)

        # テーブル
        self.yearly_table = QTableWidget()
        self.yearly_table.setColumnCount(6)
        self.yearly_table.setHorizontalHeaderLabels([
            "年", "トレード数", "勝率(%)", "平均リターン(%)", "最大勝ち(%)", "最大負け(%)"
        ])

        self.yearly_table.setStyleSheet("""
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

        header = self.yearly_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        layout.addWidget(self.yearly_table)

        return widget

    def load_trade_data(self, trade_data: Dict):
        """
        トレードデータを読み込む

        Args:
            trade_data: バックテスト結果データ（win_trades, lose_tradesを含む）
        """
        try:
            self.current_trades = trade_data
            self.update_all_trades_table()
            self.update_yearly_performance()
            self.logger.info("トレード履歴データを読み込みました")
        except Exception as e:
            self.logger.error(f"トレードデータ読み込みエラー: {e}", exc_info=True)

    def update_all_trades_table(self):
        """全トレードテーブルを更新"""
        if not self.current_trades:
            return

        win_trades = self.current_trades.get('win_trades', pd.DataFrame())
        lose_trades = self.current_trades.get('lose_trades', pd.DataFrame())

        # データフレームを結合
        all_trades = []

        # 列名の正規化（大文字・小文字両方に対応）
        close_col = 'Close' if (not win_trades.empty and 'Close' in win_trades.columns) or \
                              (not lose_trades.empty and 'Close' in lose_trades.columns) else 'close'

        if not win_trades.empty:
            for idx, row in win_trades.iterrows():
                all_trades.append({
                    'date': idx,
                    'buy_date': row.get('買入日', None),
                    'return': row.get('リターン(%)', 0),
                    'buy_price': row.get('買入日終値', 0),
                    'sell_price': row.get(close_col, 0),
                    'result': 'WIN'
                })

        if not lose_trades.empty:
            for idx, row in lose_trades.iterrows():
                all_trades.append({
                    'date': idx,
                    'buy_date': row.get('買入日', None),
                    'return': row.get('リターン(%)', 0),
                    'buy_price': row.get('買入日終値', 0),
                    'sell_price': row.get(close_col, 0),
                    'result': 'LOSE'
                })

        # 日付でソート
        all_trades.sort(key=lambda x: x['date'], reverse=True)

        # テーブルに表示
        self.populate_table(self.all_trades_table, all_trades)

    def populate_table(self, table: QTableWidget, trades: List[Dict]):
        """テーブルにデータを表示"""
        table.setSortingEnabled(False)
        table.setRowCount(0)

        for trade in trades:
            row = table.rowCount()
            table.insertRow(row)

            trade_date = trade['date']

            # 取引年
            year_item = QTableWidgetItem(str(trade_date.year))
            year_item.setTextAlignment(Qt.AlignCenter)
            table.setItem(row, 0, year_item)

            # 権利確定日（権利付最終日）
            rights_date_item = QTableWidgetItem(trade_date.strftime('%Y-%m-%d'))
            rights_date_item.setTextAlignment(Qt.AlignCenter)
            table.setItem(row, 1, rights_date_item)

            # 買入日
            buy_date = trade.get('buy_date')
            if buy_date and hasattr(buy_date, 'strftime'):
                buy_date_str = buy_date.strftime('%Y-%m-%d')
            else:
                buy_date_str = "N/A"
            buy_date_item = QTableWidgetItem(buy_date_str)
            buy_date_item.setTextAlignment(Qt.AlignCenter)
            table.setItem(row, 2, buy_date_item)

            # 買値
            buy_price = trade.get('buy_price', 0)
            buy_price_item = QTableWidgetItem(f"¥{buy_price:,.0f}")
            buy_price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            table.setItem(row, 3, buy_price_item)

            # 売値
            sell_price = trade.get('sell_price', 0)
            sell_price_item = QTableWidgetItem(f"¥{sell_price:,.0f}")
            sell_price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            table.setItem(row, 4, sell_price_item)

            # リターン
            return_val = trade.get('return', 0)
            return_item = QTableWidgetItem(f"{return_val:+.2f}%")
            return_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if return_val > 0:
                return_item.setForeground(QColor(16, 185, 129))  # 緑
            else:
                return_item.setForeground(QColor(239, 68, 68))  # 赤
            table.setItem(row, 5, return_item)

            # 結果
            result = trade.get('result', '')
            result_item = QTableWidgetItem(result)
            result_item.setTextAlignment(Qt.AlignCenter)
            if result == 'WIN':
                result_item.setForeground(QColor(16, 185, 129))
                result_item.setFont(QFont("Meiryo", 9, QFont.Bold))
            else:
                result_item.setForeground(QColor(239, 68, 68))
                result_item.setFont(QFont("Meiryo", 9, QFont.Bold))
            table.setItem(row, 6, result_item)

        table.setSortingEnabled(True)

    def update_yearly_performance(self):
        """年別パフォーマンスを更新"""
        if not self.current_trades:
            return

        win_trades = self.current_trades.get('win_trades', pd.DataFrame())
        lose_trades = self.current_trades.get('lose_trades', pd.DataFrame())

        # 年ごとに集計
        yearly_stats = {}

        # 勝ちトレード
        if not win_trades.empty:
            for idx, row in win_trades.iterrows():
                year = idx.year
                if year not in yearly_stats:
                    yearly_stats[year] = {
                        'wins': 0, 'losses': 0,
                        'returns': [], 'max_win': 0, 'max_lose': 0
                    }
                yearly_stats[year]['wins'] += 1
                return_val = row.get('リターン(%)', 0)
                yearly_stats[year]['returns'].append(return_val)
                yearly_stats[year]['max_win'] = max(yearly_stats[year]['max_win'], return_val)

        # 負けトレード
        if not lose_trades.empty:
            for idx, row in lose_trades.iterrows():
                year = idx.year
                if year not in yearly_stats:
                    yearly_stats[year] = {
                        'wins': 0, 'losses': 0,
                        'returns': [], 'max_win': 0, 'max_lose': 0
                    }
                yearly_stats[year]['losses'] += 1
                return_val = row.get('リターン(%)', 0)
                yearly_stats[year]['returns'].append(return_val)
                yearly_stats[year]['max_lose'] = min(yearly_stats[year]['max_lose'], return_val)

        # テーブルに表示
        self.yearly_table.setSortingEnabled(False)
        self.yearly_table.setRowCount(0)

        for year in sorted(yearly_stats.keys(), reverse=True):
            stats = yearly_stats[year]
            row = self.yearly_table.rowCount()
            self.yearly_table.insertRow(row)

            total_trades = stats['wins'] + stats['losses']
            win_rate = (stats['wins'] / total_trades * 100) if total_trades > 0 else 0
            avg_return = sum(stats['returns']) / len(stats['returns']) if stats['returns'] else 0

            # 年
            year_item = QTableWidgetItem(str(year))
            year_item.setTextAlignment(Qt.AlignCenter)
            self.yearly_table.setItem(row, 0, year_item)

            # トレード数
            trades_item = QTableWidgetItem(str(total_trades))
            trades_item.setTextAlignment(Qt.AlignCenter)
            self.yearly_table.setItem(row, 1, trades_item)

            # 勝率
            win_rate_item = QTableWidgetItem(f"{win_rate:.1f}%")
            win_rate_item.setTextAlignment(Qt.AlignCenter)
            if win_rate >= 70:
                win_rate_item.setForeground(QColor(16, 185, 129))
            elif win_rate >= 50:
                win_rate_item.setForeground(QColor(250, 204, 21))
            self.yearly_table.setItem(row, 2, win_rate_item)

            # 平均リターン
            avg_item = QTableWidgetItem(f"{avg_return:+.2f}%")
            avg_item.setTextAlignment(Qt.AlignCenter)
            if avg_return > 0:
                avg_item.setForeground(QColor(16, 185, 129))
            else:
                avg_item.setForeground(QColor(239, 68, 68))
            self.yearly_table.setItem(row, 3, avg_item)

            # 最大勝ち
            max_win_item = QTableWidgetItem(f"+{stats['max_win']:.2f}%")
            max_win_item.setTextAlignment(Qt.AlignCenter)
            max_win_item.setForeground(QColor(16, 185, 129))
            self.yearly_table.setItem(row, 4, max_win_item)

            # 最大負け
            max_lose_item = QTableWidgetItem(f"{stats['max_lose']:.2f}%")
            max_lose_item.setTextAlignment(Qt.AlignCenter)
            max_lose_item.setForeground(QColor(239, 68, 68))
            self.yearly_table.setItem(row, 5, max_lose_item)

        self.yearly_table.setSortingEnabled(True)

    def on_filter_changed(self, index: int):
        """フィルターが変更された時の処理"""
        # TODO: フィルター機能の実装
        pass

    def export_to_csv(self):
        """CSV出力"""
        # TODO: CSV出力機能の実装
        self.logger.info("CSV出力機能は未実装です")

    def clear(self):
        """データをクリア"""
        self.current_trades = None
        self.all_trades_table.setRowCount(0)
        self.yearly_table.setRowCount(0)
