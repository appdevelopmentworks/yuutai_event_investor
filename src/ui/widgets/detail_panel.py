"""
Detail Panel Widget
詳細分析パネル

Author: Yuutai Event Investor Team
Date: 2024-11-07
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QGridLayout, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
import logging
from typing import Dict, Optional
from .chart_widget import ChartWidget
from .trade_history_widget import TradeHistoryWidget
from .risk_metrics_widget import RiskMetricsWidget


class StockInfoCard(QWidget):
    """銘柄情報カード"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """UIを初期化"""
        self.setFixedHeight(220)
        self.setStyleSheet("""
            QWidget {
                background-color: #2D2D2D;
                border-radius: 8px;
                border: 1px solid #404040;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)

        # タイトル行（コンテナでマージンを追加）
        title_container = QWidget()
        title_container.setStyleSheet("border: none;")
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(12, 0, 12, 0)
        title_layout.setSpacing(10)

        self.name_label = QLabel("銘柄を選択してください")
        self.name_label.setFont(QFont("Meiryo", 14, QFont.Bold))
        self.name_label.setStyleSheet("color: #E0E0E0; border: none;")
        title_layout.addWidget(self.name_label)

        title_layout.addStretch()

        self.code_label = QLabel("")
        self.code_label.setFont(QFont("Meiryo", 11))
        self.code_label.setStyleSheet("""
            color: #B0B0B0;
            border: none;
            background-color: #3A3A3A;
            border-radius: 12px;
            padding: 4px 12px;
        """)
        title_layout.addWidget(self.code_label)

        layout.addWidget(title_container)

        # 統計情報グリッド
        self.stats_grid = QGridLayout()
        self.stats_grid.setSpacing(15)

        # ラベルを作成
        self.optimal_days_label = self._create_stat_label("最適買入日", "-", "#1E90FF")
        self.win_rate_label = self._create_stat_label("勝率", "-", "#10B981")
        self.expected_return_label = self._create_stat_label("期待リターン", "-", "#FACC15")
        self.avg_win_label = self._create_stat_label("平均勝ち", "-", "#10B981")
        self.avg_lose_label = self._create_stat_label("平均負け", "-", "#EF4444")
        self.total_trades_label = self._create_stat_label("総トレード", "-", "#B0B0B0")

        # グリッドに配置（3x2）
        self.stats_grid.addWidget(self.optimal_days_label['container'], 0, 0)
        self.stats_grid.addWidget(self.win_rate_label['container'], 0, 1)
        self.stats_grid.addWidget(self.expected_return_label['container'], 1, 0)
        self.stats_grid.addWidget(self.total_trades_label['container'], 1, 1)
        self.stats_grid.addWidget(self.avg_win_label['container'], 2, 0)
        self.stats_grid.addWidget(self.avg_lose_label['container'], 2, 1)

        layout.addLayout(self.stats_grid)

    def _create_stat_label(self, title: str, value: str, color: str) -> Dict:
        """統計ラベルを作成"""
        container = QWidget()
        container.setStyleSheet("border: none;")
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(12, 6, 12, 6)
        container_layout.setSpacing(10)

        # タイトル
        title_label = QLabel(title)
        title_label.setFont(QFont("Meiryo", 10))
        title_label.setStyleSheet("color: #B0B0B0; border: none;")
        container_layout.addWidget(title_label)

        container_layout.addStretch()

        # 値
        value_label = QLabel(value)
        value_label.setFont(QFont("Meiryo", 10, QFont.Bold))
        value_label.setStyleSheet(f"color: {color}; border: none;")
        container_layout.addWidget(value_label)

        return {
            'container': container,
            'title': title_label,
            'value': value_label
        }

    def update_stock_info(self, stock_data: Dict, result_data: Optional[Dict] = None):
        """
        銘柄情報を更新

        Args:
            stock_data: 銘柄データ
            result_data: バックテスト結果データ
        """
        # 銘柄名とコード
        name = stock_data.get('name', '不明')
        code = stock_data.get('code', '')
        self.name_label.setText(name)
        self.code_label.setText(f"({code})" if code else "")

        # 結果データがある場合は統計情報を更新
        if result_data:
            # 最適買入日
            optimal_days = result_data.get('optimal_days', 0)
            self.optimal_days_label['value'].setText(f"{optimal_days}日前")

            # 勝率
            win_rate = result_data.get('win_rate', 0)
            self.win_rate_label['value'].setText(f"{win_rate*100:.1f}%")
            # 勝率によって色を変更
            if win_rate >= 0.7:
                self.win_rate_label['value'].setStyleSheet("color: #10B981; border: none; font-weight: bold;")
            elif win_rate >= 0.5:
                self.win_rate_label['value'].setStyleSheet("color: #FACC15; border: none; font-weight: bold;")
            else:
                self.win_rate_label['value'].setStyleSheet("color: #EF4444; border: none; font-weight: bold;")

            # 期待リターン
            expected_return = result_data.get('expected_return', 0)
            self.expected_return_label['value'].setText(f"{expected_return:+.2f}%")
            # プラスマイナスで色を変更
            color = "#10B981" if expected_return > 0 else "#EF4444" if expected_return < 0 else "#B0B0B0"
            self.expected_return_label['value'].setStyleSheet(f"color: {color}; border: none; font-weight: bold;")

            # 総トレード数
            total_trades = result_data.get('total_count', 0)
            self.total_trades_label['value'].setText(f"{total_trades}回")
            self.total_trades_label['value'].setStyleSheet("color: #B0B0B0; border: none; font-weight: bold;")

            # 平均勝ちリターン
            avg_win = result_data.get('avg_win_return', 0)
            self.avg_win_label['value'].setText(f"{avg_win:+.2f}%")
            self.avg_win_label['value'].setStyleSheet("color: #10B981; border: none; font-weight: bold;")

            # 平均負けリターン
            avg_lose = result_data.get('avg_lose_return', 0)
            self.avg_lose_label['value'].setText(f"{avg_lose:+.2f}%")
            self.avg_lose_label['value'].setStyleSheet("color: #EF4444; border: none; font-weight: bold;")
        else:
            # デフォルト値
            self.optimal_days_label['value'].setText("-")
            self.win_rate_label['value'].setText("-")
            self.expected_return_label['value'].setText("-")
            self.total_trades_label['value'].setText("-")
            self.avg_win_label['value'].setText("-")
            self.avg_lose_label['value'].setText("-")

    def clear(self):
        """カードをクリア"""
        self.name_label.setText("銘柄を選択してください")
        self.code_label.setText("")
        self.optimal_days_label['value'].setText("-")
        self.win_rate_label['value'].setText("-")
        self.expected_return_label['value'].setText("-")
        self.total_trades_label['value'].setText("-")
        self.avg_win_label['value'].setText("-")
        self.avg_lose_label['value'].setText("-")


class DetailStatsTable(QWidget):
    """詳細統計テーブル"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """UIを初期化"""
        self.setStyleSheet("""
            QWidget {
                background-color: #2D2D2D;
                border-radius: 8px;
                border: 1px solid #404040;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)

        # タイトル（データ行と同じスタイル）
        title_container = QWidget()
        title_container.setStyleSheet("border: none;")
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(12, 6, 12, 6)
        title_layout.setSpacing(0)

        title = QLabel("詳細統計")
        title.setFont(QFont("Meiryo", 11, QFont.Bold))
        title.setStyleSheet("color: #E0E0E0; border: none;")
        title_layout.addWidget(title)
        title_layout.addStretch()

        layout.addWidget(title_container)

        # 統計情報グリッド
        self.stats_layout = QVBoxLayout()
        self.stats_layout.setSpacing(8)

        # 各統計項目
        self.total_trades_label = self._create_stat_row("総トレード数", "-")
        self.win_count_label = self._create_stat_row("勝ちトレード数", "-")
        self.lose_count_label = self._create_stat_row("負けトレード数", "-")
        self.max_return_label = self._create_stat_row("最大リターン", "-")
        self.max_loss_label = self._create_stat_row("最大損失", "-")
        self.avg_win_label = self._create_stat_row("平均勝ちリターン", "-")
        self.avg_loss_label = self._create_stat_row("平均負けリターン", "-")

        layout.addLayout(self.stats_layout)

    def _create_stat_row(self, label: str, value: str) -> Dict:
        """統計行を作成"""
        row = QWidget()
        row.setStyleSheet("border: none;")
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(12, 6, 12, 6)
        row_layout.setSpacing(10)

        # ラベル
        label_widget = QLabel(label)
        label_widget.setFont(QFont("Meiryo", 10))
        label_widget.setStyleSheet("color: #B0B0B0; border: none;")
        row_layout.addWidget(label_widget)

        row_layout.addStretch()

        # 値
        value_widget = QLabel(value)
        value_widget.setFont(QFont("Meiryo", 10, QFont.Bold))
        value_widget.setStyleSheet("color: #E0E0E0; border: none;")
        row_layout.addWidget(value_widget)

        self.stats_layout.addWidget(row)

        return {
            'container': row,
            'label': label_widget,
            'value': value_widget
        }

    def update_stats(self, result_data: Dict):
        """
        統計情報を更新

        Args:
            result_data: バックテスト結果データ
        """
        # 総トレード数
        total_trades = result_data.get('total_count', 0)
        self.total_trades_label['value'].setText(f"{total_trades}回")

        # 勝ちトレード数
        win_count = result_data.get('win_count', 0)
        self.win_count_label['value'].setText(f"{win_count}回")
        self.win_count_label['value'].setStyleSheet("color: #10B981; border: none; font-weight: bold;")

        # 負けトレード数
        lose_count = result_data.get('lose_count', 0)
        self.lose_count_label['value'].setText(f"{lose_count}回")
        self.lose_count_label['value'].setStyleSheet("color: #EF4444; border: none; font-weight: bold;")

        # 最大リターン
        max_return = result_data.get('max_win_return', 0)
        self.max_return_label['value'].setText(f"{max_return:+.2f}%")
        self.max_return_label['value'].setStyleSheet("color: #10B981; border: none; font-weight: bold;")

        # 最大損失
        max_loss = result_data.get('max_lose_return', 0)
        self.max_loss_label['value'].setText(f"{max_loss:+.2f}%")
        self.max_loss_label['value'].setStyleSheet("color: #EF4444; border: none; font-weight: bold;")

        # 平均勝ちリターン
        avg_win = result_data.get('avg_win_return', 0)
        self.avg_win_label['value'].setText(f"{avg_win:+.2f}%")
        self.avg_win_label['value'].setStyleSheet("color: #10B981; border: none; font-weight: bold;")

        # 平均負けリターン
        avg_loss = result_data.get('avg_lose_return', 0)
        self.avg_loss_label['value'].setText(f"{avg_loss:+.2f}%")
        self.avg_loss_label['value'].setStyleSheet("color: #EF4444; border: none; font-weight: bold;")

    def clear(self):
        """テーブルをクリア"""
        for stat_label in [self.total_trades_label, self.win_count_label, self.lose_count_label,
                           self.max_return_label, self.max_loss_label, self.avg_win_label, self.avg_loss_label]:
            stat_label['value'].setText("-")
            stat_label['value'].setStyleSheet("color: #E0E0E0; border: none; font-weight: bold;")


class DetailPanel(QWidget):
    """詳細分析パネル"""

    # シグナル定義
    analysis_requested = Signal(str)  # 分析が要求されたときのシグナル（ティッカーコード）
    backtest_completed = Signal(str, int)  # バックテスト完了シグナル（銘柄コード, 権利月）

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.current_stock = None
        self.current_result = None

        self.init_ui()

    def init_ui(self):
        """UIを初期化"""
        # スクロールエリアを作成
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #1E1E1E;
            }
            QScrollBar:vertical {
                background-color: #2D2D2D;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #404040;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #4A4A4A;
            }
        """)

        # スクロール可能なコンテンツウィジェット
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(15)

        # ========================================
        # タイトル
        # ========================================
        title = QLabel("📈 詳細分析")
        title.setFont(QFont("Meiryo", 14, QFont.Bold))
        title.setStyleSheet("color: #1E90FF;")
        content_layout.addWidget(title)

        # ========================================
        # 銘柄情報カード
        # ========================================
        self.info_card = StockInfoCard()
        content_layout.addWidget(self.info_card)

        # ========================================
        # チャート
        # ========================================
        self.chart_widget = ChartWidget()
        self.chart_widget.setMinimumHeight(400)
        content_layout.addWidget(self.chart_widget)

        # ========================================
        # 詳細統計テーブル
        # ========================================
        self.stats_table = DetailStatsTable()
        content_layout.addWidget(self.stats_table)

        # ========================================
        # トレード履歴ウィジェット
        # ========================================
        self.trade_history_widget = TradeHistoryWidget()
        self.trade_history_widget.setMinimumHeight(400)
        content_layout.addWidget(self.trade_history_widget)

        # ========================================
        # リスク指標ウィジェット
        # ========================================
        self.risk_metrics_widget = RiskMetricsWidget()
        self.risk_metrics_widget.setMinimumHeight(400)
        content_layout.addWidget(self.risk_metrics_widget)

        content_layout.addStretch()

        scroll_area.setWidget(content_widget)

        # メインレイアウト
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)

    def update_stock_detail(self, stock_data: Dict, result_data: Optional[Dict] = None, emit_completed: bool = False):
        """
        銘柄詳細を更新

        Args:
            stock_data: 銘柄データ
            result_data: バックテスト結果データ
            emit_completed: バックテスト完了シグナルを発火するか（新しいバックテスト完了時のみTrue）
        """
        self.current_stock = stock_data
        self.current_result = result_data

        self.logger.info(f"銘柄詳細を更新: {stock_data.get('code')} - {stock_data.get('name')}")

        # 銘柄情報カードを更新
        self.info_card.update_stock_info(stock_data, result_data)

        # 結果データがある場合はチャートと統計を更新
        if result_data:
            self.chart_widget.plot_data(result_data)
            self.stats_table.update_stats(result_data)

            # トレード履歴ウィジェットを更新
            if 'win_trades' in result_data and 'lose_trades' in result_data:
                self.trade_history_widget.load_trade_data(result_data)

                # リスク指標ウィジェットを更新
                self.risk_metrics_widget.load_risk_metrics(
                    result_data['win_trades'],
                    result_data['lose_trades']
                )
            else:
                self.logger.warning("トレード履歴データが結果に含まれていません")
                self.trade_history_widget.clear()
                self.risk_metrics_widget.clear()

            # バックテスト完了シグナルを発信（グリッド更新のため）
            # emit_completedがTrueの場合のみ（新しいバックテスト完了時）
            if emit_completed:
                code = stock_data.get('code')
                rights_month = stock_data.get('rights_month')
                if code and rights_month:
                    self.backtest_completed.emit(code, rights_month)
        else:
            self.chart_widget.clear()
            self.stats_table.clear()
            self.trade_history_widget.clear()
            self.risk_metrics_widget.clear()

    def clear(self):
        """パネルをクリア"""
        self.current_stock = None
        self.current_result = None
        self.info_card.clear()
        self.chart_widget.clear()
        self.stats_table.clear()
        self.trade_history_widget.clear()
        self.risk_metrics_widget.clear()
