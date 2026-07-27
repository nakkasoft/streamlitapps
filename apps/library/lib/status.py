"""상태 결정 (Status Decision) 순수 함수.

원본: sblib-search/src/status.py

한 도서 항목의 소장 도서관 목록으로부터 그 도서의 처리 상태를 결정한다.

    | 조건                              | 결과 상태                     |
    | --------------------------------- | ----------------------------- |
    | 소장 도서관 0건(검색 결과 없음)   | NO_RESULTS                    |
    | 무인예약 지원 도서관 ≥ 1          | UNMANNED_AVAILABLE (+ 목록)   |
    | 소장 도서관은 있으나 무인예약 0   | UNMANNED_UNAVAILABLE          |

``REQUEST_ERROR`` / ``PARSE_ERROR`` 는 네트워크·파싱 예외를 포착하는
상위 실행기(app.py의 확인 작업 실행 로직)가 결정하며, 이 순수 함수의
책임이 아니다.
"""

from __future__ import annotations

from .models import BookStatus, Library, LibraryHolding
from .result_parser import determine_unmanned


def determine_status(
    holdings: list[LibraryHolding],
) -> tuple[BookStatus, tuple[Library, ...]]:
    """소장 도서관 목록으로부터 도서 상태와 무인예약 가능 도서관을 결정한다.

    Returns:
        ``(status, unmanned_libraries)`` 튜플.
        - 소장 목록이 비어 있으면 ``(NO_RESULTS, ())``.
        - 무인예약 지원 도서관이 하나 이상이면
          ``(UNMANNED_AVAILABLE, (<무인예약 지원 도서관들>, ...))``.
        - 소장 도서관은 있으나 무인예약 지원이 하나도 없으면
          ``(UNMANNED_UNAVAILABLE, ())``.
    """
    if not holdings:
        return BookStatus.NO_RESULTS, ()

    unmanned_libraries = tuple(determine_unmanned(holdings))
    if unmanned_libraries:
        return BookStatus.UNMANNED_AVAILABLE, unmanned_libraries

    return BookStatus.UNMANNED_UNAVAILABLE, ()
