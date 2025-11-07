"""
Notification Module
通知機能モジュール

Author: Yuutai Event Investor Team
Date: 2024-11-07
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

from ..core.database import DatabaseManager


class NotificationManager:
    """通知を管理するクラス"""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """
        Args:
            db_manager: DatabaseManagerインスタンス
        """
        self.logger = logging.getLogger(__name__)
        self.db = db_manager or DatabaseManager()

    def create_notification(self, code: str, target_date: str) -> bool:
        """
        通知を作成

        Args:
            code: 銘柄コード
            target_date: 通知対象日（YYYY-MM-DD形式）

        Returns:
            bool: 成功した場合True
        """
        try:
            return self.db.create_notification(code, target_date)

        except Exception as e:
            self.logger.error(f"通知作成エラー: {e}")
            return False

    def get_pending_notifications(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """
        今後の通知を取得

        Args:
            days_ahead: 何日先まで取得するか

        Returns:
            List[Dict]: 通知リスト
        """
        try:
            today = datetime.now().date()
            end_date = today + timedelta(days=days_ahead)

            notifications = self.db.get_pending_notifications(end_date.isoformat())

            return notifications

        except Exception as e:
            self.logger.error(f"通知取得エラー: {e}")
            return []

    def get_today_notifications(self) -> List[Dict[str, Any]]:
        """
        今日の通知を取得

        Returns:
            List[Dict]: 今日の通知リスト
        """
        try:
            today = datetime.now().date().isoformat()
            # get_pending_notificationsを使用して今日の通知を取得
            all_notifications = self.db.get_pending_notifications(today)
            # 今日の日付のものだけフィルタ
            return [n for n in all_notifications if n.get('target_date') == today]

        except Exception as e:
            self.logger.error(f"今日の通知取得エラー: {e}")
            return []

    def mark_as_notified(self, notification_id: int) -> bool:
        """
        通知済みとしてマーク

        Args:
            notification_id: 通知ID

        Returns:
            bool: 成功した場合True
        """
        try:
            return self.db.mark_notification_as_sent(notification_id)

        except Exception as e:
            self.logger.error(f"通知マークエラー: {e}")
            return False

    def delete_notification(self, notification_id: int) -> bool:
        """
        通知を削除

        Args:
            notification_id: 通知ID

        Returns:
            bool: 成功した場合True
        """
        try:
            return self.db.delete_notification(notification_id)

        except Exception as e:
            self.logger.error(f"通知削除エラー: {e}")
            return False

    def auto_create_notifications_for_watchlist(self, days_before: int = 7) -> int:
        """
        ウォッチリストの銘柄に対して自動的に通知を作成

        Args:
            days_before: 最適買入日の何日前に通知するか

        Returns:
            int: 作成した通知の数
        """
        try:
            # ウォッチリストを取得
            watchlist = self.db.get_watchlist()

            created_count = 0

            for item in watchlist:
                code = item['code']
                stock = self.db.get_stock(code)

                if not stock or not stock.get('rights_date'):
                    continue

                # 権利確定日から最適買入日を計算（仮に30日前とする）
                # 実際にはシミュレーション結果から取得すべき
                rights_date = datetime.fromisoformat(stock['rights_date'])
                optimal_buy_date = rights_date - timedelta(days=30)

                # 通知日を設定（最適買入日の days_before 日前）
                notification_date = optimal_buy_date - timedelta(days=days_before)

                # 過去の日付はスキップ
                if notification_date.date() < datetime.now().date():
                    continue

                # 通知を作成
                if self.create_notification(code, notification_date.date().isoformat()):
                    created_count += 1
                    self.logger.info(f"通知作成: {code} - {notification_date.date()}")

            self.logger.info(f"{created_count}件の通知を作成しました")
            return created_count

        except Exception as e:
            self.logger.error(f"自動通知作成エラー: {e}", exc_info=True)
            return 0

    def check_and_show_notifications(self) -> List[str]:
        """
        通知をチェックして表示すべきメッセージを返す

        Returns:
            List[str]: 通知メッセージのリスト
        """
        try:
            today_notifications = self.get_today_notifications()

            messages = []

            for notif in today_notifications:
                if notif.get('notified'):
                    continue  # 既に通知済み

                code = notif['code']
                stock = self.db.get_stock(code)

                if stock:
                    message = f"🔔 {stock['name']}({code})\n最適買入日が近づいています！"
                    messages.append(message)

                    # 通知済みとしてマーク
                    self.mark_as_notified(notif['id'])

            return messages

        except Exception as e:
            self.logger.error(f"通知チェックエラー: {e}")
            return []

    def get_notification_summary(self) -> Dict[str, int]:
        """
        通知の概要を取得

        Returns:
            Dict: 通知の概要
        """
        try:
            today_count = len(self.get_today_notifications())
            week_count = len(self.get_pending_notifications(days_ahead=7))
            month_count = len(self.get_pending_notifications(days_ahead=30))

            return {
                'today': today_count,
                'week': week_count,
                'month': month_count
            }

        except Exception as e:
            self.logger.error(f"通知概要取得エラー: {e}")
            return {'today': 0, 'week': 0, 'month': 0}


class NotificationDialog:
    """通知ダイアログ（将来的に実装）"""

    def __init__(self):
        pass

    def show_notification(self, message: str):
        """
        通知を表示

        Args:
            message: 通知メッセージ
        """
        # TODO: PySide6のQMessageBoxやトースト通知を実装
        print(f"[通知] {message}")
