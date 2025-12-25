"""
Main Window Module (Version 3 - Phase 4 integrated)
メインウィンドウ（Phase 4統合版）

Author: Yuutai Event Investor Team
Date: 2024-11-07
Version: 3.0.0
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSplitter, QStatusBar, QMessageBox,
    QProgressDialog, QTabWidget, QFileDialog, QMenu
)
from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtGui import QFont, QAction
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import pandas as pd
import threading
import json

from ..core.database import DatabaseManager
from ..core.calculator import OptimalTimingCalculator
from ..core.data_fetcher import StockDataFetcher
from .widgets import StockListWidget, DetailPanel, FilterPanel, ComparisonPanel, PortfolioPanel
from .widgets.watchlist_widget import WatchlistWidget
from .dialogs import SettingsDialog
from .import_dialog import ImportDialog
from ..utils.export import DataExporter, ScreenshotExporter
from ..utils.notification import NotificationManager


class AnalysisWorkerSignals(QObject):
    """AnalysisWorker用のシグナル"""
    finished = Signal(dict)
    error = Signal(str)


class AnalysisWorker:
    """バックグラウンドでバックテストを実行するワーカー

    Note: macOSでQThread + SQLiteの競合によるSIGSEGVクラッシュを回避するため、
    QThreadではなくthreading.Threadを使用
    """

    def __init__(self, ticker: str, rights_date: str):
        self.ticker = ticker
        self.rights_date = rights_date
        self.logger = logging.getLogger(__name__)
        self.signals = AnalysisWorkerSignals()
        self._thread = None

    @property
    def finished(self):
        return self.signals.finished

    @property
    def error(self):
        return self.signals.error

    def start(self):
        """ワーカースレッドを開始"""
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def isRunning(self):
        """スレッドが実行中かどうか"""
        return self._thread is not None and self._thread.is_alive()

    def _run(self):
        """バックテスト実行"""
        fetcher = None
        try:
            self.logger.info(f"バックテスト開始: {self.ticker}")

            fetcher = StockDataFetcher()
            calculator = OptimalTimingCalculator(fetcher)

            result = calculator.find_optimal_timing(self.ticker, self.rights_date)

            if result:
                self.logger.info(f"バックテスト完了: {self.ticker}")
                self.signals.finished.emit(result)
            else:
                self.signals.error.emit("分析結果が取得できませんでした")

        except Exception as e:
            self.logger.error(f"バックテストエラー: {e}", exc_info=True)
            self.signals.error.emit(f"分析エラー: {str(e)}")
        finally:
            if fetcher and hasattr(fetcher, 'close'):
                fetcher.close()


class TradeDetailsWorkerSignals(QObject):
    """TradeDetailsWorker用のシグナル"""
    finished = Signal(dict)
    error = Signal(str)


class TradeDetailsWorker:
    """バックグラウンドでトレード詳細を取得するワーカー

    Note: macOSでQThread + SQLiteの競合によるSIGSEGVクラッシュを回避するため、
    QThreadではなくthreading.Threadを使用
    """

    def __init__(self, ticker: str, rights_month: int, buy_days_before: int):
        self.ticker = ticker
        self.rights_month = rights_month
        self.buy_days_before = buy_days_before
        self.logger = logging.getLogger(__name__)
        self.signals = TradeDetailsWorkerSignals()
        self._thread = None

    @property
    def finished(self):
        return self.signals.finished

    @property
    def error(self):
        return self.signals.error

    def start(self):
        """ワーカースレッドを開始"""
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def isRunning(self):
        """スレッドが実行中かどうか"""
        return self._thread is not None and self._thread.is_alive()

    def _run(self):
        """トレード詳細取得"""
        fetcher = None
        try:
            self.logger.info(f"トレード詳細取得開始: {self.ticker}, 月={self.rights_month}, 日数={self.buy_days_before}")

            fetcher = StockDataFetcher()
            calculator = OptimalTimingCalculator(fetcher)

            trade_details = calculator.get_trade_details(
                self.ticker,
                self.rights_month,
                self.buy_days_before
            )

            if trade_details:
                win_count = len(trade_details.get('win_trades', pd.DataFrame()))
                lose_count = len(trade_details.get('lose_trades', pd.DataFrame()))
                self.logger.info(f"トレード詳細取得完了: {self.ticker}, 勝ち={win_count}, 負け={lose_count}")
                self.signals.finished.emit(trade_details)
            else:
                self.logger.warning(f"トレード詳細がNone: {self.ticker}")
                self.signals.error.emit("トレード詳細が取得できませんでした")

        except Exception as e:
            self.logger.error(f"トレード詳細取得エラー: {e}", exc_info=True)
            self.signals.error.emit(f"トレード詳細取得エラー: {str(e)}")
        finally:
            if fetcher and hasattr(fetcher, 'close'):
                fetcher.close()


class MainWindow(QMainWindow):
    """メインウィンドウクラス（Phase 4統合版）"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

        # データベースマネージャー
        self.db = DatabaseManager()

        # エクスポーター
        self.data_exporter = DataExporter()
        self.screenshot_exporter = ScreenshotExporter()

        # 通知マネージャー
        self.notification_manager = NotificationManager(self.db)

        # 現在の設定を読み込む
        self.current_settings = self._load_settings()

        # 現在のデータ
        self.all_stocks = []
        self.filtered_stocks = []
        self.current_analysis_worker = None
        self.current_trade_details_worker = None
        self.current_selected_stock = None
        self.current_result = None

        # ウィンドウ設定
        self.setWindowTitle("Yuutai Event Investor - 株主優待イベント投資分析ツール")
        # ウィンドウサイズを大きく設定（全てのコントロールが見えるように）
        self.setGeometry(50, 50, 2000, 1500)
        # 最小サイズも設定
        self.setMinimumSize(1400, 900)

        # UI初期化
        self.init_ui()

        # データ読み込み
        self.load_initial_data()

        # 通知チェック（データベースメソッドが実装されるまで無効化）
        # self.check_notifications()

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
        # タブウィジェット
        # ========================================
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: #1E1E1E;
            }
            QTabBar::tab {
                background-color: #2D2D2D;
                color: #B0B0B0;
                padding: 10px 20px;
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

        # メインタブ（銘柄リストと分析）
        main_tab = self.create_main_tab()
        self.tab_widget.addTab(main_tab, "📊 銘柄分析")

        # ウォッチリストタブ
        self.watchlist_widget = WatchlistWidget(self.db)
        self.watchlist_widget.stock_selected.connect(self.on_stock_selected)
        self.tab_widget.addTab(self.watchlist_widget, "⭐ ウォッチリスト")

        # 比較パネルタブ
        self.comparison_panel = ComparisonPanel()
        self.comparison_panel.send_to_portfolio.connect(self.on_send_to_portfolio)
        self.tab_widget.addTab(self.comparison_panel, "📈 銘柄比較")

        # ポートフォリオパネルタブ
        self.portfolio_panel = PortfolioPanel()
        self.tab_widget.addTab(self.portfolio_panel, "💼 ポートフォリオ")

        main_layout.addWidget(self.tab_widget)

        # ========================================
        # ステータスバー
        # ========================================
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("準備完了")

        # メニューバー
        self.create_menu_bar()

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

        # エクスポートボタン
        export_btn = QPushButton("💾 エクスポート")
        export_btn.setFixedSize(130, 35)
        export_btn.setObjectName("exportButton")
        export_btn.clicked.connect(self.show_export_menu)
        layout.addWidget(export_btn)

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

        return header

    def create_main_tab(self) -> QWidget:
        """メインタブ（銘柄リスト+分析）を作成"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # スプリッター
        splitter = QSplitter(Qt.Horizontal)

        # 左パネル（フィルター）
        self.filter_panel = FilterPanel()
        self.filter_panel.setMaximumWidth(280)
        self.filter_panel.setMinimumWidth(220)
        self.filter_panel.filter_changed.connect(self.on_filter_changed)
        splitter.addWidget(self.filter_panel)

        # 中央パネル（銘柄リスト）
        self.stock_list_widget = StockListWidget()
        self.stock_list_widget.setMinimumWidth(350)
        self.stock_list_widget.stock_selected.connect(self.on_stock_selected)
        # 右クリックメニューシグナル接続
        self.stock_list_widget.add_to_watchlist_requested.connect(self.add_to_watchlist_from_signal)
        self.stock_list_widget.add_to_comparison_requested.connect(self.add_to_comparison_from_signal)
        self.stock_list_widget.add_to_portfolio_requested.connect(self.add_to_portfolio_from_signal)
        splitter.addWidget(self.stock_list_widget)

        # 右パネル（詳細表示）
        self.detail_panel = DetailPanel()
        self.detail_panel.setMinimumWidth(450)
        self.detail_panel.backtest_completed.connect(self.on_backtest_completed)
        splitter.addWidget(self.detail_panel)

        # スプリッターの初期サイズ比率を設定（interact/sc002.png参考）
        # フィルター: 13%, 銘柄リスト: 33%, 詳細パネル: 54%
        splitter.setStretchFactor(0, 13)  # フィルターパネル
        splitter.setStretchFactor(1, 33)  # 銘柄リスト
        splitter.setStretchFactor(2, 54)  # 詳細パネル

        # 初期サイズを明示的に設定（ウィンドウ幅1330pxの場合）
        # フィルター: 180px (13%), 銘柄リスト: 440px (33%), 詳細パネル: 710px (54%)
        splitter.setSizes([180, 440, 710])

        layout.addWidget(splitter)

        return widget

    def create_menu_bar(self):
        """メニューバーを作成"""
        menubar = self.menuBar()

        # ファイルメニュー
        file_menu = menubar.addMenu("ファイル(&F)")

        # CSVインポート
        import_action = QAction("CSVから銘柄をインポート(&I)...", self)
        import_action.setShortcut("Ctrl+I")
        import_action.triggered.connect(self.show_import_dialog)
        file_menu.addAction(import_action)

        file_menu.addSeparator()

        export_action = QAction("エクスポート(&E)...", self)
        export_action.triggered.connect(self.show_export_menu)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        exit_action = QAction("終了(&X)", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 表示メニュー
        view_menu = menubar.addMenu("表示(&V)")

        watchlist_action = QAction("ウォッチリスト(&W)", self)
        watchlist_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(1))
        view_menu.addAction(watchlist_action)

        # ツールメニュー
        tools_menu = menubar.addMenu("ツール(&T)")

        refresh_action = QAction("データ更新(&R)", self)
        refresh_action.triggered.connect(self.on_refresh_data)
        tools_menu.addAction(refresh_action)

        tools_menu.addSeparator()

        # 一括バックテストメニュー
        batch_menu = tools_menu.addMenu("一括バックテスト(&B)")

        # 現在の月の銘柄
        batch_current_action = QAction("現在のフィルター条件の銘柄", self)
        batch_current_action.triggered.connect(self.run_batch_backtest_current)
        batch_menu.addAction(batch_current_action)

        batch_menu.addSeparator()

        # 各月
        for month in range(1, 13):
            action = QAction(f"{month}月の銘柄", self)
            action.triggered.connect(lambda checked, m=month: self.run_batch_backtest_month(m))
            batch_menu.addAction(action)

        batch_menu.addSeparator()

        # 全銘柄
        batch_all_action = QAction("全銘柄（時間がかかります）", self)
        batch_all_action.triggered.connect(self.run_batch_backtest_all)
        batch_menu.addAction(batch_all_action)

        tools_menu.addSeparator()

        settings_action = QAction("設定(&S)...", self)
        settings_action.triggered.connect(self.on_settings)
        tools_menu.addAction(settings_action)

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
            #refreshButton, #exportButton {
                background-color: #4682B4;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 15px;
                font-size: 12px;
            }
            #refreshButton:hover, #exportButton:hover {
                background-color: #1E90FF;
            }
            #settingsButton {
                background-color: #3A3A3A;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 15px;
                font-size: 12px;
            }
            #settingsButton:hover {
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
            QMenuBar {
                background-color: #2D2D2D;
                color: #E0E0E0;
            }
            QMenuBar::item:selected {
                background-color: #1E90FF;
            }
            QMenu {
                background-color: #2D2D2D;
                color: #E0E0E0;
                border: 1px solid #404040;
            }
            QMenu::item:selected {
                background-color: #1E90FF;
            }
        """)

    def load_initial_data(self):
        """初期データを読み込む"""
        try:
            self.logger.info("初期データを読み込み中...")
            self.status_bar.showMessage("データを読み込み中...")

            stocks = self.db.get_all_stocks()

            if not stocks:
                self.logger.warning("データベースに銘柄データがありません")
                self.status_bar.showMessage("銘柄データがありません")
                return

            self.all_stocks = []
            for stock in stocks:
                code = stock.get('code', '')
                rights_month = stock.get('rights_month', 0)

                # シミュレーションキャッシュから最適な結果を取得（権利確定月を指定）
                best_result = self.db.get_best_simulation_result(code, rights_month)

                stock_data = {
                    'code': code,
                    'name': stock.get('name', ''),
                    'rights_month': rights_month,
                    'rights_date': stock.get('rights_date', ''),
                    'yuutai_genre': stock.get('yuutai_genre', ''),
                    'yuutai_content': stock.get('yuutai_content', ''),
                    'optimal_days': best_result.get('buy_days_before') if best_result else None,
                    'win_rate': best_result.get('win_rate') if best_result else None,
                    'expected_return': best_result.get('expected_return') if best_result else None
                }
                self.all_stocks.append(stock_data)

            self.filtered_stocks = self.all_stocks.copy()
            self.stock_list_widget.load_stocks(self.filtered_stocks)

            self.logger.info(f"{len(self.all_stocks)}件の銘柄データを読み込みました")
            self.status_bar.showMessage(f"{len(self.all_stocks)}件の銘柄データを読み込みました")

        except Exception as e:
            self.logger.error(f"データ読み込みエラー: {e}", exc_info=True)
            self.status_bar.showMessage(f"エラー: {str(e)}")

    def on_filter_changed(self, filters: Dict[str, Any]):
        """フィルター条件が変更された時の処理"""
        try:
            filtered = self.all_stocks.copy()

            if filters['rights_month'] is not None:
                filtered = [s for s in filtered if s.get('rights_month') == filters['rights_month']]

            if filters['min_win_rate'] > 0:
                filtered = [s for s in filtered if s.get('win_rate') is not None and s.get('win_rate') >= filters['min_win_rate']]

            if filters['min_expected_return'] > 0:
                filtered = [s for s in filtered if s.get('expected_return') is not None and s.get('expected_return') >= filters['min_expected_return']]

            sort_by = filters['sort_by']
            sort_order = filters['sort_order']

            if sort_by == 'code':
                filtered.sort(key=lambda x: x.get('code', ''), reverse=(sort_order == 'desc'))
            elif sort_by in ['expected_return', 'win_rate']:
                filtered.sort(key=lambda x: (x.get(sort_by) is None, x.get(sort_by, 0)), reverse=(sort_order == 'desc'))

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
            rights_month = stock_data.get('rights_month')

            self.logger.info(f"銘柄選択: {code} - {name}")

            self.current_selected_stock = stock_data

            # タブを切り替え（メインタブに戻す）
            self.tab_widget.setCurrentIndex(0)

            # まずキャッシュから結果を取得
            cached_results = self.db.get_simulation_cache(code, rights_month)

            if cached_results:
                # キャッシュデータから結果を構築
                self.logger.info(f"キャッシュデータを使用: {code} ({len(cached_results)}件)")
                self.status_bar.showMessage(f"{name}({code})の分析結果を表示中...")

                # キャッシュデータのキー名を変換（buy_days_before -> days_before）
                converted_results = []
                for r in cached_results:
                    converted_results.append({
                        'days_before': r['buy_days_before'],
                        'win_count': r['win_count'],
                        'lose_count': r['lose_count'],
                        'win_rate': r['win_rate'],
                        'expected_return': r['expected_return'],
                        'avg_win_return': r['avg_win_return'],
                        'max_win_return': r['max_win_return'],
                        'avg_lose_return': r['avg_lose_return'],
                        'max_lose_return': r['max_lose_return']
                    })

                # 最適な結果を見つける
                best_result = max(cached_results, key=lambda x: x['expected_return'] * x['win_rate'])

                result_data = {
                    'ticker': code,
                    'rights_month': rights_month,
                    'optimal_days': best_result['buy_days_before'],
                    'win_rate': best_result['win_rate'],
                    'expected_return': best_result['expected_return'],
                    'win_count': best_result['win_count'],
                    'lose_count': best_result['lose_count'],
                    'total_count': best_result['win_count'] + best_result['lose_count'],
                    'avg_win_return': best_result['avg_win_return'],
                    'max_win_return': best_result['max_win_return'],
                    'avg_lose_return': best_result['avg_lose_return'],
                    'max_lose_return': best_result['max_lose_return'],
                    'all_results': converted_results  # 変換後のデータを使用
                }

                # トレード詳細を取得（バックグラウンドで）
                self.logger.info(f"トレード詳細取得を開始: {code}, 月={rights_month}, 日数={best_result['buy_days_before']}")
                self.fetch_trade_details(code, rights_month, best_result['buy_days_before'], result_data, stock_data)

                self.current_result = result_data
                # キャッシュから表示する場合はグリッド更新不要（emit_completed=False）
                self.detail_panel.update_stock_detail(stock_data, result_data, emit_completed=False)
                self.status_bar.showMessage(f"{name}({code})の分析結果を表示しました（キャッシュ）")

            else:
                # キャッシュがない場合のみバックテストを実行
                self.logger.info(f"キャッシュなし。バックテストを実行: {code}")
                self.status_bar.showMessage(f"{name}({code})を分析中...")

                # 銘柄情報のみ表示
                self.detail_panel.update_stock_detail(stock_data, None, emit_completed=False)

                # バックテストをバックグラウンドで実行
                self.run_analysis(code, rights_date, stock_data)

        except Exception as e:
            self.logger.error(f"銘柄選択処理エラー: {e}", exc_info=True)

    def run_analysis(self, ticker: str, rights_date: str, stock_data: Dict[str, Any]):
        """バックグラウンドで分析を実行"""
        if self.current_analysis_worker and self.current_analysis_worker.isRunning():
            self.current_analysis_worker.quit()
            self.current_analysis_worker.wait()

        self.current_analysis_worker = AnalysisWorker(ticker, rights_date)
        self.current_analysis_worker.finished.connect(
            lambda result: self.on_analysis_finished(result, stock_data)
        )
        self.current_analysis_worker.error.connect(self.on_analysis_error)
        self.current_analysis_worker.start()

    def on_analysis_finished(self, result_data: Dict[str, Any], stock_data: Dict[str, Any]):
        """分析完了時の処理"""
        try:
            code = stock_data.get('code')
            rights_month = stock_data.get('rights_month')

            self.logger.info(f"分析完了: {code}")

            # データベースに全ての結果を保存
            if 'all_results' in result_data:
                for result in result_data['all_results']:
                    self.db.insert_simulation_cache(
                        code=code,
                        rights_month=rights_month,
                        buy_days_before=result['days_before'],
                        win_count=result['win_count'],
                        lose_count=result['lose_count'],
                        win_rate=result['win_rate'],
                        expected_return=result['expected_return'],
                        avg_win_return=result['avg_win_return'],
                        max_win_return=result['max_win_return'],
                        avg_lose_return=result['avg_lose_return'],
                        max_lose_return=result['max_lose_return']
                    )
                self.logger.info(f"分析結果をデータベースに保存: {code} ({len(result_data['all_results'])}件)")

            self.current_result = result_data
            # 新しいバックテスト完了時はグリッド更新が必要（emit_completed=True）
            self.detail_panel.update_stock_detail(stock_data, result_data, emit_completed=True)
            self.status_bar.showMessage(f"{stock_data.get('name')}の分析が完了しました")

        except Exception as e:
            self.logger.error(f"分析結果表示エラー: {e}", exc_info=True)

    def on_analysis_error(self, error_message: str):
        """分析エラー時の処理"""
        self.logger.error(f"分析エラー: {error_message}")
        self.status_bar.showMessage(f"分析エラー: {error_message}")

    def on_backtest_completed(self, code: str, rights_month: int):
        """バックテスト完了時に左側のグリッドを更新"""
        try:
            self.logger.info(f"バックテスト完了、グリッド更新: {code} ({rights_month}月)")

            # データベースから最新の結果を取得（権利確定月を指定）
            best_result = self.db.get_best_simulation_result(code, rights_month)

            if not best_result:
                self.logger.warning(f"バックテスト結果が見つかりません: {code} ({rights_month}月)")
                return

            # all_stocksリストを更新
            for stock in self.all_stocks:
                if stock.get('code') == code and stock.get('rights_month') == rights_month:
                    stock['optimal_days'] = best_result.get('buy_days_before')
                    stock['win_rate'] = best_result.get('win_rate')
                    stock['expected_return'] = best_result.get('expected_return')
                    break

            # filtered_stocksリストも更新
            for stock in self.filtered_stocks:
                if stock.get('code') == code and stock.get('rights_month') == rights_month:
                    stock['optimal_days'] = best_result.get('buy_days_before')
                    stock['win_rate'] = best_result.get('win_rate')
                    stock['expected_return'] = best_result.get('expected_return')
                    break

            # 左側のグリッドを再描画（フィルタリング済みのリストを使用）
            self.stock_list_widget.load_stocks(self.filtered_stocks)

            self.logger.info(f"グリッド更新完了: {code} ({rights_month}月)")

        except Exception as e:
            self.logger.error(f"グリッド更新エラー: {e}", exc_info=True)

    def show_stock_context_menu(self, position):
        """銘柄リストのコンテキストメニューを表示"""
        row = self.stock_list_widget.table.rowAt(position.y())
        if row < 0:
            return

        code_item = self.stock_list_widget.table.item(row, 0)
        month_item = self.stock_list_widget.table.item(row, 2)
        if not code_item or not month_item:
            return

        code = code_item.text()
        # 権利月から数値を抽出
        month_text = month_item.text()
        try:
            rights_month = int(month_text.replace('月', ''))
        except ValueError:
            return

        # 該当する銘柄データを取得
        stock_data = None
        for stock in self.filtered_stocks:
            if stock.get('code') == code and stock.get('rights_month') == rights_month:
                stock_data = stock
                break

        if not stock_data:
            return

        menu = QMenu(self)

        # ウォッチリストに追加/削除
        if self.watchlist_widget.is_in_watchlist(code):
            remove_action = QAction("ウォッチリストから削除", self)
            remove_action.triggered.connect(lambda: self.remove_from_watchlist(code))
            menu.addAction(remove_action)
        else:
            add_action = QAction("ウォッチリストに追加", self)
            add_action.triggered.connect(lambda: self.add_to_watchlist(code))
            menu.addAction(add_action)

        menu.addSeparator()

        # 比較リストに追加/削除
        if self.comparison_panel.is_stock_compared(code, rights_month):
            remove_compare_action = QAction("比較リストから削除", self)
            remove_compare_action.triggered.connect(
                lambda: self.comparison_panel.remove_stock(code, rights_month)
            )
            menu.addAction(remove_compare_action)
        else:
            add_compare_action = QAction("比較リストに追加", self)
            add_compare_action.triggered.connect(
                lambda: self.add_to_comparison(stock_data)
            )
            menu.addAction(add_compare_action)

        menu.exec(self.stock_list_widget.table.mapToGlobal(position))

    def add_to_watchlist(self, code: str):
        """ウォッチリストに追加"""
        if self.watchlist_widget.add_to_watchlist(code):
            stock = self.db.get_stock(code)
            name = stock['name'] if stock else code
            self.status_bar.showMessage(f"{name}をウォッチリストに追加しました", 3000)

    def remove_from_watchlist(self, code: str):
        """ウォッチリストから削除"""
        if self.watchlist_widget.remove_from_watchlist(code):
            stock = self.db.get_stock(code)
            name = stock['name'] if stock else code
            self.status_bar.showMessage(f"{name}をウォッチリストから削除しました", 3000)

    def add_to_comparison(self, stock_data: Dict[str, Any]):
        """比較リストに追加"""
        if self.comparison_panel.add_stock(stock_data):
            name = stock_data.get('name', stock_data.get('code', ''))
            rights_month = stock_data.get('rights_month', 0)
            self.status_bar.showMessage(f"{name}({rights_month}月)を比較リストに追加しました", 3000)
            # 比較タブに切り替え
            self.tab_widget.setCurrentIndex(2)

    def add_to_watchlist_from_signal(self, stock_data: Dict[str, Any]):
        """シグナルからウォッチリストに追加"""
        code = stock_data.get('code')
        if code:
            self.add_to_watchlist(code)

    def add_to_comparison_from_signal(self, stock_data: Dict[str, Any]):
        """シグナルから比較リストに追加"""
        self.add_to_comparison(stock_data)

    def add_to_portfolio_from_signal(self, stock_data: Dict[str, Any]):
        """シグナルからポートフォリオに追加"""
        if self.portfolio_panel.add_stock(stock_data):
            name = stock_data.get('name', stock_data.get('code', ''))
            rights_month = stock_data.get('rights_month', 0)
            self.status_bar.showMessage(f"{name}({rights_month}月)をポートフォリオに追加しました", 3000)
            # ポートフォリオタブに切り替え
            self.tab_widget.setCurrentIndex(3)

    def show_import_dialog(self):
        """CSVインポートダイアログを表示"""
        try:
            dialog = ImportDialog(self.db, self)
            dialog.import_completed.connect(self.on_import_completed)
            dialog.exec()
        except Exception as e:
            self.logger.error(f"インポートダイアログエラー: {e}", exc_info=True)
            QMessageBox.critical(self, "エラー", f"インポートダイアログの表示に失敗しました:\n{str(e)}")

    def on_import_completed(self):
        """インポート完了後の処理"""
        try:
            self.logger.info("インポート完了 - データを再読み込み")
            # データを再読み込み
            self.load_initial_data()
            self.status_bar.showMessage("銘柄データを再読み込みしました", 3000)
        except Exception as e:
            self.logger.error(f"データ再読み込みエラー: {e}", exc_info=True)
            QMessageBox.warning(self, "警告", "データの再読み込みに失敗しました")

    def show_export_menu(self):
        """エクスポートメニューを表示"""
        menu = QMenu(self)

        csv_action = QAction("CSVにエクスポート", self)
        csv_action.triggered.connect(self.export_to_csv)
        menu.addAction(csv_action)

        json_action = QAction("JSONにエクスポート", self)
        json_action.triggered.connect(self.export_to_json)
        menu.addAction(json_action)

        menu.addSeparator()

        screenshot_action = QAction("スクリーンショット保存", self)
        screenshot_action.triggered.connect(self.save_screenshot)
        menu.addAction(screenshot_action)

        menu.exec(self.sender().mapToGlobal(self.sender().rect().bottomLeft()))

    def export_to_csv(self):
        """CSVにエクスポート"""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "CSVにエクスポート", "", "CSV Files (*.csv)"
        )

        if filepath:
            if self.data_exporter.export_stock_list(self.filtered_stocks, filepath):
                QMessageBox.information(self, "成功", "CSVファイルにエクスポートしました")
                self.logger.info(f"CSVエクスポート成功: {filepath}")
            else:
                QMessageBox.critical(self, "エラー", "CSVエクスポートに失敗しました")

    def export_to_json(self):
        """JSONにエクスポート"""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "JSONにエクスポート", "", "JSON Files (*.json)"
        )

        if filepath:
            if self.data_exporter.export_to_json(self.filtered_stocks, filepath):
                QMessageBox.information(self, "成功", "JSONファイルにエクスポートしました")
                self.logger.info(f"JSONエクスポート成功: {filepath}")
            else:
                QMessageBox.critical(self, "エラー", "JSONエクスポートに失敗しました")

    def save_screenshot(self):
        """スクリーンショット保存"""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "スクリーンショット保存", "", "PNG Files (*.png);;JPEG Files (*.jpg)"
        )

        if filepath:
            if self.screenshot_exporter.capture_widget(self, filepath):
                QMessageBox.information(self, "成功", "スクリーンショットを保存しました")
                self.logger.info(f"スクリーンショット保存成功: {filepath}")
            else:
                QMessageBox.critical(self, "エラー", "スクリーンショット保存に失敗しました")

    def check_notifications(self):
        """通知をチェック"""
        try:
            messages = self.notification_manager.check_and_show_notifications()

            if messages:
                notification_text = "\n\n".join(messages)
                QMessageBox.information(self, "通知", notification_text)

        except Exception as e:
            self.logger.error(f"通知チェックエラー: {e}")

    def on_refresh_data(self):
        """データ更新ボタンクリック時の処理"""
        QMessageBox.information(
            self,
            "データ更新",
            "データ更新機能は現在開発中です。\nスクレイピング機能の実装が必要です。"
        )

    def on_settings(self):
        """設定ボタンクリック時の処理"""
        dialog = SettingsDialog(self)
        dialog.settings_changed.connect(self.on_settings_changed)
        dialog.exec()

    def on_settings_changed(self, settings: Dict[str, Any]):
        """設定が変更された時の処理"""
        self.logger.info(f"設定が変更されました: {settings}")

        # データ取得期間の変更をチェック
        old_period = self._get_period_value(self.current_settings.get('data_period', '10y'))
        new_period = self._get_period_value(settings.get('data_period', '10y'))

        if new_period > old_period:
            # 期間が長くなった場合、キャッシュをクリア
            reply = QMessageBox.question(
                self,
                "キャッシュクリア確認",
                f"データ取得期間が変更されました。\n"
                f"より正確な計算のため、既存のバックテスト結果を削除して\n"
                f"再計算する必要があります。削除しますか？\n\n"
                f"（削除しないと古い期間のデータで計算された結果が残ります）",
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                self._clear_simulation_cache()
                QMessageBox.information(
                    self,
                    "完了",
                    "キャッシュをクリアしました。\n"
                    "次回の銘柄選択時に新しい設定で再計算されます。"
                )

        # 設定を更新
        self.current_settings = settings

    def on_send_to_portfolio(self, stocks: List[Dict]):
        """比較パネルからポートフォリオパネルに銘柄を送信"""
        try:
            self.portfolio_panel.set_stocks(stocks)
            # ポートフォリオタブに切り替え
            self.tab_widget.setCurrentWidget(self.portfolio_panel)
            self.logger.info(f"{len(stocks)}銘柄をポートフォリオに送信しました")
        except Exception as e:
            self.logger.error(f"ポートフォリオ送信エラー: {e}", exc_info=True)
            QMessageBox.critical(
                self, "エラー",
                f"ポートフォリオへの送信に失敗しました: {str(e)}"
            )

    def fetch_trade_details(self, code: str, rights_month: int, buy_days_before: int,
                           result_data: Dict, stock_data: Dict):
        """トレード詳細をバックグラウンドで取得"""
        try:
            # 既存のワーカーがあれば停止
            if self.current_trade_details_worker and self.current_trade_details_worker.isRunning():
                self.current_trade_details_worker.quit()
                self.current_trade_details_worker.wait()

            # 新しいワーカーを作成
            self.current_trade_details_worker = TradeDetailsWorker(code, rights_month, buy_days_before)
            self.current_trade_details_worker.finished.connect(
                lambda trade_details: self.on_trade_details_fetched(trade_details, result_data, stock_data)
            )
            self.current_trade_details_worker.error.connect(
                lambda err: self.logger.warning(f"トレード詳細取得エラー: {err}")
            )
            self.current_trade_details_worker.start()

        except Exception as e:
            self.logger.error(f"トレード詳細取得開始エラー: {e}", exc_info=True)

    def on_trade_details_fetched(self, trade_details: Dict, result_data: Dict, stock_data: Dict):
        """トレード詳細取得完了時の処理"""
        try:
            code = stock_data.get('code')
            rights_month = stock_data.get('rights_month')

            self.logger.info(f"トレード詳細取得コールバック: {code}, 月={rights_month}")

            # 現在選択されている銘柄と一致するか確認
            if self.current_selected_stock:
                current_code = self.current_selected_stock.get('code')
                current_month = self.current_selected_stock.get('rights_month')
                self.logger.info(f"現在選択中: {current_code}, 月={current_month}")

                if current_code == code and current_month == rights_month:
                    # result_dataにトレード詳細を追加
                    win_trades = trade_details['win_trades']
                    lose_trades = trade_details['lose_trades']

                    self.logger.info(f"トレード詳細: 勝ち={len(win_trades)}, 負け={len(lose_trades)}")

                    result_data['win_trades'] = win_trades
                    result_data['lose_trades'] = lose_trades

                    # current_resultも更新
                    self.current_result = result_data

                    # 詳細パネルを更新
                    self.detail_panel.update_stock_detail(stock_data, result_data, emit_completed=False)

                    self.logger.info(f"トレード詳細を追加し、パネルを更新しました: {code}")
                else:
                    self.logger.info(f"別の銘柄が選択されているため、トレード詳細の更新をスキップします")
            else:
                self.logger.warning("current_selected_stockがNoneです")

        except Exception as e:
            self.logger.error(f"トレード詳細追加エラー: {e}", exc_info=True)

    def run_batch_backtest_current(self):
        """現在のフィルター条件の銘柄で一括バックテスト"""
        if not self.filtered_stocks:
            QMessageBox.warning(self, "警告", "銘柄がありません。フィルター条件を確認してください。")
            return
        self._start_batch_backtest(self.filtered_stocks)

    def run_batch_backtest_month(self, month: int):
        """指定月の銘柄で一括バックテスト"""
        stocks = self.db.get_all_stocks(rights_month=month)
        if not stocks:
            QMessageBox.warning(self, "警告", f"{month}月の銘柄がありません。")
            return
        self._start_batch_backtest(stocks)

    def run_batch_backtest_all(self):
        """全銘柄で一括バックテスト"""
        stocks = self.db.get_all_stocks()
        if not stocks:
            QMessageBox.warning(self, "警告", "銘柄がありません。")
            return

        reply = QMessageBox.question(
            self, "確認",
            f"全 {len(stocks)} 銘柄のバックテストを実行します。\n"
            "これには時間がかかる場合があります。続行しますか？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._start_batch_backtest(stocks)

    def _start_batch_backtest(self, stocks: list):
        """一括バックテストを開始"""
        from ..core.batch_processor import BatchCalculationWorker

        # 進捗ダイアログを作成
        self.batch_progress = QProgressDialog(
            "バックテストを実行中...", "キャンセル", 0, len(stocks), self
        )
        self.batch_progress.setWindowTitle("一括バックテスト")
        self.batch_progress.setWindowModality(Qt.WindowModal)
        self.batch_progress.setMinimumDuration(0)
        self.batch_progress.setValue(0)

        # 計算機を作成
        fetcher = StockDataFetcher()
        calculator = OptimalTimingCalculator(fetcher)

        # ワーカーを作成
        self.batch_worker = BatchCalculationWorker(stocks, calculator, max_workers=4)
        self.batch_worker.progress_updated.connect(self._on_batch_progress)
        self.batch_worker.stock_completed.connect(self._on_stock_completed)
        self.batch_worker.batch_completed.connect(self._on_batch_completed)
        self.batch_worker.error_occurred.connect(self._on_batch_error)

        # キャンセルボタン
        self.batch_progress.canceled.connect(self._on_batch_canceled)

        # 開始
        self.batch_worker.start()
        self.statusBar().showMessage(f"一括バックテスト実行中: {len(stocks)}銘柄")

    def _on_batch_progress(self, current: int, total: int):
        """バッチ処理の進捗更新"""
        if hasattr(self, 'batch_progress') and self.batch_progress:
            self.batch_progress.setValue(current)
            self.batch_progress.setLabelText(f"バックテスト実行中... ({current}/{total})")

    def _on_stock_completed(self, code: str, result: dict):
        """1銘柄のバックテスト完了"""
        self.logger.info(f"バックテスト完了: {code}")

        # 結果をDBに保存
        try:
            rights_month = result.get('rights_month', 0)
            all_results = result.get('all_results', [])

            # all_resultsの各日数の結果を保存
            for day_result in all_results:
                # Calculatorは'days_before'を使用
                buy_days_before = day_result.get('days_before', day_result.get('buy_days_before', 0))
                self.db.insert_simulation_cache(
                    code=code,
                    rights_month=rights_month,
                    buy_days_before=buy_days_before,
                    win_count=day_result.get('win_count', 0),
                    lose_count=day_result.get('lose_count', 0),
                    win_rate=day_result.get('win_rate', 0.0),
                    expected_return=day_result.get('expected_return', 0.0),
                    avg_win_return=day_result.get('avg_win_return', 0.0),
                    max_win_return=day_result.get('max_win_return', 0.0),
                    avg_lose_return=day_result.get('avg_lose_return', 0.0),
                    max_lose_return=day_result.get('max_lose_return', 0.0)
                )
        except Exception as e:
            self.logger.error(f"バックテスト結果の保存エラー: {code} - {e}")

    def _on_batch_completed(self, results: list):
        """バッチ処理完了"""
        if hasattr(self, 'batch_progress') and self.batch_progress:
            self.batch_progress.close()

        success_count = len(results)
        QMessageBox.information(
            self, "完了",
            f"一括バックテストが完了しました。\n成功: {success_count}件"
        )
        self.statusBar().showMessage(f"一括バックテスト完了: {success_count}件成功")

        # リストを更新
        self.load_initial_data()

    def _on_batch_error(self, code: str, error: str):
        """バッチ処理エラー"""
        self.logger.error(f"バッチエラー: {code} - {error}")

    def _on_batch_canceled(self):
        """バッチ処理キャンセル"""
        if hasattr(self, 'batch_worker') and self.batch_worker:
            self.batch_worker.stop()
        self.statusBar().showMessage("一括バックテストがキャンセルされました")

    def _load_settings(self) -> Dict[str, Any]:
        """設定を読み込む"""
        try:
            config_path = Path(__file__).parent.parent.parent / "config" / "settings.json"

            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # デフォルト設定
                return self._get_default_settings()

        except Exception as e:
            self.logger.error(f"設定読み込みエラー: {e}")
            return self._get_default_settings()

    def _get_default_settings(self) -> Dict[str, Any]:
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

    def _get_period_value(self, period: str) -> int:
        """期間文字列を数値に変換（比較用）"""
        period_map = {
            '1y': 1, '3y': 3, '5y': 5, '10y': 10,
            '15y': 15, '20y': 20, 'max': 999
        }
        return period_map.get(period, 10)

    def _clear_simulation_cache(self):
        """シミュレーションキャッシュを全削除"""
        try:
            conn = self.db.connect()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM simulation_cache")
            conn.commit()
            conn.close()
            self.logger.info("シミュレーションキャッシュを全削除しました")

            # UIをリフレッシュ
            self.load_initial_data()

        except Exception as e:
            self.logger.error(f"キャッシュクリアエラー: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "エラー",
                f"キャッシュのクリアに失敗しました:\n{str(e)}"
            )

    def closeEvent(self, event):
        """ウィンドウを閉じる時の処理"""
        # スレッドベースのワーカーは daemon=True なので自動終了
        # ただしログは残す
        if self.current_analysis_worker and self.current_analysis_worker.isRunning():
            self.logger.info("分析ワーカーが実行中です")

        if self.current_trade_details_worker and self.current_trade_details_worker.isRunning():
            self.logger.info("トレード詳細ワーカーが実行中です")

        if hasattr(self, 'batch_worker') and self.batch_worker and self.batch_worker.isRunning():
            self.batch_worker.stop()
            self.logger.info("バッチワーカーを停止しました")

        self.logger.info("アプリケーションを終了します")
        event.accept()
