"""Check database simulation_cache data"""
import sqlite3
from pathlib import Path

db_path = Path("data/yuutai.db")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# シミュレーションキャッシュのレコード数
cursor.execute("SELECT COUNT(*) as count FROM simulation_cache")
count = cursor.fetchone()['count']
print(f"simulation_cache records: {count}")

# サンプルデータを表示
cursor.execute("""
    SELECT code, rights_month, buy_days_before, win_rate, expected_return
    FROM simulation_cache
    LIMIT 10
""")

print("\nSample data:")
for row in cursor.fetchall():
    print(f"  Code: {row['code']}, Month: {row['rights_month']}, Days: {row['buy_days_before']}, "
          f"Win Rate: {row['win_rate']:.2%}, Expected Return: {row['expected_return']:+.2f}%")

# 銘柄ごとの最適結果を確認
cursor.execute("""
    SELECT code, buy_days_before, win_rate, expected_return,
           (expected_return * win_rate) as score
    FROM simulation_cache
    GROUP BY code
    HAVING score = MAX(score)
    LIMIT 10
""")

print("\nBest results by stock:")
for row in cursor.fetchall():
    print(f"  Code: {row['code']}, Days: {row['buy_days_before']}, "
          f"Win Rate: {row['win_rate']:.2%}, Expected Return: {row['expected_return']:+.2f}%")

conn.close()
