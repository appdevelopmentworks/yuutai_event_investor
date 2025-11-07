"""
Database Initialization Script
データベース初期化とサンプルデータ投入スクリプト

Author: Yuutai Event Investor Team
Date: 2024-11-07
Version: 1.0.0
"""

import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.database import DatabaseManager
import logging

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def init_database():
    """データベースを初期化"""
    logger.info("=" * 60)
    logger.info("データベース初期化を開始します")
    logger.info("=" * 60)
    
    # DatabaseManagerのインスタンス作成
    db = DatabaseManager()
    
    # データベースファイルのパスを表示
    logger.info(f"データベースパス: {db.db_path}")
    
    # 既存のデータベースを削除（開発用）
    if db.db_path.exists():
        logger.warning("既存のデータベースを削除します...")
        db.db_path.unlink()
    
    # データベース初期化
    if db.initialize_database():
        logger.info("✅ データベースの初期化に成功しました")
        
        # スキーマバージョンを確認
        version = db.get_schema_version()
        logger.info(f"スキーマバージョン: {version}")
        
        return True
    else:
        logger.error("❌ データベースの初期化に失敗しました")
        return False


def insert_sample_data():
    """サンプルデータを投入"""
    logger.info("\n" + "=" * 60)
    logger.info("サンプルデータを投入します")
    logger.info("=" * 60)
    
    db = DatabaseManager()
    
    # サンプル銘柄データ
    sample_stocks = [
        {
            "code": "9202",
            "name": "ANAホールディングス",
            "rights_month": 3,
            "rights_date": "2024-03-31",
            "yuutai_genre": "優待券",
            "yuutai_content": "国内線50%割引券2枚",
            "yuutai_detail": "国内線片道1区間50%割引券×2枚、株主優待番号の案内（運賃の50%割引）",
            "min_shares": 100,
            "data_source": "sample"
        },
        {
            "code": "8591",
            "name": "オリックス",
            "rights_month": 3,
            "rights_date": "2024-03-31",
            "yuutai_genre": "カタログギフト",
            "yuutai_content": "カタログギフト（3,000円相当）",
            "yuutai_detail": "100株以上：Aコース、1,000株以上：Cコース、2,000株以上：Fコース",
            "min_shares": 100,
            "data_source": "sample"
        },
        {
            "code": "7201",
            "name": "日産自動車",
            "rights_month": 3,
            "rights_date": "2024-03-31",
            "yuutai_genre": "カタログ",
            "yuutai_content": "自社製品カタログギフト",
            "yuutai_detail": "100株以上：オリジナルカタログギフト",
            "min_shares": 100,
            "data_source": "sample"
        },
        {
            "code": "8304",
            "name": "あおぞら銀行",
            "rights_month": 3,
            "rights_date": "2024-03-31",
            "yuutai_genre": "金券",
            "yuutai_content": "カタログギフト",
            "yuutai_detail": "100株以上：カタログギフト2,000円相当、500株以上：4,000円相当",
            "min_shares": 100,
            "data_source": "sample"
        },
        {
            "code": "8306",
            "name": "三菱UFJフィナンシャル・グループ",
            "rights_month": 3,
            "rights_date": "2024-03-31",
            "yuutai_genre": "金融サービス",
            "yuutai_content": "自社グループ優待",
            "yuutai_detail": "100株以上：カタログギフト",
            "min_shares": 100,
            "data_source": "sample"
        },
        {
            "code": "9433",
            "name": "KDDI",
            "rights_month": 3,
            "rights_date": "2024-03-31",
            "yuutai_genre": "カタログギフト",
            "yuutai_content": "カタログギフト（3,000円相当）",
            "yuutai_detail": "100株以上：カタログギフト3,000円相当",
            "min_shares": 100,
            "data_source": "sample"
        },
        {
            "code": "2914",
            "name": "日本たばこ産業（JT）",
            "rights_month": 12,
            "rights_date": "2024-12-31",
            "yuutai_genre": "自社製品",
            "yuutai_content": "自社グループ商品",
            "yuutai_detail": "100株以上：自社グループ商品（2,500円相当）",
            "min_shares": 100,
            "data_source": "sample"
        }
    ]
    
    # データ投入
    success_count = 0
    for stock in sample_stocks:
        if db.insert_stock(**stock):
            logger.info(f"✅ {stock['code']} {stock['name']} を追加しました")
            success_count += 1
        else:
            logger.error(f"❌ {stock['code']} {stock['name']} の追加に失敗しました")
    
    logger.info(f"\n投入完了: {success_count}/{len(sample_stocks)} 件")
    
    return success_count == len(sample_stocks)


def verify_database():
    """データベースの内容を確認"""
    logger.info("\n" + "=" * 60)
    logger.info("データベースの内容を確認します")
    logger.info("=" * 60)
    
    db = DatabaseManager()
    
    # 全銘柄を取得
    stocks = db.get_all_stocks()
    logger.info(f"\n登録銘柄数: {len(stocks)} 件\n")
    
    if stocks:
        logger.info("登録銘柄一覧:")
        logger.info("-" * 80)
        for stock in stocks:
            logger.info(
                f"{stock['code']:>6} | {stock['name']:<20} | "
                f"{stock['rights_month']:>2}月 | {stock['yuutai_genre']:<15}"
            )
        logger.info("-" * 80)
    
    # 3月銘柄のみ取得
    march_stocks = db.get_all_stocks(rights_month=3)
    logger.info(f"\n3月権利確定銘柄: {len(march_stocks)} 件")
    
    # 12月銘柄のみ取得
    december_stocks = db.get_all_stocks(rights_month=12)
    logger.info(f"12月権利確定銘柄: {len(december_stocks)} 件")
    
    return True


def main():
    """メイン処理"""
    logger.info("\n🚀 データベース初期化スクリプトを開始します\n")
    
    try:
        # 1. データベース初期化
        if not init_database():
            logger.error("データベース初期化に失敗しました")
            sys.exit(1)
        
        # 2. サンプルデータ投入
        if not insert_sample_data():
            logger.error("サンプルデータ投入に失敗しました")
            sys.exit(1)
        
        # 3. データ確認
        verify_database()
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ すべての処理が正常に完了しました")
        logger.info("=" * 60)
        logger.info("\n次のステップ:")
        logger.info("  python main.py")
        logger.info("\n")
        
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
