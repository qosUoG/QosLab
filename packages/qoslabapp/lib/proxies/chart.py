import asyncio

from threading import Lock
from typing import Any

from fastapi import WebSocket

from qoslablib.extensions.chart import ChartABC


class _Subscriber:
    def __init__(self):
        self._rate = 10
        self._active_frames_lock = Lock()
        self._active_frames = bytes()

    def toOwnedFrames(self):
        with self._active_frames_lock:
            if self._active_frames == bytes():
                return None

            frames = self._active_frames
            self._active_frames = bytes()
            return frames

    def appendFrame(self, frame: bytes):
        with self._active_frames_lock:
            self._active_frames += frame

    def setRate(self, rate: int):
        self._rate = rate

    def getRate(self):
        return self._rate


class ChartProxy:
    def __init__(self, *, chartT: type[ChartABC], kwargs: Any):
        # underlying chart instance
        self._chart = chartT(self._plot_fn, **kwargs)
        self._subscribers: dict[WebSocket, _Subscriber] = {}

        # Lock synchronizing frame history and subscriber creation
        self._frames_history = bytes()
        self.tick_lock = Lock()

    """Public Interface towards ExperimentProxy"""

    def getConfig(self):
        return self._chart.config.toDict()

    def getChart(self):
        return self._chart

    async def cleanup(self):
        # Close all ws connetions
        for ws in self._subscribers.keys():
            await ws.close(code=1001)

        self._subscribers.clear()

    """Public Interface for frontend WebSocket control"""

    def subscribe(self, ws: WebSocket):
        frames_history: bytes
        subscriber: _Subscriber

        # Shares the frames history lock such that make sure the subscriber gets a history right at the moment of creation, such that
        with self.tick_lock:
            frames_history = self._frames_history
            subscriber = _Subscriber(ws)
            self._subscribers[ws] = subscriber

        # Function that yield frames according to the rate
        async def subscription():
            # First yield frames available before subscription
            if frames_history:
                yield frames_history

            while True:
                await asyncio.sleep(1 / subscriber.getRate())
                frames = subscriber.toOwnedFrames()
                if frames is not None:
                    yield frames

        def unsubscribe():
            del self._subscribers[ws]

        def setRate(rate: int):
            self._subscribers[ws].setRate(rate)

        return (subscription, unsubscribe, setRate)

    """_plot_fn to be used by underlying chart"""

    def _plot_fn(self, frame: bytes):
        with self.tick_lock:
            # Make sure to have a copy
            self._frames_history += frame
            # subscriber and frames history shares a lock such that the history is fetched at the same time as the subscriber list is modified
            for subscriber in self._subscribers.values():
                subscriber.appendFrame(frame)
