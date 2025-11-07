"""
Settings Dialog
設定ダイアログ

Author: Yuutai Event Investor Team
Date: 2024-11-07
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QWidget, QLabel, QLineEdit, QSpinBox, QCheckBox,
    QPushButton, QGroupBox, QComboBox, QFormLayout,
    QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
import logging
import json
from pathlib import Path
from typing import Dict, Any


class SettingsDialog(QDialog):
    """設定ダイアログ"""

    # シグナル定義
    settings_changed = Signal(dict)  # 設定が変更されたときのシグナル

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.settings = self.load_settings()

        self.setWindowTitle("設定")
        self.setMinimumSize(600, 500)

        self.init_ui()

    def init_ui(self):
        """UIを初期化"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # タブウィジェット
        tab_widget = QTabWidget()

        # 各タブを追加
        tab_widget.addTab(self.create_general_tab(), "一般")
        tab_widget.addTab(self.create_data_tab(), "データ")
        tab_widget.addTab(self.create_notification_tab(), "通知")
        tab_widget.addTab(self.create_display_tab(), "表示")

        layout.addWidget(tab_widget)

        # ボタン
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("キャンセル")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.save_settings)
        save_btn.setDefault(True)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

        # スタイル適用
        self.setStyleSheet("""
            QDialog {
                background-color: #1E1E1E;
            }
            QLabel {
                color: #E0E0E0;
            }
            QLineEdit, QSpinBox, QComboBox {
                background-color: #2D2D2D;
                color: #E0E0E0;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 5px;
            }
            QCheckBox {
                color: #E0E0E0;
            }
            QPushButton {
                background-color: #3A3A3A;
                color: #E0E0E0;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #404040;
            }
            QPushButton:default {
                background-color: #1E90FF;
            }
            QGroupBox {
                color: #E0E0E0;
                border: 1px solid #404040;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QTabWidget::pane {
                border: 1px solid #404040;
                background-color: #1E1E1E;
            }
            QTabBar::tab {
                background-color: #2D2D2D;
                color: #B0B0B0;
                padding: 8px 16px;
                border: 1px solid #404040;
            }
            QTabBar::tab:selected {
                background-color: #1E1E1E;
                color: #1E90FF;
                border-bottom: 2px solid #1E90FF;
            }
        """)

    def create_general_tab(self) -> QWidget:
        """一般タブを作成"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)

        # データベースパス
        db_group = QGroupBox("データベース")
        db_layout = QFormLayout()

        self.db_path_edit = QLineEdit()
        self.db_path_edit.setText(self.settings.get('database_path', 'data/yuutai.db'))
        db_layout.addRow("データベースパス:", self.db_path_edit)

        db_group.setLayout(db_layout)
        layout.addWidget(db_group)

        # 起動時の動作
        startup_group = QGroupBox("起動時の動作")
        startup_layout = QVBoxLayout()

        self.auto_update_check = QCheckBox("起動時に自動でデータを更新")
        self.auto_update_check.setChecked(self.settings.get('auto_update_on_startup', False))
        startup_layout.addWidget(self.auto_update_check)

        self.show_watchlist_check = QCheckBox("起動時にウォッチリストを表示")
        self.show_watchlist_check.setChecked(self.settings.get('show_watchlist_on_startup', True))
        startup_layout.addWidget(self.show_watchlist_check)

        startup_group.setLayout(startup_layout)
        layout.addWidget(startup_group)

        layout.addStretch()

        return widget

    def create_data_tab(self) -> QWidget:
        """データタブを作成"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)

        # データ更新設定
        update_group = QGroupBox("データ更新")
        update_layout = QFormLayout()

        self.update_interval_spin = QSpinBox()
        self.update_interval_spin.setRange(1, 30)
        self.update_interval_spin.setValue(self.settings.get('update_interval_days', 7))
        self.update_interval_spin.setSuffix(" 日")
        update_layout.addRow("自動更新間隔:", self.update_interval_spin)

        self.cache_days_spin = QSpinBox()
        self.cache_days_spin.setRange(1, 90)
        self.cache_days_spin.setValue(self.settings.get('cache_expiry_days', 7))
        self.cache_days_spin.setSuffix(" 日")
        update_layout.addRow("キャッシュ有効期限:", self.cache_days_spin)

        update_group.setLayout(update_layout)
        layout.addWidget(update_group)

        # バックテスト設定
        backtest_group = QGroupBox("バックテスト")
        backtest_layout = QFormLayout()

        # データ取得期間
        self.data_period_combo = QComboBox()
        self.data_period_combo.addItems(["1年", "3年", "5年", "10年", "15年", "20年", "すべて"])
        period_map = {'1y': 0, '3y': 1, '5y': 2, '10y': 3, '15y': 4, '20y': 5, 'max': 6}
        current_period = self.settings.get('data_period', '10y')
        self.data_period_combo.setCurrentIndex(period_map.get(current_period, 3))
        backtest_layout.addRow("データ取得期間:", self.data_period_combo)

        self.max_days_spin = QSpinBox()
        self.max_days_spin.setRange(30, 240)
        self.max_days_spin.setValue(self.settings.get('max_days_before', 120))
        self.max_days_spin.setSuffix(" 日")
        backtest_layout.addRow("最大検証期間:", self.max_days_spin)

        self.min_trades_spin = QSpinBox()
        self.min_trades_spin.setRange(1, 10)
        self.min_trades_spin.setValue(self.settings.get('min_trade_count', 3))
        self.min_trades_spin.setSuffix(" 回")
        backtest_layout.addRow("最小トレード数:", self.min_trades_spin)

        backtest_group.setLayout(backtest_layout)
        layout.addWidget(backtest_group)

        layout.addStretch()

        return widget

    def create_notification_tab(self) -> QWidget:
        """通知タブを作成"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)

        # 通知設定
        notif_group = QGroupBox("通知設定")
        notif_layout = QVBoxLayout()

        self.enable_notifications_check = QCheckBox("通知を有効にする")
        self.enable_notifications_check.setChecked(self.settings.get('enable_notifications', True))
        notif_layout.addWidget(self.enable_notifications_check)

        days_layout = QFormLayout()
        self.notify_days_spin = QSpinBox()
        self.notify_days_spin.setRange(1, 30)
        self.notify_days_spin.setValue(self.settings.get('notify_days_before', 7))
        self.notify_days_spin.setSuffix(" 日前")
        days_layout.addRow("最適買入日の:", self.notify_days_spin)

        notif_layout.addLayout(days_layout)

        notif_group.setLayout(notif_layout)
        layout.addWidget(notif_group)

        layout.addStretch()

        return widget

    def create_display_tab(self) -> QWidget:
        """表示タブを作成"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)

        # 表示設定
        display_group = QGroupBox("表示設定")
        display_layout = QFormLayout()

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["ダーク", "ライト", "自動"])
        current_theme = self.settings.get('theme', 'dark')
        theme_map = {'dark': 0, 'light': 1, 'auto': 2}
        self.theme_combo.setCurrentIndex(theme_map.get(current_theme, 0))
        display_layout.addRow("テーマ:", self.theme_combo)

        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 20)
        self.font_size_spin.setValue(self.settings.get('font_size', 10))
        self.font_size_spin.setSuffix(" pt")
        display_layout.addRow("フォントサイズ:", self.font_size_spin)

        display_group.setLayout(display_layout)
        layout.addWidget(display_group)

        # チャート設定
        chart_group = QGroupBox("チャート設定")
        chart_layout = QVBoxLayout()

        self.show_grid_check = QCheckBox("グリッド線を表示")
        self.show_grid_check.setChecked(self.settings.get('show_chart_grid', True))
        chart_layout.addWidget(self.show_grid_check)

        self.show_legend_check = QCheckBox("凡例を表示")
        self.show_legend_check.setChecked(self.settings.get('show_chart_legend', True))
        chart_layout.addWidget(self.show_legend_check)

        chart_group.setLayout(chart_layout)
        layout.addWidget(chart_group)

        layout.addStretch()

        return widget

    def load_settings(self) -> Dict[str, Any]:
        """設定を読み込む"""
        try:
            config_path = Path(__file__).parent.parent.parent.parent / "config" / "settings.json"

            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # デフォルト設定
                return self.get_default_settings()

        except Exception as e:
            self.logger.error(f"設定読み込みエラー: {e}")
            return self.get_default_settings()

    def get_default_settings(self) -> Dict[str, Any]:
        """デフォルト設定を取得"""
        return {
            'database_path': 'data/yuutai.db',
            'auto_update_on_startup': False,
            'show_watchlist_on_startup': True,
            'update_interval_days': 7,
            'cache_expiry_days': 7,
            'data_period': '10y',
            'max_days_before': 120,
            'min_trade_count': 3,
            'enable_notifications': True,
            'notify_days_before': 7,
            'theme': 'dark',
            'font_size': 10,
            'show_chart_grid': True,
            'show_chart_legend': True
        }

    def save_settings(self):
        """設定を保存"""
        try:
            # UIから設定を取得
            period_values = ['1y', '3y', '5y', '10y', '15y', '20y', 'max']
            new_settings = {
                'database_path': self.db_path_edit.text(),
                'auto_update_on_startup': self.auto_update_check.isChecked(),
                'show_watchlist_on_startup': self.show_watchlist_check.isChecked(),
                'update_interval_days': self.update_interval_spin.value(),
                'cache_expiry_days': self.cache_days_spin.value(),
                'data_period': period_values[self.data_period_combo.currentIndex()],
                'max_days_before': self.max_days_spin.value(),
                'min_trade_count': self.min_trades_spin.value(),
                'enable_notifications': self.enable_notifications_check.isChecked(),
                'notify_days_before': self.notify_days_spin.value(),
                'theme': ['dark', 'light', 'auto'][self.theme_combo.currentIndex()],
                'font_size': self.font_size_spin.value(),
                'show_chart_grid': self.show_grid_check.isChecked(),
                'show_chart_legend': self.show_legend_check.isChecked()
            }

            # 設定ファイルに保存
            config_path = Path(__file__).parent.parent.parent.parent / "config" / "settings.json"
            config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(new_settings, f, ensure_ascii=False, indent=2)

            self.settings = new_settings
            self.settings_changed.emit(new_settings)

            self.logger.info("設定を保存しました")
            QMessageBox.information(self, "成功", "設定を保存しました")

            self.accept()

        except Exception as e:
            self.logger.error(f"設定保存エラー: {e}", exc_info=True)
            QMessageBox.critical(self, "エラー", f"設定の保存に失敗しました:\n{str(e)}")
