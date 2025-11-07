"""
Notification Worker Module
通知チェック用ワーカースレッド

Author: Yuutai Event Investor Team
Date: 2024-11-07
"""

import logging
from datetime import datetime
from typing import Optional
from PySide6.QtCore import QThread, Signal, QTimer
from .notification import NotificationManager
from .desktop_notifier import DesktopNotifier, QtDesktopNotifier


class NotificationWorker(QThread):
    """
    バックグラウンドで通知をチェックするワーカースレッド
    """

    # シグナル定義
    notification_found = Signal(str, str)  # タイトル、メッセージ
    error_occurred = Signal(str)  # エラーメッセージ

    def __init__(
        self,
        check_interval_minutes: int = 60,
        system_tray_icon=None
    ):
        """
        Args:
            check_interval_minutes: チェック間隔（分）
            system_tray_icon: QSystemTrayIconインスタンス（Qtフォールバック用）
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.check_interval = check_interval_minutes * 60 * 1000  # ミリ秒に変換
        self.running = False

        # 通知マネージャーとnotifierを初期化
        self.notification_manager = NotificationManager()
        self.desktop_notifier = DesktopNotifier()
        self.qt_notifier = QtDesktopNotifier(system_tray_icon)

        # タイマーを作成
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_notifications)

    def run(self):
        """スレッドのメイン処理"""
        self.logger.info(f"通知チェックスレッドを開始（間隔: {self.check_interval/1000/60}分）")
        self.running = True

        # 初回チェックを実行
        self.check_notifications()

        # タイマーを開始
        self.timer.start(self.check_interval)

        # イベントループを開始
        self.exec()

    def check_notifications(self):
        """通知をチェックして送信"""
        if not self.running:
            return

        try:
            self.logger.info("通知チェック実行中...")

            # 今日の通知を取得
            messages = self.notification_manager.check_and_show_notifications()

            # 通知がある場合は送信
            for message in messages:
                self.logger.info(f"通知を送信: {message}")

                # デスクトップ通知を送信
                success = self.desktop_notifier.send_notification(
                    title="買いタイミング通知",
                    message=message,
                    duration=8000
                )

                # デスクトップ通知が失敗した場合はQt通知を試す
                if not success:
                    self.qt_notifier.send_notification(
                        title="買いタイミング通知",
                        message=message,
                        duration=8000
                    )

                # シグナルを発信
                self.notification_found.emit("買いタイミング通知", message)

            if messages:
                self.logger.info(f"{len(messages)}件の通知を送信しました")
            else:
                self.logger.debug("送信すべき通知はありません")

        except Exception as e:
            error_msg = f"通知チェックエラー: {e}"
            self.logger.error(error_msg, exc_info=True)
            self.error_occurred.emit(error_msg)

    def stop(self):
        """スレッドを停止"""
        self.logger.info("通知チェックスレッドを停止中...")
        self.running = False
        self.timer.stop()
        self.quit()
        self.wait()
        self.logger.info("通知チェックスレッドを停止しました")

    def force_check(self):
        """即座に通知チェックを実行"""
        self.logger.info("手動通知チェックを実行")
        self.check_notifications()

    def set_interval(self, minutes: int):
        """
        チェック間隔を変更

        Args:
            minutes: チェック間隔（分）
        """
        self.check_interval = minutes * 60 * 1000
        if self.timer.isActive():
            self.timer.setInterval(self.check_interval)
        self.logger.info(f"通知チェック間隔を{minutes}分に変更しました")


class NotificationScheduler:
    """
    通知スケジューリングを管理するクラス
    特定の時刻に通知をチェックする機能を提供
    """

    def __init__(self, notification_manager: Optional[NotificationManager] = None):
        """
        Args:
            notification_manager: NotificationManagerインスタンス
        """
        self.logger = logging.getLogger(__name__)
        self.notification_manager = notification_manager or NotificationManager()
        self.desktop_notifier = DesktopNotifier()

        # スケジュール設定（デフォルト: 毎日9:00と15:00）
        self.scheduled_times = ["09:00", "15:00"]
        self.last_check_date = None

        # タイマーを作成（1分ごとにチェック）
        self.timer = QTimer()
        self.timer.timeout.connect(self._check_schedule)
        self.timer.start(60000)  # 1分 = 60,000ミリ秒

    def _check_schedule(self):
        """スケジュールをチェックして該当時刻であれば通知を送信"""
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        current_date = now.date()

        # 今日既にチェック済みの場合はスキップ
        if current_date == self.last_check_date:
            return

        # スケジュールされた時刻かどうかチェック
        if current_time in self.scheduled_times:
            self.logger.info(f"スケジュール実行: {current_time}")
            self._send_scheduled_notifications()
            self.last_check_date = current_date

    def _send_scheduled_notifications(self):
        """スケジュールされた通知を送信"""
        try:
            # 今後7日間の通知を取得
            upcoming_notifications = self.notification_manager.get_pending_notifications(days_ahead=7)

            if not upcoming_notifications:
                self.logger.info("送信すべき通知はありません")
                return

            # サマリーメッセージを作成
            summary = f"今後7日間で {len(upcoming_notifications)} 件の買いタイミングがあります。"

            # 詳細メッセージを作成（最大5件まで）
            details = []
            for i, notif in enumerate(upcoming_notifications[:5]):
                target_date = notif.get('target_date', '不明')
                code = notif.get('code', '不明')
                details.append(f"{target_date}: {code}")

            if len(upcoming_notifications) > 5:
                details.append(f"... 他{len(upcoming_notifications) - 5}件")

            message = summary + "\n" + "\n".join(details)

            # 通知を送信
            self.desktop_notifier.send_notification(
                title="Yuutai Event Investor - 今後の買いタイミング",
                message=message,
                duration=10000
            )

            self.logger.info(f"スケジュール通知を送信: {len(upcoming_notifications)}件")

        except Exception as e:
            self.logger.error(f"スケジュール通知エラー: {e}", exc_info=True)

    def set_schedule(self, times: list[str]):
        """
        スケジュール時刻を設定

        Args:
            times: 時刻のリスト（"HH:MM"形式）
        """
        self.scheduled_times = times
        self.logger.info(f"通知スケジュールを設定: {times}")

    def stop(self):
        """スケジューラーを停止"""
        self.timer.stop()
        self.logger.info("通知スケジューラーを停止しました")
