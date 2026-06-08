from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from app.core.models import Alert, AlertCreate
from app.services.stock_service import stock_service

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.post("", response_model=Alert, summary="创建价格预警")
async def create_alert(alert: AlertCreate):
    """
    创建股票价格条件预警，当价格满足条件时会通过 WebSocket 推送通知

    - **symbol**: 股票代码
    - **condition**: 条件
        - `gt`: 当前价格 >= 目标价格时触发
        - `lt`: 当前价格 <= 目标价格时触发
    - **target_price**: 目标价格（必须 > 0）
    - **user_id**: 用户标识（用于 WebSocket 推送匹配）
    - **note**: 可选备注信息
    """
    if not stock_service.get_stock_info(alert.symbol):
        raise HTTPException(status_code=404, detail=f"股票代码 {alert.symbol} 不存在")
    return await stock_service.create_alert(
        symbol=alert.symbol,
        condition=alert.condition,
        target_price=alert.target_price,
        user_id=alert.user_id,
        note=alert.note
    )


@router.get("", response_model=List[Alert], summary="获取预警列表")
async def get_alerts(user_id: Optional[str] = Query(None, description="按用户ID筛选")):
    """
    获取所有价格预警列表，可按用户ID筛选

    - **user_id**: 可选，用户标识
    """
    return stock_service.get_alerts(user_id=user_id)


@router.delete("/{alert_id}", summary="删除预警")
async def delete_alert(alert_id: str):
    """
    删除指定ID的价格预警

    - **alert_id**: 预警ID
    """
    deleted = await stock_service.delete_alert(alert_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"预警 {alert_id} 不存在")
    return {"message": "删除成功", "alert_id": alert_id}
