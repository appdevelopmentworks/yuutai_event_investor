"""
Data Export Module
データエクスポート機能

Author: Yuutai Event Investor Team
Date: 2024-11-07
"""

import csv
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import io


class DataExporter:
    """データをエクスポートするクラス"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def export_to_csv(self, data: List[Dict[str, Any]], filepath: str,
                     columns: Optional[List[str]] = None) -> bool:
        """
        データをCSVファイルにエクスポート

        Args:
            data: エクスポートするデータ
            filepath: 出力ファイルパス
            columns: 出力するカラム（Noneの場合は全カラム）

        Returns:
            bool: 成功した場合True
        """
        try:
            if not data:
                self.logger.warning("エクスポートするデータがありません")
                return False

            # カラムを決定
            if columns is None:
                columns = list(data[0].keys())

            self.logger.info(f"CSVエクスポート開始: {filepath}")

            # CSVファイルに書き込み
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=columns)
                writer.writeheader()

                for row in data:
                    # 指定されたカラムのみ抽出
                    filtered_row = {k: row.get(k, '') for k in columns}
                    writer.writerow(filtered_row)

            self.logger.info(f"CSVエクスポート完了: {len(data)}件")
            return True

        except Exception as e:
            self.logger.error(f"CSVエクスポートエラー: {e}", exc_info=True)
            return False

    def export_to_json(self, data: Any, filepath: str,
                      indent: int = 2) -> bool:
        """
        データをJSONファイルにエクスポート

        Args:
            data: エクスポートするデータ
            filepath: 出力ファイルパス
            indent: インデント幅

        Returns:
            bool: 成功した場合True
        """
        try:
            self.logger.info(f"JSONエクスポート開始: {filepath}")

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=indent)

            self.logger.info("JSONエクスポート完了")
            return True

        except Exception as e:
            self.logger.error(f"JSONエクスポートエラー: {e}", exc_info=True)
            return False

    def export_stock_list(self, stocks: List[Dict[str, Any]],
                         filepath: str) -> bool:
        """
        銘柄リストをエクスポート

        Args:
            stocks: 銘柄データのリスト
            filepath: 出力ファイルパス

        Returns:
            bool: 成功した場合True
        """
        columns = [
            'code', 'name', 'rights_month', 'rights_date',
            'optimal_days', 'win_rate', 'expected_return',
            'yuutai_genre', 'yuutai_content'
        ]

        return self.export_to_csv(stocks, filepath, columns)

    def export_simulation_results(self, results: Dict[str, Any],
                                  filepath: str) -> bool:
        """
        シミュレーション結果をエクスポート

        Args:
            results: シミュレーション結果
            filepath: 出力ファイルパス

        Returns:
            bool: 成功した場合True
        """
        try:
            # ファイル拡張子で判定
            file_ext = Path(filepath).suffix.lower()

            if file_ext == '.csv':
                # all_resultsをCSVに
                if 'all_results' in results:
                    return self.export_to_csv(results['all_results'], filepath)
                else:
                    return False
            elif file_ext == '.json':
                # 全データをJSONに
                return self.export_to_json(results, filepath)
            else:
                self.logger.error(f"未対応のファイル形式: {file_ext}")
                return False

        except Exception as e:
            self.logger.error(f"シミュレーション結果エクスポートエラー: {e}")
            return False

    def export_watchlist(self, watchlist: List[Dict[str, Any]],
                        filepath: str) -> bool:
        """
        ウォッチリストをエクスポート

        Args:
            watchlist: ウォッチリストデータ
            filepath: 出力ファイルパス

        Returns:
            bool: 成功した場合True
        """
        columns = [
            'code', 'name', 'rights_month', 'rights_date',
            'optimal_days', 'win_rate', 'added_at', 'memo'
        ]

        return self.export_to_csv(watchlist, filepath, columns)

    def generate_report(self, stocks: List[Dict[str, Any]],
                       filepath: str) -> bool:
        """
        分析レポートを生成

        Args:
            stocks: 銘柄データのリスト
            filepath: 出力ファイルパス

        Returns:
            bool: 成功した場合True
        """
        try:
            self.logger.info(f"レポート生成開始: {filepath}")

            # レポートデータを作成
            report = {
                'generated_at': datetime.now().isoformat(),
                'total_stocks': len(stocks),
                'summary': self._generate_summary(stocks),
                'stocks': stocks
            }

            return self.export_to_json(report, filepath)

        except Exception as e:
            self.logger.error(f"レポート生成エラー: {e}")
            return False

    def _generate_summary(self, stocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        サマリーを生成

        Args:
            stocks: 銘柄データのリスト

        Returns:
            Dict: サマリー情報
        """
        if not stocks:
            return {}

        # 勝率の統計
        win_rates = [s['win_rate'] for s in stocks if s.get('win_rate') is not None]
        avg_win_rate = sum(win_rates) / len(win_rates) if win_rates else 0

        # 期待リターンの統計
        expected_returns = [s['expected_return'] for s in stocks if s.get('expected_return') is not None]
        avg_expected_return = sum(expected_returns) / len(expected_returns) if expected_returns else 0

        # 権利月ごとの集計
        month_counts = {}
        for stock in stocks:
            month = stock.get('rights_month')
            if month:
                month_counts[month] = month_counts.get(month, 0) + 1

        return {
            'average_win_rate': round(avg_win_rate, 4),
            'average_expected_return': round(avg_expected_return, 2),
            'stocks_by_month': month_counts,
            'high_win_rate_stocks': len([s for s in stocks if s.get('win_rate', 0) >= 0.7]),
            'positive_return_stocks': len([s for s in stocks if s.get('expected_return', 0) > 0])
        }


