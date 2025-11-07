"""
Main Window Module
メインウィンドウ

Author: Yuutai Event Investor Team
Date: 2024-11-07
Version: 1.0.0
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSplitter, QStatusBar
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import logging


class MainWindow(QMainWindow):
    """メインウィンドウクラス"""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # ウィンドウ設定
        self.setWindowTitle("Yuutai Event Investor - 株主優待イベント投資分析ツール")
        self.setGeometry(100, 100, 1280, 800)
        
        # UI初期化
        self.init_ui()
        
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
        # コンテンツエリア（スプリッター）
        # ========================================
        splitter = QSplitter(Qt.Horizontal)
        
        # 左サイドバー（銘柄リスト）
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # 右側（詳細パネル）
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # スプリッターの初期サイズ比率を設定
        splitter.setStretchFactor(0, 1)  # 左: 1
        splitter.setStretchFactor(1, 2)  # 右: 2
        
        main_layout.addWidget(splitter)
        
        # ========================================
        # ステータスバー
        # ========================================
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("準備完了")
    
    def create_header(self) -> QWidget:
        """ヘッダーを作成"""
        header = QWidget()
        header.setFixedHeight(60)
        header.setStyleSheet("""
            QWidget {
                background-color: #2D2D2D;
                border-bottom: 1px solid #404040;
            }
        """)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 10, 20, 10)
        
        # タイトル
        title = QLabel("📈 Yuutai Event Investor")
        title_font = QFont("Meiryo", 16, QFont.Bold)
        title.setFont(title_font)
        title.setStyleSheet("color: #1E90FF;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # 更新ボタン
        refresh_btn = QPushButton("🔄 データ更新")
        refresh_btn.setFixedSize(120, 35)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #4682B4;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 15px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #1E90FF;
            }
        """)
        refresh_btn.clicked.connect(self.on_refresh_data)
        layout.addWidget(refresh_btn)
        
        # 設定ボタン
        settings_btn = QPushButton("⚙ 設定")
        settings_btn.setFixedSize(80, 35)
        settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #3A3A3A;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 15px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #404040;
            }
        """)
        settings_btn.clicked.connect(self.on_settings)
        layout.addWidget(settings_btn)
        
        # テーマ切替ボタン
        theme_btn = QPushButton("🌙")
        theme_btn.setFixedSize(35, 35)
        theme_btn.setStyleSheet("""
            QPushButton {
                background-color: #3A3A3A;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #404040;
            }
        """)
        theme_btn.clicked.connect(self.on_toggle_theme)
        layout.addWidget(theme_btn)
        
        return header
    
    def create_left_panel(self) -> QWidget:
        """左パネル（銘柄リスト）を作成"""
        panel = QWidget()
        panel.setStyleSheet("""
            QWidget {
                background-color: #1E1E1E;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # タイトル
        title = QLabel("📊 銘柄リスト")
        title_font = QFont("Meiryo", 14, QFont.Bold)
        title.setFont(title_font)
        title.setStyleSheet("color: #E0E0E0; padding: 10px;")
        layout.addWidget(title)
        
        # プレースホルダー
        placeholder = QLabel("銘柄データを読み込み中...")
        placeholder.setStyleSheet("color: #B0B0B0; padding: 20px;")
        placeholder.setAlignment(Qt.AlignCenter)
        layout.addWidget(placeholder)
        
        layout.addStretch()
        
        return panel
    
    def create_right_panel(self) -> QWidget:
        """右パネル（詳細表示）を作成"""
        panel = QWidget()
        panel.setStyleSheet("""
            QWidget {
                background-color: #1E1E1E;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # タイトル
        title = QLabel("📈 詳細分析")
        title_font = QFont("Meiryo", 14, QFont.Bold)
        title.setFont(title_font)
        title.setStyleSheet("color: #E0E0E0; padding: 10px;")
        layout.addWidget(title)
        
        # 銘柄情報カード（プレースホルダー）
        card = QWidget()
        card.setFixedHeight(120)
        card.setStyleSheet("""
            QWidget {
                background-color: #2D2D2D;
                border-radius: 8px;
                border: 1px solid #404040;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 15, 20, 15)
        
        card_title = QLabel("銘柄を選択してください")
        card_title.setFont(QFont("Meiryo", 12, QFont.Bold))
        card_title.setStyleSheet("color: #E0E0E0;")
        card_layout.addWidget(card_title)
        
        card_desc = QLabel("左側の銘柄リストから分析したい銘柄を選択してください")
        card_desc.setStyleSheet("color: #B0B0B0;")
        card_layout.addWidget(card_desc)
        
        layout.addWidget(card)
        
        # チャートエリア（プレースホルダー）
        chart_area = QLabel("📊 チャート表示エリア")
        chart_area.setStyleSheet("""
            QLabel {
                background-color: #2D2D2D;
                border-radius: 8px;
                border: 1px solid #404040;
                color: #B0B0B0;
                padding: 40px;
            }
        """)
        chart_area.setAlignment(Qt.AlignCenter)
        layout.addWidget(chart_area)
        
        return panel
    
    # ========================================
    # イベントハンドラー
    # ========================================
    
    def on_refresh_data(self):
        """データ更新ボタンクリック時の処理"""
        self.status_bar.showMessage("データを更新中...")
        self.logger.info("データ更新を開始")
        # TODO: スクレイピング処理を実装
        self.status_bar.showMessage("データ更新完了", 3000)
    
    def on_settings(self):
        """設定ボタンクリック時の処理"""
        self.logger.info("設定画面を開く")
        # TODO: 設定ダイアログを実装
        self.status_bar.showMessage("設定機能は未実装です", 3000)
    
    def on_toggle_theme(self):
        """テーマ切替ボタンクリック時の処理"""
        self.logger.info("テーマを切り替え")
        # TODO: テーマ切替を実装
        self.status_bar.showMessage("テーマ切替機能は未実装です", 3000)
