"""확인 작업 실행기 — Streamlit용 단순화 버전.

원본: sblib-search/webapp/job_runner.py (CheckJobRunner)

원본은 FastAPI 백그라운드 스레드 + JobManager로 비동기 실행했지만, Streamlit은
버튼 클릭 한 번에 스크립트가 위에서 아래로 동기 실행되는 모델이라 별도의
백그라운드 스레드/작업 매니저가 필요 없다. 이 모듈은 원본 ``CheckJobRunner``와
동일한 오류→상태 매핑 규칙을 유지하면서, 도서 1건 처리마다 콜백
(``on_progress``)을 호출하는 단순 동기 함수로 재구성한 것이다.

매핑 규칙(원본과 동일):
- ``searcher.search(entry)`` 가 ``RequestError`` 를 던지면(재시도 소진)
  → ``BookStatus.REQUEST_ERROR``.
- ``parser.parse_holdings(response)`` 가 ``ParseError`` 를 던지면(구조 해석 실패)
  → ``BookStatus.PARSE_ERROR``.
- 정상 처리되면 ``determine_status(holdings)`` 로 상태를 결정한다.

한 항목의 실패가 나머지 항목 처리를 막지 않는다(실패 격리).
"""

from __future__ import annotations

from collections.abc import Callable

from .errors import ParseError, RequestError
from .models import BookEntry, BookResult, BookStatus
from .rate_limiter import RateLimiter
from .result_parser import ResultParser, SblibHtmlResultParser
from .retry_policy import RetryPolicy
from .searcher import RequestsHttpClient, Searcher
from .status import determine_status

__all__ = ["CheckRunner", "build_default_searcher", "build_default_parser"]


def build_default_searcher(
    min_interval_seconds: float = 1.0, max_retries: int = 3
) -> Searcher:
    """실제 네트워크 요청을 보내는 기본 :class:`Searcher` 를 만든다."""
    http_client = RequestsHttpClient()
    rate_limiter = RateLimiter(min_interval_seconds=min_interval_seconds)
    retry_policy = RetryPolicy(max_retries=max_retries)
    return Searcher(
        http_client=http_client, rate_limiter=rate_limiter, retry_policy=retry_policy
    )


def build_default_parser() -> ResultParser:
    """기본 HTML 결과 파서(서울시립도서관 통합검색용)를 만든다."""
    return SblibHtmlResultParser()


class CheckRunner:
    """``Searcher``/``ResultParser``/``determine_status`` 를 조합해 도서 목록을
    순차 처리하며, 도서 1건이 최종 상태에 도달할 때마다 콜백을 호출한다.
    """

    def __init__(self, searcher: Searcher, parser: ResultParser) -> None:
        self._searcher = searcher
        self._parser = parser

    def run(
        self,
        entries: list[BookEntry],
        on_progress: Callable[[int, int, BookResult], None] | None = None,
    ) -> list[BookResult]:
        """도서 항목 목록을 순서대로 처리하여 :class:`BookResult` 목록을 반환한다.

        Args:
            entries: 처리할 도서 항목 목록(순서 보존).
            on_progress: 항목 1건이 처리될 때마다 호출되는 콜백.
                ``(완료개수, 전체개수, 해당 결과)`` 를 인자로 받는다.

        Returns:
            입력 ``entries`` 와 동일한 순서의 :class:`BookResult` 목록.
        """
        results: list[BookResult] = []
        total = len(entries)
        for index, entry in enumerate(entries):
            result = self._process_entry(entry)
            results.append(result)
            if on_progress is not None:
                on_progress(index + 1, total, result)
        return results

    def _process_entry(self, entry: BookEntry) -> BookResult:
        """도서 항목 한 건을 처리하여 :class:`BookResult` 로 변환한다."""
        try:
            response = self._searcher.search(entry)
        except RequestError:
            return BookResult(entry=entry, status=BookStatus.REQUEST_ERROR)

        try:
            holdings = self._parser.parse_holdings(response)
        except ParseError:
            return BookResult(entry=entry, status=BookStatus.PARSE_ERROR)

        status, unmanned_libraries = determine_status(holdings)
        return BookResult(
            entry=entry,
            status=status,
            unmanned_libraries=unmanned_libraries,
        )
