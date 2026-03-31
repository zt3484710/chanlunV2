# -*- coding: utf-8 -*-
"""AKShare 股票数据服务"""
import time
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Literal

# 简单内存缓存
_cache: dict[str, tuple[float, any]] = {}


def _get_cache(key: str, minutes: int = 5):
    """读取缓存，未过期则返回数据"""
    if key in _cache:
        ts, data = _cache[key]
        if time.time() - ts < minutes * 60:
            return data
    return None


def _set_cache(key: str, data):
    _cache[key] = (time.time(), data)


def get_stock_info(stock_code: str) -> dict:
    """获取股票基本信息"""
    cache_key = f"info_{stock_code}"
    cached = _get_cache(cache_key, 60)
    if cached is not None:
        return cached

    try:
        df = ak.stock_individual_info_em(symbol=stock_code)
        info = {row["item"]: row["value"] for _, row in df.iterrows()}
        _set_cache(cache_key, info)
        return info
    except Exception as e:
        return {"error": str(e)}


def get_kline_data(
    stock_code: str,
    period: Literal["15", "30", "60", "daily", "weekly", "monthly"] = "daily",
    adjust: Literal["qfq", "hfq", ""] = "qfq",
) -> pd.DataFrame:
    """获取K线数据"""
    cache_key = f"kline_{stock_code}_{period}_{adjust}"
    cached = _get_cache(cache_key)
    if cached is not None:
        return cached

    try:
        if period == "daily":
            df = ak.stock_zh_a_hist(symbol=stock_code, period="daily", adjust=adjust)
        elif period == "weekly":
            df = ak.stock_zh_a_hist(symbol=stock_code, period="weekly", adjust=adjust)
        elif period == "monthly":
            df = ak.stock_zh_a_hist(symbol=stock_code, period="monthly", adjust=adjust)
        else:
            df = ak.stock_zh_a_hist(symbol=stock_code, period="daily", adjust=adjust)

        # 统一列名
        df.columns = [c.lower() for c in df.columns]
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
        df.sort_values("date", inplace=True)
        df.reset_index(drop=True, inplace=True)

        _set_cache(cache_key, df)
        return df
    except Exception as e:
        return pd.DataFrame({"error": [str(e)]})


def get_realtime_quote(stock_code: str) -> dict:
    """获取实时行情"""
    cache_key = f"quote_{stock_code}"
    cached = _get_cache(cache_key, 1)  # 1分钟缓存
    if cached is not None:
        return cached

    try:
        df = ak.stock_zh_a_spot_em()
        row = df[df["代码"] == stock_code]
        if row.empty:
            return {"error": "股票不存在"}
        r = row.iloc[0].to_dict()
        _set_cache(cache_key, r)
        return r
    except Exception as e:
        return {"error": str(e)}


def get_financial_data(stock_code: str) -> dict:
    """获取财务数据（PE、PB、ROE等）"""
    cache_key = f"financial_{stock_code}"
    cached = _get_cache(cache_key, 60)
    if cached is not None:
        return cached

    try:
        df = ak.stock_financial_analysis_indicator(symbol=stock_code)
        latest = df.iloc[0].to_dict()
        _set_cache(cache_key, latest)
        return latest
    except Exception as e:
        return {"error": str(e)}
