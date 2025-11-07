"""
Filter Panel Widget
フィルターパネルウィジェット

Author: Yuutai Event Investor Team
Date: 2024-11-07
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QSlider, QSpinBox, QPushButton, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
import logging
from typing import Dict, Any


class FilterPanel(QWidget):
    """フィルターパネル"""

    # シグナル定義
    filter_changed = Signal(dict)  # フィルター条件が変更されたときのシグナル

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.init_ui()

    def init_ui(self):
        """UIを初期化"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(20)

        # ========================================
        # タイトル
        # ========================================
        title = QLabel("🔍 フィルター")
        title.setFont(QFont("Meiryo", 13, QFont.Bold))
        title.setStyleSheet("color: #E0E0E0;")
        layout.addWidget(title)

        # 区切り線
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #404040;")
        layout.addWidget(line)

        # ========================================
        # 権利確定月フィルター
        # ========================================
        month_section = self._create_section_title("権利確定月")
        layout.addWidget(month_section)

        self.month_filter = QComboBox()
        self.month_filter.addItems([
            "全て", "3月優待", "6月優待", "9月優待", "12月優待",
            "1月", "2月", "4月", "5月", "7月", "8月", "10月", "11月"
        ])
        self.month_filter.setStyleSheet(self._get_combobox_style())
        self.month_filter.currentIndexChanged.connect(self._on_filter_changed)
        layout.addWidget(self.month_filter)

        # ========================================
        # 勝率フィルター
        # ========================================
        win_rate_section = self._create_section_title("最低勝率")
        layout.addWidget(win_rate_section)

        win_rate_layout = QHBoxLayout()
        win_rate_layout.setSpacing(10)

        self.win_rate_slider = QSlider(Qt.Horizontal)
        self.win_rate_slider.setMinimum(0)
        self.win_rate_slider.setMaximum(100)
        self.win_rate_slider.setValue(50)
        self.win_rate_slider.setTickPosition(QSlider.TicksBelow)
        self.win_rate_slider.setTickInterval(10)
        self.win_rate_slider.setStyleSheet(self._get_slider_style())
        self.win_rate_slider.valueChanged.connect(self._update_win_rate_label)
        self.win_rate_slider.valueChanged.connect(self._on_filter_changed)
        win_rate_layout.addWidget(self.win_rate_slider)

        self.win_rate_value_label = QLabel("50%")
        self.win_rate_value_label.setFont(QFont("Meiryo", 11, QFont.Bold))
        self.win_rate_value_label.setStyleSheet("color: #1E90FF;")
        self.win_rate_value_label.setFixedWidth(50)
        self.win_rate_value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        win_rate_layout.addWidget(self.win_rate_value_label)

        layout.addLayout(win_rate_layout)

        # ========================================
        # 期待リターンフィルター
        # ========================================
        return_section = self._create_section_title("最低期待リターン")
        layout.addWidget(return_section)

        return_layout = QHBoxLayout()
        return_layout.setSpacing(10)

        self.return_slider = QSlider(Qt.Horizontal)
        self.return_slider.setMinimum(-100)
        self.return_slider.setMaximum(200)
        self.return_slider.setValue(0)
        self.return_slider.setTickPosition(QSlider.TicksBelow)
        self.return_slider.setTickInterval(50)
        self.return_slider.setStyleSheet(self._get_slider_style())
        self.return_slider.valueChanged.connect(self._update_return_label)
        self.return_slider.valueChanged.connect(self._on_filter_changed)
        return_layout.addWidget(self.return_slider)

        self.return_value_label = QLabel("0.0%")
        self.return_value_label.setFont(QFont("Meiryo", 11, QFont.Bold))
        self.return_value_label.setStyleSheet("color: #1E90FF;")
        self.return_value_label.setFixedWidth(60)
        self.return_value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        return_layout.addWidget(self.return_value_label)

        layout.addLayout(return_layout)

        # ========================================
        # 投資金額フィルター
        # ========================================
        amount_section = self._create_section_title("上限投資金額")
        layout.addWidget(amount_section)

        amount_layout = QHBoxLayout()
        amount_layout.setSpacing(10)

        self.amount_spinbox = QSpinBox()
        self.amount_spinbox.setMinimum(10)
        self.amount_spinbox.setMaximum(10000)
        self.amount_spinbox.setValue(1000)
        self.amount_spinbox.setSingleStep(10)
        self.amount_spinbox.setSuffix(" 万円")
        self.amount_spinbox.setStyleSheet(self._get_spinbox_style())
        self.amount_spinbox.valueChanged.connect(self._on_filter_changed)
        amount_layout.addWidget(self.amount_spinbox)

        layout.addLayout(amount_layout)

        # ========================================
        # 並び替え
        # ========================================
        sort_section = self._create_section_title("並び替え")
        layout.addWidget(sort_section)

        self.sort_combo = QComboBox()
        self.sort_combo.addItems([
            "期待リターン（高い順）",
            "期待リターン（低い順）",
            "勝率（高い順）",
            "勝率（低い順）",
            "コード順",
            "権利確定日（近い順）"
        ])
        self.sort_combo.setStyleSheet(self._get_combobox_style())
        self.sort_combo.currentIndexChanged.connect(self._on_filter_changed)
        layout.addWidget(self.sort_combo)

        # ========================================
        # リセットボタン
        # ========================================
        reset_btn = QPushButton("🔄 フィルターをリセット")
        reset_btn.setFixedHeight(35)
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #3A3A3A;
                color: #E0E0E0;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 5px 15px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #404040;
                border: 1px solid #4682B4;
            }
            QPushButton:pressed {
                background-color: #2D2D2D;
            }
        """)
        reset_btn.clicked.connect(self.reset_filters)
        layout.addWidget(reset_btn)

        layout.addStretch()

    def _create_section_title(self, text: str) -> QLabel:
        """セクションタイトルを作成"""
        label = QLabel(text)
        label.setFont(QFont("Meiryo", 10, QFont.Bold))
        label.setStyleSheet("color: #B0B0B0;")
        return label

    def _get_combobox_style(self) -> str:
        """コンボボックスのスタイルを取得"""
        return """
            QComboBox {
                background-color: #2D2D2D;
                color: #E0E0E0;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 5px 10px;
                min-height: 25px;
            }
            QComboBox:hover {
                border: 1px solid #4682B4;
            }
            QComboBox:focus {
                border: 1px solid #1E90FF;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 10px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid #B0B0B0;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: #2D2D2D;
                color: #E0E0E0;
                selection-background-color: #1E90FF;
                selection-color: white;
                border: 1px solid #404040;
            }
        """

    def _get_slider_style(self) -> str:
        """スライダーのスタイルを取得"""
        return """
            QSlider::groove:horizontal {
                background: #2D2D2D;
                height: 6px;
                border-radius: 3px;
                border: 1px solid #404040;
            }
            QSlider::handle:horizontal {
                background: #1E90FF;
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: #4682B4;
            }
            QSlider::sub-page:horizontal {
                background: #1E90FF;
                border-radius: 3px;
            }
        """

    def _get_spinbox_style(self) -> str:
        """スピンボックスのスタイルを取得"""
        return """
            QSpinBox {
                background-color: #2D2D2D;
                color: #E0E0E0;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 5px 10px;
                min-height: 25px;
            }
            QSpinBox:hover {
                border: 1px solid #4682B4;
            }
            QSpinBox:focus {
                border: 1px solid #1E90FF;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #3A3A3A;
                border: none;
                width: 16px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #404040;
            }
            QSpinBox::up-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-bottom: 6px solid #B0B0B0;
            }
            QSpinBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid #B0B0B0;
            }
        """

    def _update_win_rate_label(self, value: int):
        """勝率ラベルを更新"""
        self.win_rate_value_label.setText(f"{value}%")

    def _update_return_label(self, value: int):
        """期待リターンラベルを更新"""
        value_float = value / 10.0
        self.return_value_label.setText(f"{value_float:+.1f}%")

    def _on_filter_changed(self):
        """フィルター条件が変更されたときの処理"""
        filters = self.get_filters()
        self.logger.debug(f"フィルター条件が変更されました: {filters}")
        self.filter_changed.emit(filters)

    def get_filters(self) -> Dict[str, Any]:
        """
        現在のフィルター条件を取得

        Returns:
            フィルター条件の辞書
        """
        # 権利確定月
        month_index = self.month_filter.currentIndex()
        month_map = {
            0: None,  # 全て
            1: 3,     # 3月優待
            2: 6,     # 6月優待
            3: 9,     # 9月優待
            4: 12,    # 12月優待
            5: 1, 6: 2, 7: 4, 8: 5, 9: 7, 10: 8, 11: 10, 12: 11
        }
        rights_month = month_map.get(month_index)

        # 勝率（パーセントを小数に変換）
        min_win_rate = self.win_rate_slider.value() / 100.0

        # 期待リターン（10倍されているので元に戻す）
        min_expected_return = self.return_slider.value() / 10.0

        # 投資金額（万円から円に変換）
        max_amount = self.amount_spinbox.value() * 10000

        # 並び替え
        sort_map = {
            0: ('expected_return', 'desc'),
            1: ('expected_return', 'asc'),
            2: ('win_rate', 'desc'),
            3: ('win_rate', 'asc'),
            4: ('code', 'asc'),
            5: ('rights_date', 'asc')
        }
        sort_by, sort_order = sort_map.get(self.sort_combo.currentIndex(), ('expected_return', 'desc'))

        return {
            'rights_month': rights_month,
            'min_win_rate': min_win_rate,
            'min_expected_return': min_expected_return,
            'max_amount': max_amount,
            'sort_by': sort_by,
            'sort_order': sort_order
        }

    def reset_filters(self):
        """フィルターをリセット"""
        self.logger.info("フィルターをリセット")

        # 各フィルターをデフォルト値に戻す
        self.month_filter.setCurrentIndex(0)
        self.win_rate_slider.setValue(50)
        self.return_slider.setValue(0)
        self.amount_spinbox.setValue(1000)
        self.sort_combo.setCurrentIndex(0)

        # フィルター変更シグナルを発行
        self._on_filter_changed()

    def set_filters(self, filters: Dict[str, Any]):
        """
        フィルター条件を設定

        Args:
            filters: 設定するフィルター条件
        """
        # 権利確定月
        rights_month = filters.get('rights_month')
        if rights_month is not None:
            month_reverse_map = {
                None: 0, 3: 1, 6: 2, 9: 3, 12: 4,
                1: 5, 2: 6, 4: 7, 5: 8, 7: 9, 8: 10, 10: 11, 11: 12
            }
            month_index = month_reverse_map.get(rights_month, 0)
            self.month_filter.setCurrentIndex(month_index)

        # 勝率
        if 'min_win_rate' in filters:
            win_rate_percent = int(filters['min_win_rate'] * 100)
            self.win_rate_slider.setValue(win_rate_percent)

        # 期待リターン
        if 'min_expected_return' in filters:
            return_value = int(filters['min_expected_return'] * 10)
            self.return_slider.setValue(return_value)

        # 投資金額
        if 'max_amount' in filters:
            amount_man = filters['max_amount'] // 10000
            self.amount_spinbox.setValue(amount_man)

        # 並び替え
        if 'sort_by' in filters and 'sort_order' in filters:
            sort_reverse_map = {
                ('expected_return', 'desc'): 0,
                ('expected_return', 'asc'): 1,
                ('win_rate', 'desc'): 2,
                ('win_rate', 'asc'): 3,
                ('code', 'asc'): 4,
                ('rights_date', 'asc'): 5
            }
            sort_index = sort_reverse_map.get((filters['sort_by'], filters['sort_order']), 0)
            self.sort_combo.setCurrentIndex(sort_index)
