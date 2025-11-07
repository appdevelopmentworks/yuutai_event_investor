"""
Yutai.net-ir.ne.jp Scraper Module
yutai.net-ir.ne.jp から株主優待データをスクレイピング

Author: Yuutai Event Investor Team
Date: 2025-11-07
Version: 1.0.0
"""

from typing import List, Dict, Any, Optional
import re
from datetime import datetime
from .base_scraper import BaseScraper


class ScraperYutaiNet(BaseScraper):
    """yutai.net-ir.ne.jp 専用スクレイパー"""

    def get_site_name(self) -> str:
        return "yutai_net"

    def get_base_url(self) -> str:
        return "https://yutai.net-ir.ne.jp"

    def scrape_stocks(self, month: Optional[int] = None, **kwargs) -> List[Dict[str, Any]]:
        """
        株主優待銘柄データをスクレイピング

        Args:
            month: 権利確定月（1-12）
            **kwargs: その他のパラメータ

        Returns:
            List[Dict]: 銘柄データのリスト
        """
        stocks = []

        try:
            self.logger.info(f"yutai.net-ir.ne.jp からデータ取得開始（month={month}）")

            if month:
                # 指定月のデータを取得
                stocks = self._scrape_by_month(month)
            else:
                # 全月のデータを取得
                for m in range(1, 13):
                    month_stocks = self._scrape_by_month(m)
                    stocks.extend(month_stocks)

            self.logger.info(f"yutai.net-ir.ne.jp からデータ取得完了: {len(stocks)}件")
            return stocks

        except Exception as e:
            self.logger.error(f"yutai.net-ir.ne.jp スクレイピングエラー: {e}", exc_info=True)
            return []

    def _scrape_by_month(self, month: int) -> List[Dict[str, Any]]:
        """
        指定された月のデータをスクレイピング

        Args:
            month: 権利確定月（1-12）

        Returns:
            List[Dict]: 銘柄データのリスト
        """
        stocks = []

        # 検索URLを構築（search_ext_col_07が権利確定月のパラメータと推定）
        url = f"{self.get_base_url()}/search/?search_ext_col_07[]={month}"

        soup = self.fetch_page(url)
        if not soup:
            return stocks

        # テーブル行を取得（複数セレクターを試行）
        rows = self.try_selectors(soup, "stock_rows", method='select')
        if not rows:
            # フォールバック：一般的なテーブル構造を試行
            rows = soup.select("table tr.data-row")
            if not rows:
                rows = soup.select("table tbody tr")

        if not rows:
            self.logger.warning(f"テーブル行が見つかりません: {url}")
            return stocks

        self.logger.info(f"テーブル行数: {len(rows)}")

        # 各行からデータを抽出
        for row in rows:
            try:
                stock = self._parse_row(row, month)
                if stock and self.validate_stock_data(stock):
                    stocks.append(stock)
            except Exception as e:
                self.logger.debug(f"行のパースエラー: {e}")
                continue

        return stocks

    def _parse_row(self, row, month: int) -> Optional[Dict[str, Any]]:
        """
        テーブル行から銘柄データを抽出

        Args:
            row: BeautifulSoupのTRエレメント
            month: 権利確定月

        Returns:
            Dict: 銘柄データ、抽出できない場合はNone
        """
        try:
            cells = row.find_all('td')
            if len(cells) < 2:
                return None

            # 証券コード（1列目）
            code_cell = cells[0]
            code_link = code_cell.find('a')
            if code_link:
                code_text = self.clean_text(code_link.get_text())
            else:
                code_text = self.clean_text(code_cell.get_text())

            code = re.search(r'\d{4}', code_text)
            if not code:
                return None
            code = code.group()

            # 銘柄名（2列目）
            name_cell = cells[1]
            name_link = name_cell.find('a')
            if name_link:
                name = self.clean_text(name_link.get_text())
            else:
                name = self.clean_text(name_cell.get_text())

            if not name:
                return None

            # 権利確定日（3列目、存在する場合）
            rights_date = None
            if len(cells) >= 3:
                date_text = self.clean_text(cells[2].get_text())
                # 日付フォーマット：MM/DD または YYYY-MM-DD
                date_match = re.search(r'(\d{1,2})[/-](\d{1,2})', date_text)
                if date_match:
                    m, d = date_match.groups()
                    current_year = datetime.now().year
                    rights_date = f"{current_year}-{int(m):02d}-{int(d):02d}"

            # 権利確定日がない場合は月末を仮定
            if not rights_date:
                current_year = datetime.now().year
                if month == 12:
                    last_day = 31
                elif month in [1, 3, 5, 7, 8, 10]:
                    last_day = 31
                elif month in [4, 6, 9, 11]:
                    last_day = 30
                else:  # 2月
                    last_day = 28
                rights_date = f"{current_year}-{month:02d}-{last_day}"

            # 優待内容（4列目、存在する場合）
            yuutai_content = ''
            if len(cells) >= 4:
                yuutai_content = self.clean_text(cells[3].get_text())

            # 最低投資金額（5列目、存在する場合）
            min_investment = 0
            if len(cells) >= 5:
                inv_text = self.clean_text(cells[4].get_text())
                # 数値を抽出（カンマ区切りに対応）
                inv_match = re.search(r'([\d,]+)', inv_text)
                if inv_match:
                    try:
                        min_investment = int(inv_match.group(1).replace(',', ''))
                    except ValueError:
                        pass

            stock = {
                'code': code,
                'name': name,
                'rights_month': month,
                'rights_date': rights_date,
                'yuutai_genre': '',  # yutai.net にはジャンル情報がある場合とない場合がある
                'yuutai_content': yuutai_content,
                'min_investment': min_investment
            }

            return stock

        except Exception as e:
            self.logger.debug(f"行パースエラー: {e}")
            return None
