# -*- coding: utf-8 -*-
"""股票池路由"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.watchlist import Watchlist, WatchlistStock
from app.models.user import User
from app.schemas.watchlist import WatchlistCreate, WatchlistOut, WatchlistStockCreate, WatchlistStockOut
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/watchlist", tags=["股票池"])


@router.get("/", response_model=list[WatchlistOut])
def list_watchlists(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    watchlists = db.query(Watchlist).filter(Watchlist.user_id == current_user.id).all()
    return watchlists


@router.post("/", response_model=WatchlistOut)
def create_watchlist(
    data: WatchlistCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    wl = Watchlist(user_id=current_user.id, name=data.name, description=data.description)
    db.add(wl)
    db.commit()
    db.refresh(wl)
    return wl


@router.delete("/{watchlist_id}")
def delete_watchlist(
    watchlist_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    wl = db.query(Watchlist).filter(Watchlist.id == watchlist_id, Watchlist.user_id == current_user.id).first()
    if not wl:
        raise HTTPException(status_code=404, detail="股票池不存在")
    db.delete(wl)
    db.commit()
    return {"ok": True}


@router.post("/{watchlist_id}/stocks", response_model=WatchlistStockOut)
def add_stock(
    watchlist_id: int,
    data: WatchlistStockCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    wl = db.query(Watchlist).filter(Watchlist.id == watchlist_id, Watchlist.user_id == current_user.id).first()
    if not wl:
        raise HTTPException(status_code=404, detail="股票池不存在")

    # 检查是否已存在
    existing = db.query(WatchlistStock).filter(
        WatchlistStock.watchlist_id == watchlist_id,
        WatchlistStock.stock_code == data.stock_code,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="股票已在池中")

    stock = WatchlistStock(
        watchlist_id=watchlist_id,
        stock_code=data.stock_code,
        stock_name=data.stock_name or data.stock_code,
    )
    db.add(stock)
    db.commit()
    db.refresh(stock)
    return stock


@router.delete("/{watchlist_id}/stocks/{stock_id}")
def remove_stock(
    watchlist_id: int,
    stock_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    wl = db.query(Watchlist).filter(Watchlist.id == watchlist_id, Watchlist.user_id == current_user.id).first()
    if not wl:
        raise HTTPException(status_code=404, detail="股票池不存在")

    stock = db.query(WatchlistStock).filter(
        WatchlistStock.id == stock_id,
        WatchlistStock.watchlist_id == watchlist_id,
    ).first()
    if not stock:
        raise HTTPException(status_code=404, detail="股票不存在")
    db.delete(stock)
    db.commit()
    return {"ok": True}
