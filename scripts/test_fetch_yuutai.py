"""
優待データ取得のテストスクリプト（1月のみ）
"""

import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import requests
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_fetch_january():
    """1月の優待データを取得テスト"""
    url = "https://kabutan.jp/yutai/?month=1"

    logger.info(f"アクセス中: {url}")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        response.encoding = response.apparent_encoding

        logger.info(f"ステータスコード: {response.status_code}")
        logger.info(f"レスポンスサイズ: {len(response.text)} bytes")

        soup = BeautifulSoup(response.text, 'html.parser')

        # テーブル検索
        table = soup.find('table', class_='stock_table')

        if table:
            logger.info("✓ データテーブルを発見")
            rows = table.find_all('tr')
            logger.info(f"  行数: {len(rows)}")

            # 最初の数行を表示
            logger.info("\n最初の5銘柄:")
            for i, row in enumerate(rows[1:6], 1):  # ヘッダーをスキップ
                cols = row.find_all('td')
                if len(cols) >= 2:
                    code = cols[0].text.strip()
                    name = cols[1].text.strip()
                    logger.info(f"  {i}. {code} - {name}")

            return True
        else:
            logger.warning("✗ データテーブルが見つかりません")

            # ページ構造を確認
            logger.info("\nページ構造を確認:")
            tables = soup.find_all('table')
            logger.info(f"  テーブル数: {len(tables)}")

            for i, t in enumerate(tables[:3], 1):
                classes = t.get('class', [])
                logger.info(f"  テーブル {i}: class={classes}")

            return False

    except requests.exceptions.RequestException as e:
        logger.error(f"リクエストエラー: {e}")
        return False
    except Exception as e:
        logger.error(f"エラー: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("優待データ取得テスト（1月）")
    print("=" * 60)
    print()

    success = test_fetch_january()

    print()
    if success:
        print("✓ テスト成功！データを取得できます")
        print("\n次のステップ:")
        print("  python scripts/fetch_yuutai_data.py")
        print("  で全月のデータを取得してください")
    else:
        print("✗ テスト失敗")
        print("\n可能性:")
        print("  1. サイト構造が変更された")
        print("  2. アクセスが制限されている")
        print("  3. ネットワークエラー")
    print("=" * 60)
