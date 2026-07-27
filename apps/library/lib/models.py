"""핵심 데이터 모델.

원본: sblib-search/src/models.py
모든 데이터 구조는 불변(frozen dataclass)으로 정의하여 값 동등성과
해시 가능성을 확보하고, 순수 함수 계층에서 안전하게 다룰 수 있게 한다.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class BookEntry:
    """도서 항목: 검색 대상 단위."""

    title: str                     # 필수, 정규화(trim) 후 비어 있지 않음
    author: str | None = None      # 선택, 없으면 None


@dataclass(frozen=True)
class Library:
    """개별 도서관."""

    name: str
    code: str | None = None        # 사이트가 제공하는 식별자(있으면)


@dataclass(frozen=True)
class LibraryHolding:
    """특정 도서를 소장한 도서관과 그 도서관의 무인예약 지원 여부."""

    library: Library
    unmanned_supported: bool       # 이 도서에 대해 해당 도서관이 무인예약을 지원하는지


class BookStatus(Enum):
    """도서 항목 처리 결과 분류."""

    UNMANNED_AVAILABLE = "무인예약 가능"
    UNMANNED_UNAVAILABLE = "무인예약 불가"
    NO_RESULTS = "검색 결과 없음"
    REQUEST_ERROR = "요청 오류"
    PARSE_ERROR = "파싱 오류"


@dataclass(frozen=True)
class BookResult:
    """한 도서 항목의 최종 처리 결과."""

    entry: BookEntry
    status: BookStatus
    unmanned_libraries: tuple[Library, ...] = ()   # status가 무인예약 가능일 때 채워짐


@dataclass(frozen=True)
class SearchQuery:
    """검색 요청 파라미터(사이트 구조에 독립적인 논리 표현)."""

    title: str
    author: str | None = None


@dataclass(frozen=True)
class RawSearchResponse:
    """검색 응답의 원시 표현(HTML 본문 또는 파싱 전 페이로드)."""

    status_code: int
    body: str


@dataclass(frozen=True)
class RunConfig:
    """실행 구성."""

    book_list_path: str
    min_interval_seconds: float = 1.0
    max_retries: int = 3
