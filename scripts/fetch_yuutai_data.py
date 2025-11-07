"""
株主優待データ取得スクリプト
みんなの株式（株探）から優待情報を取得

Author: Yuutai Event Investor Team
Date: 2025-11-07
"""

import sys
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import time
import re
import csv
from datetime import datetime
import logging

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def fetch_yuutai_list_by_month(month: int) -> list:
    """
    指定月の優待銘柄リストを取得

    Args:
        month: 権利確定月（1-12）

    Returns:
        list: 銘柄リスト
    """
    stocks = []

    # 株探の優待検索URL（権利確定月で絞り込み）
    url = f"https://kabutan.jp/yutai/?month={month}"

    try:
        logger.info(f"{month}月の優待銘柄を取得中: {url}")

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        response.encoding = response.apparent_encoding

        soup = BeautifulSoup(response.text, 'html.parser')

        # テーブルから銘柄情報を抽出
        table = soup.find('table', class_='stock_table')

        if not table:
            logger.warning(f"{month}月: データテーブルが見つかりません")
            return stocks

        rows = table.find_all('tr')[1:]  # ヘッダー行をスキップ

        for row in rows:
            try:
                cols = row.find_all('td')
                if len(cols) < 4:
                    continue

                # 銘柄コード
                code_link = cols[0].find('a')
                if not code_link:
                    continue
                code = code_link.text.strip()

                # 銘柄名
                name = cols[1].text.strip()

                # 優待内容
                yuutai_content = cols[2].text.strip() if len(cols) > 2 else ''

                # 最低投資金額
                min_investment_text = cols[3].text.strip() if len(cols) > 3 else '0'
                min_investment = 0
                try:
                    # "123,456円" -> 123456
                    min_investment = int(re.sub(r'[^\d]', '', min_investment_text))
                except:
                    min_investment = 0

                # 権利確定日を推定（月末を仮定）
                if month in [1, 3, 5, 7, 8, 10, 12]:
                    day = 31
                elif month in [4, 6, 9, 11]:
                    day = 30
                else:
                    day = 28  # 2月（閏年は考慮しない）

                rights_date = f"2025-{month:02d}-{day:02d}"

                stock_data = {
                    'code': code,
                    'name': name,
                    'rights_month': month,
                    'rights_date': rights_date,
                    'yuutai_content': yuutai_content,
                    'min_investment': min_investment
                }

                stocks.append(stock_data)
                logger.debug(f"  取得: {code} - {name}")

            except Exception as e:
                logger.error(f"  行の解析エラー: {e}")
                continue

        logger.info(f"{month}月: {len(stocks)}件の銘柄を取得")
        time.sleep(2)  # サーバー負荷軽減

    except requests.exceptions.RequestException as e:
        logger.error(f"{month}月の取得エラー: {e}")
    except Exception as e:
        logger.error(f"{month}月の処理エラー: {e}")

    return stocks


def fetch_all_yuutai_data() -> list:
    """
    全ての月の優待銘柄データを取得

    Returns:
        list: 全銘柄リスト
    """
    all_stocks = []

    logger.info("=" * 60)
    logger.info("株主優待データ取得開始")
    logger.info("=" * 60)

    for month in range(1, 13):
        stocks = fetch_yuutai_list_by_month(month)
        all_stocks.extend(stocks)
        time.sleep(3)  # 各月の間隔を空ける

    logger.info("=" * 60)
    logger.info(f"取得完了: 合計 {len(all_stocks)}件の銘柄")
    logger.info("=" * 60)

    return all_stocks


def save_to_csv(stocks: list, output_path: str):
    """
    CSVファイルに保存

    Args:
        stocks: 銘柄リスト
        output_path: 出力ファイルパス
    """
    try:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'code', 'name', 'rights_month', 'rights_date',
                'yuutai_content', 'min_investment'
            ])

            writer.writeheader()
            writer.writerows(stocks)

        logger.info(f"CSVファイルに保存: {output_path}")
        logger.info(f"  {len(stocks)}件のデータを書き込みました")

    except Exception as e:
        logger.error(f"CSV保存エラー: {e}")


def main():
    """メイン処理"""
    print("=" * 60)
    print("株主優待データ取得スクリプト")
    print("=" * 60)
    print()
    print("注意:")
    print("  - データ取得には数分かかります")
    print("  - サーバー負荷を考慮し、適切な間隔を空けています")
    print("  - エラーが発生した場合は時間を空けて再実行してください")
    print()

    input("Enterキーを押すと開始します...")
    print()

    # データ取得
    stocks = fetch_all_yuutai_data()

    if not stocks:
        logger.error("データを取得できませんでした")
        return

    # CSV保存
    output_path = project_root / "data" / "yuutai_data_fetched.csv"
    save_to_csv(stocks, str(output_path))

    # サマリー表示
    print()
    print("=" * 60)
    print("取得サマリー")
    print("=" * 60)

    # 月別集計
    monthly_count = {}
    for stock in stocks:
        month = stock['rights_month']
        monthly_count[month] = monthly_count.get(month, 0) + 1

    for month in sorted(monthly_count.keys()):
        print(f"  {month:2d}月: {monthly_count[month]:4d}件")

    print(f"\n  合計: {len(stocks)}件")
    print()
    print("=" * 60)
    print(f"データをCSVファイルに保存しました: {output_path}")
    print()
    print("次のステップ:")
    print("  1. CSVファイルを確認")
    print("  2. アプリで「ファイル」→「CSVから銘柄をインポート」")
    print("  3. 保存したCSVファイルを選択")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n中断されました")
    except Exception as e:
        logger.error(f"予期しないエラー: {e}", exc_info=True)
