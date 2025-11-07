"""
96ut.com Scraper Module
96ut.com から株主優待データをスクレイピング

Author: Yuutai Event Investor Team
Date: 2025-11-07
Version: 1.0.0
"""

from typing import List, Dict, Any, Optional
import re
from datetime import datetime
from .base_scraper import BaseScraper


class Scraper96ut(BaseScraper):
    """96ut.com 専用スクレイパー"""

    def get_site_name(self) -> str:
        return "96ut"

    def get_base_url(self) -> str:
        return "https://96ut.com"

    def scrape_stocks(self, term: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
        """
        株主優待銘柄データをスクレイピング

        Args:
            term: 権利確定月（例: "3月末", "12月末"）
            **kwargs: その他のパラメータ

        Returns:
            List[Dict]: 銘柄データのリスト
        """
        stocks = []

        try:
            self.logger.info(f"96ut.com からデータ取得開始（term={term}）")

            # 権利確定月でフィルター
            if term:
                url = f"{self.get_base_url()}/stock/list.php?term={term}&key=y"
            else:
                # 全データ取得（1月～12月まで順番に）
                for month in range(1, 13):
                    month_term = f"{month}月末"
                    month_stocks = self._scrape_by_term(month_term)
                    stocks.extend(month_stocks)
                return stocks

            # 指定月のデータを取得
            stocks = self._scrape_by_term(term)

            self.logger.info(f"96ut.com からデータ取得完了: {len(stocks)}件")
            return stocks

        except Exception as e:
            self.logger.error(f"96ut.com スクレイピングエラー: {e}", exc_info=True)
            return []

    def _scrape_by_term(self, term: str) -> List[Dict[str, Any]]:
        """
        指定された権利確定月のデータをスクレイピング

        Args:
            term: 権利確定月（例: "3月末"）

        Returns:
            List[Dict]: 銘柄データのリスト
        """
        stocks = []
        url = f"{self.get_base_url()}/stock/list.php?term={term}&key=y"

        soup = self.fetch_page(url)
        if not soup:
            return stocks

        # テーブル行を取得（複数セレクターを試行）
        rows = self.try_selectors(soup, "stock_rows", method='select')
        if not rows:
            # フォールバック：一般的なテーブル構造を試行
            rows = soup.select("table.footable tbody tr")

        if not rows:
            self.logger.warning(f"テーブル行が見つかりません: {url}")
            return stocks

        self.logger.info(f"テーブル行数: {len(rows)}")

        # 各行からデータを抽出
        for row in rows:
            try:
                stock = self._parse_row(row, term)
                if stock and self.validate_stock_data(stock):
                    stocks.append(stock)
            except Exception as e:
                self.logger.debug(f"行のパースエラー: {e}")
                continue

        return stocks

    def _parse_row(self, row, term: str) -> Optional[Dict[str, Any]]:
        """
        テーブル行から銘柄データを抽出

        Args:
            row: BeautifulSoupのTRエレメント
            term: 権利確定月

        Returns:
            Dict: 銘柄データ、抽出できない場合はNone
        """
        try:
            cells = row.find_all('td')
            if len(cells) < 2:
                return None

            # 証券コード（最初の列）
            code_text = self.clean_text(cells[0].get_text())
            code = re.search(r'\d{4}', code_text)
            if not code:
                return None
            code = code.group()

            # 銘柄名（2列目）
            name = self.clean_text(cells[1].get_text())
            if not name:
                return None

            # 権利確定月を抽出（例: "3月末" -> 3）
            month_match = re.search(r'(\d+)月', term)
            if not month_match:
                return None
            rights_month = int(month_match.group(1))

            # 権利確定日を推定（月末最終営業日の2営業日前と仮定）
            # 実際の日付は後で手動調整が必要
            current_year = datetime.now().year
            if rights_month == 12:
                rights_date = f"{current_year}-12-28"  # 12月は28日と仮定
            else:
                # 月末日を計算
                if rights_month in [1, 3, 5, 7, 8, 10]:
                    last_day = 31
                elif rights_month in [4, 6, 9, 11]:
                    last_day = 30
                else:  # 2月
                    last_day = 28
                rights_date = f"{current_year}-{rights_month:02d}-{last_day}"

            stock = {
                'code': code,
                'name': name,
                'rights_month': rights_month,
                'rights_date': rights_date,
                'yuutai_genre': '',  # 96ut.com には優待ジャンル情報がない場合が多い
                'yuutai_content': '',  # 96ut.com には優待内容が詳細ページにある
                'min_investment': 0  # 96ut.com には最低投資金額情報がない
            }

            return stock

        except Exception as e:
            self.logger.debug(f"行パースエラー: {e}")
            return None
