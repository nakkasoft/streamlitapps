"""BookRepository — 도서 목록 CRUD + books.txt 영속화.

원본: sblib-search/webapp/repository.py

기존 ``ListLoader.parse``/``serialize``/``load`` 를 그대로 재사용한다.
쓰기 메서드(``add``/``update``/``delete``)는 유효성 검증을 상태 변경
**이전에** 모두 완료하여, 검증에 실패하면 인메모리 상태와 파일 어느
쪽에도 부수효과를 남기지 않는다(원자성).

Streamlit 환경에서는 스레드 락 대신 단순 순차 처리로 충분하므로, 원본의
``threading.Lock`` 은 유지하되(안전망) 동시성 관리 자체는 단순화했다.
"""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass
from pathlib import Path

from .errors import CountOutOfRangeError, InvalidEntryError
from .list_loader import MAX_ENTRY_COUNT, MIN_ENTRY_COUNT, ListLoader
from .models import BookEntry

__all__ = ["BookRepository", "BookItem", "BookNotFoundError"]


class BookNotFoundError(Exception):
    """지정된 id의 도서 항목이 도서 목록에 존재하지 않는 경우."""

    def __init__(self, book_id: str, message: str | None = None) -> None:
        self.book_id = book_id
        if message is None:
            message = f"도서 항목을 찾을 수 없습니다: {book_id}"
        super().__init__(message)


@dataclass(frozen=True)
class BookItem:
    """웹(UI) 계층에서만 쓰이는 식별자 부여 래퍼. 기존 BookEntry는 변경하지 않는다."""

    id: str
    entry: BookEntry


class BookRepository:
    """도서 목록을 인메모리로 관리하고, 변경마다 파일(books.txt)에 동기화한다."""

    def __init__(self, loader: ListLoader, file_path: str) -> None:
        """저장소를 초기화한다.

        - ``file_path`` 가 존재하면 ``ListLoader.load`` 로 읽어 초기 상태를 구성한다.
        - 존재하지 않으면 빈 목록으로 시작한다(첫 도서 추가 시 파일이 생성됨).
        """
        self._loader = loader
        self._file_path = file_path
        self._lock = threading.Lock()

        if Path(file_path).exists():
            entries = self._loader.load(file_path)
        else:
            entries = []

        self._items: list[BookItem] = [
            BookItem(id=self._new_id(), entry=entry) for entry in entries
        ]

    def list_all(self) -> list[BookItem]:
        """현재 도서 목록을 등록 순서대로 반환한다."""
        with self._lock:
            return list(self._items)

    def add(self, title: str, author: str | None) -> BookItem:
        """도서 항목을 추가하고 파일에 동기화한다.

        Raises:
            InvalidEntryError: ``title`` 이 공백뿐인 경우.
            CountOutOfRangeError: 추가 후 개수가 50을 초과하는 경우.
        """
        with self._lock:
            normalized_title = self._validate_title(title)
            normalized_author = self._normalize_author(author)

            if len(self._items) + 1 > MAX_ENTRY_COUNT:
                raise CountOutOfRangeError(len(self._items) + 1)

            item = BookItem(
                id=self._new_id(),
                entry=BookEntry(title=normalized_title, author=normalized_author),
            )
            new_items = [*self._items, item]
            self._sync(new_items)
            self._items = new_items
            return item

    def update(self, book_id: str, title: str, author: str | None) -> BookItem:
        """지정한 id의 항목만 갱신한다.

        Raises:
            BookNotFoundError: ``book_id`` 가 존재하지 않는 경우.
            InvalidEntryError: ``title`` 이 공백뿐인 경우.
        """
        with self._lock:
            index = self._find_index(book_id)
            if index is None:
                raise BookNotFoundError(book_id)

            normalized_title = self._validate_title(title)
            normalized_author = self._normalize_author(author)

            updated_item = BookItem(
                id=book_id,
                entry=BookEntry(title=normalized_title, author=normalized_author),
            )
            new_items = list(self._items)
            new_items[index] = updated_item
            self._sync(new_items)
            self._items = new_items
            return updated_item

    def delete(self, book_id: str) -> None:
        """지정한 id의 항목을 제거한다.

        Raises:
            BookNotFoundError: ``book_id`` 가 존재하지 않는 경우.
            CountOutOfRangeError: 삭제 후 개수가 0이 되는 경우.
        """
        with self._lock:
            index = self._find_index(book_id)
            if index is None:
                raise BookNotFoundError(book_id)

            if len(self._items) - 1 < MIN_ENTRY_COUNT:
                raise CountOutOfRangeError(len(self._items) - 1)

            new_items = list(self._items)
            del new_items[index]
            self._sync(new_items)
            self._items = new_items

    def to_entries(self) -> list[BookEntry]:
        """확인 작업 시작 시 전달할 순수 ``BookEntry`` 목록(id 제외)을 반환한다."""
        with self._lock:
            return [item.entry for item in self._items]

    def _sync(self, items: list[BookItem]) -> None:
        """``items`` 를 직렬화하여 파일에 UTF-8로 동기화한다."""
        text = self._loader.serialize([item.entry for item in items])
        Path(self._file_path).write_text(text, encoding="utf-8")

    def _find_index(self, book_id: str) -> int | None:
        for index, item in enumerate(self._items):
            if item.id == book_id:
                return index
        return None

    @staticmethod
    def _validate_title(title: str) -> str:
        """제목을 trim하고, 공백뿐이면 ``InvalidEntryError`` 를 발생시킨다."""
        normalized = title.strip()
        if not normalized:
            raise InvalidEntryError(line_number=1, message="도서 제목은 필수입니다.")
        return normalized

    @staticmethod
    def _normalize_author(author: str | None) -> str | None:
        """저자를 trim하고, 공백뿐이거나 ``None`` 이면 ``None`` 을 반환한다."""
        if author is None:
            return None
        normalized = author.strip()
        return normalized or None

    @staticmethod
    def _new_id() -> str:
        """새 도서 항목에 부여할 고유 id를 생성한다."""
        return uuid.uuid4().hex
