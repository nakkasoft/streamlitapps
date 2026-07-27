"""재시도 정책 (RetryPolicy).

원본: sblib-search/src/retry_policy.py

핵심 규칙:

- 재시도 대상 예외(기본: :class:`NetworkError`)가 발생하면 최대 ``max_retries`` 회까지
  연산을 재시도한다.
- 총 시도 횟수 = 1(최초) + ``max_retries`` (기본값 3 → 최대 4회).
- 재시도 대상이 아닌 예외는 즉시 전파한다(재시도하지 않는다).
- 모든 재시도가 소진된 후에도 실패하면, 마지막 원인 예외를 감싼
  :class:`RequestError` 를 발생시킨다(``cause`` 와 ``attempts`` 를 설정).
"""

from __future__ import annotations

from typing import Callable, TypeVar

from .errors import NetworkError, RequestError

T = TypeVar("T")


class RetryPolicy:
    """재시도 대상 예외에 대해 고정 횟수만큼 연산을 재시도하는 정책.

    Attributes:
        max_retries: 최초 시도 이후 추가로 허용되는 재시도 횟수.
        retryable_exceptions: 재시도 대상 예외 타입 튜플.
    """

    def __init__(
        self,
        max_retries: int = 3,
        retryable_exceptions: tuple[type[Exception], ...] = (NetworkError,),
    ) -> None:
        self.max_retries = max_retries
        self.retryable_exceptions = retryable_exceptions

    def execute(self, operation: Callable[[], T]) -> T:
        """``operation`` 을 실행하고, 재시도 대상 예외 발생 시 재시도한다.

        Raises:
            RequestError: 모든 재시도가 소진된 후에도 재시도 대상 예외가 지속되는 경우.
            Exception: 재시도 대상이 아닌 예외는 그대로 즉시 전파된다.
        """
        max_attempts = 1 + self.max_retries
        last_exception: Exception | None = None

        for attempt in range(1, max_attempts + 1):
            try:
                return operation()
            except self.retryable_exceptions as exc:
                last_exception = exc
                if attempt >= max_attempts:
                    break

        raise RequestError(
            f"검색 요청이 {max_attempts}회 시도 후에도 실패했습니다.",
            cause=last_exception,
            attempts=max_attempts,
        )
