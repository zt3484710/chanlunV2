# -*- coding: utf-8 -*-
"""缠论分析路由"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.chanlun_config import ChanlunConfig
from app.schemas.chanlun_config import ChanlunConfigCreate, ChanlunConfigOut
from app.routers.auth import get_current_user
from app.services.stock_data import get_kline_data
from app.services.chanlun import analyze_chanlun

router = APIRouter(prefix="/api/chanlun", tags=["缠论分析"])

# 周期层级映射：当前周期 -> [上层周期, 再上层周期]
PERIOD_HIERARCHY = {
    "15min": ["60min", "daily"],
    "60min": ["daily", "weekly"],
    "daily": ["weekly", "monthly"],
    "weekly": ["monthly", "quarterly"],
    "monthly": ["quarterly", "yearly"],
}


@router.get("/analyze")
def analyze(
    stock_code: str = Query(..., description="股票代码，如 000001"),
    period: str = Query("daily", description="周期: daily/weekly/monthly"),
    adjust: str = Query("qfq", description="复权: qfq/hfq"),
    limit: int = Query(240, description="K线数量限制"),
    current_user: User = Depends(get_current_user),
):
    """完整的缠论分析（分型/笔/线段/中枢/背驰/买卖点）+ 三层MACD"""
    from app.services.chanlun_analysis import calculate_macd
    
    # 1. 获取当前周期数据
    df = get_kline_data(stock_code, period, adjust, limit=limit)
    if df.empty:
        return {"error": "无数据"}
    
    # 2. 缠论分析
    result = analyze_chanlun(df)
    
    # 3. 当前周期MACD (L1)
    macd_df = calculate_macd(df)
    result["kline"] = df.to_dict("records") if not df.empty else []
    result["macd"] = macd_df.to_dict("records") if not macd_df.empty else []
    
    # 4. 获取上层周期MACD (L2, L3)
    hierarchy = PERIOD_HIERARCHY.get(period, [None, None])
    l2_period, l3_period = hierarchy[0], hierarchy[1]
    
    # L2 - 上层周期
    if l2_period:
        df_l2 = get_kline_data(stock_code, l2_period, adjust, limit=limit // 4)
        if not df_l2.empty:
            macd_l2 = calculate_macd(df_l2)
            result["macd_l2"] = macd_l2.to_dict("records") if not macd_l2.empty else []
        else:
            result["macd_l2"] = []
    else:
        result["macd_l2"] = []
    
    # L3 - 再上层周期
    if l3_period:
        df_l3 = get_kline_data(stock_code, l3_period, adjust, limit=limit // 16)
        if not df_l3.empty:
            macd_l3 = calculate_macd(df_l3)
            result["macd_l3"] = macd_l3.to_dict("records") if not macd_l3.empty else []
        else:
            result["macd_l3"] = []
    else:
        result["macd_l3"] = []
    
    return result


@router.get("/configs", response_model=list[ChanlunConfigOut])
def list_configs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取用户的缠论配置列表"""
    configs = db.query(ChanlunConfig).filter(ChanlunConfig.user_id == current_user.id).all()
    return configs


@router.post("/configs", response_model=ChanlunConfigOut)
def save_config(
    data: ChanlunConfigCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """保存缠论配置"""
    config = ChanlunConfig(
        user_id=current_user.id,
        name=data.name,
        config=data.config,
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


@router.delete("/configs/{config_id}")
def delete_config(
    config_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除缠论配置"""
    cfg = db.query(ChanlunConfig).filter(
        ChanlunConfig.id == config_id,
        ChanlunConfig.user_id == current_user.id,
    ).first()
    if not cfg:
        return {"error": "配置不存在"}
    db.delete(cfg)
    db.commit()
    return {"ok": True}
