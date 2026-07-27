"""검색기 (Searcher).

원본: sblib-search/src/searcher.py

검색기는 도서 항목(:class:`BookEntry`)을 검색 요청으로 변환하고 대상 웹사이트에
요청을 전송하는 수집 계층 구성요소다.

- **요청 생성(``build_query``)**: 도서 항목을 사이트 구조에 독립적인 논리
  검색 질의(:class:`SearchQuery`)로 변환하는 순수 함수.
- **네트워크 전송(``HttpClient`` / ``search``)**: 실제 HTTP 전송은
  :class:`HttpClient` 인터페이스 뒤로 격리한다. ``Searcher.search`` 는
  :class:`RateLimiter` (요청 속도 제한)와 :class:`RetryPolicy` (재시도)를
  결합하여 HTTP 요청을 보낸다.

대상 사이트(서울시립도서관 통합검색)의 실제 파라미터 매핑은
:func:`to_site_params` 헬퍼로 이 계층 안에 격리한다.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import TYPE_CHECKING

from .errors import NetworkError
from .models import BookEntry, RawSearchResponse, SearchQuery

if TYPE_CHECKING:  # pragma: no cover - 타입 검사 전용
    from .rate_limiter import RateLimiter
    from .retry_policy import RetryPolicy


# ---------------------------------------------------------------------------
# 대상 사이트 엔드포인트/기본값
# ---------------------------------------------------------------------------

BASE_URL = "https://www.sblib.seoul.kr"
SEARCH_RESULT_LIST_URL = (
    BASE_URL + "/library/menu/10012/program/30003/searchResultList.do"
)


class HttpClient(ABC):
    """검색 요청을 실제로 전송하는 HTTP 클라이언트 인터페이스."""

    @abstractmethod
    def get(
        self, url: str, params: Mapping[str, str] | None = None
    ) -> RawSearchResponse:
        """``url`` 에 주어진 ``params`` 로 GET 요청을 보내고 응답을 반환한다.

        Raises:
            NetworkError: 연결 실패/타임아웃/5xx 등 재시도 대상 네트워크 오류.
        """
        raise NotImplementedError


def to_site_params(query: SearchQuery) -> dict[str, str]:
    """논리 :class:`SearchQuery` 를 대상 사이트의 요청 파라미터로 매핑한다.

    - **제목만**: ``query=<제목>`` + ``f1=TITLE`` (간략검색).
    - **제목 + 저자**: ``detailTitle=<제목>`` + ``detailAuthor=<저자>`` (상세검색,
      이때 ``query`` 는 비우고 ``f1=ALL``).
    """
    params: dict[str, str] = {
        "collection": "book",
        "sort": "RANK/DESC",
        "resultCount": "50",
        "startCount": "0",
    }
    if query.author is not None:
        params["query"] = ""
        params["f1"] = "ALL"
        params["detailTitle"] = query.title
        params["detailAuthor"] = query.author
    else:
        params["query"] = query.title
        params["f1"] = "TITLE"
    return params


class Searcher:
    """도서 항목을 검색 요청으로 변환하고 대상 웹사이트에 전송하는 검색기."""

    def __init__(
        self,
        http_client: HttpClient | None = None,
        rate_limiter: "RateLimiter | None" = None,
        retry_policy: "RetryPolicy | None" = None,
    ) -> None:
        self._http_client = http_client
        self._rate_limiter = rate_limiter
        self._retry_policy = retry_policy

    def build_query(self, entry: BookEntry) -> SearchQuery:
        """도서 항목을 사이트에 독립적인 논리 검색 질의로 변환한다.

        - 항상 도서 제목을 검색어로 포함한다.
        - 도서 항목에 저자가 지정된 경우에만 질의에 저자를 포함한다.
        """
        raw_author = entry.author
        has_author = raw_author is not None and raw_author.strip() != ""
        author = raw_author if has_author else None
        return SearchQuery(title=entry.title, author=author)

    def search(self, entry: BookEntry) -> RawSearchResponse:
        """도서 항목을 검색하여 원시 응답(:class:`RawSearchResponse`)을 반환한다.

        Raises:
            RequestError: 최대 재시도 후에도 네트워크 오류가 지속되는 경우.
            RuntimeError: 네트워크 의존성이 주입되지 않은 인스턴스에서 호출된 경우.
        """
        if (
            self._http_client is None
            or self._rate_limiter is None
            or self._retry_policy is None
        ):
            raise RuntimeError(
                "search()를 사용하려면 http_client, rate_limiter, retry_policy를 "
                "모두 주입해야 합니다."
            )

        query = self.build_query(entry)
        params = to_site_params(query)

        # 1) 요청 속도 제한: 재시도 루프 이전에 한 번 획득한다.
        self._rate_limiter.acquire()

        # 2) HTTP 전송을 재시도 정책으로 감싼다.
        def _send() -> RawSearchResponse:
            return self._http_client.get(SEARCH_RESULT_LIST_URL, params)

        return self._retry_policy.execute(_send)


class RequestsHttpClient(HttpClient):
    """``requests`` 라이브러리 기반 :class:`HttpClient` 구현체.

    세션을 재사용하여 연결을 효율화하고, 타임아웃과 현실적인 ``User-Agent``
    헤더를 적용한다. 오류는 재시도 정책이 재시도 대상으로 인식할 수 있도록
    :class:`~.errors.NetworkError` 로 승격한다.
    """

    #: 기본 요청 타임아웃(초). 연결/응답 모두에 적용한다.
    DEFAULT_TIMEOUT: float = 10.0
    #: 기본 User-Agent(실제 브라우저와 유사한 문자열).
    DEFAULT_USER_AGENT: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    def __init__(
        self,
        session: "object | None" = None,
        timeout: float = DEFAULT_TIMEOUT,
        user_agent: str = DEFAULT_USER_AGENT,
    ) -> None:
        import requests

        self._requests = requests
        self._session = session if session is not None else requests.Session()
        self._timeout = timeout
        self._session.headers.setdefault("User-Agent", user_agent)

    def get(
        self, url: str, params: Mapping[str, str] | None = None
    ) -> RawSearchResponse:
        """``url`` 에 GET 요청을 전송하고 응답을 :class:`RawSearchResponse` 로 반환한다.

        Raises:
            NetworkError: 연결 실패/타임아웃 등 전송 예외 또는 5xx 응답
                (재시도 대상).
        """
        try:
            response = self._session.get(
                url,
                params=dict(params) if params is not None else None,
                timeout=self._timeout,
            )
        except self._requests.exceptions.RequestException as exc:
            raise NetworkError(
                f"HTTP 요청 중 네트워크 오류가 발생했습니다: {url}", cause=exc
            ) from exc

        if response.status_code >= 500:
            raise NetworkError(
                f"서버 오류 응답({response.status_code})을 받았습니다: {url}"
            )

        return RawSearchResponse(status_code=response.status_code, body=response.text)
