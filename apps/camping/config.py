"""
캠핑장 앱 설정
다중 캠핑장 지원. 새 캠핑장을 추가하려면 CAMPSITES 리스트에 항목을 추가하세요.

camp.xticket.kr 예약 조회는 브라우저 세션이 필요하므로 (scraper.py 참고),
각 캠핑장은 shop_encode(예약 페이지 URL의 shopEncode 파라미터 값)로 식별합니다.
"""

BASE_URL = "https://camp.xticket.kr"

# 서비스 포트
PORT = 8502

# 캠핑장 목록
# shop_encode는 예약 페이지 URL의 shopEncode= 뒤에 오는 긴 해시 값입니다.
# 예: https://camp.xticket.kr/web/main?shopEncode=<이 값>
CAMPSITES = [
    {
        "name": "우이동 가족 캠핑장",
        "shop_encode": "13896b8dd3600159017b0e96c5bd5be7df3236beaa12b8fdb7aa462bab916b2f",
    },
    {
        "name": "그린웨이가족캠핑장",
        "shop_encode": "5f9422e223671b122a7f2c94f4e15c6f71cd1a49141314cf19adccb98162b5b0",
    },
]

BOOK_DAYS = "1"
TWO_STAY_DAYS = "0"
