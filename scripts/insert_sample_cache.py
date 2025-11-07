"""
Insert sample simulation_cache data
サンプルのシミュレーションキャッシュデータを挿入
"""

import sys
from pathlib import Path
import sqlite3
import random

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.database import DatabaseManager

def generate_sample_data(code: str, rights_month: int, max_days: int = 120):
    """
    サンプルのバックテストデータを生成

    Args:
        code: 銘柄コード
        rights_month: 権利確定月
        max_days: 最大検証日数

    Returns:
        List[Dict]: シミュレーション結果のリスト
    """
    results = []

    # ランダムなベース勝率を設定（50-80%）
    base_win_rate = random.uniform(0.5, 0.8)

    # 最適日数をランダムに設定（30-60日前）
    optimal_days = random.randint(30, 60)

    for days_before in range(1, max_days + 1):
        # 最適日数付近で勝率が高くなるようにする
        distance = abs(days_before - optimal_days)
        win_rate = base_win_rate * (1 - distance / 200)
        win_rate = max(0.3, min(0.9, win_rate))  # 30%-90%の範囲

        # トレード数（3-15回）
        total_trades = random.randint(3, 15)
        win_count = int(total_trades * win_rate)
        lose_count = total_trades - win_count

        # リターン
        avg_win_return = random.uniform(2.0, 8.0)  # +2% ~ +8%
        max_win_return = avg_win_return + random.uniform(2.0, 5.0)
        avg_lose_return = random.uniform(-5.0, -1.0)  # -5% ~ -1%
        max_lose_return = avg_lose_return - random.uniform(1.0, 3.0)

        expected_return = (avg_win_return * win_rate) + (avg_lose_return * (1 - win_rate))

        results.append({
            'code': code,
            'rights_month': rights_month,
            'buy_days_before': days_before,
            'win_count': win_count,
            'lose_count': lose_count,
            'win_rate': win_rate,
            'expected_return': expected_return,
            'avg_win_return': avg_win_return,
            'max_win_return': max_win_return,
            'avg_lose_return': avg_lose_return,
            'max_lose_return': max_lose_return
        })

    return results

def main():
    """メイン処理"""
    print("サンプルシミュレーションデータを生成中...")

    db = DatabaseManager()

    # 全銘柄を取得
    stocks = db.get_all_stocks()
    print(f"{len(stocks)}件の銘柄を取得しました")

    if not stocks:
        print("エラー: 銘柄データがありません。先に初期化スクリプトを実行してください。")
        return

    total_inserted = 0

    for stock in stocks:
        code = stock['code']
        name = stock['name']
        rights_month = stock.get('rights_month', 3)

        print(f"処理中: {code} ({name})...")

        # サンプルデータを生成
        sample_data = generate_sample_data(code, rights_month)

        # データベースに保存
        for data in sample_data:
            db.insert_simulation_cache(
                code=data['code'],
                rights_month=data['rights_month'],
                buy_days_before=data['buy_days_before'],
                win_count=data['win_count'],
                lose_count=data['lose_count'],
                win_rate=data['win_rate'],
                expected_return=data['expected_return'],
                avg_win_return=data['avg_win_return'],
                max_win_return=data['max_win_return'],
                avg_lose_return=data['avg_lose_return'],
                max_lose_return=data['max_lose_return']
            )
            total_inserted += 1

        print(f"  OK {len(sample_data)}件のデータを挿入しました")

    print(f"\n完了: 合計 {total_inserted}件のデータを挿入しました")

    # 確認
    conn = db.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM simulation_cache")
    count = cursor.fetchone()['count']
    print(f"simulation_cache テーブルのレコード数: {count}")
    conn.close()

if __name__ == "__main__":
    main()
