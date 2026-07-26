"""
도서관 크롤링 모듈
실제 도서관 사이트에서 데이터를 가져오는 로직을 구현합니다.
"""

import pandas as pd
from common.utils import fetch_html
from .config import LIBRARIES, WATCHLIST


def search_book(library_url: str, book_title: str) -> dict | None:
    """도서관에서 책을 검색합니다.

    Args:
        library_url: 도서관 검색 URL
        book_title: 검색할 도서명

    Returns:
        검색 결과 딕셔너리 또는 None

    TODO: 실제 도서관 사이트 구조에 맞게 구현하세요.
    """
    # soup = fetch_html(f"{library_url}?keyword={book_title}")
    # if soup is None:
    #     return None
    # 실제 파싱 로직 구현
    pass


def fetch_all_books() -> pd.DataFrame:
    """모든 관심 도서의 현황을 가져옵니다.

    Returns:
        도서 현황 DataFrame
    """
    results = []

    for library in LIBRARIES:
        for book_title in WATCHLIST:
            result = search_book(library["search_url"], book_title)
            if result:
                results.append(result)

    if not results:
        # 데이터가 없으면 빈 DataFrame 반환
        return pd.DataFrame(columns=["도서명", "저자", "도서관", "상태", "반납예정일"])

    return pd.DataFrame(results)
