"""결과 파서 (Result_Parser) 계층 — 사이트 구조 의존 지점(격리).

원본: sblib-search/src/result_parser.py

이 계층은 검색 응답에서 소장 도서관 목록을 추출하고(``parse_holdings``),
각 도서관의 무인예약 지원 여부로 무인예약 가능 도서관을 판별한다
(``determine_unmanned``). 대상 사이트(서울시립도서관 통합검색)의 실제 응답
구조에 의존하는 유일한 지점이므로 추상 인터페이스 뒤로 격리한다.

추출 규칙(원본 조사 결과 기반, ``SblibHtmlResultParser``):
- 검색 결과는 서버 렌더 HTML(``GET searchResultList.do``)로 반환된다.
- 소장 도서관명은 각 결과 항목의 ``dd.site`` 중 ``도서관:`` span 에서 추출한다.
- 무인예약 지원 여부는 ``.state.typeD`` 요소로 판별한다
  (``a``=무인예약신청→지원 / ``span``=무인예약불가→미지원).
- 결과 0건은 ``ul.resultList`` 가 비어 있음으로 판별(빈 리스트 반환),
  ``ul.resultList`` 컨테이너 자체가 없으면 구조 해석 실패(``ParseError``).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from bs4 import BeautifulSoup
from bs4.element import Tag

from .errors import ParseError
from .models import Library, LibraryHolding, RawSearchResponse


def determine_unmanned(holdings: list[LibraryHolding]) -> list[Library]:
    """소장 도서관 목록에서 무인예약을 지원하는 도서관만 골라 반환한다.

    부수효과 없는 순수 함수로, 오직 각 ``LibraryHolding`` 의
    ``unmanned_supported`` 플래그로만 판별한다(입력 순서 보존).
    """
    return [holding.library for holding in holdings if holding.unmanned_supported]


class ResultParser(ABC):
    """검색 응답 → 소장 도서관 + 무인예약 판별을 담당하는 추상 인터페이스."""

    @abstractmethod
    def parse_holdings(self, response: RawSearchResponse) -> list[LibraryHolding]:
        """응답에서 소장 도서관 목록을 추출한다.

        - 검색 결과가 0건이면 빈 리스트를 반환한다.

        Raises:
            ParseError: 응답에서 소장 도서관 목록을 추출할 수 없는 경우
                (구조 해석 실패).
        """
        raise NotImplementedError

    def determine_unmanned(self, holdings: list[LibraryHolding]) -> list[Library]:
        """소장 도서관 목록에서 무인예약을 지원하는 도서관만 골라 반환한다."""
        return determine_unmanned(holdings)


class SblibHtmlResultParser(ResultParser):
    """서울시립도서관(JNET 계열) 통합검색 결과 HTML 파서 구현체.

    추출 규칙(요약):
    - 결과 목록 컨테이너: ``form#basketForm > ul.resultList`` 이며, 그 안의
      각 ``li`` 자식이 소장 항목 1건(특정 도서관의 소장)이다.
    - 도서관명: 항목의 ``dd.site span`` 중 텍스트가 ``도서관`` 으로 시작하는
      span 에서 ``:`` 뒤 값을 trim 한다.
    - 무인예약 지원 여부: 항목의 ``.state.typeD`` 요소로 판별한다. 태그가
      ``a`` (무인예약신청 링크)면 지원(True), ``span`` (무인예약불가)이면
      미지원(False). typeA/typeB/typeC 는 다른 서비스이므로 반드시 typeD 로
      한정한다.
    - 결과 0건: ``ul.resultList`` 는 존재하지만 ``li`` 자식이 없으면 빈
      리스트를 반환한다(검색 결과 없음).
    - 구조 해석 실패: ``ul.resultList`` 컨테이너 자체가 없으면 ``ParseError``
      를 발생시킨다(정상 0건 케이스와 구분).
    """

    _RESULT_LIST_SELECTOR = "form#basketForm ul.resultList"
    _UNMANNED_SELECTOR = ".state.typeD"
    _LIBRARY_LABEL = "도서관"

    def parse_holdings(self, response: RawSearchResponse) -> list[LibraryHolding]:
        """응답 HTML에서 소장 도서관 목록을 추출한다.

        Raises:
            ParseError: ``ul.resultList`` 컨테이너가 없거나 개별 소장 항목의
                구조(도서관명/무인예약 상태)를 해석할 수 없는 경우.
        """
        soup = BeautifulSoup(response.body, "lxml")

        result_list = soup.select_one(self._RESULT_LIST_SELECTOR)
        if result_list is None:
            raise ParseError(
                "검색 결과 목록 컨테이너(form#basketForm > ul.resultList)를 "
                "찾을 수 없어 응답 구조 해석에 실패했습니다."
            )

        holdings: list[LibraryHolding] = []
        for item in result_list.find_all("li", recursive=False):
            holdings.append(self._parse_holding(item))
        return holdings

    def _parse_holding(self, item: Tag) -> LibraryHolding:
        """단일 결과 항목(``li``)을 ``LibraryHolding`` 으로 변환한다."""
        library_name = self._extract_library_name(item)
        unmanned_supported = self._extract_unmanned_supported(item)
        return LibraryHolding(
            library=Library(name=library_name),
            unmanned_supported=unmanned_supported,
        )

    def _extract_library_name(self, item: Tag) -> str:
        """항목에서 도서관명을 추출한다(``dd.site`` 의 ``도서관:`` span)."""
        for span in item.select("dd.site span"):
            text = span.get_text(strip=True)
            if text.startswith(self._LIBRARY_LABEL):
                _, _, value = text.partition(":")
                name = value.strip()
                if name:
                    return name
        raise ParseError(
            "소장 항목에서 도서관명(dd.site 의 '도서관:' span)을 추출할 수 "
            "없어 구조 해석에 실패했습니다."
        )

    def _extract_unmanned_supported(self, item: Tag) -> bool:
        """항목의 무인예약 지원 여부를 ``.state.typeD`` 태그 종류로 판별한다.

        ``a`` 태그(무인예약신청)면 지원(True), 그 외(``span`` = 무인예약불가)면
        미지원(False).
        """
        state = item.select_one(self._UNMANNED_SELECTOR)
        if state is None:
            raise ParseError(
                "소장 항목에서 무인예약 상태(.state.typeD)를 추출할 수 없어 "
                "구조 해석에 실패했습니다."
            )
        return state.name == "a"
