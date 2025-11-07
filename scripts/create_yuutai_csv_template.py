"""
優待銘柄CSVテンプレート作成スクリプト
主要な優待銘柄のリストを含むCSVファイルを作成

Author: Yuutai Event Investor Team
Date: 2025-11-07
"""

import csv
from pathlib import Path

# 主要な優待銘柄リスト（権利確定月別）
MAJOR_YUUTAI_STOCKS = [
    # 1月
    {'code': '8267', 'name': 'イオン', 'rights_month': 2, 'rights_date': '2025-02-28', 'yuutai_genre': '買物券・プリペイドカード', 'yuutai_content': 'イオンギフトカード（保有株数に応じて）', 'min_investment': 200000},

    # 3月（最も多い月）
    {'code': '2914', 'name': '日本たばこ産業（JT）', 'rights_month': 12, 'rights_date': '2025-12-31', 'yuutai_genre': '食品', 'yuutai_content': '自社グループ商品（2,500円相当）', 'min_investment': 300000},
    {'code': '7201', 'name': 'トヨタ自動車', 'rights_month': 3, 'rights_date': '2025-03-31', 'yuutai_genre': 'その他', 'yuutai_content': 'カタログギフト', 'min_investment': 500000},
    {'code': '8001', 'name': '伊藤忠商事', 'rights_month': 3, 'rights_date': '2025-03-31', 'yuutai_genre': '金券・ギフト', 'yuutai_content': 'カタログギフト（3,000円相当）', 'min_investment': 300000},
    {'code': '8031', 'name': '三井物産', 'rights_month': 3, 'rights_date': '2025-03-31', 'yuutai_genre': '食品', 'yuutai_content': '自社グループ商品', 'min_investment': 300000},
    {'code': '8058', 'name': '三菱商事', 'rights_month': 3, 'rights_date': '2025-03-31', 'yuutai_genre': '金券・ギフト', 'yuutai_content': 'カタログギフト', 'min_investment': 500000},
    {'code': '8304', 'name': 'あおぞら銀行', 'rights_month': 3, 'rights_date': '2025-03-31', 'yuutai_genre': 'その他', 'yuutai_content': 'QUOカード（500円）', 'min_investment': 100000},
    {'code': '8306', 'name': '三菱UFJフィナンシャル・グループ', 'rights_month': 3, 'rights_date': '2025-03-31', 'yuutai_genre': 'その他', 'yuutai_content': 'カタログギフト', 'min_investment': 150000},
    {'code': '8591', 'name': 'オリックス', 'rights_month': 3, 'rights_date': '2025-03-31', 'yuutai_genre': 'カタログギフト', 'yuutai_content': 'カタログギフト（株主カード）', 'min_investment': 200000},
    {'code': '9202', 'name': 'ANAホールディングス', 'rights_month': 3, 'rights_date': '2025-03-31', 'yuutai_genre': '交通', 'yuutai_content': '株主優待券（50%割引）', 'min_investment': 200000},
    {'code': '9433', 'name': 'KDDI', 'rights_month': 3, 'rights_date': '2025-03-31', 'yuutai_genre': 'カタログギフト', 'yuutai_content': 'カタログギフト（3,000円相当）', 'min_investment': 200000},

    # 9月
    {'code': '8001', 'name': '伊藤忠商事', 'rights_month': 9, 'rights_date': '2025-09-30', 'yuutai_genre': '金券・ギフト', 'yuutai_content': 'カタログギフト（3,000円相当）', 'min_investment': 300000},

    # 12月
    {'code': '2914', 'name': '日本たばこ産業（JT）', 'rights_month': 12, 'rights_date': '2025-12-31', 'yuutai_genre': '食品', 'yuutai_content': '自社グループ商品（2,500円相当）', 'min_investment': 300000},
]


def create_csv_template(output_path: str):
    """
    CSVテンプレートを作成

    Args:
        output_path: 出力ファイルパス
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'code', 'name', 'rights_month', 'rights_date',
            'yuutai_genre', 'yuutai_content', 'min_investment'
        ])

        writer.writeheader()
        writer.writerows(MAJOR_YUUTAI_STOCKS)

    print(f"CSVファイルを作成しました: {output_path}")
    print(f"  銘柄数: {len(MAJOR_YUUTAI_STOCKS)}件")
    print()
    print("次のステップ:")
    print("  1. アプリケーションを起動")
    print("  2. 「ファイル」→「CSVから銘柄をインポート」")
    print(f"  3. {output_path} を選択")
    print()


def main():
    """メイン処理"""
    project_root = Path(__file__).parent.parent
    output_path = project_root / "data" / "major_yuutai_stocks.csv"

    print("=" * 60)
    print("優待銘柄CSVテンプレート作成")
    print("=" * 60)
    print()
    print("主要な優待銘柄のリストを含むCSVファイルを作成します。")
    print()

    create_csv_template(str(output_path))

    print("=" * 60)
    print()
    print("📝 注意:")
    print("  このファイルには主要銘柄のみが含まれています。")
    print("  さらに銘柄を追加したい場合は、CSVファイルを編集してください。")
    print()
    print("  推奨されるデータ取得方法:")
    print("  1. 証券会社のWebサイトで優待銘柄一覧をダウンロード")
    print("  2. Excel等で編集して必要なカラムに変換")
    print("  3. CSV形式で保存")
    print("  4. アプリでインポート")
    print("=" * 60)


if __name__ == "__main__":
    main()
