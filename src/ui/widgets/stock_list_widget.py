"""
Stock List Widget
銘柄リスト表示ウィジェット

Author: Yuutai Event Investor Team
Date: 2024-11-07
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QLineEdit, QComboBox,
    QLabel, QPushButton
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
import logging
from typing import List, Dict, Any, Optional


class StockListWidget(QWidget):
    """銘柄リストウィジェット"""

    # シグナル定義
    stock_selected = Signal(dict)  # 銘柄が選択されたときのシグナル

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.stocks_data = []

        self.init_ui()

    def init_ui(self):
        """UIを初期化"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # ========================================
        # タイトルとフィルター
        # ========================================
        header_layout = QHBoxLayout()

        # タイトル
        title = QLabel("銘柄リスト")
        title_font = QFont("Meiryo", 14, QFont.Bold)
        title.setFont(title_font)
        title.setStyleSheet("color: #E0E0E0;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # 検索ボックス
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("検索...")
        self.search_box.setFixedWidth(150)
        self.search_box.setStyleSheet("""
            QLineEdit {
                background-color: #2D2D2D;
                color: #E0E0E0;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 5px 10px;
            }
            QLineEdit:focus {
                border: 1px solid #1E90FF;
            }
        """)
        self.search_box.textChanged.connect(self.on_search)
        header_layout.addWidget(self.search_box)

        layout.addLayout(header_layout)

        # ========================================
        # フィルターエリア
        # ========================================
        filter_layout = QHBoxLayout()

        # 権利確定月フィルター
        month_label = QLabel("権利月:")
        month_label.setStyleSheet("color: #B0B0B0;")
        filter_layout.addWidget(month_label)

        self.month_filter = QComboBox()
        self.month_filter.addItems([
            "全て", "1月", "2月", "3月", "4月", "5月", "6月",
            "7月", "8月", "9月", "10月", "11月", "12月"
        ])
        self.month_filter.setStyleSheet("""
            QComboBox {
                background-color: #2D2D2D;
                color: #E0E0E0;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 5px 10px;
                min-width: 80px;
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
        self.month_filter.currentIndexChanged.connect(self.on_filter_changed)
        filter_layout.addWidget(self.month_filter)

        filter_layout.addStretch()

        # 件数表示
        self.count_label = QLabel("0件")
        self.count_label.setStyleSheet("color: #B0B0B0;")
        filter_layout.addWidget(self.count_label)

        layout.addLayout(filter_layout)

        # ========================================
        # テーブル
        # ========================================
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "コード", "銘柄名", "権利月", "最適日数", "勝率", "期待値"
        ])

        # テーブルスタイル
        self.table.setStyleSheet("""
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
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # コード
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # 銘柄名
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # 権利月
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # 最適日数
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # 勝率
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # 期待値

        # 行選択モード
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)

        # クリックイベント
        self.table.cellClicked.connect(self.on_row_clicked)

        # ソート有効化
        self.table.setSortingEnabled(True)

        layout.addWidget(self.table)

    def load_stocks(self, stocks: List[Dict[str, Any]]):
        """
        銘柄データを読み込む

        Args:
            stocks: 銘柄データのリスト
        """
        self.stocks_data = stocks
        self.update_table()
        self.count_label.setText(f"{len(stocks)}件")
        self.logger.info(f"銘柄データを読み込みました: {len(stocks)}件")

    def update_table(self, filtered_stocks: Optional[List[Dict[str, Any]]] = None):
        """
        テーブルを更新

        Args:
            filtered_stocks: フィルタリング済みの銘柄データ（Noneの場合は全データ）
        """
        stocks = filtered_stocks if filtered_stocks is not None else self.stocks_data

        # ソートを一時的に無効化
        self.table.setSortingEnabled(False)

        # テーブルをクリア
        self.table.setRowCount(0)

        # データを追加
        for stock in stocks:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # コード
            code_item = QTableWidgetItem(stock.get('code', ''))
            code_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, code_item)

            # 銘柄名
            name_item = QTableWidgetItem(stock.get('name', ''))
            self.table.setItem(row, 1, name_item)

            # 権利月
            month = stock.get('rights_month', '')
            month_item = QTableWidgetItem(f"{month}月" if month else '')
            month_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 2, month_item)

            # 最適日数
            optimal_days = stock.get('optimal_days', '')
            days_item = QTableWidgetItem(f"{optimal_days}日前" if optimal_days else '-')
            days_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, days_item)

            # 勝率
            win_rate = stock.get('win_rate', 0)
            win_rate_item = QTableWidgetItem(f"{win_rate*100:.1f}%" if win_rate else '-')
            win_rate_item.setTextAlignment(Qt.AlignCenter)
            # 勝率が高い場合は緑色
            if win_rate and win_rate >= 0.7:
                win_rate_item.setForeground(QColor(16, 185, 129))  # 緑
            elif win_rate and win_rate >= 0.5:
                win_rate_item.setForeground(QColor(250, 204, 21))  # 黄色
            self.table.setItem(row, 4, win_rate_item)

            # 期待値
            expected_return = stock.get('expected_return', 0)
            return_item = QTableWidgetItem(f"{expected_return:+.2f}%" if expected_return else '-')
            return_item.setTextAlignment(Qt.AlignCenter)
            # 期待値がプラスの場合は緑色、マイナスの場合は赤色
            if expected_return and expected_return > 0:
                return_item.setForeground(QColor(16, 185, 129))  # 緑
            elif expected_return and expected_return < 0:
                return_item.setForeground(QColor(239, 68, 68))  # 赤
            self.table.setItem(row, 5, return_item)

        # ソートを再度有効化
        self.table.setSortingEnabled(True)

        # 件数を更新
        self.count_label.setText(f"{len(stocks)}件")

    def on_search(self, text: str):
        """検索テキスト変更時の処理"""
        if not text:
            self.update_table()
            return

        # 検索条件に一致する銘柄のみフィルタリング
        filtered = [
            stock for stock in self.stocks_data
            if text.lower() in stock.get('code', '').lower() or
               text.lower() in stock.get('name', '').lower()
        ]

        self.update_table(filtered)

    def on_filter_changed(self, index: int):
        """権利月フィルター変更時の処理"""
        if index == 0:  # 全て
            self.update_table()
            return

        # 選択された月でフィルタリング
        selected_month = index
        filtered = [
            stock for stock in self.stocks_data
            if stock.get('rights_month') == selected_month
        ]

        self.update_table(filtered)

    def on_row_clicked(self, row: int, column: int):
        """行クリック時の処理"""
        # コードを取得
        code_item = self.table.item(row, 0)
        if not code_item:
            return

        code = code_item.text()

        # 該当する銘柄データを探す
        selected_stock = None
        for stock in self.stocks_data:
            if stock.get('code') == code:
                selected_stock = stock
                break

        if selected_stock:
            self.logger.info(f"銘柄が選択されました: {code} - {selected_stock.get('name')}")
            self.stock_selected.emit(selected_stock)

    def get_selected_stock(self) -> Optional[Dict[str, Any]]:
        """選択中の銘柄データを取得"""
        current_row = self.table.currentRow()
        if current_row < 0:
            return None

        code_item = self.table.item(current_row, 0)
        if not code_item:
            return None

        code = code_item.text()

        for stock in self.stocks_data:
            if stock.get('code') == code:
                return stock

        return None
