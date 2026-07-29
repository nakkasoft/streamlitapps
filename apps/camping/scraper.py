"""
캠핑장 크롤링 모듈

camp.xticket.kr 은 예약 조회 API(GetBookProduct010001.json 등)를 호출하기 전에
반드시 브라우저 세션이 필요합니다. 세션은 다음 순서로만 만들어집니다.

    1. GET /web/main?shopEncode=<캠핑장 고유 토큰> 접속 (JSESSIONID 쿠키 발급)
    2. 그 페이지의 JS가 내부적으로 GetShopInformation.json 을 호출해서
       세션에 매장 정보(shop_code 등)를 바인딩함
    3. 그 다음부터 GetBookProductGroup.json / GetBookProduct010001.json 같은
       조회 API가 정상 동작함

즉 shop_code(숫자)만으로는 세션을 열 수 없고, shopEncode(긴 해시 토큰)로 실제
예약 페이지에 먼저 접속해야 합니다. 이 흐름을 requests만으로 재현하기 어려워서
(내부 상태가 서버 세션에 저장되고 클라이언트 JS 로직이 개입), Playwright
(headless 브라우저)로 페이지를 로드해 세션을 만들고, 그 세션 위에서 동일한
fetch 요청을 그대로 실행합니다.

중요: Streamlit(Tornado 이벤트 루프)과 Playwright의 동기(sync) API를 같은
프로세스에서 함께 실행하면 이벤트 루프 충돌로 Streamlit 서버 프로세스 자체가
아무 에러 로그도 없이 조용히 종료되는 문제가 확인되었다(Streamlit 커뮤니티
포럼에도 보고된 알려진 문제: sync_playwright는 내부적으로 별도 스레드에서
asyncio 이벤트 루프 + greenlet을 사용하는데, 이게 Tornado 이벤트 루프와
같은 프로세스에서 충돌한다). 그래서 실제 Playwright 크롤링은
crawler_worker.py를 별도의 OS 프로세스(subprocess)로 실행해서 수행하고,
결과만 JSON으로 전달받는다.

참고: apps/camping/scraper_sample.py (콘솔 출력 버전 원본)
"""

from __future__ import annotations

import json
import subprocess
import sys
import os

import pandas as pd

RESULT_COLUMNS = ["캠핑장", "날짜", "상품군", "객실명", "상태"]

_WORKER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "crawler_worker.py")


def fetch_availability(campsites: list[dict], dates: list[str], progress_callback=None) -> pd.DataFrame:
    """여러 캠핑장의 예약 가능 현황을 한 번에 조회합니다.

    실제 크롤링은 별도 프로세스(crawler_worker.py)에서 수행합니다. Streamlit과
    Playwright(sync API)를 같은 프로세스에서 함께 실행하면 이벤트 루프 충돌로
    서버가 죽는 문제를 피하기 위한 구조입니다.

    Args:
        campsites: config.py의 CAMPSITES 항목들
        dates: 조회할 날짜 리스트 (YYYYMMDD 형식)
        progress_callback: (완료 개수, 전체 개수, 캠핑장 dict)를 받는 콜백.
            진행률 표시용. 워커 프로세스가 전체를 한 번에 처리하므로, 여기서는
            시작 시 0/total, 완료 시 total/total로만 호출된다.

    Returns:
        컬럼: 캠핑장, 날짜, 상품군, 객실명, 상태
    """
    total = len(campsites)

    if progress_callback:
        progress_callback(0, total, {"name": "크롤링 준비 중"})

    campsites_json = json.dumps(campsites, ensure_ascii=False)
    dates_json = json.dumps(dates)

    try:
        result = subprocess.run(
            [sys.executable, _WORKER_PATH, campsites_json, dates_json],
            capture_output=True,
            text=True,
            timeout=180,
            start_new_session=True,  # Chromium 자식 프로세스가 부모(Streamlit)의
            # 프로세스 그룹/시그널에 영향을 주지 않도록 완전히 새 세션으로 분리한다.
        )
    except subprocess.TimeoutExpired:
        if progress_callback:
            progress_callback(total, total, {"name": "타임아웃"})
        return pd.DataFrame(
            [{"캠핑장": "-", "날짜": "-", "상품군": "-", "객실명": "조회 시간이 초과되었습니다.", "상태": "오류"}]
        )

    if progress_callback:
        progress_callback(total, total, {"name": "완료"})

    if result.returncode != 0:
        error_msg = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "알 수 없는 오류"
        return pd.DataFrame(
            [{"캠핑장": "-", "날짜": "-", "상품군": "-", "객실명": f"크롤링 프로세스 오류: {error_msg}", "상태": "오류"}]
        )

    try:
        rows = json.loads(result.stdout.strip())
    except (json.JSONDecodeError, ValueError):
        return pd.DataFrame(
            [{"캠핑장": "-", "날짜": "-", "상품군": "-", "객실명": "크롤링 결과를 해석할 수 없습니다.", "상태": "오류"}]
        )

    if not rows:
        return pd.DataFrame(columns=RESULT_COLUMNS)

    return pd.DataFrame(rows)
