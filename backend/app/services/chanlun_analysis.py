# -*- coding: utf-8 -*-
"""缠论分析核心算法（从现有项目迁移）"""
import pandas as pd
import numpy as np
from app.services.stock_data import get_kline_data


def df_to_jsonable(df: pd.DataFrame) -> list:
    """将 DataFrame 转为 JSON 安全格式（NaN → None，大数→字符串）"""
    if df.empty:
        return []
    # 替换 NaN
    df = df.replace({np.nan: None})
    # amount 列可能数值过大，转字符串防精度丢失
    if "amount" in df.columns:
        df["amount"] = df["amount"].apply(lambda x: str(x) if x is not None else None)
    records = df.to_dict("records")
    # 确保所有值都是 JSON 原生类型
    for row in records:
        for k, v in list(row.items()):
            if isinstance(v, (np.floating, np.integer)):
                row[k] = float(v) if isinstance(v, np.floating) else int(v)
            elif v is np.nan:
                row[k] = None
    return records


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
    df_daily = get_kline_data(stock_code, "daily")
    macd_daily = calculate_macd(df_daily)

    df_weekly = get_kline_data(stock_code, "weekly")
    macd_weekly = calculate_macd(df_weekly)

    return {
        "daily": df_to_jsonable(macd_daily),
        "weekly": df_to_jsonable(macd_weekly),
    }


def get_kline_with_indicators(
    stock_code: str,
    period: str = "daily",
    adjust: str = "qfq",
    limit: int = 240,
) -> dict:
    """获取K线数据及指标（供前端使用）"""
    df = get_kline_data(stock_code, period, adjust, limit=limit)
    if df.empty:
        return {"error": "无数据"}

    # 计算MA
    for window in [5, 10, 20, 60]:
        if "close" in df.columns:
            df[f"ma{window}"] = df["close"].rolling(window).mean()

    # 计算MACD
    macd_df = calculate_macd(df)

    return {
        "kline": df_to_jsonable(df),
        "macd": df_to_jsonable(macd_df),
    }
