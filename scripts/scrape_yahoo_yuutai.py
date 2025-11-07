"""
Yahoo!ファイナンス 株主優待検索スクレイパー

Yahoo!ファイナンスの株主優待検索から銘柄データを取得

Requirements:
    pip install selenium webdriver-manager

Usage:
    python scripts/scrape_yahoo_yuutai.py --month 3 --output data/yahoo_yuutai.csv

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
    from selenium.webdriver.support.ui import WebDriverWait, Select
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


def scrape_yahoo_yuutai(month: Optional[int] = None, headless: bool = True) -> List[Dict]:
    """
    Yahoo!ファイナンスから優待銘柄を取得

    Args:
        month: 権利確定月（1-12）
        headless: ヘッドレスモード

    Returns:
        銘柄データのリスト
    """
    if not SELENIUM_AVAILABLE:
        print("エラー: Seleniumがインストールされていません", file=sys.stderr)
        return []

    stocks = []

    # Chromeオプション設定
    chrome_options = Options()
    if headless:
        chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')

    print("ブラウザを起動中...")
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except Exception as e:
        print(f"エラー: ブラウザの起動に失敗: {e}", file=sys.stderr)
        return []

    try:
        url = "https://finance.yahoo.co.jp/shareholder/search"
        print(f"\nYahoo!ファイナンス 株主優待検索にアクセス中...")
        print(f"URL: {url}")

        driver.get(url)
        time.sleep(3)  # ページ読み込み待機

        # 権利確定月を選択
        if month:
            try:
                print(f"{month}月を選択中...")

                # プルダウンメニューを探す
                month_select = driver.find_element(By.NAME, "month")
                select = Select(month_select)
                select.select_by_value(str(month))

                time.sleep(1)

                # 検索ボタンをクリック
                search_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
                search_button.click()

                time.sleep(3)  # 結果読み込み待機

            except Exception as e:
                print(f"月選択エラー: {e}")

        # 結果を取得
        print("検索結果を取得中...")

        # ページネーション対応
        page = 1
        max_pages = 10  # 最大ページ数

        while page <= max_pages:
            print(f"ページ {page} を処理中...")

            # 銘柄リストを取得
            try:
                # テーブル行を探す
                rows = driver.find_elements(By.CSS_SELECTOR, "table tr, div.stock-item")

                if not rows:
                    print("データ行が見つかりません")
                    break

                for row in rows:
                    try:
                        # 銘柄コードを探す
                        code_elem = row.find_element(By.CSS_SELECTOR, "a.stock-code, .code")
                        code_text = code_elem.text.strip()

                        # 数字4桁を抽出
                        code_match = re.search(r'(\d{4})', code_text)
                        if not code_match:
                            continue

                        code = code_match.group(1)

                        # 銘柄名
                        name_elem = row.find_element(By.CSS_SELECTOR, ".name, .stock-name, a")
                        name = name_elem.text.strip()

                        # 権利確定月を取得（ページから）
                        try:
                            month_elem = row.find_element(By.CSS_SELECTOR, ".month, .rights-month")
                            month_text = month_elem.text.strip()
                            month_match = re.search(r'(\d+)月', month_text)
                            rights_month = int(month_match.group(1)) if month_match else (month or 3)
                        except:
                            rights_month = month or 3

                        # 優待内容
                        try:
                            content_elem = row.find_element(By.CSS_SELECTOR, ".content, .benefit")
                            yuutai_content = content_elem.text.strip()
                        except:
                            yuutai_content = ""

                        # 権利確定日を推定
                        year = datetime.now().year
                        if rights_month == 2:
                            rights_date = f"{year}-02-28"
                        elif rights_month in [4, 6, 9, 11]:
                            rights_date = f"{year}-{rights_month:02d}-30"
                        else:
                            rights_date = f"{year}-{rights_month:02d}-31"

                        # 重複チェック
                        if not any(s['code'] == code and s['rights_month'] == rights_month for s in stocks):
                            stocks.append({
                                'code': code,
                                'name': name,
                                'rights_month': rights_month,
                                'rights_date': rights_date,
                                'yuutai_genre': "その他",
                                'yuutai_content': yuutai_content,
                                'min_investment': 0
                            })
                            print(f"  追加: {code} {name}")

                    except Exception as e:
                        # デバッグ出力を抑制（大量のエラーを防ぐ）
                        continue

            except Exception as e:
                print(f"ページ処理エラー: {e}")
                break

            # 次のページへ
            try:
                next_button = driver.find_element(By.CSS_SELECTOR, "a.next, button.next, a[rel='next']")
                if not next_button.is_enabled():
                    break

                next_button.click()
                time.sleep(2)
                page += 1

            except:
                # 次のページがない
                break

        print(f"\n合計 {len(stocks)} 件の銘柄を取得しました")

    finally:
        driver.quit()
        print("ブラウザを終了しました")

    return stocks


def save_to_csv(stocks: List[Dict], output_path: str):
    """CSVに保存"""
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

    print(f"\nCSVファイルを保存: {output_path}")
    print(f"銘柄数: {len(stocks)}件")


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description="Yahoo!ファイナンスから株主優待銘柄をスクレイピング"
    )
    parser.add_argument(
        '--month',
        type=int,
        choices=range(1, 13),
        help="権利確定月（1-12）"
    )
    parser.add_argument(
        '--output',
        default='data/yahoo_yuutai.csv',
        help="出力CSVファイルパス"
    )
    parser.add_argument(
        '--show-browser',
        action='store_true',
        help="ブラウザを表示する"
    )

    args = parser.parse_args()

    if not SELENIUM_AVAILABLE:
        print("エラー: Seleniumがインストールされていません", file=sys.stderr)
        print("インストール: pip install selenium webdriver-manager", file=sys.stderr)
        return 1

    print("=" * 60)
    print("Yahoo!ファイナンス 株主優待スクレイピング")
    print("=" * 60)
    print(f"権利確定月: {args.month if args.month else '全て'}")
    print(f"出力ファイル: {args.output}")
    print()

    stocks = scrape_yahoo_yuutai(
        month=args.month,
        headless=not args.show_browser
    )

    if not stocks:
        print("データを取得できませんでした", file=sys.stderr)
        print("--show-browser オプションでブラウザを表示して確認してください", file=sys.stderr)
        return 1

    save_to_csv(stocks, args.output)

    print()
    print("=" * 60)
    print("次のステップ:")
    print("  1. アプリを起動")
    print("  2. ファイル → CSVから銘柄をインポート")
    print(f"  3. {args.output} を選択")
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
