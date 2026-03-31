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


@router.get("/analyze")
def analyze(
    stock_code: str = Query(..., description="股票代码，如 000001"),
    period: str = Query("daily", description="周期: daily/weekly/monthly"),
    adjust: str = Query("qfq", description="复权: qfq/hfq"),
    current_user: User = Depends(get_current_user),
):
    """完整的缠论分析（分型/笔/线段/中枢/背驰/买卖点）"""
    df = get_kline_data(stock_code, period, adjust)
    if df.empty:
        return {"error": "无数据"}
    result = analyze_chanlun(df)
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
