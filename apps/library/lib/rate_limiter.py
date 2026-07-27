"""요청 속도 제한기 (RateLimiter).

원본: sblib-search/src/rate_limiter.py

대상 사이트에 과도한 부하를 주지 않도록 두 가지 정책을 강제한다.

- **최소 간격**: 연속된 두 요청의 (기록) 시각 차이가 항상
  ``min_interval_seconds`` 이상이 되도록, 직전 요청과의 간격이 최소 지연보다
  짧으면 남은 시간만큼 대기한 뒤 현재 요청 시각을 기록한다.
- **단일 동시성**: 내부 락으로 한 시점에 하나의 요청만 통과시켜
  여러 스레드가 동시에 진입하더라도 요청이 직렬화되도록 한다.
"""

from __future__ import annotations

import threading
import time
from abc import ABC, abstractmethod


class Clock(ABC):
    """현재 시각을 초 단위 단조(monotonic-friendly) 실수로 제공하는 인터페이스."""

    @abstractmethod
    def now(self) -> float:
        """현재 시각을 초 단위 실수로 반환한다."""
        raise NotImplementedError


class Sleeper(ABC):
    """지정한 시간(초)만큼 대기하는 인터페이스."""

    @abstractmethod
    def sleep(self, seconds: float) -> None:
        """``seconds`` 초 동안 대기한다. 0 이하이면 대기하지 않는다."""
        raise NotImplementedError


class SystemClock(Clock):
    """실제 시스템 시계 구현(:func:`time.monotonic` 사용)."""

    def now(self) -> float:
        return time.monotonic()


class SystemSleeper(Sleeper):
    """실제 시스템 대기 구현(:func:`time.sleep`)."""

    def sleep(self, seconds: float) -> None:
        if seconds > 0:
            time.sleep(seconds)


class RateLimiter:
    """연속 요청 사이 최소 지연과 단일 요청 동시성을 보장하는 속도 제한기."""

    def __init__(
        self,
        min_interval_seconds: float = 1.0,
        clock: Clock | None = None,
        sleeper: Sleeper | None = None,
    ) -> None:
        """속도 제한기를 초기화한다.

        Args:
            min_interval_seconds: 연속된 두 요청 사이의 최소 간격(초). 기본 1.0초.
            clock: 현재 시각 조회에 사용할 시계. 미지정 시 :class:`SystemClock`.
            sleeper: 대기에 사용할 슬리퍼. 미지정 시 :class:`SystemSleeper`.
        """
        self._min_interval_seconds = min_interval_seconds
        self._clock: Clock = clock if clock is not None else SystemClock()
        self._sleeper: Sleeper = sleeper if sleeper is not None else SystemSleeper()
        self._lock = threading.Lock()
        self._last_request_time: float | None = None

    def acquire(self) -> None:
        """요청 슬롯을 획득한다.

        직전 요청 시각과의 간격이 ``min_interval_seconds`` 미만이면 남은 시간만큼
        대기한 뒤 현재 요청 시각을 기록한다. 내부 락으로 한 시점에 하나의 요청만
        통과시킨다.
        """
        with self._lock:
            now = self._clock.now()
            if self._last_request_time is not None:
                elapsed = now - self._last_request_time
                remaining = self._min_interval_seconds - elapsed
                if remaining > 0:
                    self._sleeper.sleep(remaining)
                    now = self._clock.now()
            self._last_request_time = now
