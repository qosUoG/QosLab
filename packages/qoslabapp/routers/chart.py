import asyncio
import json
from typing import Any, TypedDict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel


from ..lib.state import AppState


router = APIRouter()


@router.websocket("/chart/{experiment_id}/{title}")
async def getChartDataWs(experiment_id: str, title: str, ws: WebSocket):
    await ws.accept()

    (yieldFn, unsubscribe, setRate) = AppState.getChartSubscription(
        experiment_id, title
    )

    if yieldFn is None:
        await ws.close()
        return

    async def producer():
        try:
            while True:
                async for frames in yieldFn():
                    await ws.send_bytes(frames)
        except WebSocketDisconnect:
            unsubscribe()

    async def consumer():
        async for message in ws:
            data = json.loads(message)
            assert data["type"] == "rate"
            await setRate(data["value"])

    producer_task = asyncio.create_task(producer())
    consumer_task = asyncio.create_task(consumer())

    await producer_task
    consumer_task.cancel()
