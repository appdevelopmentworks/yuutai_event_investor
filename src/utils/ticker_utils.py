"""
Ticker Utilities Module
ティッカーコード処理ユーティリティ

Author: Yuutai Event Investor Team
Date: 2024-11-07
Version: 1.0.0
"""

import re
from typing import Optional


def check_ticker(ticker: str) -> str:
    """
    ティッカーコードを検証し、日本株の場合は".T"サフィックスを追加
    
    Args:
        ticker: ティッカーコード（例: "9202", "AAPL"）
        
    Returns:
        str: 処理済みティッカーコード（例: "9202.T", "AAPL"）
        
    Examples:
        >>> check_ticker("9202")
        '9202.T'
        >>> check_ticker("AAPL")
        'AAPL'
        >>> check_ticker("8151")
        '8151.T'
    """
    # 有効な英大文字を定義（日本株コードに使用される文字）
    valid_letters = "ACDFGHJKLMPNRSTUWX-Y"
    
    # 日本株のパターン：4桁の数字と文字の組み合わせ
    # 例: 9202, 8151, 7203
    pattern = rf"^[0-9][0-9{valid_letters}][0-9][0-9{valid_letters}]$"
    
    # パターンにマッチしない場合はそのまま返す（米国株など）
    if not re.match(pattern, ticker):
        return ticker
    
    # 日本株の場合は".T"サフィックスを追加
    return ticker + ".T"


def is_japanese_stock(ticker: str) -> bool:
    """
    ティッカーコードが日本株かどうかを判定
    
    Args:
        ticker: ティッカーコード
        
    Returns:
        bool: 日本株の場合True
        
    Examples:
        >>> is_japanese_stock("9202.T")
        True
        >>> is_japanese_stock("AAPL")
        False
    """
    # .Tサフィックスがあるか、4桁の数字で始まる場合
    if ticker.endswith(".T"):
        return True
    
    # 4桁の数字で始まる場合（未処理の日本株コード）
    if re.match(r"^\d{4}$", ticker):
        return True
    
    return False


def normalize_ticker(ticker: str) -> str:
    """
    ティッカーコードを正規化（大文字化、空白削除、.T処理）
    
    Args:
        ticker: ティッカーコード
        
    Returns:
        str: 正規化されたティッカーコード
        
    Examples:
        >>> normalize_ticker(" 9202 ")
        '9202.T'
        >>> normalize_ticker("aapl")
        'AAPL'
    """
    # 空白を削除し、大文字化
    ticker = ticker.strip().upper()
    
    # 日本株の場合は.Tを追加
    return check_ticker(ticker)


def extract_code(ticker: str) -> str:
    """
    ティッカーコードから証券コード部分のみを抽出（.Tサフィックスを削除）
    
    Args:
        ticker: ティッカーコード
        
    Returns:
        str: 証券コード
        
    Examples:
        >>> extract_code("9202.T")
        '9202'
        >>> extract_code("AAPL")
        'AAPL'
    """
    if ticker.endswith(".T"):
        return ticker[:-2]
    return ticker
