# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Yuutai Event Investor** is a desktop application for analyzing optimal timing for Japanese stock shareholder benefit (株主優待) event investing. It uses historical backtesting to calculate win rates and expected returns for different purchase timings before ex-dividend dates.

**Key Concept:** The app analyzes past 10 years of stock price data to determine the statistically optimal day to buy before the ex-dividend date (権利付最終日) to maximize returns from shareholder benefit events.

**Future Extension:** The app is designed to support high-dividend stocks (高配当銘柄) in addition to shareholder benefit stocks. Database schema and CSV import templates are prepared. See `docs/FUTURE_FEATURES.md` for details.

## Running the Application

```bash
# Install dependencies
pip install -r requirements.txt

# Run the main application
python main.py

# Initialize/reset database
python scripts/init_database.py

# Run backtest test script
python scripts/test_backtest.py
```

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_database.py
pytest tests/test_data_fetcher.py

# Run tests with coverage
pytest --cov=src tests/
```

## Database Management

```bash
# Initialize database from scratch
python scripts/init_database.py

# Apply database optimizations (indexes and views)
sqlite3 data/yuutai.db < data/optimize_database.sql

# Database location
data/yuutai.db
```

## Architecture Overview

### Core Data Flow

1. **Data Acquisition** → 2. **Backtest Calculation** → 3. **UI Display**

```
Web Scraping (96ut.com, yutai.net-ir.ne.jp)
    ↓
Database (SQLite) ← Stock Data + Price History
    ↓
Calculator.find_optimal_timing()
    ↓
MainWindow → DetailPanel → ChartWidget
```

### Key Architecture Patterns

**Backtest Calculation Pipeline:**
```
Calculator.calculate_returns(df, buy_days_before, kenrlast, rights_month)
    → Returns (win_trades, lose_trades) DataFrames
    → Calculator.calculate_statistics(win_trades, lose_trades)
    → Returns statistics dict with win_rate, expected_return, etc.
```

The calculator scans 1-120 days before ex-dividend date, running backtests for each day to find the optimal timing with highest `expected_return * win_rate` score.

**期待リターン (Expected Return) Formula:**
```python
expected_return = (avg_win_return × win_rate) + (avg_lose_return × (1 - win_rate))
```

**Widget Hierarchy:**
```
MainWindow (main_window_v3.py) - Current production version
├── FilterPanel - Left sidebar for filtering stocks
├── StockListWidget - Center panel showing filtered stocks
├── DetailPanel - Right panel with analysis
│   ├── StockInfoCard - Summary metrics (6 cards in 3×2 grid)
│   ├── ChartWidget - matplotlib charts
│   └── DetailStatsTable - Detailed statistics
└── WatchlistWidget - Separate tab for saved stocks
```

### Critical Data Structure

**Backtest Result Dictionary** (returned by `Calculator.find_optimal_timing`):
```python
{
    'ticker': str,           # Stock code
    'rights_month': int,     # Ex-dividend month
    'optimal_days': int,     # Optimal buy day (days before ex-dividend)
    'win_rate': float,       # Win rate (0.0-1.0)
    'expected_return': float,# Expected return percentage
    'win_count': int,
    'lose_count': int,
    'total_count': int,
    'avg_win_return': float,
    'max_win_return': float,
    'avg_lose_return': float,
    'max_lose_return': float,
    'all_results': list      # Results for all tested days
}
```

**IMPORTANT:** `DetailStatsTable.update_stats()` expects these exact keys:
- `total_count` (NOT `total_trades`)
- `max_win_return` (NOT `max_return`)
- `max_lose_return` (NOT `max_loss`)
- `avg_lose_return` (NOT `avg_loss_return`)

**Key Name Mismatch:** `all_results` uses `days_before` but DB uses `buy_days_before`:
```python
# Calculator output
{'days_before': 52, 'win_rate': 0.6, ...}

