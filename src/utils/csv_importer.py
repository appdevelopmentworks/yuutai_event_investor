"""
CSV Import Utility
CSV形式の銘柄リストをインポートするユーティリティ

Author: Yuutai Event Investor Team
Date: 2025-11-07
"""

import csv
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class CSVImporter:
    """CSVファイルから銘柄データをインポートするクラス"""

    # 必須カラム
    REQUIRED_COLUMNS = ['code', 'name', 'rights_date']

    # オプションカラム（デフォルト値あり）
    OPTIONAL_COLUMNS = {
        'rights_month': None,
        'yuutai_genre': 'その他',
        'yuutai_content': '',
        'min_investment': 0
    }

    def __init__(self, db_manager):
        """
        初期化

        Args:
            db_manager: DatabaseManagerインスタンス
        """
        self.db = db_manager
        self.logger = logging.getLogger(__name__)

    def validate_csv_file(self, file_path: str) -> Tuple[bool, str, List[str]]:
        """
        CSVファイルのフォーマットを検証

        Args:
            file_path: CSVファイルパス

        Returns:
            Tuple[bool, str, List[str]]: (検証結果, エラーメッセージ, カラム名リスト)
        """
        try:
            path = Path(file_path)

            # ファイル存在チェック
            if not path.exists():
                return False, f"ファイルが見つかりません: {file_path}", []

            # ファイル拡張子チェック
            if path.suffix.lower() not in ['.csv', '.txt']:
                return False, "CSVファイル (.csv) を選択してください", []

            # CSVファイル読み込み
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                columns = reader.fieldnames

                if not columns:
                    return False, "CSVファイルにヘッダー行がありません", []

                # 必須カラムチェック
                missing_columns = [col for col in self.REQUIRED_COLUMNS if col not in columns]
                if missing_columns:
                    return False, f"必須カラムが不足しています: {', '.join(missing_columns)}", columns

                self.logger.info(f"CSV検証成功: {file_path}")
                return True, "", columns

        except UnicodeDecodeError:
            return False, "文字エンコーディングエラー（UTF-8で保存してください）", []
        except Exception as e:
            self.logger.error(f"CSV検証エラー: {e}", exc_info=True)
            return False, f"ファイル読み込みエラー: {str(e)}", []

    def parse_csv_file(self, file_path: str) -> Tuple[List[Dict], List[str]]:
        """
        CSVファイルを解析して銘柄データを抽出

        Args:
            file_path: CSVファイルパス

        Returns:
            Tuple[List[Dict], List[str]]: (銘柄データリスト, エラーメッセージリスト)
        """
        stocks = []
        errors = []

        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)

                for row_num, row in enumerate(reader, start=2):  # 2から開始（ヘッダー行考慮）
                    try:
                        # 必須フィールドの検証
                        code = row.get('code', '').strip()
                        name = row.get('name', '').strip()
                        rights_date = row.get('rights_date', '').strip()

                        if not code:
                            errors.append(f"行{row_num}: 銘柄コードが空です")
                            continue

                        if not name:
                            errors.append(f"行{row_num}: 銘柄名が空です")
                            continue

                        if not rights_date:
                            errors.append(f"行{row_num}: 権利確定日が空です")
                            continue

                        # 権利確定日の検証（YYYY-MM-DD形式）
                        try:
                            datetime.strptime(rights_date, '%Y-%m-%d')
                        except ValueError:
                            errors.append(f"行{row_num}: 権利確定日の形式が不正です（YYYY-MM-DD形式で入力してください）")
                            continue

                        # 権利確定月の抽出（rights_monthが指定されていない場合）
                        rights_month = row.get('rights_month', '').strip()
                        if not rights_month:
                            try:
                                date_obj = datetime.strptime(rights_date, '%Y-%m-%d')
                                rights_month = date_obj.month
                            except:
                                rights_month = None
                        else:
                            try:
                                rights_month = int(rights_month)
                                if not (1 <= rights_month <= 12):
                                    errors.append(f"行{row_num}: 権利確定月は1-12の範囲で指定してください")
                                    continue
                            except ValueError:
                                errors.append(f"行{row_num}: 権利確定月が数値ではありません")
                                continue

                        # 最低投資金額の検証
                        min_investment = row.get('min_investment', '').strip()
                        if min_investment:
                            try:
                                min_investment = int(min_investment)
                            except ValueError:
                                self.logger.warning(f"行{row_num}: 最低投資金額が数値ではありません（デフォルト値0を使用）")
                                min_investment = 0
                        else:
                            min_investment = 0

                        # 銘柄データを構築
                        stock_data = {
                            'code': code,
                            'name': name,
                            'rights_month': rights_month,
                            'rights_date': rights_date,
                            'yuutai_genre': row.get('yuutai_genre', 'その他').strip() or 'その他',
                            'yuutai_content': row.get('yuutai_content', '').strip(),
                            'min_investment': min_investment
                        }

                        stocks.append(stock_data)
                        self.logger.debug(f"行{row_num}: {code} - {name} を解析")

                    except Exception as e:
                        errors.append(f"行{row_num}: 解析エラー - {str(e)}")
                        self.logger.error(f"行{row_num}の解析エラー: {e}", exc_info=True)

            self.logger.info(f"CSV解析完了: {len(stocks)}件の銘柄データを抽出（エラー: {len(errors)}件）")
            return stocks, errors

        except Exception as e:
            self.logger.error(f"CSVファイル解析エラー: {e}", exc_info=True)
            return [], [f"ファイル読み込みエラー: {str(e)}"]

    def import_stocks(self, file_path: str, overwrite: bool = False) -> Tuple[int, int, List[str]]:
        """
        CSVファイルから銘柄データをデータベースにインポート

        Args:
            file_path: CSVファイルパス
            overwrite: 既存データを上書きするか（True: 上書き, False: スキップ）

        Returns:
            Tuple[int, int, List[str]]: (成功件数, スキップ件数, エラーメッセージリスト)
        """
        # CSV検証
        is_valid, error_msg, columns = self.validate_csv_file(file_path)
        if not is_valid:
            return 0, 0, [error_msg]

        # CSV解析
        stocks, parse_errors = self.parse_csv_file(file_path)
        if not stocks:
            return 0, 0, parse_errors if parse_errors else ["インポート可能な銘柄データがありません"]

        # データベースにインポート
        success_count = 0
        skip_count = 0
        import_errors = []

        for stock in stocks:
            try:
                code = stock['code']
                rights_month = stock['rights_month']

                # 既存データの確認（複合主キーで検索）
                existing = self.db.get_stock(code, rights_month)
                existing_match = existing  # get_stockは指定した(code, rights_month)のレコードを返す

                if existing_match:
                    if overwrite:
                        # 既存データを更新
                        self.db.update_stock(
                            code=code,
                            name=stock['name'],
                            rights_month=stock['rights_month'],
                            rights_date=stock['rights_date'],
                            yuutai_genre=stock['yuutai_genre'],
                            yuutai_content=stock['yuutai_content'],
                            min_investment=stock['min_investment']
                        )
                        success_count += 1
                        self.logger.info(f"銘柄更新: {code}({rights_month}月) - {stock['name']}")
                    else:
                        # 既存データをスキップ
                        skip_count += 1
                        self.logger.debug(f"銘柄スキップ（既存）: {code}({rights_month}月) - {stock['name']}")
                else:
                    # 新規データを追加
                    success = self.db.insert_stock(
                        code=code,
                        name=stock['name'],
                        rights_month=stock['rights_month'],
                        rights_date=stock['rights_date'],
                        yuutai_genre=stock['yuutai_genre'],
                        yuutai_content=stock['yuutai_content']
                    )
                    if success:
                        success_count += 1
                        self.logger.info(f"銘柄追加: {code}({rights_month}月) - {stock['name']}")
                    else:
                        import_errors.append(f"{code}({rights_month}月) - {stock['name']}: insert_stock failed")

            except Exception as e:
                error_msg = f"{stock['code']} - {stock['name']}: {str(e)}"
                import_errors.append(error_msg)
                self.logger.error(f"銘柄インポートエラー: {error_msg}", exc_info=True)

        all_errors = parse_errors + import_errors
        self.logger.info(f"インポート完了: 成功 {success_count}件, スキップ {skip_count}件, エラー {len(all_errors)}件")

        return success_count, skip_count, all_errors

    def get_csv_format_info(self) -> Dict[str, str]:
        """
        CSVフォーマット情報を取得

        Returns:
            Dict[str, str]: フォーマット情報（カラム名: 説明）
        """
        return {
            'code': '銘柄コード（必須） - 例: 8001',
            'name': '銘柄名（必須） - 例: 伊藤忠商事',
            'rights_date': '権利確定日（必須） - YYYY-MM-DD形式 例: 2025-03-31',
            'rights_month': '権利確定月（オプション） - 1-12 ※省略時は権利確定日から自動判定',
            'yuutai_genre': '優待ジャンル（オプション） - 例: 食品、金券、買物券 ※省略時は「その他」',
            'yuutai_content': '優待内容（オプション） - 例: カタログギフト（3000円相当）',
            'min_investment': '最低投資金額（オプション） - 例: 300000 ※省略時は0'
        }
