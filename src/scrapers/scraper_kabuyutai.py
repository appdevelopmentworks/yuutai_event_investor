"""
Kabuyutai.com Scraper Module
kabuyutai.com から株主優待データをスクレイピング

Based on: interact/yuutai_fullyear_scraper_v5_2_sjis.py

Author: Yuutai Event Investor Team
Date: 2025-11-07
Version: 1.0.0
"""

from typing import List, Dict, Any, Optional
import re
import calendar
from datetime import date
from urllib.parse import urljoin
from .base_scraper import BaseScraper


class ScraperKabuyutai(BaseScraper):
    """kabuyutai.com 専用スクレイパー"""

    # 月のスラッグマッピング
    MONTH_SLUGS = {
        1: "january", 2: "february", 3: "march", 4: "april",
        5: "may", 6: "june", 7: "july", 8: "august",
        9: "september", 10: "october", 11: "november", 12: "december",
    }

    def __init__(self, config_path=None):
        super().__init__(config_path)
        # 正規表現パターン
        self.day_paren_re = re.compile(r"[（(]\s*(\d{1,2})\s*日\s*[）)]")
        self.code_in_parens_re = re.compile(r"[（(]\s*([0-9]{4})\s*[）)]")
        self.yen_re = re.compile(r"([0-9,]+)\s*円")

    def get_site_name(self) -> str:
        return "kabuyutai"

    def get_base_url(self) -> str:
        return "https://www.kabuyutai.com"

    def scrape_stocks(self, month: Optional[int] = None, year: int = None, **kwargs) -> List[Dict[str, Any]]:
        """
        株主優待銘柄データをスクレイピング

        Args:
            month: 権利確定月（1-12）、Noneの場合は全月
            year: 年（デフォルト: 現在年）
            **kwargs: その他のパラメータ

        Returns:
            List[Dict]: 銘柄データのリスト
        """
        if year is None:
            year = date.today().year

        stocks = []

        try:
            if month:
                self.logger.info(f"kabuyutai.com から {month}月のデータ取得開始")
                month_stocks = self._scrape_month(month, year)
                stocks.extend(month_stocks)
            else:
                self.logger.info(f"kabuyutai.com から全月のデータ取得開始")
                for m in range(1, 13):
                    month_stocks = self._scrape_month(m, year)
                    stocks.extend(month_stocks)

            # 重複除去
            stocks = self._deduplicate(stocks)

            self.logger.info(f"kabuyutai.com からデータ取得完了: {len(stocks)}件")
            return stocks

        except Exception as e:
            self.logger.error(f"kabuyutai.com スクレイピングエラー: {e}", exc_info=True)
            return []

    def _scrape_month(self, month: int, year: int) -> List[Dict[str, Any]]:
        """指定月のデータをスクレイピング"""
        stocks = []

        # 月のページURLを取得
        page_urls = self._discover_month_pages(month)

        if not page_urls:
            self.logger.warning(f"{month}月のページが見つかりません")
            return stocks

        # 各ページから銘柄URLを収集
        company_urls = set()
        for page_url in page_urls:
            soup = self.fetch_page(page_url)
            if not soup:
                continue

            # /kobetu/ へのリンクを収集
            for a in soup.find_all("a", href=True):
                href = a.get("href")
                if "/kobetu/" in href:
                    abs_url = urljoin(self.get_base_url(), href)
                    company_urls.add(abs_url)

        self.logger.info(f"{month}月: {len(company_urls)}社の詳細ページを発見")

        # 各銘柄ページから詳細を取得
        for company_url in company_urls:
            stock = self._extract_from_company_page(company_url, year, month)
            if stock and self.validate_stock_data(stock):
                stocks.append(stock)

        return stocks

    def _discover_month_pages(self, month: int) -> List[str]:
        """月のページURL一覧を取得"""
        slug = self.MONTH_SLUGS[month]
        first_url = f"{self.get_base_url()}/yutai/{slug}.html"

        soup = self.fetch_page(first_url)
        if not soup:
            return []

        urls = [first_url]

        # ページネーションリンクを探す（例: january2.html, january3.html）
        pattern = re.compile(rf"(?:/yutai/|^){slug}(\d+)\.html$")
        pages = set()

        for a in soup.find_all("a", href=True):
            href = a.get("href")
            match = pattern.search(href)
            if match:
                pages.add(int(match.group(1)))

        # ページ番号順にURL追加
        for page_num in sorted(pages):
            urls.append(f"{self.get_base_url()}/yutai/{slug}{page_num}.html")

        return urls

    def _extract_from_company_page(self, url: str, year: int, month: int) -> Optional[Dict[str, Any]]:
        """企業詳細ページから銘柄データを抽出"""
        soup = self.fetch_page(url)
        if not soup:
            return None

        # 企業名とコードを取得
        name, code = self._extract_name_and_code(soup)
        if not name or not code:
            self.logger.debug(f"企業名またはコードが取得できません: {url}")
            return None

        # 全テキストを取得
        text_all = soup.get_text("\n", strip=True)

        # ラベル付きフィールドを抽出
        yuutai_content = self._pick_field(text_all, "優待内容")
        rights_month_str = self._pick_field(text_all, "権利確定月")
        min_invest_str = self._pick_field(text_all, "必要投資金額")

        # 権利確定日を推定
        day_match = self.day_paren_re.search(rights_month_str)
        if day_match:
            day = int(day_match.group(1))
        else:
            day = calendar.monthrange(year, month)[1]  # 月末

        rights_date = date(year, month, day).isoformat()

        # 最低投資金額を抽出
        min_investment = 0
        yen_match = self.yen_re.search(min_invest_str)
        if yen_match:
            try:
                min_investment = int(yen_match.group(1).replace(",", ""))
            except ValueError:
                pass

        # ジャンルを推定
        yuutai_genre = self._infer_genre(yuutai_content)

        return {
            'code': code,
            'name': name,
            'rights_month': month,
            'rights_date': rights_date,
            'yuutai_genre': yuutai_genre,
            'yuutai_content': yuutai_content,
            'min_investment': min_investment
        }

    def _extract_name_and_code(self, soup) -> tuple:
        """H1タグから企業名とコードを抽出"""
        name, code = "", ""

        h1 = soup.find("h1")
        if h1:
            h1_text = h1.get_text(" ", strip=True)

            # コードを抽出（例: 「（1234）」）
            code_match = self.code_in_parens_re.search(h1_text)
            if code_match:
                code = code_match.group(1)

            # 企業名をクリーン化
            name = self._clean_company_name(h1_text)

        # コードが見つからない場合のフォールバック
        if not code:
            text_all = soup.get_text("\n", strip=True)
            code_match = re.search(r"(?:銘柄コード|コード)\s*[:：]?\s*([0-9]{4})", text_all)
            if code_match:
                code = code_match.group(1)
            else:
                code_match = self.code_in_parens_re.search(text_all)
                if code_match:
                    code = code_match.group(1)

        return name, code

    def _clean_company_name(self, name: str) -> str:
        """企業名をクリーン化（括弧、優待情報などを除去）"""
        if not name:
            return ""

        # 括弧付きセグメントを削除
        s = re.sub(r"[【〖［\[\(（].*?[】〗］\]\)）]", "", name)

        # 末尾の「...の株主優待」「...株主優待」などを削除
        s = re.sub(r"(の)?(株主)?優待(情報)?(?:.*)$", "", s)

        # 空白を正規化
        s = s.replace("\u3000", " ").strip()
        s = re.sub(r"\s+", " ", s)

        return s

    def _pick_field(self, text: str, label: str) -> str:
        """ラベル付きフィールドを抽出（例: 【優待内容】...）"""
        # 〖 〗 または 【 】 に対応
        pattern = re.compile(rf"[〖【]\s*{label}\s*[〗】]\s*(.+)")
        match = pattern.search(text)

        if not match:
            return ""

        value = match.group(1)

        # 次のラベルマーカーまたは改行でカット
        value = value.split("〖")[0].split("【")[0].split("\n")[0].strip()

        return value

    def _infer_genre(self, content: str) -> str:
        """優待内容からジャンルを推定"""
        if not content:
            return "その他"

        content_lower = content.lower()

        if re.search(r"quo|クオカード|図書カード|ギフトカード|商品券|金券|ポイント|pay", content, re.I):
            return "金券・ギフト"
        elif re.search(r"買物|買い物|クーポン|プリペイド|割引券|優待券", content, re.I):
            return "買物券・プリペイドカード"
        elif "カタログギフト" in content:
            return "カタログギフト"
        elif re.search(r"食事|レストラン|外食|飲食", content):
            return "食事券"
        elif re.search(r"自社商品|食品|詰合せ|米|お米|麺|菓子|飲料", content):
            return "食品"
        elif re.search(r"交通|旅行|宿泊|ホテル|航空券", content):
            return "交通・旅行"
        else:
            return "その他"

    def _deduplicate(self, stocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """重複を除去（code + rights_month + content で判定）"""
        seen = {}

        for stock in stocks:
            key = (
                stock.get('code'),
                stock.get('rights_month'),
                stock.get('yuutai_content')
            )
            seen[key] = stock

        return list(seen.values())
