"""
優待情報スクレイピングスクリプト（Selenium版）

Seleniumを使って動的コンテンツも取得可能

Requirements:
    pip install selenium webdriver-manager

Usage:
    python scripts/scrape_yuutai_selenium.py --month 3 --output data/scraped_yuutai.csv

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

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


def scrape_96ut_selenium(month: Optional[int] = None, headless: bool = True) -> List[Dict]:
    """
    Seleniumを使って96ut.comから優待銘柄を取得

    Args:
        month: 権利確定月（1-12）、Noneの場合は全月
        headless: ヘッドレスモード（ブラウザを表示しない）

    Returns:
        銘柄データのリスト
    """
    if not SELENIUM_AVAILABLE:
        print("エラー: Seleniumがインストールされていません", file=sys.stderr)
        print("インストール: pip install selenium webdriver-manager", file=sys.stderr)
        return []

    stocks = []

    # Chromeオプション設定
    chrome_options = Options()
    if headless:
        chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    # WebDriverを初期化
    print("ブラウザを起動中...")
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except Exception as e:
        print(f"エラー: ブラウザの起動に失敗しました: {e}", file=sys.stderr)
        return []

    try:
        months = [month] if month else range(1, 13)

        for m in months:
            url = f"https://96ut.com/yuutai/list.php?m={m}"
            print(f"\n{m}月のデータを取得中...")
            print(f"URL: {url}")

            driver.get(url)

            # ページの読み込みを待つ
            time.sleep(2)

            # ボタンを探してクリック（必要な場合）
            try:
                # 「リスト出力」ボタンなどがあればクリック
                buttons = driver.find_elements(By.TAG_NAME, "button")
                for button in buttons:
                    if "出力" in button.text or "表示" in button.text:
                        print(f"ボタンをクリック: {button.text}")
                        button.click()
                        time.sleep(2)
                        break
            except Exception as e:
                print(f"ボタン操作スキップ: {e}")

            # テーブルを探す
            try:
                # 複数のセレクタを試す
                table = None
                selectors = [
                    "table",
                    "table.yuutai-list",
                    "table.stock-list",
                    "div.yuutai-table table",
                ]

                for selector in selectors:
                    try:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        if elements:
                            table = elements[0]
                            print(f"テーブル発見: {selector}")
                            break
                    except:
                        continue

                if not table:
                    # divやulなどの他の構造も試す
                    print("テーブルが見つかりません。他の構造を探索中...")

                    # リスト構造を探す
                    items = driver.find_elements(By.CSS_SELECTOR, "div.stock-item, li.stock-item, div.yuutai-item")

                    if items:
                        print(f"{len(items)}件のアイテムを発見")

                        for item in items:
                            try:
                                # 銘柄コードを探す
                                code_elem = item.find_element(By.CSS_SELECTOR, ".code, .stock-code")
                                code = code_elem.text.strip()

                                if not code.isdigit():
                                    continue

                                # 銘柄名
                                name_elem = item.find_element(By.CSS_SELECTOR, ".name, .stock-name")
                                name = name_elem.text.strip()

                                # 優待内容
                                try:
                                    content_elem = item.find_element(By.CSS_SELECTOR, ".content, .yuutai-content")
                                    yuutai_content = content_elem.text.strip()
                                except:
                                    yuutai_content = ""

                                # 権利確定日を推定
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
                                    'yuutai_genre': "その他",
                                    'yuutai_content': yuutai_content,
                                    'min_investment': 0
                                })

                            except Exception as e:
                                print(f"アイテムの解析エラー: {e}")
                                continue

                    else:
                        print("データ要素が見つかりません")
                        # ページソースを保存してデバッグ
                        debug_file = Path(f"debug_page_{m}.html")
                        debug_file.write_text(driver.page_source, encoding='utf-8')
                        print(f"デバッグ用にページソースを保存: {debug_file}")

                else:
                    # テーブルからデータを抽出
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    print(f"{len(rows)}行のデータを発見")

                    for row in rows[1:]:  # ヘッダー行をスキップ
                        try:
                            cols = row.find_elements(By.TAG_NAME, "td")
                            if len(cols) < 2:
                                continue

                            # 銘柄コード
                            code = cols[0].text.strip()
                            if not code.isdigit():
                                continue

                            # 銘柄名
                            name = cols[1].text.strip()

                            # 優待内容（あれば）
                            yuutai_content = cols[2].text.strip() if len(cols) > 2 else ""

                            # 優待ジャンル（あれば）
                            yuutai_genre = cols[3].text.strip() if len(cols) > 3 else "その他"

                            # 権利確定日を推定
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
                                'min_investment': 0
                            })

                        except Exception as e:
                            print(f"行の解析エラー: {e}")
                            continue

            except Exception as e:
                print(f"データ抽出エラー: {e}", file=sys.stderr)

            time.sleep(1)  # 次のページへの間隔

        print(f"\n合計 {len(stocks)} 件の銘柄を取得しました")

    finally:
        driver.quit()
        print("ブラウザを終了しました")

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
        description="優待情報をスクレイピングしてCSVファイルに保存（Selenium版）"
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
        '--show-browser',
        action='store_true',
        help="ブラウザを表示する（デバッグ用）"
    )

    args = parser.parse_args()

    if not SELENIUM_AVAILABLE:
        print("エラー: Seleniumがインストールされていません", file=sys.stderr)
        print("\nインストール方法:", file=sys.stderr)
        print("  pip install selenium webdriver-manager", file=sys.stderr)
        return 1

    print("=" * 60)
    print("優待情報スクレイピング（Selenium版）")
    print("=" * 60)
    print()
    print(f"権利確定月: {'全月' if args.month is None else f'{args.month}月'}")
    print(f"出力ファイル: {args.output}")
    print(f"ヘッドレスモード: {'無効' if args.show_browser else '有効'}")
    print()

    # スクレイピング実行
    print("スクレイピングを開始...")

    stocks = scrape_96ut_selenium(
        month=args.month,
        headless=not args.show_browser
    )

    if not stocks:
        print("\nデータを取得できませんでした", file=sys.stderr)
        print("\nトラブルシューティング:", file=sys.stderr)
        print("  1. --show-browser オプションでブラウザを表示して確認", file=sys.stderr)
        print("  2. debug_page_*.html ファイルを確認", file=sys.stderr)
        print("  3. サイトの構造が変更されている可能性があります", file=sys.stderr)
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
        import traceback
        traceback.print_exc()
        sys.exit(1)
