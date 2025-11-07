"""
Main Window Module (Version 2 - Integrated)
メインウィンドウ（統合版）

Author: Yuutai Event Investor Team
Date: 2024-11-07
Version: 2.0.0
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSplitter, QStatusBar, QMessageBox,
    QProgressDialog
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont
import logging
from typing import List, Dict, Any, Optional

from ..core.database import DatabaseManager
from ..core.calculator import OptimalTimingCalculator
from ..core.data_fetcher import StockDataFetcher
from .widgets import StockListWidget, DetailPanel, FilterPanel


class AnalysisWorker(QThread):
    """バックグラウンドでバックテストを実行するワーカー"""

    # シグナル定義
    finished = Signal(dict)  # 分析完了シグナル（結果データを渡す）
    error = Signal(str)  # エラーシグナル

    def __init__(self, ticker: str, rights_date: str):
        super().__init__()
        self.ticker = ticker
        self.rights_date = rights_date
        self.logger = logging.getLogger(__name__)

    def run(self):
        """バックテスト実行"""
        try:
            self.logger.info(f"バックテスト開始: {self.ticker}")

            # データフェッチャーとカリキュレーターを初期化
            fetcher = StockDataFetcher()
            calculator = OptimalTimingCalculator(fetcher)

            # 最適タイミングを計算
            result = calculator.find_optimal_timing(self.ticker, self.rights_date)

            if result:
                self.logger.info(f"バックテスト完了: {self.ticker}")
                self.finished.emit(result)
            else:
                self.error.emit("分析結果が取得できませんでした")

        except Exception as e:
            self.logger.error(f"バックテストエラー: {e}", exc_info=True)
            self.error.emit(f"分析エラー: {str(e)}")


class MainWindow(QMainWindow):
    """メインウィンドウクラス（統合版）"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

        # データベースマネージャー
        self.db = DatabaseManager()

        # 現在のデータ
        self.all_stocks = []
        self.filtered_stocks = []
        self.current_analysis_worker = None

        # ウィンドウ設定
        self.setWindowTitle("Yuutai Event Investor - 株主優待イベント投資分析ツール")
        self.setGeometry(100, 100, 1400, 900)

        # UI初期化
        self.init_ui()

        # データ読み込み
        self.load_initial_data()

        self.logger.info("メインウィンドウを初期化しました")

    def init_ui(self):
        """UIコンポーネントを初期化"""

        # 中央ウィジェット
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # メインレイアウト
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ========================================
        # ヘッダー
        # ========================================
        header = self.create_header()
        main_layout.addWidget(header)

        # ========================================
        # コンテンツエリア（3カラムレイアウト）
        # ========================================
        content_splitter = QSplitter(Qt.Horizontal)

        # 左パネル（フィルター）
        self.filter_panel = FilterPanel()
        self.filter_panel.setMaximumWidth(280)
        self.filter_panel.setMinimumWidth(220)
        self.filter_panel.filter_changed.connect(self.on_filter_changed)
        content_splitter.addWidget(self.filter_panel)

        # 中央パネル（銘柄リスト）
        self.stock_list_widget = StockListWidget()
        self.stock_list_widget.setMinimumWidth(350)
        self.stock_list_widget.stock_selected.connect(self.on_stock_selected)
        content_splitter.addWidget(self.stock_list_widget)

        # 右パネル（詳細表示）
        self.detail_panel = DetailPanel()
        self.detail_panel.setMinimumWidth(450)
        content_splitter.addWidget(self.detail_panel)

        # スプリッターの初期サイズ比率を設定
        content_splitter.setStretchFactor(0, 1)  # 左: 1
        content_splitter.setStretchFactor(1, 2)  # 中央: 2
        content_splitter.setStretchFactor(2, 3)  # 右: 3

        main_layout.addWidget(content_splitter)

        # ========================================
        # ステータスバー
        # ========================================
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("準備完了")

        # スタイルシート適用
        self.apply_styles()

    def create_header(self) -> QWidget:
        """ヘッダーを作成"""
        header = QWidget()
        header.setFixedHeight(60)
        header.setObjectName("header")

        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 10, 20, 10)

        # タイトル
        title = QLabel("📈 Yuutai Event Investor")
        title_font = QFont("Meiryo", 16, QFont.Bold)
        title.setFont(title_font)
        title.setObjectName("headerTitle")
        layout.addWidget(title)

        layout.addStretch()

        # 更新ボタン
        refresh_btn = QPushButton("🔄 データ更新")
        refresh_btn.setFixedSize(120, 35)
        refresh_btn.setObjectName("refreshButton")
        refresh_btn.clicked.connect(self.on_refresh_data)
        layout.addWidget(refresh_btn)

        # 設定ボタン
        settings_btn = QPushButton("⚙ 設定")
        settings_btn.setFixedSize(80, 35)
        settings_btn.setObjectName("settingsButton")
        settings_btn.clicked.connect(self.on_settings)
        layout.addWidget(settings_btn)

        # テーマ切替ボタン
        theme_btn = QPushButton("🌙")
        theme_btn.setFixedSize(35, 35)
        theme_btn.setObjectName("themeButton")
        theme_btn.clicked.connect(self.on_toggle_theme)
        layout.addWidget(theme_btn)

        return header

    def apply_styles(self):
        """スタイルシートを適用"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1E1E1E;
            }

            #header {
                background-color: #2D2D2D;
                border-bottom: 1px solid #404040;
            }

            #headerTitle {
                color: #1E90FF;
            }

            #refreshButton {
                background-color: #4682B4;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 15px;
                font-size: 12px;
            }
            #refreshButton:hover {
                background-color: #1E90FF;
            }

            #settingsButton, #themeButton {
                background-color: #3A3A3A;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 15px;
                font-size: 12px;
            }
            #settingsButton:hover, #themeButton:hover {
                background-color: #404040;
            }

            QSplitter::handle {
                background-color: #404040;
                width: 1px;
            }

            QStatusBar {
                background-color: #2D2D2D;
                color: #B0B0B0;
                border-top: 1px solid #404040;
            }
        """)

    # ========================================
    # データ処理
    # ========================================

    def load_initial_data(self):
        """初期データを読み込む"""
        try:
            self.logger.info("初期データを読み込み中...")
            self.status_bar.showMessage("データを読み込み中...")

            # データベースから全銘柄を取得
            stocks = self.db.get_all_stocks()

            self.logger.debug(f"取得した銘柄数: {len(stocks)}")
            if stocks:
                self.logger.debug(f"最初の銘柄データ: {stocks[0]}")
                self.logger.debug(f"データ型: {type(stocks[0])}")

            if not stocks:
                self.logger.warning("データベースに銘柄データがありません")
                self.status_bar.showMessage("銘柄データがありません。データ更新を実行してください。")
                QMessageBox.information(
                    self,
                    "データがありません",
                    "銘柄データが見つかりませんでした。\n「データ更新」ボタンをクリックしてデータを取得してください。"
                )
                return

            # 簡易的な統計情報を追加（実際のバックテストは選択時に実行）
            self.all_stocks = []
            for stock in stocks:
                # 辞書としてアクセス
                stock_data = {
                    'code': stock.get('code', ''),
                    'name': stock.get('name', ''),
                    'rights_month': stock.get('rights_month', 0),
                    'rights_date': stock.get('rights_date', ''),
                    # プレースホルダー値
                    'optimal_days': None,
                    'win_rate': None,
                    'expected_return': None
                }
                self.all_stocks.append(stock_data)

            # フィルタリングして表示
            self.filtered_stocks = self.all_stocks.copy()
            self.stock_list_widget.load_stocks(self.filtered_stocks)

            self.logger.info(f"{len(self.all_stocks)}件の銘柄データを読み込みました")
            self.status_bar.showMessage(f"{len(self.all_stocks)}件の銘柄データを読み込みました")

        except Exception as e:
            self.logger.error(f"データ読み込みエラー: {e}", exc_info=True)
            self.status_bar.showMessage(f"データ読み込みエラー: {str(e)}")
            QMessageBox.critical(
                self,
                "エラー",
                f"データの読み込みに失敗しました。\n{str(e)}"
            )

    def on_filter_changed(self, filters: Dict[str, Any]):
        """フィルター条件が変更された時の処理"""
        try:
            self.logger.debug(f"フィルター適用: {filters}")

            # フィルタリング
            filtered = self.all_stocks.copy()

            # 権利確定月でフィルター
            if filters['rights_month'] is not None:
                filtered = [s for s in filtered if s.get('rights_month') == filters['rights_month']]

            # 勝率でフィルター（Noneを除外）
            if filters['min_win_rate'] > 0:
                filtered = [s for s in filtered if s.get('win_rate') is not None and s.get('win_rate') >= filters['min_win_rate']]

            # 期待リターンでフィルター（Noneを除外）
            if filters['min_expected_return'] > 0:
                filtered = [s for s in filtered if s.get('expected_return') is not None and s.get('expected_return') >= filters['min_expected_return']]

            # ソート
            sort_by = filters['sort_by']
            sort_order = filters['sort_order']

            if sort_by == 'code':
                filtered.sort(key=lambda x: x.get('code', ''), reverse=(sort_order == 'desc'))
            elif sort_by == 'expected_return':
                # Noneを最後に
                filtered.sort(key=lambda x: (x.get('expected_return') is None, x.get('expected_return', 0)), reverse=(sort_order == 'desc'))
            elif sort_by == 'win_rate':
                # Noneを最後に
                filtered.sort(key=lambda x: (x.get('win_rate') is None, x.get('win_rate', 0)), reverse=(sort_order == 'desc'))
            elif sort_by == 'rights_date':
                filtered.sort(key=lambda x: x.get('rights_date', ''), reverse=(sort_order == 'desc'))

            # 更新
            self.filtered_stocks = filtered
            self.stock_list_widget.load_stocks(self.filtered_stocks)

            self.status_bar.showMessage(f"{len(filtered)}件の銘柄を表示中")

        except Exception as e:
            self.logger.error(f"フィルター処理エラー: {e}", exc_info=True)

    def on_stock_selected(self, stock_data: Dict[str, Any]):
        """銘柄が選択された時の処理"""
        try:
            code = stock_data.get('code')
            name = stock_data.get('name')
            rights_date = stock_data.get('rights_date')

            self.logger.info(f"銘柄選択: {code} - {name}")
            self.status_bar.showMessage(f"{name}({code})を分析中...")

            # まず銘柄情報のみ表示（結果はNone）
            self.detail_panel.update_stock_detail(stock_data, None)

            # バックテストをバックグラウンドで実行
            self.run_analysis(code, rights_date, stock_data)

        except Exception as e:
            self.logger.error(f"銘柄選択処理エラー: {e}", exc_info=True)
            self.status_bar.showMessage(f"エラー: {str(e)}")

    def run_analysis(self, ticker: str, rights_date: str, stock_data: Dict[str, Any]):
        """バックグラウンドで分析を実行"""
        # 既存のワーカーが動作中の場合は停止
        if self.current_analysis_worker and self.current_analysis_worker.isRunning():
            self.current_analysis_worker.quit()
            self.current_analysis_worker.wait()

        # ワーカーを作成して実行
        self.current_analysis_worker = AnalysisWorker(ticker, rights_date)
        self.current_analysis_worker.finished.connect(
            lambda result: self.on_analysis_finished(result, stock_data)
        )
        self.current_analysis_worker.error.connect(self.on_analysis_error)
        self.current_analysis_worker.start()

    def on_analysis_finished(self, result_data: Dict[str, Any], stock_data: Dict[str, Any]):
        """分析完了時の処理"""
        try:
            self.logger.info(f"分析完了: {stock_data.get('code')}")

            # 詳細パネルを更新
            self.detail_panel.update_stock_detail(stock_data, result_data)

            self.status_bar.showMessage(f"{stock_data.get('name')}の分析が完了しました")

        except Exception as e:
            self.logger.error(f"分析結果表示エラー: {e}", exc_info=True)
            self.status_bar.showMessage(f"エラー: {str(e)}")

    def on_analysis_error(self, error_message: str):
        """分析エラー時の処理"""
        self.logger.error(f"分析エラー: {error_message}")
        self.status_bar.showMessage(f"分析エラー: {error_message}")
        QMessageBox.warning(self, "分析エラー", error_message)

    # ========================================
    # イベントハンドラー
    # ========================================

    def on_refresh_data(self):
        """データ更新ボタンクリック時の処理"""
        self.status_bar.showMessage("データを更新中...")
        self.logger.info("データ更新を開始")

        # TODO: スクレイピング処理を実装
        QMessageBox.information(
            self,
            "データ更新",
            "データ更新機能は現在開発中です。\nPhase 4で実装予定です。"
        )

        self.status_bar.showMessage("データ更新完了", 3000)

    def on_settings(self):
        """設定ボタンクリック時の処理"""
        self.logger.info("設定画面を開く")

        # TODO: 設定ダイアログを実装
        QMessageBox.information(
            self,
            "設定",
            "設定機能は現在開発中です。"
        )

        self.status_bar.showMessage("設定機能は未実装です", 3000)

    def on_toggle_theme(self):
        """テーマ切替ボタンクリック時の処理"""
        self.logger.info("テーマを切り替え")

        # TODO: テーマ切替を実装
        QMessageBox.information(
            self,
            "テーマ切替",
            "テーマ切替機能は現在開発中です。"
        )

        self.status_bar.showMessage("テーマ切替機能は未実装です", 3000)

    def closeEvent(self, event):
        """ウィンドウを閉じる時の処理"""
        # ワーカーが動作中の場合は停止
        if self.current_analysis_worker and self.current_analysis_worker.isRunning():
            self.current_analysis_worker.quit()
            self.current_analysis_worker.wait()

        # データベース接続を閉じる
        self.db.close()

        self.logger.info("アプリケーションを終了します")
        event.accept()
