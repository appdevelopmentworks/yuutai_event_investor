"""
Web Scraping Module
優待データのスクレイピング

Author: Yuutai Event Investor Team
Date: 2024-11-07
Version: 1.0.0
"""

import requests
from bs4 import BeautifulSoup
import time
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
import json
from pathlib import Path

from ..core.database import DatabaseManager


class YuutaiScraper:
    """株主優待データをスクレイピングするクラス"""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """
        Args:
            db_manager: DatabaseManagerインスタンス
        """
        self.logger = logging.getLogger(__name__)
        self.db = db_manager or DatabaseManager()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        # 設定ファイルを読み込み
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """スクレイピング設定を読み込む"""
        try:
            config_path = Path(__file__).parent.parent.parent / "config" / "scraping_config.json"
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                self.logger.warning("設定ファイルが見つかりません。デフォルト設定を使用します。")
                return {
                    "delay_seconds": 1,
                    "timeout": 10,
                    "max_retries": 3,
                    "sources": []
                }
        except Exception as e:
            self.logger.error(f"設定ファイル読み込みエラー: {e}")
            return {"delay_seconds": 1, "timeout": 10, "max_retries": 3, "sources": []}

    def scrape_96ut(self, month: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        96ut.comから優待データをスクレイピング

        Args:
            month: 権利確定月（1-12）、Noneの場合は全月

        Returns:
            List[Dict]: 銘柄データのリスト
        """
        self.logger.info(f"96ut.comからスクレイピング開始（月: {month or '全て'}）")

        stocks = []
        base_url = "https://96ut.com/yuutai/"

        try:
            # 月ごとにスクレイピング
            months_to_scrape = [month] if month else range(1, 13)

            for m in months_to_scrape:
                url = f"{base_url}?month={m}"
                self.logger.info(f"{m}月のデータを取得中: {url}")

                # リクエスト送信
                response = self.session.get(url, timeout=self.config.get('timeout', 10))
                response.raise_for_status()

                # HTMLをパース
                soup = BeautifulSoup(response.content, 'html.parser')

                # テーブルから銘柄データを抽出
                # 注: 実際のHTMLストラクチャに応じて調整が必要
                table = soup.find('table', class_='yuutai-table')

                if not table:
                    self.logger.warning(f"{m}月のデータテーブルが見つかりません")
                    continue

                rows = table.find_all('tr')[1:]  # ヘッダー行をスキップ

                for row in rows:
                    try:
                        cols = row.find_all('td')
                        if len(cols) < 4:
                            continue

                        # データ抽出（実際の構造に応じて調整）
                        code = cols[0].text.strip()
                        name = cols[1].text.strip()
                        genre = cols[2].text.strip() if len(cols) > 2 else ""
                        content = cols[3].text.strip() if len(cols) > 3 else ""

                        # 権利確定日を推定（月末）
                        rights_date = f"2024-{m:02d}-{self._get_last_day_of_month(m):02d}"

                        stock_data = {
                            'code': code,
                            'name': name,
                            'rights_month': m,
                            'rights_date': rights_date,
                            'yuutai_genre': genre,
                            'yuutai_content': content,
                            'yuutai_detail': content,
                            'min_shares': 100,  # デフォルト値
                            'data_source': '96ut'
                        }

                        stocks.append(stock_data)

                    except Exception as e:
                        self.logger.error(f"行の解析エラー: {e}")
                        continue

                # レート制限
                time.sleep(self.config.get('delay_seconds', 1))

            self.logger.info(f"96ut.comから{len(stocks)}件のデータを取得しました")
            return stocks

        except requests.RequestException as e:
            self.logger.error(f"96ut.comへのリクエストエラー: {e}")
            return []
        except Exception as e:
            self.logger.error(f"96ut.comスクレイピングエラー: {e}")
            return []

    def scrape_netir(self, month: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        yutai.net-ir.ne.jpから優待データをスクレイピング

        Args:
            month: 権利確定月（1-12）

        Returns:
            List[Dict]: 銘柄データのリスト
        """
        self.logger.info(f"net-irからスクレイピング開始（月: {month or '全て'}）")

        stocks = []
        base_url = "https://yutai.net-ir.ne.jp/"

        try:
            # 実装例: 実際のサイト構造に応じて実装
            # ここでは簡易的なプレースホルダー実装

            self.logger.info("net-irのスクレイピングは未実装です")
            return stocks

        except Exception as e:
            self.logger.error(f"net-irスクレイピングエラー: {e}")
            return []

    def _get_last_day_of_month(self, month: int, year: int = 2024) -> int:
        """月の最終日を取得"""
        if month == 12:
            next_month = datetime(year + 1, 1, 1)
        else:
            next_month = datetime(year, month + 1, 1)

        from datetime import timedelta
        last_day = next_month - timedelta(days=1)
        return last_day.day

    def save_to_database(self, stocks: List[Dict[str, Any]]) -> int:
        """
        スクレイピングしたデータをデータベースに保存

        Args:
            stocks: 銘柄データのリスト

        Returns:
            int: 保存成功件数
        """
        success_count = 0

        for stock in stocks:
            try:
                if self.db.insert_stock(**stock):
                    success_count += 1
                    self.logger.debug(f"保存成功: {stock['code']} - {stock['name']}")
                else:
                    self.logger.warning(f"保存失敗: {stock['code']} - {stock['name']}")

            except Exception as e:
                self.logger.error(f"データベース保存エラー: {stock.get('code', 'Unknown')} - {e}")

        self.logger.info(f"データベースに{success_count}/{len(stocks)}件を保存しました")
        return success_count

    def scrape_all(self, save_to_db: bool = True) -> List[Dict[str, Any]]:
        """
        全ソースから優待データをスクレイピング

        Args:
            save_to_db: データベースに保存するかどうか

        Returns:
            List[Dict]: 全銘柄データ
        """
        self.logger.info("全ソースからスクレイピング開始")

        all_stocks = []

        # 96ut.comからスクレイピング
        stocks_96ut = self.scrape_96ut()
        all_stocks.extend(stocks_96ut)

        # net-irからスクレイピング（未実装）
        # stocks_netir = self.scrape_netir()
        # all_stocks.extend(stocks_netir)

        # 重複除去（コードをキーに）
        unique_stocks = {}
        for stock in all_stocks:
            code = stock['code']
            if code not in unique_stocks:
                unique_stocks[code] = stock
            else:
                # 既存データより詳細な情報があれば更新
                if len(stock.get('yuutai_detail', '')) > len(unique_stocks[code].get('yuutai_detail', '')):
                    unique_stocks[code] = stock

        all_stocks = list(unique_stocks.values())

        self.logger.info(f"合計{len(all_stocks)}件のユニークな銘柄データを取得しました")

        # データベースに保存
        if save_to_db and all_stocks:
            self.save_to_database(all_stocks)

        return all_stocks

    def update_stock_prices(self, codes: Optional[List[str]] = None) -> Dict[str, bool]:
        """
        株価データを更新

        Args:
            codes: 更新する銘柄コードのリスト（Noneの場合は全銘柄）

        Returns:
            Dict[str, bool]: 銘柄コードごとの成功/失敗
        """
        from ..core.data_fetcher import DataFetcher

        fetcher = DataFetcher(self.db)

        if codes is None:
            # 全銘柄を取得
            stocks = self.db.get_all_stocks()
            codes = [stock['code'] for stock in stocks]

        self.logger.info(f"{len(codes)}銘柄の株価データを更新中...")

        results = fetcher.bulk_update(codes, period="10y")

        success_count = sum(1 for v in results.values() if v)
        self.logger.info(f"株価データ更新完了: {success_count}/{len(codes)}銘柄")

        return results

    def close(self):
        """リソースをクリーンアップ"""
        self.session.close()
        self.db.close()


class ScrapingWorker:
    """
    バックグラウンドでスクレイピングを実行するワーカークラス
    QThreadで使用する想定
    """

    def __init__(self, scraper: Optional[YuutaiScraper] = None):
        """
        Args:
            scraper: YuutaiScraperインスタンス
        """
        self.logger = logging.getLogger(__name__)
        self.scraper = scraper or YuutaiScraper()

    def run_scraping(self, update_prices: bool = True) -> Dict[str, Any]:
        """
        スクレイピングを実行

        Args:
            update_prices: 株価データも更新するか

        Returns:
            Dict: 実行結果
        """
        try:
            self.logger.info("スクレイピングワーカー開始")

            # 優待データをスクレイピング
            stocks = self.scraper.scrape_all(save_to_db=True)

            result = {
                'success': True,
                'stocks_count': len(stocks),
                'message': f"{len(stocks)}件の銘柄データを取得しました"
            }

            # 株価データを更新
            if update_prices and stocks:
                codes = [s['code'] for s in stocks[:10]]  # 最初の10銘柄のみテスト
                price_results = self.scraper.update_stock_prices(codes)
                result['price_update'] = price_results
                result['message'] += f"\n株価データ: {sum(1 for v in price_results.values() if v)}/{len(codes)}銘柄更新"

            self.logger.info("スクレイピングワーカー完了")
            return result

        except Exception as e:
            self.logger.error(f"スクレイピングワーカーエラー: {e}", exc_info=True)
            return {
                'success': False,
                'stocks_count': 0,
                'message': f"エラー: {str(e)}"
            }

        finally:
            self.scraper.close()