class ScreenshotExporter:
    """スクリーンショットをエクスポートするクラス"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def capture_widget(self, widget, filepath: str) -> bool:
        """
        ウィジェットのスクリーンショットを保存

        Args:
            widget: キャプチャするウィジェット
            filepath: 出力ファイルパス

        Returns:
            bool: 成功した場合True
        """
        try:
            from PySide6.QtGui import QPixmap

            self.logger.info(f"スクリーンショット保存: {filepath}")

            # ウィジェットをキャプチャ
            pixmap = widget.grab()

            # ファイルに保存
            success = pixmap.save(filepath)

            if success:
                self.logger.info("スクリーンショット保存完了")
            else:
                self.logger.error("スクリーンショット保存失敗")

            return success

        except Exception as e:
            self.logger.error(f"スクリーンショットエラー: {e}", exc_info=True)
            return False

    def capture_chart(self, chart_widget, filepath: str) -> bool:
        """
        チャートのスクリーンショットを保存

        Args:
            chart_widget: ChartWidgetインスタンス
            filepath: 出力ファイルパス

        Returns:
            bool: 成功した場合True
        """
        try:
            self.logger.info(f"チャート画像保存: {filepath}")

            # matplotlibのfigureから直接保存
            if hasattr(chart_widget, 'figure'):
                chart_widget.figure.savefig(
                    filepath,
                    dpi=300,
                    bbox_inches='tight',
                    facecolor='#1E1E1E'
                )
                self.logger.info("チャート画像保存完了")
                return True
            else:
                # fallback: ウィジェット全体をキャプチャ
                return self.capture_widget(chart_widget, filepath)

        except Exception as e:
            self.logger.error(f"チャート画像保存エラー: {e}", exc_info=True)
            return False


class PDFExporter:
    """PDF出力機能"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def export_stock_analysis_to_pdf(
        self,
        stock_data: Dict[str, Any],
        result_data: Dict[str, Any],
        chart_widget,
        filepath: str
    ) -> bool:
        """
        銘柄分析結果をPDFにエクスポート

        Args:
            stock_data: 銘柄データ
            result_data: バックテスト結果データ
            chart_widget: ChartWidgetインスタンス
            filepath: 出力ファイルパス

        Returns:
            bool: 成功した場合True
        """
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.lib.units import mm
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            import matplotlib.pyplot as plt

            self.logger.info(f"PDF出力開始: {filepath}")

            # 日本語フォントを登録（Windows環境）
            try:
                import platform
                if platform.system() == 'Windows':
                    pdfmetrics.registerFont(TTFont('Japanese', 'msgothic.ttc'))
                    font_name = 'Japanese'
                else:
                    font_name = 'Helvetica'
            except:
                font_name = 'Helvetica'
                self.logger.warning("日本語フォントの登録に失敗しました")

            # PDFドキュメント作成
            doc = SimpleDocTemplate(filepath, pagesize=A4)
            story = []

            # スタイル設定
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontName=font_name,
                fontSize=18,
                textColor=colors.HexColor('#1E90FF')
            )
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontName=font_name,
                fontSize=14,
                textColor=colors.HexColor('#333333')
            )

            # タイトル
            title = Paragraph(f"銘柄分析レポート", title_style)
            story.append(title)
            story.append(Spacer(1, 10*mm))

            # 銘柄情報
            stock_info = Paragraph(
                f"{stock_data.get('name', '不明')} ({stock_data.get('code', '')})",
                heading_style
            )
            story.append(stock_info)
            story.append(Spacer(1, 5*mm))

            # 基本情報テーブル
            basic_data = [
                ['項目', '値'],
                ['権利確定月', f"{stock_data.get('rights_month', '-')}月"],
                ['権利確定日', stock_data.get('rights_date', '-')],
                ['最適買入日', f"{result_data.get('optimal_days', 0)}日前"],
                ['勝率', f"{result_data.get('win_rate', 0)*100:.1f}%"],
                ['期待リターン', f"{result_data.get('expected_return', 0):+.2f}%"],
            ]

            basic_table = Table(basic_data, colWidths=[60*mm, 80*mm])
            basic_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4A4A4A')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F5F5F5')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            story.append(basic_table)
            story.append(Spacer(1, 10*mm))

            # 詳細統計テーブル
            stats_heading = Paragraph("詳細統計", heading_style)
            story.append(stats_heading)
            story.append(Spacer(1, 5*mm))

            stats_data = [
                ['項目', '値'],
                ['総トレード数', f"{result_data.get('total_count', 0)}回"],
                ['勝ちトレード数', f"{result_data.get('win_count', 0)}回"],
                ['負けトレード数', f"{result_data.get('lose_count', 0)}回"],
                ['最大リターン', f"{result_data.get('max_win_return', 0):+.2f}%"],
                ['最大損失', f"{result_data.get('max_lose_return', 0):+.2f}%"],
                ['平均勝ちリターン', f"{result_data.get('avg_win_return', 0):+.2f}%"],
                ['平均負けリターン', f"{result_data.get('avg_lose_return', 0):+.2f}%"],
            ]

            stats_table = Table(stats_data, colWidths=[60*mm, 80*mm])
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4A4A4A')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F5F5F5')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            story.append(stats_table)
            story.append(Spacer(1, 10*mm))

            # チャート画像を追加
            if chart_widget and hasattr(chart_widget, 'figure'):
                chart_heading = Paragraph("分析チャート", heading_style)
                story.append(chart_heading)
                story.append(Spacer(1, 5*mm))

                # チャートを一時ファイルとして保存
                temp_chart_path = filepath.replace('.pdf', '_temp_chart.png')
                chart_widget.figure.savefig(
                    temp_chart_path,
                    dpi=150,
                    bbox_inches='tight',
                    facecolor='white'
                )

                # 画像を追加
                img = Image(temp_chart_path, width=160*mm, height=120*mm)
                story.append(img)

            # フッター
            story.append(Spacer(1, 10*mm))
            footer = Paragraph(
                f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>Yuutai Event Investor",
                styles['Normal']
            )
            story.append(footer)

            # PDF生成
            doc.build(story)

            # 一時ファイルを削除
            try:
                Path(temp_chart_path).unlink()
            except:
                pass

            self.logger.info("PDF出力完了")
            return True

        except ImportError as e:
            self.logger.error(f"reportlabがインストールされていません: {e}")
            self.logger.error("PDF出力を使用するには 'pip install reportlab' を実行してください")
            return False
        except Exception as e:
            self.logger.error(f"PDF出力エラー: {e}", exc_info=True)
            return False


class ConfigExporter:
    """設定のエクスポート/インポート"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def export_settings(self, settings: Dict[str, Any], filepath: str) -> bool:
        """
        設定をエクスポート

        Args:
            settings: 設定データ
            filepath: 出力ファイルパス

        Returns:
            bool: 成功した場合True
        """
        try:
            self.logger.info(f"設定エクスポート: {filepath}")

            exporter = DataExporter()
            return exporter.export_to_json(settings, filepath)

        except Exception as e:
            self.logger.error(f"設定エクスポートエラー: {e}")
            return False

    def import_settings(self, filepath: str) -> Optional[Dict[str, Any]]:
        """
        設定をインポート

        Args:
            filepath: 設定ファイルパス

        Returns:
            Dict: 設定データ、失敗時はNone
        """
        try:
            self.logger.info(f"設定インポート: {filepath}")

            with open(filepath, 'r', encoding='utf-8') as f:
                settings = json.load(f)

            self.logger.info("設定インポート完了")
            return settings

        except Exception as e:
            self.logger.error(f"設定インポートエラー: {e}")
            return None