# When saving to DB, use:
buy_days_before = day_result.get('days_before', day_result.get('buy_days_before', 0))
```

### Database Schema

**Core Tables:**
- `stocks` - Stock master (code, name, rights_month, rights_date, yuutai_genre, yuutai_content)
- `price_history` - Daily OHLCV data (code, date, open, high, low, close, volume)
- `simulation_cache` - Cached backtest results
- `watchlist` - User's watched stocks
- `notifications` - Buy timing notifications

**Key Indexes:**
- `idx_stocks_rights_month` - Filter by ex-dividend month
- `idx_price_code_date` - Stock price lookups
- `idx_simulation_score` - Sort by expected_return DESC, win_rate DESC

**Useful Views:**
- `v_watchlist_detail` - Watchlist with latest backtest results
- `v_today_notifications` - Today's pending notifications
- `v_high_winrate_stocks` - Stocks with win_rate >= 0.7

## Multi-threading Architecture

### Backtest Processing
- `BatchCalculationWorker` - Parallel backtest for multiple stocks (uses `threading.Thread` + `QObject` signals)
- Uses `ThreadPoolExecutor` with configurable `max_workers` (default: 4)
- Progress tracking via Qt signals: `progress_updated`, `stock_completed`, `batch_completed`
- Access via menu: Tools → Batch Backtest (月別 or 全銘柄)

### Notification System
- `NotificationWorker` - Background notification checker (uses `threading.Thread`)
- `NotificationScheduler` - Time-based notification (default: 9:00, 15:00)
- Desktop notifications via `DesktopNotifier` (Windows/macOS/Linux)

**Note:** All background workers use `threading.Thread` instead of `QThread` to avoid SQLite crashes on macOS. See Common Pitfalls #6.

## Key File Relationships

**Main Window Versions:**
- `main_window.py` - Phase 1 (deprecated)
- `main_window_v2.py` - Phase 3 (deprecated)
- `main_window_v3.py` - **CURRENT** production version (Phase 4+)

**Calculator Chain:**
- `Calculator` (calculator.py) - Core backtest logic
- `OptimalTimingCalculator` (calculator.py) - Wrapper with data fetcher integration
- `DataFetcher` (data_fetcher.py) - yfinance stock data fetcher
- `DatabaseManager` (database.py) - SQLite operations

**Export Capabilities:**
- `DataExporter` - CSV/JSON export
- `ScreenshotExporter` - Widget screenshots
- `PDFExporter` - Analysis reports (requires reportlab)
- `ConfigExporter` - Settings import/export

## Important Implementation Details

### Japanese Font Configuration (chart_widget.py)
```python
import platform
if platform.system() == 'Windows':
    matplotlib.rc('font', family='MS Gothic')
elif platform.system() == 'Darwin':
    matplotlib.rc('font', family='Hiragino Sans')
else:
    matplotlib.rc('font', family='Noto Sans CJK JP')
