"""
Stock List Widget
銘柄リスト表示ウィジェット

Author: Yuutai Event Investor Team
Date: 2024-11-07
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QLineEdit, QComboBox,
    QLabel, QPushButton, QMenu
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor, QAction, QCursor
import logging
from typing import List, Dict, Any, Optional


class NumericTableWidgetItem(QTableWidgetItem):
    """数値ソート用のカスタムQTableWidgetItem"""

    def __init__(self, text: str, numeric_value: Optional[float] = None):
        super().__init__(text)
        self.numeric_value = numeric_value

    def __lt__(self, other):
        """ソート時の比較演算子"""
        if isinstance(other, NumericTableWidgetItem):
            # 両方が数値を持つ場合は数値で比較
            self_val = self.numeric_value if self.numeric_value is not None else float('-inf')
            other_val = other.numeric_value if other.numeric_value is not None else float('-inf')
            return self_val < other_val
        return super().__lt__(other)


class StockListWidget(QWidget):
    """銘柄リストウィジェット"""

    # シグナル定義
    stock_selected = Signal(dict)  # 銘柄が選択されたときのシグナル
    add_to_watchlist_requested = Signal(dict)  # ウォッチリスト追加要求
    add_to_comparison_requested = Signal(dict)  # 比較追加要求
    add_to_portfolio_requested = Signal(dict)  # ポートフォリオ追加要求

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

        # アクションボタン（選択中の銘柄を追加）
        self.action_button = QPushButton("選択中の銘柄を追加 ▼")
        self.action_button.setEnabled(False)  # 初期状態は無効
        self.action_button.setFixedHeight(28)
        self.action_button.setStyleSheet("""
            QPushButton {
                background-color: #1E90FF;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1C7ED6;
            }
            QPushButton:disabled {
                background-color: #3A3A3A;
                color: #666666;
            }
        """)
        self.action_button.clicked.connect(self.show_action_menu)
        filter_layout.addWidget(self.action_button)

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

        # 選択変更イベント（アクションボタンの有効/無効切り替え用）
        self.table.itemSelectionChanged.connect(self.on_selection_changed)

        # 右クリックメニュー設定
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

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

            # 権利月（数値ソート対応）
            month = stock.get('rights_month', '')
            month_item = NumericTableWidgetItem(
                f"{month}月" if month else '',
                float(month) if month else None
            )
            month_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 2, month_item)

            # 最適日数（数値ソート対応）
            optimal_days = stock.get('optimal_days', '')
            days_item = NumericTableWidgetItem(
                f"{optimal_days}日前" if optimal_days else '-',
                float(optimal_days) if optimal_days else None
            )
            days_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, days_item)

            # 勝率（数値ソート対応）
            win_rate = stock.get('win_rate', 0)
            win_rate_item = NumericTableWidgetItem(
                f"{win_rate*100:.1f}%" if win_rate else '-',
                float(win_rate) if win_rate else None
            )
            win_rate_item.setTextAlignment(Qt.AlignCenter)
            # 勝率が高い場合は緑色
            if win_rate and win_rate >= 0.7:
                win_rate_item.setForeground(QColor(16, 185, 129))  # 緑
            elif win_rate and win_rate >= 0.5:
                win_rate_item.setForeground(QColor(250, 204, 21))  # 黄色
            self.table.setItem(row, 4, win_rate_item)

            # 期待値（数値ソート対応）
            expected_return = stock.get('expected_return', 0)
            return_item = NumericTableWidgetItem(
                f"{expected_return:+.2f}%" if expected_return else '-',
                float(expected_return) if expected_return else None
            )
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
        # コードと権利月を取得
        code_item = self.table.item(row, 0)
        month_item = self.table.item(row, 2)

        if not code_item or not month_item:
            return

        code = code_item.text()
        # 権利月から数値を抽出（例: "3月" → 3）
        month_text = month_item.text()
        try:
            rights_month = int(month_text.replace('月', ''))
        except ValueError:
            self.logger.warning(f"権利月の解析に失敗しました: {month_text}")
            return

        # コードと権利月の両方で該当する銘柄データを探す
        selected_stock = None
        for stock in self.stocks_data:
            if stock.get('code') == code and stock.get('rights_month') == rights_month:
                selected_stock = stock
                break

        if selected_stock:
            self.logger.info(f"銘柄が選択されました: {code} ({rights_month}月) - {selected_stock.get('name')}")
            self.stock_selected.emit(selected_stock)
        else:
            self.logger.warning(f"銘柄データが見つかりません: {code} ({rights_month}月)")

    def get_selected_stock(self) -> Optional[Dict[str, Any]]:
        """選択中の銘柄データを取得"""
        current_row = self.table.currentRow()
        if current_row < 0:
            return None

        code_item = self.table.item(current_row, 0)
        month_item = self.table.item(current_row, 2)

        if not code_item or not month_item:
            return None

        code = code_item.text()
        # 権利月から数値を抽出（例: "3月" → 3）
        month_text = month_item.text()
        try:
            rights_month = int(month_text.replace('月', ''))
        except ValueError:
            return None

        # コードと権利月の両方で該当する銘柄データを探す
        for stock in self.stocks_data:
            if stock.get('code') == code and stock.get('rights_month') == rights_month:
                return stock

        return None

    def on_selection_changed(self):
        """選択変更時の処理（アクションボタンの有効/無効切り替え）"""
        has_selection = len(self.table.selectedItems()) > 0
        self.action_button.setEnabled(has_selection)

    def show_action_menu(self):
        """アクションボタンのドロップダウンメニューを表示"""
        stock_data = self.get_selected_stock()
        if not stock_data:
            return

        # ドロップダウンメニューを作成
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2D2D2D;
                color: #E0E0E0;
                border: 1px solid #404040;
            }
            QMenu::item {
                padding: 8px 24px;
            }
            QMenu::item:selected {
                background-color: #1E90FF;
            }
        """)

        # メニュー項目
        watchlist_action = QAction("⭐ ウォッチリストに追加", self)
        watchlist_action.triggered.connect(lambda: self.add_to_watchlist_requested.emit(stock_data))
        menu.addAction(watchlist_action)

        comparison_action = QAction("📈 銘柄比較に追加", self)
        comparison_action.triggered.connect(lambda: self.add_to_comparison_requested.emit(stock_data))
        menu.addAction(comparison_action)

        portfolio_action = QAction("💼 ポートフォリオに追加", self)
        portfolio_action.triggered.connect(lambda: self.add_to_portfolio_requested.emit(stock_data))
        menu.addAction(portfolio_action)

        # ボタンの下にメニューを表示
        button_pos = self.action_button.mapToGlobal(self.action_button.rect().bottomLeft())
        menu.exec(button_pos)

    def show_context_menu(self, position):
        """右クリックメニューを表示"""
        # 選択された行を取得
        row = self.table.rowAt(position.y())
        if row < 0:
            return

        # 選択された銘柄データを取得
        self.table.selectRow(row)
        stock_data = self.get_selected_stock()
        if not stock_data:
            return

        # コンテキストメニューを作成
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2D2D2D;
                color: #E0E0E0;
                border: 1px solid #404040;
            }
            QMenu::item {
                padding: 6px 20px;
            }
            QMenu::item:selected {
                background-color: #1E90FF;
            }
        """)

        # メニュー項目
        watchlist_action = QAction("⭐ ウォッチリストに追加", self)
        watchlist_action.triggered.connect(lambda: self.add_to_watchlist_requested.emit(stock_data))
        menu.addAction(watchlist_action)

        comparison_action = QAction("📈 銘柄比較に追加", self)
        comparison_action.triggered.connect(lambda: self.add_to_comparison_requested.emit(stock_data))
        menu.addAction(comparison_action)

        portfolio_action = QAction("💼 ポートフォリオに追加", self)
        portfolio_action.triggered.connect(lambda: self.add_to_portfolio_requested.emit(stock_data))
        menu.addAction(portfolio_action)

        # メニューを表示
        menu.exec(self.table.viewport().mapToGlobal(position))
