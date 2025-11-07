"""
Yuutai Event Investor - Main Entry Point
株主優待イベント投資分析ツール

Author: Your Name
Date: 2024-11-06
Version: 1.0.0
"""

import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def main():
    """アプリケーションのメインエントリーポイント"""
    import logging
    
    # ロギング設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Yuutai Event Investor v1.0.0 起動中...")
    
    try:
        from PySide6.QtWidgets import QApplication
        # Phase 4統合版のMainWindowを使用
        from src.ui.main_window_v3 import MainWindow

        # アプリケーション作成
        app = QApplication(sys.argv)
        app.setApplicationName("Yuutai Event Investor")
        app.setOrganizationName("Yuutai Investor Team")

        # メインウィンドウ作成
        window = MainWindow()
        window.show()

        logger.info("アプリケーションを起動しました")

        # イベントループ開始
        sys.exit(app.exec())
        
    except ImportError as e:
        logger.error(f"依存パッケージが見つかりません: {e}")
        print("\n" + "=" * 60)
        print("エラー: 必要なパッケージがインストールされていません")
        print("=" * 60)
        print("\n以下のコマンドを実行してください:")
        print("  pip install -r requirements.txt")
        print("\n" + "=" * 60)
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"アプリケーション起動エラー: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
