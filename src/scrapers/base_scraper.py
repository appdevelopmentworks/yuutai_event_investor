"""
Base Scraper Module
スクレイパーの抽象基底クラス

Author: Yuutai Event Investor Team
Date: 2025-11-07
Version: 1.0.0
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
import logging
import json
from pathlib import Path
import time
import requests
from bs4 import BeautifulSoup


class BaseScraper(ABC):
    """スクレイパーの抽象基底クラス"""

    def __init__(self, config_path: Optional[Path] = None):
        """
        Args:
            config_path: セレクター設定ファイルのパス
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        # セレクター設定を読み込み
        if config_path is None:
            config_path = Path(__file__).parent / "selectors.json"

        self.selectors = self._load_selectors(config_path)

        # リトライ設定
        self.max_retries = 3
        self.retry_delay = 2  # 秒

    def _load_selectors(self, config_path: Path) -> Dict[str, Any]:
        """セレクター設定を読み込む"""
        try:
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    site_name = self.get_site_name()
                    return config.get(site_name, {})
            else:
                self.logger.warning(f"設定ファイルが見つかりません: {config_path}")
                return {}
        except Exception as e:
            self.logger.error(f"設定ファイル読み込みエラー: {e}")
            return {}

    @abstractmethod
    def get_site_name(self) -> str:
        """
        サイト名を取得（設定ファイルのキーとして使用）

        Returns:
            str: サイト名（例: "96ut", "yutai_net"）
        """
        pass

    @abstractmethod
    def get_base_url(self) -> str:
        """
        ベースURLを取得

        Returns:
            str: ベースURL
        """
        pass

    def fetch_page(self, url: str, retries: int = 0) -> Optional[BeautifulSoup]:
        """
        ページを取得してBeautifulSoupオブジェクトを返す

        Args:
            url: 取得するURL
            retries: リトライ回数

        Returns:
            BeautifulSoup: パース済みHTMLオブジェクト、失敗時はNone
        """
        try:
            self.logger.info(f"ページ取得: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            response.encoding = response.apparent_encoding

            return BeautifulSoup(response.text, 'html.parser')

        except requests.RequestException as e:
            self.logger.error(f"ページ取得エラー: {url} - {e}")

            if retries < self.max_retries:
                self.logger.info(f"リトライ {retries + 1}/{self.max_retries}...")
                time.sleep(self.retry_delay)
                return self.fetch_page(url, retries + 1)

            return None

    def try_selectors(self, soup: BeautifulSoup, selector_key: str,
                     method: str = 'select') -> Optional[Any]:
        """
        複数のセレクターを試行して要素を取得

        Args:
            soup: BeautifulSoupオブジェクト
            selector_key: セレクターのキー名
            method: 'select' または 'select_one'

        Returns:
            要素または要素リスト、見つからない場合はNone
        """
        selectors = self.selectors.get(selector_key, [])
        if isinstance(selectors, str):
            selectors = [selectors]

        for selector in selectors:
            try:
                if method == 'select':
                    result = soup.select(selector)
                    if result:
                        self.logger.debug(f"セレクター成功: {selector}")
                        return result
                else:  # select_one
                    result = soup.select_one(selector)
                    if result:
                        self.logger.debug(f"セレクター成功: {selector}")
                        return result
            except Exception as e:
                self.logger.debug(f"セレクター失敗: {selector} - {e}")
                continue

        self.logger.warning(f"全セレクターが失敗: {selector_key}")
        return None

    @abstractmethod
    def scrape_stocks(self, **kwargs) -> List[Dict[str, Any]]:
        """
        株主優待銘柄データをスクレイピング

        Args:
            **kwargs: サイト固有のパラメータ

        Returns:
            List[Dict]: 銘柄データのリスト
            各辞書は以下のキーを含む:
            - code: 証券コード (str)
            - name: 銘柄名 (str)
            - rights_month: 権利確定月 (int)
            - rights_date: 権利確定日 (str, YYYY-MM-DD)
            - yuutai_genre: 優待ジャンル (str, optional)
            - yuutai_content: 優待内容 (str, optional)
            - min_investment: 最低投資金額 (int, optional)
        """
        pass

    def validate_stock_data(self, stock: Dict[str, Any]) -> bool:
        """
        銘柄データの妥当性をチェック

        Args:
            stock: 銘柄データ

        Returns:
            bool: 妥当な場合True
        """
        required_keys = ['code', 'name', 'rights_month']

        for key in required_keys:
            if key not in stock or not stock[key]:
                self.logger.warning(f"必須フィールド不足: {key}")
                return False

        # 証券コードの形式チェック（4桁の数字）
        code = str(stock['code'])
        if not code.isdigit() or len(code) != 4:
            self.logger.warning(f"無効な証券コード: {code}")
            return False

        # 権利確定月のチェック（1-12）
        try:
            month = int(stock['rights_month'])
            if not 1 <= month <= 12:
                self.logger.warning(f"無効な権利確定月: {month}")
                return False
        except (ValueError, TypeError):
            self.logger.warning(f"権利確定月の型が不正: {stock['rights_month']}")
            return False

        return True

    def clean_text(self, text: Optional[str]) -> str:
        """
        テキストをクリーニング

        Args:
            text: クリーニング対象のテキスト

        Returns:
            str: クリーニング済みテキスト
        """
        if not text:
            return ""

        # 前後の空白を削除
        text = text.strip()

        # 改行を空白に置換
        text = text.replace('\n', ' ').replace('\r', ' ')

        # 連続する空白を1つに
        import re
        text = re.sub(r'\s+', ' ', text)

        return text

    def close(self):
        """セッションをクローズ"""
        self.session.close()
        self.logger.info("セッションをクローズしました")
