"""목록 로더 (List_Loader) — 순수 파싱/직렬화 로직.

원본: sblib-search/src/list_loader.py

파일 형식 규칙 요약:
- 인코딩: UTF-8 (파일 I/O는 ``load`` 에서 담당하며, 본 모듈은 텍스트만 다룬다)
- 논리적 한 줄 = 도서 항목 하나
- 필드 구분자: ``" | "`` (공백-파이프-공백). 구분자 앞이 제목, 뒤가 저자.
- 저자 생략 가능: 구분자가 없으면 줄 전체가 제목.
- ``#`` 으로 시작하는 줄과 공백만 있는 줄은 무시한다(주석/공백).
- 제목/저자 앞뒤 공백은 제거(trim)한다.
- (제목, 저자)가 모두 동일한 항목은 하나로 정규화한다(최초 등장 순서 유지).
"""

from __future__ import annotations

from .errors import BookListNotFoundError, CountOutOfRangeError, InvalidEntryError
from .models import BookEntry

#: 처리 가능한 도서 항목 수의 최소값(포함).
MIN_ENTRY_COUNT = 1

#: 처리 가능한 도서 항목 수의 최대값(포함).
MAX_ENTRY_COUNT = 50

#: 제목과 저자를 구분하는 필드 구분자(공백-파이프-공백).
FIELD_DELIMITER = " | "

#: 주석 줄을 나타내는 접두사.
COMMENT_PREFIX = "#"


class ListLoader:
    """도서 목록 파일 텍스트와 도서 항목 집합 사이를 변환한다.

    ``parse``/``serialize`` 는 순수 함수이며 서로 역함수 관계를 이룬다.
    """

    def parse(self, text: str) -> list[BookEntry]:
        """도서 목록 파일 텍스트를 순서 있는 도서 항목 집합으로 파싱한다.

        Raises:
            InvalidEntryError: 제목이 비어 있는 항목 줄이 존재하는 경우.
        """
        entries: list[BookEntry] = []
        seen: set[tuple[str, str | None]] = set()

        for line_number, raw_line in enumerate(text.splitlines(), start=1):
            stripped = raw_line.strip()

            if not stripped or stripped.startswith(COMMENT_PREFIX):
                continue

            title, author = self._split_entry(raw_line)

            if not title:
                raise InvalidEntryError(line_number)

            key = (title, author)
            if key in seen:
                continue
            seen.add(key)
            entries.append(BookEntry(title=title, author=author))

        return entries

    def serialize(self, entries: list[BookEntry]) -> str:
        """도서 항목 집합을 도서 목록 파일 형식 텍스트로 직렬화한다."""
        lines: list[str] = []
        for entry in entries:
            if entry.author is not None:
                lines.append(f"{entry.title}{FIELD_DELIMITER}{entry.author}")
            else:
                lines.append(entry.title)
        return "\n".join(lines)

    def load(self, path: str) -> list[BookEntry]:
        """파일을 읽어 ``parse`` 한 뒤 항목 수 범위(1~50)를 검증한다.

        Raises:
            BookListNotFoundError: 지정된 파일이 존재하지 않는 경우.
            InvalidEntryError: 제목이 비어 있는 항목 줄이 존재하는 경우(``parse`` 전파).
            CountOutOfRangeError: 항목 수가 1 미만 또는 50 초과인 경우.
        """
        try:
            with open(path, encoding="utf-8") as file:
                text = file.read()
        except FileNotFoundError as exc:
            raise BookListNotFoundError(path) from exc

        entries = self.parse(text)

        count = len(entries)
        if count < MIN_ENTRY_COUNT or count > MAX_ENTRY_COUNT:
            raise CountOutOfRangeError(count)

        return entries

    @staticmethod
    def _split_entry(line: str) -> tuple[str, str | None]:
        """항목 줄을 ``(제목, 저자)`` 로 분해하고 각 값을 trim한다."""
        if FIELD_DELIMITER in line:
            title_part, author_part = line.split(FIELD_DELIMITER, 1)
            title = title_part.strip()
            author = author_part.strip()
            return title, (author or None)
        return line.strip(), None
