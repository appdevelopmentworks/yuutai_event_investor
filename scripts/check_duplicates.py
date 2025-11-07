import csv
from collections import Counter

with open('data/all_yuutai_stocks_fixed.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

codes = [r['code'] for r in rows]
code_counts = Counter(codes)

unique_codes = len(code_counts)
duplicates = {code: count for code, count in code_counts.items() if count > 1}

print(f"CSV総行数: {len(rows)}件")
print(f"ユニークな証券コード数: {unique_codes}件")
print(f"重複している証券コード数: {len(duplicates)}件")
print(f"削減される件数: {len(rows) - unique_codes}件")
print()

if duplicates:
    print(f"重複例（最初の10件）:")
    for i, (code, count) in enumerate(sorted(duplicates.items())):
        if i >= 10:
            break
        # 該当するレコードを表示
        matching_rows = [r for r in rows if r['code'] == code]
        print(f"\n  {code}: {count}回出現")
        for r in matching_rows:
            print(f"    - {r['name']} (権利確定月: {r['rights_month']}月)")
