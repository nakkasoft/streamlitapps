"""
캠핑장 앱 설정
다중 캠핑장 지원. 새 캠핑장을 추가하려면 CAMPSITES 리스트에 항목을 추가하세요.
"""

# 서비스 포트
PORT = 8502

# 캠핑장 목록
# 각 캠핑장은 xticket API 기반으로 조회합니다.
# 새 캠핑장을 추가하려면 아래 형식에 맞춰 추가하세요.
CAMPSITES = [
    {
        "name": "캠핑장 A",
        "api_url": "https://camp.xticket.kr/Web/Book/GetBookProduct010001.json",
        "web_url": "https://camp.xticket.kr/web/main?shopEncode=5f9422e223671b122a7f2c94f4e15c6f71cd1a49141314cf19adccb98162b5b0",
        "shop_code": "210820613601",
        "product_group_code": "0002",
    },
    {
        "name": "캠핑장 B (xticket 예시)",
        "api_url": "https://camp.xticket.kr/Web/Book/GetBookProduct010001.json",
        "web_url": "https://camp.xticket.kr/web/main?shopEncode=5f9422e223671b122a7f2c94f4e15c6f71cd1a49141314cf19adccb98162b5b0",
        "shop_code": "210820613601",  # 실제 다른 캠핑장의 shopCode로 교체
        "product_group_code": "0002",
    },
]

# 캐시 TTL (초)
CACHE_TTL = 300  # 5분
