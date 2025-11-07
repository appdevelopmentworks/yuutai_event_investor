"""
Scraper Manager Module
複数のスクレイパーを統合管理

Author: Yuutai Event Investor Team
Date: 2025-11-07
Version: 1.0.0
"""

from typing import List, Dict, Any, Optional
import logging
from pathlib import Path

from .scraper_96ut import Scraper96ut
from .scraper_yutai_net import ScraperYutaiNet
from .scraper_kabuyutai import ScraperKabuyutai


class ScraperManager:
    """スクレイパーマネージャー - 複数のスクレイパーを統合管理"""

    def __init__(self, config_path: Optional[Path] = None):
        """
        Args:
            config_path: セレクター設定ファイルのパス
        """
        self.logger = logging.getLogger(__name__)

        # スクレイパーインスタンスを初期化
        self.scrapers = {
            'kabuyutai': ScraperKabuyutai(config_path),
            '96ut': Scraper96ut(config_path),
            'yutai_net': ScraperYutaiNet(config_path)
        }

        # 優先順位（最初に成功したスクレイパーのデータを使用）
        # kabuyutai.com が最も信頼性が高い
        self.priority = ['kabuyutai', 'yutai_net', '96ut']

    def scrape_all(self, month: Optional[int] = None, **kwargs) -> List[Dict[str, Any]]:
        """
        全スクレイパーからデータを取得（優先順位に従う）

        Args:
            month: 権利確定月（1-12）、Noneの場合は全月
            **kwargs: スクレイパー固有のパラメータ

        Returns:
            List[Dict]: 銘柄データのリスト
        """
        all_stocks = []

        for scraper_name in self.priority:
            try:
                self.logger.info(f"{scraper_name} でスクレイピング開始")

                scraper = self.scrapers[scraper_name]

                if scraper_name == '96ut':
                    # 96ut は term パラメータを使用
                    if month:
                        term = f"{month}月末"
                        stocks = scraper.scrape_stocks(term=term)
                    else:
                        stocks = scraper.scrape_stocks()
                else:
                    # kabuyutai, yutai_net は month パラメータを使用
                    stocks = scraper.scrape_stocks(month=month)

                if stocks:
                    self.logger.info(f"{scraper_name} から {len(stocks)}件取得")
                    all_stocks.extend(stocks)
                else:
                    self.logger.warning(f"{scraper_name} からデータ取得なし")

            except Exception as e:
                self.logger.error(f"{scraper_name} スクレイピングエラー: {e}")
                continue

        # 重複を除去（証券コードで判定）
        unique_stocks = self._deduplicate_stocks(all_stocks)

        self.logger.info(f"合計 {len(unique_stocks)}件の銘柄データを取得")
        return unique_stocks

    def scrape_with_fallback(self, month: Optional[int] = None, **kwargs) -> List[Dict[str, Any]]:
        """
        フォールバック戦略でデータを取得（最初に成功したスクレイパーのデータを使用）

        Args:
            month: 権利確定月（1-12）、Noneの場合は全月
            **kwargs: スクレイパー固有のパラメータ

        Returns:
            List[Dict]: 銘柄データのリスト
        """
        for scraper_name in self.priority:
            try:
                self.logger.info(f"{scraper_name} でスクレイピング開始（フォールバックモード）")

                scraper = self.scrapers[scraper_name]

                if scraper_name == '96ut':
                    if month:
                        term = f"{month}月末"
                        stocks = scraper.scrape_stocks(term=term)
                    else:
                        stocks = scraper.scrape_stocks()
                else:
                    # kabuyutai, yutai_net は month パラメータを使用
                    stocks = scraper.scrape_stocks(month=month)

                if stocks:
                    self.logger.info(f"{scraper_name} から {len(stocks)}件取得成功")
                    return stocks
                else:
                    self.logger.warning(f"{scraper_name} からデータ取得なし、次のスクレイパーを試行")

            except Exception as e:
                self.logger.error(f"{scraper_name} スクレイピングエラー: {e}、次のスクレイパーを試行")
                continue

        self.logger.error("全スクレイパーが失敗しました")
        return []

    def scrape_by_source(self, source: str, month: Optional[int] = None, **kwargs) -> List[Dict[str, Any]]:
        """
        指定されたソースからデータを取得

        Args:
            source: スクレイパー名（'96ut' または 'yutai_net'）
            month: 権利確定月（1-12）、Noneの場合は全月
            **kwargs: スクレイパー固有のパラメータ

        Returns:
            List[Dict]: 銘柄データのリスト
        """
        if source not in self.scrapers:
            self.logger.error(f"無効なスクレイパー名: {source}")
            return []

        try:
            scraper = self.scrapers[source]

            if source == '96ut':
                if month:
                    term = f"{month}月末"
                    return scraper.scrape_stocks(term=term)
                else:
                    return scraper.scrape_stocks()
            else:
                return scraper.scrape_stocks(month=month)

        except Exception as e:
            self.logger.error(f"{source} スクレイピングエラー: {e}", exc_info=True)
            return []

    def _deduplicate_stocks(self, stocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        重複する銘柄を除去（証券コードで判定）

        優先順位：
        1. より多くの情報を持つ銘柄
        2. 後から追加された銘柄（上書き）

        Args:
            stocks: 銘柄データのリスト

        Returns:
            List[Dict]: 重複を除去した銘柄データのリスト
        """
        stock_dict = {}

        for stock in stocks:
            code = stock.get('code')
            if not code:
                continue

            key = f"{code}_{stock.get('rights_month')}"

            if key not in stock_dict:
                stock_dict[key] = stock
            else:
                # 既存のデータと比較して、より多くの情報を持つ方を採用
                existing = stock_dict[key]
                if self._compare_completeness(stock, existing) > 0:
                    stock_dict[key] = stock

        return list(stock_dict.values())

    def _compare_completeness(self, stock1: Dict[str, Any], stock2: Dict[str, Any]) -> int:
        """
        2つの銘柄データの完全性を比較

        Args:
            stock1: 銘柄データ1
            stock2: 銘柄データ2

        Returns:
            int: stock1の方が完全なら1、stock2の方が完全なら-1、同等なら0
        """
        # 情報の充実度を計算
        score1 = sum([
            bool(stock1.get('yuutai_genre')),
            bool(stock1.get('yuutai_content')),
            bool(stock1.get('min_investment')),
            bool(stock1.get('rights_date'))
        ])

        score2 = sum([
            bool(stock2.get('yuutai_genre')),
            bool(stock2.get('yuutai_content')),
            bool(stock2.get('min_investment')),
            bool(stock2.get('rights_date'))
        ])

        if score1 > score2:
            return 1
        elif score1 < score2:
            return -1
        else:
            return 0

    def close_all(self):
        """全スクレイパーのセッションをクローズ"""
        for scraper in self.scrapers.values():
            try:
                scraper.close()
            except Exception as e:
                self.logger.error(f"スクレイパークローズエラー: {e}")
