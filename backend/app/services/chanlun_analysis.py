# -*- coding: utf-8 -*-
"""缠论分析核心算法（从现有项目迁移）"""
import pandas as pd
import numpy as np
from app.services.stock_data import get_kline_data


def calculate_macd(
    df: pd.DataFrame,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> pd.DataFrame:
    """计算MACD指标"""
    if df.empty or "close" not in df.columns:
        return pd.DataFrame()

    close = df["close"].astype(float)
    exp1 = close.ewm(span=fast, adjust=False).mean()
    exp2 = close.ewm(span=slow, adjust=False).mean()
    macd_dif = exp1 - exp2
    macd_dea = macd_dif.ewm(span=signal, adjust=False).mean()
    macd_bar = 2 * (macd_dif - macd_dea)

    result = df[["date", "close"]].copy()
    result["dif"] = macd_dif.values
    result["dea"] = macd_dea.values
    result["macd"] = macd_bar.values
    return result


def get_multi_period_macd(stock_code: str) -> dict:
    """获取多周期MACD（15分/60分/日线三层展开）"""
    # 日线MACD
    df_daily = get_kline_data(stock_code, "daily")
    macd_daily = calculate_macd(df_daily)

    # 周线MACD（用日线数据按7倍展开）
    df_weekly = get_kline_data(stock_code, "weekly")
    macd_weekly = calculate_macd(df_weekly)

    return {
        "daily": macd_daily.to_dict("records") if not macd_daily.empty else [],
        "weekly": macd_weekly.to_dict("records") if not macd_weekly.empty else [],
    }


def get_kline_with_indicators(
    stock_code: str,
    period: str = "daily",
    adjust: str = "qfq",
) -> dict:
    """获取K线数据及指标（供前端使用）"""
    df = get_kline_data(stock_code, period, adjust)
    if df.empty:
        return {"error": "无数据"}

    # 计算MA
    for window in [5, 10, 20, 60]:
        col = f"ma{window}"
        if col not in df.columns and "close" in df.columns:
            df[col] = df["close"].rolling(window).mean()

    # 计算MACD
    macd_df = calculate_macd(df)

    return {
        "kline": df.to_dict("records"),
        "macd": macd_df.to_dict("records") if not macd_df.empty else [],
    }
