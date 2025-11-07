"""
Import Dialog
CSVインポートダイアログ

Author: Yuutai Event Investor Team
Date: 2025-11-07
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QRadioButton, QTextEdit, QProgressBar, QGroupBox,
    QCheckBox, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QFont
import logging
from pathlib import Path
from typing import Optional

from src.utils.csv_importer import CSVImporter


class ImportWorker(QThread):
    """CSVインポートのバックグラウンドワーカー"""

    progress_updated = Signal(int, str)  # 進捗, メッセージ
    import_completed = Signal(int, int, list)  # 成功件数, スキップ件数, エラーリスト

    def __init__(self, importer: CSVImporter, file_path: str, overwrite: bool):
        super().__init__()
        self.importer = importer
        self.file_path = file_path
        self.overwrite = overwrite

    def run(self):
        """インポート実行"""
        try:
            self.progress_updated.emit(10, "CSVファイルを検証中...")

            # 検証
            is_valid, error_msg, columns = self.importer.validate_csv_file(self.file_path)
            if not is_valid:
                self.import_completed.emit(0, 0, [error_msg])
                return

            self.progress_updated.emit(30, "データを解析中...")

            # インポート
            success, skipped, errors = self.importer.import_stocks(self.file_path, self.overwrite)

            self.progress_updated.emit(100, "完了")
            self.import_completed.emit(success, skipped, errors)

        except Exception as e:
            self.import_completed.emit(0, 0, [f"インポートエラー: {str(e)}"])


class ImportDialog(QDialog):
    """CSVインポートダイアログ"""

    import_completed = Signal()  # インポート完了シグナル

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.importer = CSVImporter(db_manager)
        self.logger = logging.getLogger(__name__)
        self.worker: Optional[ImportWorker] = None
        self.selected_file_path: Optional[str] = None

        self.init_ui()

    def init_ui(self):
        """UIを初期化"""
        self.setWindowTitle("銘柄リストをインポート")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # ========================================
        # タイトル
        # ========================================
        title_label = QLabel("CSVファイルから銘柄をインポート")
        title_label.setFont(QFont("", 14, QFont.Bold))
        layout.addWidget(title_label)

        # ========================================
        # ファイル選択
        # ========================================
        file_group = QGroupBox("ステップ1: CSVファイルを選択")
        file_layout = QVBoxLayout(file_group)

        file_select_layout = QHBoxLayout()
        self.file_path_label = QLabel("ファイルが選択されていません")
        self.file_path_label.setStyleSheet("color: #B0B0B0; padding: 5px;")
        file_select_layout.addWidget(self.file_path_label, 1)

        self.browse_btn = QPushButton("参照...")
        self.browse_btn.setFixedWidth(100)
        self.browse_btn.clicked.connect(self.browse_file)
        file_select_layout.addWidget(self.browse_btn)

        file_layout.addLayout(file_select_layout)

        # フォーマット情報
        format_label = QLabel("📄 CSVフォーマット:")
        format_label.setFont(QFont("", 9, QFont.Bold))
        file_layout.addWidget(format_label)

        format_info = self.importer.get_csv_format_info()
        format_text = "\n".join([f"  • {key}: {value}" for key, value in format_info.items()])

        self.format_info_label = QLabel(format_text)
        self.format_info_label.setStyleSheet("color: #909090; font-size: 8pt; padding-left: 10px;")
        self.format_info_label.setWordWrap(True)
        file_layout.addWidget(self.format_info_label)

        layout.addWidget(file_group)

        # ========================================
        # インポートオプション
        # ========================================
        option_group = QGroupBox("ステップ2: インポートオプション")
        option_layout = QVBoxLayout(option_group)

        self.overwrite_check = QCheckBox("既存の銘柄データを上書きする")
        self.overwrite_check.setStyleSheet("padding: 5px;")
        option_layout.addWidget(self.overwrite_check)

        option_help = QLabel("※ チェックを外すと、既存銘柄はスキップされます")
        option_help.setStyleSheet("color: #909090; font-size: 8pt; padding-left: 20px;")
        option_layout.addWidget(option_help)

        layout.addWidget(option_group)

        # ========================================
        # プログレスバー
        # ========================================
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet("color: #B0B0B0; font-size: 9pt;")
        self.progress_label.setVisible(False)
        layout.addWidget(self.progress_label)

        # ========================================
        # 結果表示
        # ========================================
        result_group = QGroupBox("インポート結果")
        result_layout = QVBoxLayout(result_group)

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setMaximumHeight(150)
        self.result_text.setStyleSheet("""
            QTextEdit {
                background-color: #2D2D2D;
                color: #E0E0E0;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Consolas', monospace;
                font-size: 9pt;
            }
        """)
        result_layout.addWidget(self.result_text)

        layout.addWidget(result_group)

        # ========================================
        # ボタン
        # ========================================
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.import_btn = QPushButton("インポート開始")
        self.import_btn.setFixedWidth(150)
        self.import_btn.setFixedHeight(35)
        self.import_btn.setEnabled(False)
        self.import_btn.setStyleSheet("""
            QPushButton {
                background-color: #1E90FF;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4169E1;
            }
            QPushButton:disabled {
                background-color: #404040;
                color: #808080;
            }
        """)
        self.import_btn.clicked.connect(self.start_import)
        button_layout.addWidget(self.import_btn)

        self.close_btn = QPushButton("閉じる")
        self.close_btn.setFixedWidth(100)
        self.close_btn.setFixedHeight(35)
        self.close_btn.clicked.connect(self.close)
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)

    def browse_file(self):
        """ファイル選択ダイアログを開く"""
        # プロジェクトルートのdataディレクトリをデフォルトに設定
        project_root = Path(__file__).parent.parent.parent
        data_dir = project_root / "data"

        # dataディレクトリが存在しない場合は作成
        data_dir.mkdir(parents=True, exist_ok=True)

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "CSVファイルを選択",
            str(data_dir),
            "CSV Files (*.csv);;All Files (*.*)"
        )

        if file_path:
            self.selected_file_path = file_path
            self.file_path_label.setText(file_path)
            self.file_path_label.setStyleSheet("color: #E0E0E0; padding: 5px;")
            self.import_btn.setEnabled(True)
            self.result_text.clear()
            self.logger.info(f"CSVファイル選択: {file_path}")

    def start_import(self):
        """インポート開始"""
        if not self.selected_file_path:
            QMessageBox.warning(self, "エラー", "CSVファイルを選択してください")
            return

        # UI無効化
        self.import_btn.setEnabled(False)
        self.browse_btn.setEnabled(False)
        self.overwrite_check.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_label.setVisible(True)
        self.result_text.clear()

        # ワーカー起動
        overwrite = self.overwrite_check.isChecked()
        self.worker = ImportWorker(self.importer, self.selected_file_path, overwrite)
        self.worker.progress_updated.connect(self.on_progress_updated)
        self.worker.import_completed.connect(self.on_import_completed)
        self.worker.start()

        self.logger.info(f"インポート開始: {self.selected_file_path} (上書き: {overwrite})")

    def on_progress_updated(self, progress: int, message: str):
        """進捗更新"""
        self.progress_bar.setValue(progress)
        self.progress_label.setText(message)

    def on_import_completed(self, success: int, skipped: int, errors: list):
        """インポート完了"""
        # UI有効化
        self.import_btn.setEnabled(True)
        self.browse_btn.setEnabled(True)
        self.overwrite_check.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)

        # 結果表示
        result_lines = []
        result_lines.append("=" * 50)
        result_lines.append("インポート結果")
        result_lines.append("=" * 50)
        result_lines.append(f"✓ 成功: {success}件")
        result_lines.append(f"⊘ スキップ: {skipped}件")
        result_lines.append(f"✗ エラー: {len(errors)}件")
        result_lines.append("")

        if errors:
            result_lines.append("【エラー詳細】")
            for error in errors[:10]:  # 最大10件表示
                result_lines.append(f"  • {error}")
            if len(errors) > 10:
                result_lines.append(f"  ... 他 {len(errors) - 10}件")

        result_text = "\n".join(result_lines)
        self.result_text.setPlainText(result_text)

        # ログ出力
        self.logger.info(f"インポート完了: 成功 {success}件, スキップ {skipped}件, エラー {len(errors)}件")

        # 成功時はダイアログを閉じる
        if success > 0 and len(errors) == 0:
            QMessageBox.information(
                self,
                "インポート完了",
                f"{success}件の銘柄を正常にインポートしました。"
            )
            self.import_completed.emit()
            self.accept()
        elif success > 0:
            QMessageBox.warning(
                self,
                "インポート完了（一部エラー）",
                f"{success}件の銘柄をインポートしました。\n{len(errors)}件のエラーがありました。"
            )
            self.import_completed.emit()
        else:
            QMessageBox.critical(
                self,
                "インポート失敗",
                "銘柄をインポートできませんでした。\nエラー内容を確認してください。"
            )
