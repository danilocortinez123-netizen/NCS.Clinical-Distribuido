import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from .config import settings

logger = logging.getLogger(__name__)


class CircuitBreaker:
    def __init__(self):
        self._failures = 0
        self._state: str = "closed"
        self._last_failure_time: Optional[datetime] = None
        self._half_open_attempts = 0

    @property
    def is_available(self) -> bool:
        if self._state == "closed":
            return True
        if self._state == "open":
            elapsed = datetime.utcnow() - self._last_failure_time
            if elapsed.total_seconds() >= settings.circuit_breaker_reset_seconds:
                self._state = "half-open"
                self._half_open_attempts = 0
                logger.info("Circuit breaker → half-open (probando conectividad cloud)")
                return True
            return False
        if self._state == "half-open":
            return self._half_open_attempts < 1
        return True

    def record_success(self):
        if self._state == "half-open":
            logger.info("Circuit breaker → closed (cloud recuperado)")
        self._failures = 0
        self._state = "closed"
        self._last_failure_time = None
        self._half_open_attempts = 0

    def record_failure(self):
        self._failures += 1
        self._last_failure_time = datetime.utcnow()
        if self._state == "half-open":
            self._state = "open"
            logger.warning("Circuit breaker → open (half-open falló, reintentando en %ss)", settings.circuit_breaker_reset_seconds)
        elif self._failures >= settings.circuit_breaker_threshold:
            self._state = "open"
            logger.warning("Circuit breaker → open (%d fallos consecutivos, reintentando en %ss)", self._failures, settings.circuit_breaker_reset_seconds)
        else:
            self._half_open_attempts += 1

    @property
    def state(self) -> str:
        return self._state

    async def wait_for_retry(self):
        await asyncio.sleep(settings.circuit_breaker_reset_seconds)


circuit_breaker = CircuitBreaker()
