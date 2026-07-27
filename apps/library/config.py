"""
도서관 책 찾기 앱 설정

원본: D:\\workspace\\sblib-search (서울시립도서관 통합검색 무인예약 확인기)
"""

import os

# 서비스 포트
PORT = 8501

# 도서 목록 저장 파일 (원본 CLI의 books.txt와 동일한 형식)
# apps/library/books.txt 에 저장됩니다.
BOOK_LIST_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "books.txt")

# 연속 검색 요청 사이의 최소 간격(초). 대상 사이트 부하 방지.
MIN_INTERVAL_SECONDS = 1.0

# 네트워크 오류 발생 시 최대 재시도 횟수 (최초 시도 포함 총 1+N회)
MAX_RETRIES = 3

# 도서 항목 허용 개수 범위 (lib/list_loader.py의 MIN/MAX_ENTRY_COUNT와 동일)
MIN_BOOK_COUNT = 1
MAX_BOOK_COUNT = 50
