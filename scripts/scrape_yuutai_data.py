"""
優待情報スクレイピングスクリプト

96ut.comとyutai.net-ir.ne.jpから優待銘柄データを取得

Usage:
    python scripts/scrape_yuutai_data.py --site 96ut --output data/scraped_yuutai.csv
    python scripts/scrape_yuutai_data.py --site yutai --month 3 --output data/scraped_yuutai.csv

Author: Yuutai Event Investor Team
Date: 2025-11-07
"""

import argparse
import csv
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

import requests
from bs4 import BeautifulSoup


class YuutaiScraper:
    """優待情報スクレイパー基底クラス"""

    def __init__(self, delay: float = 1.0):
        """
        Args:
            delay: リクエスト間隔（秒）
        """
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        ページを取得してBeautifulSoupオブジェクトを返す

        Args:
            url: 取得するURL

        Returns:
            BeautifulSoupオブジェクト、失敗時はNone
        """
        try:
            print(f"Fetching: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            time.sleep(self.delay)
            return BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            print(f"Error fetching {url}: {e}", file=sys.stderr)
            return None

    def scrape(self, **kwargs) -> List[Dict]:
        """
        スクレイピングを実行

        Returns:
            銘柄データのリスト
        """
        raise NotImplementedError


class Ut96Scraper(YuutaiScraper):
    """96ut.comスクレイパー"""

    BASE_URL = "https://96ut.com/yuutai/list.php"

    def scrape(self, month: Optional[int] = None) -> List[Dict]:
        """
        96ut.comから優待銘柄を取得

        Args:
            month: 権利確定月（1-12）、Noneの場合は全月

        Returns:
            銘柄データのリスト
        """
        stocks = []

        if month:
            months = [month]
        else:
            months = range(1, 13)

        for m in months:
            url = f"{self.BASE_URL}?m={m}"
            soup = self.fetch_page(url)

            if not soup:
                continue

            # テーブルを探す
            table = soup.find('table')
            if not table:
                print(f"テーブルが見つかりません: {url}")
                continue

            rows = table.find_all('tr')
            print(f"{m}月: {len(rows)}行のデータを取得")

            for row in rows[1:]:  # ヘッダー行をスキップ
                cols = row.find_all('td')
                if len(cols) < 3:
                    continue

                try:
                    # 銘柄コード
                    code = cols[0].get_text(strip=True)
                    if not code.isdigit():
                        continue

                    # 銘柄名
                    name = cols[1].get_text(strip=True)

                    # 優待内容（あれば）
                    yuutai_content = cols[2].get_text(strip=True) if len(cols) > 2 else ""

                    # 優待ジャンル（あれば）
                    yuutai_genre = cols[3].get_text(strip=True) if len(cols) > 3 else "その他"

                    # 権利確定日を推定（月末）
                    year = datetime.now().year
                    if m == 2:
                        rights_date = f"{year}-02-28"
                    elif m in [4, 6, 9, 11]:
                        rights_date = f"{year}-{m:02d}-30"
                    else:
                        rights_date = f"{year}-{m:02d}-31"

                    stocks.append({
                        'code': code,
                        'name': name,
                        'rights_month': m,
                        'rights_date': rights_date,
                        'yuutai_genre': yuutai_genre,
                        'yuutai_content': yuutai_content,
                        'min_investment': 0  # スクレイピングでは取得困難
                    })

                except Exception as e:
                    print(f"行の解析エラー: {e}", file=sys.stderr)
                    continue

        return stocks


class YutaiNetScraper(YuutaiScraper):
    """yutai.net-ir.ne.jpスクレイパー"""

    SEARCH_URL = "https://yutai.net-ir.ne.jp/search/"

    def scrape(self, month: Optional[int] = None) -> List[Dict]:
        """
        yutai.net-ir.ne.jpから優待銘柄を取得

        Args:
            month: 権利確定月（1-12）、Noneの場合は全月

        Returns:
            銘柄データのリスト
        """
        stocks = []

        # 注意: このサイトは動的コンテンツ（JSON）を使用している可能性が高い
        # 実際のAPIエンドポイントを特定する必要がある

        print("警告: yutai.net-ir.ne.jpは動的コンテンツを使用しています")
        print("ブラウザの開発者ツールでネットワークタブを確認し、")
        print("JSONデータのAPIエンドポイントを特定する必要があります")

        soup = self.fetch_page(self.SEARCH_URL)
        if not soup:
            return stocks

        # 検索結果のコンテナを探す（実際の構造に応じて調整が必要）
        results = soup.find_all('div', class_=re.compile(r'stock|item|result'))

        print(f"検索結果: {len(results)}件")

        for item in results:
            try:
                # 銘柄コードを探す
                code_elem = item.find(text=re.compile(r'\d{4}'))
                if not code_elem:
                    continue

                code = re.search(r'(\d{4})', code_elem).group(1)

                # 銘柄名を探す
                name_elem = item.find('a') or item.find('span', class_=re.compile(r'name'))
                name = name_elem.get_text(strip=True) if name_elem else ""

                # 権利確定月
                month_elem = item.find(text=re.compile(r'(\d+)月'))
                rights_month = int(re.search(r'(\d+)月', month_elem).group(1)) if month_elem else 3

                # 権利確定日を推定
                year = datetime.now().year
                if rights_month == 2:
                    rights_date = f"{year}-02-28"
                elif rights_month in [4, 6, 9, 11]:
                    rights_date = f"{year}-{rights_month:02d}-30"
                else:
                    rights_date = f"{year}-{rights_month:02d}-31"

                stocks.append({
                    'code': code,
                    'name': name,
                    'rights_month': rights_month,
                    'rights_date': rights_date,
                    'yuutai_genre': "その他",
                    'yuutai_content': "",
                    'min_investment': 0
                })

            except Exception as e:
                print(f"アイテムの解析エラー: {e}", file=sys.stderr)
                continue

        return stocks


def save_to_csv(stocks: List[Dict], output_path: str):
    """
    銘柄データをCSVファイルに保存

    Args:
        stocks: 銘柄データのリスト
        output_path: 出力ファイルパス
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        'code', 'name', 'rights_month', 'rights_date',
        'yuutai_genre', 'yuutai_content', 'min_investment'
    ]

    with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(stocks)

    print(f"\nCSVファイルを保存しました: {output_path}")
    print(f"  銘柄数: {len(stocks)}件")


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description="優待情報をスクレイピングしてCSVファイルに保存"
    )
    parser.add_argument(
        '--site',
        choices=['96ut', 'yutai'],
        default='96ut',
        help="スクレイピング対象サイト（default: 96ut）"
    )
    parser.add_argument(
        '--month',
        type=int,
        choices=range(1, 13),
        help="権利確定月（1-12）、指定しない場合は全月"
    )
    parser.add_argument(
        '--output',
        default='data/scraped_yuutai.csv',
        help="出力CSVファイルパス（default: data/scraped_yuutai.csv）"
    )
    parser.add_argument(
        '--delay',
        type=float,
        default=1.0,
        help="リクエスト間隔（秒）（default: 1.0）"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("優待情報スクレイピング")
    print("=" * 60)
    print()
    print(f"対象サイト: {args.site}")
    print(f"権利確定月: {'全月' if args.month is None else f'{args.month}月'}")
    print(f"出力ファイル: {args.output}")
    print()

    # スクレイパーを選択
    if args.site == '96ut':
        scraper = Ut96Scraper(delay=args.delay)
    else:
        scraper = YutaiNetScraper(delay=args.delay)

    # スクレイピング実行
    print("スクレイピングを開始...")
    print()

    stocks = scraper.scrape(month=args.month)

    if not stocks:
        print("データを取得できませんでした", file=sys.stderr)
        return 1

    # CSVに保存
    save_to_csv(stocks, args.output)

    print()
    print("=" * 60)
    print()
    print("次のステップ:")
    print("  1. アプリケーションを起動")
    print("  2. 「ファイル」→「CSVから銘柄をインポート」")
    print(f"  3. {args.output} を選択")
    print()
    print("注意:")
    print("  - スクレイピングはサイトの構造変更に影響されます")
    print("  - 取得したデータは必ず確認してください")
    print("  - 過度なリクエストはサーバーに負荷をかけます")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n中断されました")
        sys.exit(1)
    except Exception as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)
