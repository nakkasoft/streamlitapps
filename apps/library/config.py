"""
도서관 앱 설정
크롤링 대상 URL, 관심 도서 목록 등을 관리합니다.
"""

# 서비스 포트
PORT = 8501

# 크롤링 대상 도서관 목록
LIBRARIES = [
    {
        "name": "시립도서관",
        "search_url": "https://example.com/library/search",  # 실제 URL로 교체
    },
    {
        "name": "구립도서관",
        "search_url": "https://example.com/library2/search",  # 실제 URL로 교체
    },
]

# 관심 도서 목록
WATCHLIST = [
    "클린 코드",
    "리팩터링",
    "디자인 패턴",
    "파이썬 코딩의 기술",
    "데이터 중심 애플리케이션 설계",
]

# 캐시 TTL (초)
CACHE_TTL = 300  # 5분
