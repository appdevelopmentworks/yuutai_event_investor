"""
Watchlist Widget
ウォッチリスト表示ウィジェット

Author: Yuutai Event Investor Team
Date: 2024-11-07
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton, QLabel,
    QMessageBox, QMenu
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor, QAction, QCursor
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime


class WatchlistWidget(QWidget):
    """ウォッチリストウィジェット"""

    # シグナル定義
    stock_selected = Signal(dict)  # 銘柄が選択されたときのシグナル
    watchlist_updated = Signal()  # ウォッチリストが更新されたときのシグナル

    def __init__(self, db_manager):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.db = db_manager
        self.watchlist_data = []

        self.init_ui()
        self.load_watchlist()

    def init_ui(self):
        """UIを初期化"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # ========================================
        # タイトルとボタン
        # ========================================
        header_layout = QHBoxLayout()

        # タイトル
        title = QLabel("⭐ ウォッチリスト")
        title_font = QFont("Meiryo", 14, QFont.Bold)
        title.setFont(title_font)
        title.setStyleSheet("color: #E0E0E0;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # 更新ボタン
        refresh_btn = QPushButton("🔄")
        refresh_btn.setFixedSize(32, 32)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #3A3A3A;
                color: #E0E0E0;
                border: 1px solid #404040;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #404040;
            }
        """)
        refresh_btn.clicked.connect(self.load_watchlist)
        refresh_btn.setToolTip("ウォッチリストを再読み込み")
        header_layout.addWidget(refresh_btn)

        # 全削除ボタン
        clear_btn = QPushButton("🗑")
        clear_btn.setFixedSize(32, 32)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #3A3A3A;
                color: #E0E0E0;
                border: 1px solid #404040;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #EF4444;
            }
        """)
        clear_btn.clicked.connect(self.clear_all_watchlist)
        clear_btn.setToolTip("全て削除")
        header_layout.addWidget(clear_btn)

        layout.addLayout(header_layout)

        # ========================================
        # テーブル
        # ========================================
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "コード", "銘柄名", "権利月", "最適日数", "勝率", "追加日"
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
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # 追加日

        # 行選択モード
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)

        # コンテキストメニュー
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

        # クリックイベント
        self.table.cellClicked.connect(self.on_row_clicked)

        layout.addWidget(self.table)

        # 件数表示
        self.count_label = QLabel("0件")
        self.count_label.setStyleSheet("color: #B0B0B0;")
        layout.addWidget(self.count_label)

    def load_watchlist(self):
        """ウォッチリストを読み込み"""
        try:
            self.logger.info("ウォッチリストを読み込み中...")

            # データベースから取得
            watchlist = self.db.get_watchlist()

            if not watchlist:
                self.logger.info("ウォッチリストは空です")
                self.watchlist_data = []
                self.update_table()
                return

            # 銘柄情報を取得
            self.watchlist_data = []
            for item in watchlist:
                code = item['code']
                stock = self.db.get_stock(code)

                if stock:
                    stock_data = {
                        'code': stock['code'],
                        'name': stock['name'],
                        'rights_month': stock['rights_month'],
                        'rights_date': stock.get('rights_date'),
                        'added_at': item['added_at'],
                        'memo': item.get('memo', ''),
                        # プレースホルダー
                        'optimal_days': None,
                        'win_rate': None
                    }
                    self.watchlist_data.append(stock_data)

            self.update_table()
            self.logger.info(f"ウォッチリストを読み込みました: {len(self.watchlist_data)}件")

        except Exception as e:
            self.logger.error(f"ウォッチリスト読み込みエラー: {e}", exc_info=True)

    def update_table(self):
        """テーブルを更新"""
        # テーブルをクリア
        self.table.setRowCount(0)

        if not self.watchlist_data:
            self.count_label.setText("0件")
            return

        # データを追加
        for stock in self.watchlist_data:
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
            if win_rate and win_rate >= 0.7:
                win_rate_item.setForeground(QColor(16, 185, 129))  # 緑
            elif win_rate and win_rate >= 0.5:
                win_rate_item.setForeground(QColor(250, 204, 21))  # 黄色
            self.table.setItem(row, 4, win_rate_item)

            # 追加日
            added_at = stock.get('added_at', '')
            if added_at:
                try:
                    dt = datetime.fromisoformat(added_at)
                    added_str = dt.strftime('%Y-%m-%d')
                except:
                    added_str = added_at
            else:
                added_str = '-'
            added_item = QTableWidgetItem(added_str)
            added_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 5, added_item)

        # 件数を更新
        self.count_label.setText(f"{len(self.watchlist_data)}件")

    def add_to_watchlist(self, code: str, memo: str = ""):
        """
        ウォッチリストに追加

        Args:
            code: 銘柄コード
            memo: メモ
        """
        try:
            if self.db.add_to_watchlist(code, memo):
                self.logger.info(f"ウォッチリストに追加: {code}")
                self.load_watchlist()
                self.watchlist_updated.emit()
                return True
            else:
                self.logger.warning(f"ウォッチリスト追加失敗: {code}")
                return False

        except Exception as e:
            self.logger.error(f"ウォッチリスト追加エラー: {e}")
            return False

    def remove_from_watchlist(self, code: str):
        """
        ウォッチリストから削除

        Args:
            code: 銘柄コード
        """
        try:
            if self.db.remove_from_watchlist(code):
                self.logger.info(f"ウォッチリストから削除: {code}")
                self.load_watchlist()
                self.watchlist_updated.emit()
                return True
            else:
                return False

        except Exception as e:
            self.logger.error(f"ウォッチリスト削除エラー: {e}")
            return False

    def clear_all_watchlist(self):
        """ウォッチリストを全削除"""
        reply = QMessageBox.question(
            self,
            "確認",
            "ウォッチリストを全て削除してもよろしいですか？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                # 全アイテムを削除
                for stock in self.watchlist_data:
                    self.db.remove_from_watchlist(stock['code'])

                self.load_watchlist()
                self.watchlist_updated.emit()
                self.logger.info("ウォッチリストを全削除しました")

            except Exception as e:
                self.logger.error(f"ウォッチリスト全削除エラー: {e}")
                QMessageBox.critical(self, "エラー", f"削除に失敗しました: {str(e)}")

    def show_context_menu(self, position):
        """コンテキストメニューを表示"""
        # 選択行を取得
        row = self.table.rowAt(position.y())
        if row < 0:
            return

        # メニュー作成
        menu = QMenu(self)

        # 削除アクション
        remove_action = QAction("削除", self)
        remove_action.triggered.connect(lambda: self.remove_selected())
        menu.addAction(remove_action)

        # メニュー表示
        menu.exec(QCursor.pos())

    def remove_selected(self):
        """選択された銘柄を削除"""
        current_row = self.table.currentRow()
        if current_row < 0:
            return

        code_item = self.table.item(current_row, 0)
        if not code_item:
            return

        code = code_item.text()
        name_item = self.table.item(current_row, 1)
        name = name_item.text() if name_item else code

        reply = QMessageBox.question(
            self,
            "確認",
            f"{name}({code})をウォッチリストから削除しますか？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.remove_from_watchlist(code)

    def on_row_clicked(self, row: int, column: int):
        """行クリック時の処理"""
        # コードを取得
        code_item = self.table.item(row, 0)
        if not code_item:
            return

        code = code_item.text()

        # 該当する銘柄データを探す
        selected_stock = None
        for stock in self.watchlist_data:
            if stock.get('code') == code:
                selected_stock = stock
                break

        if selected_stock:
            self.logger.info(f"ウォッチリスト銘柄が選択されました: {code}")
            self.stock_selected.emit(selected_stock)

    def is_in_watchlist(self, code: str) -> bool:
        """
        銘柄がウォッチリストに含まれているかチェック

        Args:
            code: 銘柄コード

        Returns:
            bool: ウォッチリストに含まれている場合True
        """
        return any(stock['code'] == code for stock in self.watchlist_data)
