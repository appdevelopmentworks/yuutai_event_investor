"""
Desktop Notifier Module
デスクトップ通知モジュール

Author: Yuutai Event Investor Team
Date: 2024-11-07
"""

import logging
import platform
from typing import Optional
from pathlib import Path


class DesktopNotifier:
    """
    マルチプラットフォーム対応のデスクトップ通知クラス
    Windows, macOS, Linux に対応
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.system = platform.system()
        self.logger.info(f"DesktopNotifier initialized for {self.system}")

    def send_notification(
        self,
        title: str,
        message: str,
        icon_path: Optional[str] = None,
        duration: int = 5000
    ) -> bool:
        """
        デスクトップ通知を送信

        Args:
            title: 通知のタイトル
            message: 通知メッセージ
            icon_path: アイコンファイルのパス（オプション）
            duration: 表示時間（ミリ秒）

        Returns:
            bool: 成功した場合True
        """
        try:
            if self.system == "Windows":
                return self._send_windows_notification(title, message, icon_path, duration)
            elif self.system == "Darwin":  # macOS
                return self._send_macos_notification(title, message, icon_path)
            elif self.system == "Linux":
                return self._send_linux_notification(title, message, icon_path, duration)
            else:
                self.logger.warning(f"Unsupported platform: {self.system}")
                return False

        except Exception as e:
            self.logger.error(f"通知送信エラー: {e}", exc_info=True)
            return False

    def _send_windows_notification(
        self,
        title: str,
        message: str,
        icon_path: Optional[str],
        duration: int
    ) -> bool:
        """
        Windows用の通知を送信（winotifyを使用）

        Args:
            title: タイトル
            message: メッセージ
            icon_path: アイコンパス
            duration: 表示時間

        Returns:
            bool: 成功した場合True
        """
        try:
            from winotify import Notification, audio

            toast = Notification(
                app_id="Yuutai Event Investor",
                title=title,
                msg=message,
                duration=duration // 1000  # winotifyは秒単位
            )

            # アイコンを設定
            if icon_path and Path(icon_path).exists():
                toast.set_icon(icon_path)

            # サウンドを設定
            toast.set_audio(audio.Default, loop=False)

            # 通知を表示
            toast.show()

            self.logger.info(f"Windows通知を送信: {title}")
            return True

        except ImportError:
            self.logger.warning("winotifyがインストールされていません。通知機能を使用するには 'pip install winotify' を実行してください。")
            return False
        except Exception as e:
            self.logger.error(f"Windows通知エラー: {e}", exc_info=True)
            return False

    def _send_macos_notification(
        self,
        title: str,
        message: str,
        icon_path: Optional[str]
    ) -> bool:
        """
        macOS用の通知を送信（pync または osascript を使用）

        Args:
            title: タイトル
            message: メッセージ
            icon_path: アイコンパス

        Returns:
            bool: 成功した場合True
        """
        try:
            # まずpyncを試す
            try:
                import pync
                pync.notify(
                    message,
                    title=title,
                    appIcon=icon_path if icon_path else None
                )
                self.logger.info(f"macOS通知を送信（pync）: {title}")
                return True

            except ImportError:
                # pyncがない場合はosascriptを使用
                import subprocess

                script = f'display notification "{message}" with title "{title}"'
                subprocess.run(
                    ['osascript', '-e', script],
                    check=True,
                    capture_output=True
                )
                self.logger.info(f"macOS通知を送信（osascript）: {title}")
                return True

        except Exception as e:
            self.logger.error(f"macOS通知エラー: {e}", exc_info=True)
            return False

    def _send_linux_notification(
        self,
        title: str,
        message: str,
        icon_path: Optional[str],
        duration: int
    ) -> bool:
        """
        Linux用の通知を送信（notify2 または notify-send を使用）

        Args:
            title: タイトル
            message: メッセージ
            icon_path: アイコンパス
            duration: 表示時間

        Returns:
            bool: 成功した場合True
        """
        try:
            # まずnotify2を試す
            try:
                import notify2

                notify2.init("Yuutai Event Investor")

                notification = notify2.Notification(
                    title,
                    message,
                    icon_path if icon_path else "dialog-information"
                )

                notification.set_timeout(duration)
                notification.show()

                self.logger.info(f"Linux通知を送信（notify2）: {title}")
                return True

            except ImportError:
                # notify2がない場合はnotify-sendを使用
                import subprocess

                cmd = ['notify-send', title, message]

                if icon_path:
                    cmd.extend(['-i', icon_path])

                cmd.extend(['-t', str(duration)])

                subprocess.run(cmd, check=True, capture_output=True)

                self.logger.info(f"Linux通知を送信（notify-send）: {title}")
                return True

        except Exception as e:
            self.logger.error(f"Linux通知エラー: {e}", exc_info=True)
            return False

    def test_notification(self) -> bool:
        """
        テスト通知を送信

        Returns:
            bool: 成功した場合True
        """
        return self.send_notification(
            title="Yuutai Event Investor",
            message="通知機能が正常に動作しています。",
            duration=3000
        )


# Qt6のシステムトレイ通知を使用するバージョン（フォールバック用）
class QtDesktopNotifier:
    """
    PySide6のQSystemTrayIconを使用した通知クラス
    プラットフォーム固有の通知ライブラリが使えない場合のフォールバック
    """

    def __init__(self, system_tray_icon=None):
        """
        Args:
            system_tray_icon: QSystemTrayIconインスタンス
        """
        self.logger = logging.getLogger(__name__)
        self.system_tray = system_tray_icon

    def send_notification(
        self,
        title: str,
        message: str,
        icon=None,
        duration: int = 5000
    ) -> bool:
        """
        Qt通知を送信

        Args:
            title: タイトル
            message: メッセージ
            icon: QIconインスタンス
            duration: 表示時間（ミリ秒）

        Returns:
            bool: 成功した場合True
        """
        try:
            if self.system_tray is None:
                self.logger.warning("システムトレイアイコンが設定されていません")
                return False

            from PySide6.QtWidgets import QSystemTrayIcon

            self.system_tray.showMessage(
                title,
                message,
                icon if icon else QSystemTrayIcon.Information,
                duration
            )

            self.logger.info(f"Qt通知を送信: {title}")
            return True

        except Exception as e:
            self.logger.error(f"Qt通知エラー: {e}", exc_info=True)
            return False
