# -*- coding: utf-8 -*-
"""股票数据服务 - 使用 baostock（替代 akshare，解决外网访问受限问题）"""
import baostock as bs
import pandas as pd
import time
from functools import lru_cache
from typing import Literal

# 全局登录
_bs_logged_in = False


def _ensure_login():
    global _bs_logged_in
    if not _bs_logged_in:
        bs.login()
        _bs_logged_in = True


# 简单内存缓存
_cache: dict[str, tuple[float, any]] = {}


def _get_cache(key: str, minutes: int = 5):
    if key in _cache:
        ts, data = _cache[key]
        if time.time() - ts < minutes * 60:
            return data
    return None


def _set_cache(key: str, data):
    _cache[key] = (time.time(), data)


def _to_bs_code(stock_code: str) -> str:
    """将 6 位代码转换为 baostock 格式，如 000001 -> sz.000001"""
    code = stock_code.strip()
    if len(code) != 6:
        return code
    # 根据代码判断交易所：0开头沪市，0-8深市
    if code.startswith('6'):
        return f"sh.{code}"
    else:
        return f"sz.{code}"


def get_stock_info(stock_code: str) -> dict:
    """获取股票基本信息"""
    _ensure_login()
    cache_key = f"info_{stock_code}"
    cached = _get_cache(cache_key, 60)
    if cached is not None:
        return cached

    try:
        rs = bs.query_stock_basic(code=_to_bs_code(stock_code))
        data = []
        while rs.error_code == '0' and rs.next():
            data.append(rs.get_row_data())
        if data:
            result = {f"v{i}": v for i, v in enumerate(data[0])}
            _set_cache(cache_key, result)
            return result
        return {"error": "股票不存在"}
    except Exception as e:
        return {"error": str(e)}


def get_kline_data(
    stock_code: str,
    period: Literal["daily", "weekly", "monthly"] = "daily",
    adjust: Literal["qfq", "hfq", ""] = "qfq",
    start_date: str = "2020-01-01",
    end_date: str = "2050-01-01",
) -> pd.DataFrame:
    """获取K线数据（baostock 接口）"""
    _ensure_login()
    cache_key = f"kline_{stock_code}_{period}_{adjust}"
    cached = _get_cache(cache_key, 5)
    if cached is not None:
        return cached

    try:
        # baostock frequency: d=日线, w=周线, m=月线
        freq_map = {"daily": "d", "weekly": "w", "monthly": "m"}
        freq = freq_map.get(period, "d")

        # adjust: 复权类型：1=后复权 2=前复权 3=不复权
        adjust_map = {"qfq": "2", "hfq": "1", "": "3"}
        adjtype = adjust_map.get(adjust, "3")

        rs = bs.query_history_k_data_plus(
            _to_bs_code(stock_code),
            "date,open,high,low,close,volume,amount",
            start_date=start_date,
            end_date=end_date,
            frequency=freq,
            adjustflag=adjtype,
        )

        data = []
        while rs.error_code == '0' and rs.next():
            data.append(rs.get_row_data())

        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data, columns=["date", "open", "high", "low", "close", "volume", "amount"])
        # 转换数值列
        for col in ["open", "high", "low", "close", "volume", "amount"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df["date"] = pd.to_datetime(df["date"])
        df.sort_values("date", inplace=True)
        df.reset_index(drop=True, inplace=True)
        df = df[df["close"].notna()]

        _set_cache(cache_key, df)
        return df
    except Exception as e:
        return pd.DataFrame({"error": [str(e)]})


def get_realtime_quote(stock_code: str) -> dict:
    """获取实时行情（用 baostock 实时接口）"""
    _ensure_login()
    cache_key = f"quote_{stock_code}"
    cached = _get_cache(cache_key, 1)
    if cached is not None:
        return cached

    try:
        rs = bs.query_trade_details(_to_bs_code(stock_code))
        result = {}
        while rs.error_code == '0' and rs.next():
            row = rs.get_row_data()
            result = {f"k{i}": v for i, v in enumerate(row)}
            break
        _set_cache(cache_key, result)
        return result
    except Exception as e:
        return {"error": str(e)}
