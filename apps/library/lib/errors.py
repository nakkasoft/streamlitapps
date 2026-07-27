"""예외 계층.

원본: sblib-search/src/errors.py

오류 처리 전략은 계층에 따라 두 갈래로 나뉜다.

- **입력 계층(파일/형식) 오류는 치명적(fatal)** 으로 처리한다. 잘못된 입력으로는
  의미 있는 실행이 불가능하므로, 사용자가 즉시 수정할 수 있도록 위치 정보
  (파일 경로, 1-based 행 번호, 실제 개수)를 예외 필드와 메시지에 담는다.
  - ``BookListNotFoundError`` : 파일 경로
  - ``InvalidEntryError``     : 1-based 행 번호
  - ``CountOutOfRangeError``  : 실제 항목 개수(+ 허용 범위)

- **수집/해석 계층(네트워크/파싱) 오류는 비치명적(non-fatal)** 으로 처리한다.
  일부 실패는 불가피하므로 오케스트레이터가 포착하여 도서 상태로 변환한다.
  - ``NetworkError`` : 재시도 대상. HTTP 전송 중 발생하는 연결/타임아웃/5xx 등.
  - ``RequestError`` : 재시도 소진 후 승격되는 오류. 마지막 원인 예외를 감싼다.
  - ``ParseError``   : 응답에서 소장 도서관 목록을 추출하지 못한 구조 해석 실패.
"""

from __future__ import annotations


class LibraryReservationError(Exception):
    """이 도구가 발생시키는 모든 예외의 공통 기반 클래스."""


# ---------------------------------------------------------------------------
# 입력 계층 오류 (치명적) — 위치/개수 정보를 필드로 보존
# ---------------------------------------------------------------------------


class BookListNotFoundError(LibraryReservationError):
    """지정된 도서 목록 파일이 존재하지 않는 경우.

    Attributes:
        path: 찾지 못한 도서 목록 파일 경로.
    """

    def __init__(self, path: str, message: str | None = None) -> None:
        self.path = path
        if message is None:
            message = f"도서 목록 파일을 찾을 수 없습니다: {path}"
        super().__init__(message)


class InvalidEntryError(LibraryReservationError):
    """도서 제목이 없는 도서 항목이 존재하는 경우.

    Attributes:
        line_number: 문제가 발생한 항목의 1-based 행 번호.
    """

    def __init__(self, line_number: int, message: str | None = None) -> None:
        self.line_number = line_number
        if message is None:
            message = f"{line_number}번째 줄에 제목이 없는 도서 항목이 있습니다."
        super().__init__(message)


class CountOutOfRangeError(LibraryReservationError):
    """도서 항목 수가 허용 범위(1~50)를 벗어난 경우.

    Attributes:
        count: 실제 도서 항목 개수.
        min_count: 허용되는 최소 개수.
        max_count: 허용되는 최대 개수.
    """

    def __init__(
        self,
        count: int,
        min_count: int = 1,
        max_count: int = 50,
        message: str | None = None,
    ) -> None:
        self.count = count
        self.min_count = min_count
        self.max_count = max_count
        if message is None:
            message = (
                f"도서 항목 수가 허용 범위({min_count}~{max_count})를 벗어났습니다: "
                f"{count}개"
            )
        super().__init__(message)


# ---------------------------------------------------------------------------
# 수집/해석 계층 오류 (비치명적) — 상태로 변환되거나 재시도됨
# ---------------------------------------------------------------------------


class NetworkError(LibraryReservationError):
    """HTTP 전송 중 발생하는 네트워크 계열 오류(재시도 대상).

    연결 실패, 타임아웃, 5xx 응답 등을 포괄한다. 원인 예외가 있으면
    ``cause`` 로 보존하며 ``__cause__`` 로도 연결한다.

    Attributes:
        cause: 이 네트워크 오류를 유발한 하위 예외(있으면).
    """

    def __init__(self, message: str, cause: BaseException | None = None) -> None:
        self.cause = cause
        super().__init__(message)
        if cause is not None:
            self.__cause__ = cause


class RequestError(LibraryReservationError):
    """최대 재시도 후에도 검색 요청이 실패한 경우 승격되는 오류.

    마지막으로 발생한 원인 예외를 감싸며, 총 시도 횟수를 함께 보존한다.
    이 오류는 오케스트레이터에서 도서 상태 "요청 오류"로 변환된다.

    Attributes:
        cause: 마지막으로 발생한 원인 예외(있으면).
        attempts: 총 시도 횟수(최초 1회 + 재시도 횟수).
    """

    def __init__(
        self,
        message: str,
        cause: BaseException | None = None,
        attempts: int | None = None,
    ) -> None:
        self.cause = cause
        self.attempts = attempts
        super().__init__(message)
        if cause is not None:
            self.__cause__ = cause


class ParseError(LibraryReservationError):
    """응답에서 소장 도서관 목록을 추출할 수 없는 구조 해석 실패.

    이 오류는 오케스트레이터에서 도서 상태 "파싱 오류"로 변환된다.

    Attributes:
        cause: 파싱 실패를 유발한 하위 예외(있으면).
    """

    def __init__(self, message: str, cause: BaseException | None = None) -> None:
        self.cause = cause
        super().__init__(message)
        if cause is not None:
            self.__cause__ = cause
