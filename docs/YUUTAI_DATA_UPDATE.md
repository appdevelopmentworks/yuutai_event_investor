# 優待銘柄データの取得・更新方法

## クイックスタート

### 全銘柄を一括取得してデータベースに保存

```bash
python scripts/fetch_all_yuutai_stocks.py
```

これで、全月（1-12月）の優待銘柄データを取得し、自動的にデータベースに保存されます。

## 詳細な使い方

### 1. 全銘柄取得（デフォルト）

フォールバック戦略で全月のデータを取得：

```bash
python scripts/fetch_all_yuutai_stocks.py
```

**動作:**
- yutai.net-ir.ne.jp を優先的に試行
- 失敗した場合は 96ut.com にフォールバック
- 全月（1-12月）のデータを取得
- データベースに自動保存（新規挿入 or 更新）

### 2. 全ソースから取得して統合

複数のソースからデータを取得して重複除去：

```bash
python scripts/fetch_all_yuutai_stocks.py --all
```

**動作:**
- yutai.net-ir.ne.jp と 96ut.com の両方から取得
- 重複する銘柄は自動的に統合
- より多くの情報を持つデータを優先

### 3. 特定の月のみ取得

```bash
# 3月の銘柄のみ取得
python scripts/fetch_all_yuutai_stocks.py --month 3

# 12月の銘柄のみ取得
python scripts/fetch_all_yuutai_stocks.py --month 12
```

### 4. 特定のソースから取得

```bash
# yutai.net-ir.ne.jp のみから取得
python scripts/fetch_all_yuutai_stocks.py --source yutai_net

# 96ut.com のみから取得
python scripts/fetch_all_yuutai_stocks.py --source 96ut

# 特定のソースで特定の月
python scripts/fetch_all_yuutai_stocks.py --source yutai_net --month 3
```

## 実行例

### 全銘柄取得

```bash
$ python scripts/fetch_all_yuutai_stocks.py

============================================================
全優待銘柄取得スクリプト
============================================================

============================================================
優待銘柄データ取得
============================================================
モード: fallback
対象月: 全月（1-12月）

データ取得中...
yutai.net-ir.ne.jp でスクレイピング開始（フォールバックモード）

取得件数: 1523件

月別統計:
  1月: 87件
  2月: 123件
  3月: 426件
  4月: 76件
  5月: 95件
  6月: 156件
  7月: 64件
  8月: 89件
  9月: 234件
  10月: 68件
  11月: 45件
  12月: 160件

データベースに保存中...
  100/1523件処理中...
  200/1523件処理中...
  ...
  1500/1523件処理中...

処理完了: 1523件
  新規挿入: 1234件
  更新: 289件
  エラー: 0件

============================================================
処理完了
============================================================
成功: 1523件
失敗: 0件

アプリを再起動すると新しいデータが表示されます。
```

## データの確認

### アプリで確認

```bash
python main.py
```

アプリを起動すると、取得した銘柄が左側のグリッドに表示されます。

### データベースで直接確認

```python
from src.core.database import DatabaseManager

db = DatabaseManager()
stocks = db.get_all_stocks()

print(f"総銘柄数: {len(stocks)}件")

# 月別の件数
month_counts = {}
for stock in stocks:
    m = stock['rights_month']
    month_counts[m] = month_counts.get(m, 0) + 1

for m in sorted(month_counts.keys()):
    print(f"{m}月: {month_counts[m]}件")
```

## データの更新

### 定期的な更新

優待情報は定期的に変更されるため、月1回程度の更新を推奨します：

```bash
# 月初に実行
python scripts/fetch_all_yuutai_stocks.py
```

### 特定の月のみ更新

権利確定月の1-2ヶ月前に、その月のデータのみ更新：

```bash
# 現在2月の場合、3月の銘柄を更新
python scripts/fetch_all_yuutai_stocks.py --month 3
```

## トラブルシューティング

### 問題: データが取得できない

**確認事項:**
1. ネットワーク接続を確認
2. サイトがアクセス可能か確認

**解決策:**
```bash
# 別のソースを試す
python scripts/fetch_all_yuutai_stocks.py --source 96ut
```

### 問題: エラーが多発する

**原因:** サイト構造が変更されている可能性

**解決策:**
1. ログを確認
2. `src/scrapers/selectors.json` を更新
3. 詳細は `docs/SCRAPING_USAGE.md` を参照

### 問題: 重複データが保存される

**確認:**
スクリプトは自動的に重複をチェックして更新します。もし重複が発生した場合：

```sql
-- 重複を確認
SELECT code, COUNT(*) as count
FROM stocks
GROUP BY code
HAVING count > 1;

-- 重複を削除（最新のみ残す）
DELETE FROM stocks
WHERE rowid NOT IN (
    SELECT MAX(rowid)
    FROM stocks
    GROUP BY code
);
```

## パフォーマンス

### 実行時間の目安

- **全月取得**: 約5-10分（1500件程度）
- **特定月取得**: 約30秒-2分（100-400件程度）
- **特定ソース**: 約2-5分

※ネットワーク速度やサイトのレスポンスによって変動

### 高速化のヒント

1. **特定の月のみ取得**
   ```bash
   python scripts/fetch_all_yuutai_stocks.py --month 3
   ```

2. **並列処理** (上級者向け)
   複数の月を同時に取得する場合は、スクリプトを複数起動

## 次のステップ

データ取得後は、バックテストを実行して最適な買入タイミングを計算します：

```bash
# 全銘柄のバックテストを実行
python scripts/run_all_backtests.py
```

詳細は `docs/SCRAPING_USAGE.md` を参照してください。

## まとめ

✅ **基本**: `python scripts/fetch_all_yuutai_stocks.py`
✅ **特定月**: `--month 3`
✅ **特定ソース**: `--source yutai_net`
✅ **全ソース統合**: `--all`

データ取得後、アプリを再起動すると新しいデータが表示されます。