```

### Backtest Date Logic (calculator.py)
The "kenrlast" parameter determines ex-dividend calculation:
- Japan stocks: `kenrlast=2` (2 business days before month-end)
- US stocks: `kenrlast=1` (1 business day before month-end)

Ex-dividend detection uses month boundary crossing:
```python
data["権利確定日"] = data["Month"] != data["MonthSft"]
data["権利付最終日"] = data["権利確定日"].shift(-kenrlast)
```

### StockInfoCard Display Bug Fix
The card shows 6 metrics in a 3×2 grid (increased from 4 in 2×2):
- Row 0: 最適買入日, 勝率
- Row 1: 期待リターン, 総トレード
- Row 2: 平均勝ち, 平均負け

Card height is 220px (increased from 180px).

## Common Pitfalls

1. **Database Key Mismatch:** Always use `stock.get('code')` not `stock[0]` - database returns dictionaries, not tuples.

2. **Missing rights_date:** Stocks must have `rights_date` column populated. The schema was updated in Phase 3 to add this field.

3. **Chart Display Issues:** If matplotlib shows font warnings for Japanese characters, the platform-specific font configuration may not be set correctly.

4. **Notification Libraries:** Platform-specific dependencies are optional:
   - Windows: `winotify`
   - macOS: `pync`
   - Linux: `notify2`

   Qt fallback (`QSystemTrayIcon`) is used if these aren't available.

5. **PDF Export:** Requires `reportlab` library. If missing, PDF export will log an error but won't crash.

6. **QThread + SQLite Crash on macOS:** Using QThread with SQLite causes SIGSEGV crashes on macOS due to thread affinity issues.

   **Solution:** Use `threading.Thread` with `QObject` signals instead of `QThread`:
   ```python
   # BAD - causes crash on macOS
   class MyWorker(QThread):
       finished = Signal(dict)
       def run(self):
           db = DatabaseManager()
           # ... SQLite operations
           self.finished.emit(result)

   # GOOD - works on all platforms
   class MyWorkerSignals(QObject):
       finished = Signal(dict)

   class MyWorker:
       def __init__(self):
           self.signals = MyWorkerSignals()
           self._thread = None

       @property
       def finished(self):
           return self.signals.finished

       def start(self):
           self._thread = threading.Thread(target=self._run, daemon=True)
           self._thread.start()

       def _run(self):
           fetcher = StockDataFetcher()
           try:
               # ... SQLite operations
               self.signals.finished.emit(result)
           finally:
               fetcher.close()  # Always cleanup!
   ```

   **Root cause:** macOS has stricter thread affinity for SQLite connections than Windows/Linux.

## Version History

- **v1.0.0** - Initial release with basic functionality
- **v1.1.0** - Phase 5 additions:
  - Desktop notifications (multi-platform)
  - PDF export
  - Batch processing with multi-threading
  - Keyboard shortcuts
  - Database optimizations
- **v1.1.1** - macOS crash fix:
  - Fixed SIGSEGV crash on macOS caused by QThread + SQLite conflict
  - Replaced QThread with Python's threading.Thread for AnalysisWorker and TradeDetailsWorker
  - Added DataFetcher.close() method for proper resource cleanup
  - Added DatabaseManager.close() method for connection cleanup

## Development Workflow

When adding new features:

1. **Database changes** → Update `create_tables.sql` and increment schema_version
2. **Calculator changes** → Ensure return dict matches expected keys in UI widgets
3. **UI changes** → Update corresponding widget in `src/ui/widgets/`
4. **Export features** → Add to appropriate exporter class in `export.py`
5. **Background tasks** → Use `threading.Thread` with `QObject` signals (NOT QThread - causes SQLite crashes on macOS)

When modifying backtest logic:
- Changes to `Calculator.calculate_returns()` affect all historical analysis
- Test with `scripts/test_backtest.py` before modifying
- Cache invalidation: delete rows from `simulation_cache` table

## External Dependencies

**Stock Data:** yfinance (Yahoo Finance API)
**Web Scraping:** 96ut.com, yutai.net-ir.ne.jp
**UI Framework:** PySide6 (Qt6)
**Charts:** matplotlib
**Database:** SQLite3

## Japanese Terminology Reference

- 株主優待 (kabunushi yuutai) = Shareholder benefit
- 権利確定日 (kenri kakutei bi) = Ex-dividend date
- 権利付最終日 (kenritsuki saishū bi) = Last day to own stock for benefits
- 勝率 (shōritsu) = Win rate
- 期待リターン (kitai ritān) = Expected return
- 買入日 (kainyu bi) = Purchase date
- 高配当 (kō haitō) = High dividend
- 配当利回り (haitō rimawari) = Dividend yield

## Important Configuration: kenrlast

**kenrlast** determines how many business days before the month-end the ex-dividend date occurs:
- Japan stocks: `kenrlast=2` (2 business days before month-end) - **Current default**
- US stocks: `kenrlast=1` (1 business day before month-end)

**Configuration location:** `config/settings.json`
```json
{
  "kenrlast": 2
}
```

**Future-proofing:** If Japan changes the rule to 1 business day (like US), simply change `kenrlast` to 1 and clear simulation cache. No code changes required.

**Why rights_month instead of rights_date:**
- `rights_date` (exact date) changes yearly and requires manual updates
- `rights_month` (month only) is stable and calculated dynamically using `kenrlast`
- This design supports future regulatory changes without schema modifications
