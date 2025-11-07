"""
Keyboard Shortcuts Module
キーボードショートカット管理モジュール

Author: Yuutai Event Investor Team
Date: 2024-11-07
"""

import logging
from typing import Dict, Callable, Optional
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt


class ShortcutManager:
    """
    キーボードショートカットを管理するクラス
    """

    def __init__(self, parent_widget: QWidget):
        """
        Args:
            parent_widget: ショートカットを設定する親ウィジェット
        """
        self.logger = logging.getLogger(__name__)
        self.parent = parent_widget
        self.shortcuts: Dict[str, QShortcut] = {}

    def register_shortcut(
        self,
        key_sequence: str,
        callback: Callable,
        name: str,
        description: str = ""
    ) -> bool:
        """
        ショートカットを登録

        Args:
            key_sequence: キーシーケンス（例: "Ctrl+S", "F5"）
            callback: 呼び出すコールバック関数
            name: ショートカット名
            description: 説明

        Returns:
            bool: 成功した場合True
        """
        try:
            shortcut = QShortcut(QKeySequence(key_sequence), self.parent)
            shortcut.activated.connect(callback)

            self.shortcuts[name] = {
                'shortcut': shortcut,
                'key_sequence': key_sequence,
                'callback': callback,
                'description': description
            }

            self.logger.info(f"ショートカット登録: {name} ({key_sequence})")
            return True

        except Exception as e:
            self.logger.error(f"ショートカット登録エラー: {name} - {e}")
            return False

    def unregister_shortcut(self, name: str) -> bool:
        """
        ショートカットを解除

        Args:
            name: ショートカット名

        Returns:
            bool: 成功した場合True
        """
        if name in self.shortcuts:
            self.shortcuts[name]['shortcut'].setEnabled(False)
            del self.shortcuts[name]
            self.logger.info(f"ショートカット解除: {name}")
            return True
        return False

    def enable_shortcut(self, name: str, enabled: bool = True):
        """
        ショートカットの有効/無効を切り替え

        Args:
            name: ショートカット名
            enabled: 有効にするか
        """
        if name in self.shortcuts:
            self.shortcuts[name]['shortcut'].setEnabled(enabled)

    def get_all_shortcuts(self) -> Dict[str, Dict]:
        """
        全ショートカット情報を取得

        Returns:
            Dict: ショートカット情報
        """
        return {
            name: {
                'key_sequence': info['key_sequence'],
                'description': info['description']
            }
            for name, info in self.shortcuts.items()
        }


class DefaultShortcuts:
    """
    デフォルトショートカット定義
    """

    # ファイル操作
    EXPORT_CSV = ("Ctrl+E", "CSV出力")
    EXPORT_PDF = ("Ctrl+P", "PDF出力")
    SAVE_SETTINGS = ("Ctrl+S", "設定保存")
    QUIT = ("Ctrl+Q", "アプリケーション終了")

    # 表示・ナビゲーション
    REFRESH = ("F5", "データ更新")
    TOGGLE_FULLSCREEN = ("F11", "フルスクリーン切替")
    FOCUS_SEARCH = ("Ctrl+F", "検索フォーカス")
    CLEAR_FILTERS = ("Ctrl+Shift+F", "フィルタークリア")

    # タブ切替
    TAB_ANALYSIS = ("Ctrl+1", "分析タブ")
    TAB_WATCHLIST = ("Ctrl+2", "ウォッチリストタブ")

    # ウォッチリスト操作
    ADD_TO_WATCHLIST = ("Ctrl+D", "ウォッチリストに追加")
    REMOVE_FROM_WATCHLIST = ("Ctrl+Shift+D", "ウォッチリストから削除")

    # その他
    SETTINGS = ("Ctrl+,", "設定画面")
    HELP = ("F1", "ヘルプ")
    ABOUT = ("Shift+F1", "バージョン情報")


def setup_default_shortcuts(parent_widget, callbacks: Dict[str, Callable]) -> ShortcutManager:
    """
    デフォルトショートカットをセットアップ

    Args:
        parent_widget: 親ウィジェット
        callbacks: コールバック関数の辞書
            キーはショートカット名、値はコールバック関数

    Returns:
        ShortcutManager: 設定済みのショートカットマネージャー
    """
    manager = ShortcutManager(parent_widget)

    # 定義リスト
    shortcut_definitions = [
        # ファイル操作
        ("export_csv", DefaultShortcuts.EXPORT_CSV),
        ("export_pdf", DefaultShortcuts.EXPORT_PDF),
        ("save_settings", DefaultShortcuts.SAVE_SETTINGS),
        ("quit", DefaultShortcuts.QUIT),

        # 表示・ナビゲーション
        ("refresh", DefaultShortcuts.REFRESH),
        ("toggle_fullscreen", DefaultShortcuts.TOGGLE_FULLSCREEN),
        ("focus_search", DefaultShortcuts.FOCUS_SEARCH),
        ("clear_filters", DefaultShortcuts.CLEAR_FILTERS),

        # タブ切替
        ("tab_analysis", DefaultShortcuts.TAB_ANALYSIS),
        ("tab_watchlist", DefaultShortcuts.TAB_WATCHLIST),

        # ウォッチリスト
        ("add_to_watchlist", DefaultShortcuts.ADD_TO_WATCHLIST),
        ("remove_from_watchlist", DefaultShortcuts.REMOVE_FROM_WATCHLIST),

        # その他
        ("settings", DefaultShortcuts.SETTINGS),
        ("help", DefaultShortcuts.HELP),
        ("about", DefaultShortcuts.ABOUT),
    ]

    # ショートカットを登録
    for name, (key_sequence, description) in shortcut_definitions:
        if name in callbacks:
            manager.register_shortcut(
                key_sequence=key_sequence,
                callback=callbacks[name],
                name=name,
                description=description
            )

    return manager


def create_shortcuts_help_text(manager: ShortcutManager) -> str:
    """
    ショートカットのヘルプテキストを生成

    Args:
        manager: ShortcutManager インスタンス

    Returns:
        str: ヘルプテキスト
    """
    shortcuts = manager.get_all_shortcuts()

    categories = {
        'ファイル操作': [
            'export_csv', 'export_pdf', 'save_settings', 'quit'
        ],
        '表示・ナビゲーション': [
            'refresh', 'toggle_fullscreen', 'focus_search', 'clear_filters'
        ],
        'タブ切替': [
            'tab_analysis', 'tab_watchlist'
        ],
        'ウォッチリスト': [
            'add_to_watchlist', 'remove_from_watchlist'
        ],
        'その他': [
            'settings', 'help', 'about'
        ]
    }

    help_text = "# キーボードショートカット一覧\n\n"

    for category, shortcut_names in categories.items():
        help_text += f"## {category}\n\n"
        for name in shortcut_names:
            if name in shortcuts:
                info = shortcuts[name]
                help_text += f"- **{info['key_sequence']}**: {info['description']}\n"
        help_text += "\n"

    return help_text
