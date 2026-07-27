"""
캠핑장 크롤링 모듈 (Playwright 기반)

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

참고: apps/camping/scraper_sample.py (콘솔 출력 버전 원본)
"""

import json
import pandas as pd
from playwright.sync_api import sync_playwright, Browser

from .config import BASE_URL, BOOK_DAYS, TWO_STAY_DAYS

RESULT_COLUMNS = ["캠핑장", "날짜", "상품군", "객실명", "상태"]


def _fetch_json(page, path: str, params: dict) -> dict:
    """페이지의 세션(쿠키)을 그대로 사용해 POST JSON API를 호출한다."""
    arg_json = json.dumps({"path": path, "params": params})
    script = f"""
    async () => {{
        const arg = {arg_json};
        const resp = await fetch(arg.path, {{
            method: 'POST',
            headers: {{
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'X-Requested-With': 'XMLHttpRequest'
            }},
            body: new URLSearchParams(arg.params)
        }});
        return await resp.text();
    }}
    """
    text = page.evaluate(script)
    return json.loads(text)


def _get_product_groups(page, dates: list[str]) -> list:
    """이 캠핑장에서 조회 가능한 상품군(야영데크/글램핑 등) 목록을 가져온다."""
    result = _fetch_json(
        page,
        "/Web/Book/GetBookProductGroup.json",
        {"start_date": dates[0], "end_date": dates[-1]},
    )
    if result.get("error"):
        raise RuntimeError(result["error"].get("message", "알 수 없는 오류"))
    return result["data"]["bookProductGroupList"]


def _check_date(page, product_group_code: str, date_str: str) -> list[str]:
    """특정 상품군, 특정 날짜에 예약 가능한 사이트(구역) 이름 목록을 반환한다."""
    result = _fetch_json(
        page,
        "/Web/Book/GetBookProduct010001.json",
        {
            "product_group_code": product_group_code,
            "start_date": date_str,
            "end_date": date_str,
            "book_days": BOOK_DAYS,
            "two_stay_days": TWO_STAY_DAYS,
        },
    )
    if result.get("error"):
        raise RuntimeError(result["error"].get("message", "알 수 없는 오류"))

    return [
        room["product_name"]
        for room in result["data"]["bookProductList"]
        if room["select_yn"] == "1"
    ]


def fetch_campsite_availability(browser: Browser, campsite: dict, dates: list[str]) -> pd.DataFrame:
    """캠핑장 하나에 대해 지정한 날짜들의 예약 가능 현황을 조회합니다.

    Args:
        browser: 재사용할 Playwright Browser 인스턴스 (fetch_availability에서 관리)
        campsite: config.py의 CAMPSITES 항목 ({"name", "shop_encode"})
        dates: 조회할 날짜 리스트 (YYYYMMDD 형식)

    Returns:
        컬럼: 캠핑장, 날짜, 상품군, 객실명, 상태(예약가능/매진/오류)
    """
    name = campsite["name"]
    shop_encode = campsite["shop_encode"]
    rows = []

    page = browser.new_page()
    try:
        page.goto(
            f"{BASE_URL}/web/main?shopEncode={shop_encode}",
            wait_until="networkidle",
            timeout=30000,
        )

        if "error.html" in page.url:
            rows.append({
                "캠핑장": name, "날짜": "-", "상품군": "-",
                "객실명": "잘못된 shopEncode 이거나 페이지 구조가 변경되었습니다.",
                "상태": "오류",
            })
            return pd.DataFrame(rows)

        try:
            product_groups = _get_product_groups(page, dates)
        except Exception as e:
            rows.append({
                "캠핑장": name, "날짜": "-", "상품군": "-",
                "객실명": f"상품군 조회 실패: {e}", "상태": "오류",
            })
            return pd.DataFrame(rows)

        for date_str in dates:
            formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"

            for group in product_groups:
                group_code = group["product_group_code"]
                group_name = group["product_group_name"]

                try:
                    available_rooms = _check_date(page, group_code, date_str)
                except Exception as e:
                    rows.append({
                        "캠핑장": name, "날짜": formatted_date, "상품군": group_name,
                        "객실명": f"조회 실패: {e}", "상태": "오류",
                    })
                    continue

                if available_rooms:
                    for room in available_rooms:
                        rows.append({
                            "캠핑장": name, "날짜": formatted_date, "상품군": group_name,
                            "객실명": room, "상태": "예약가능",
                        })
                else:
                    rows.append({
                        "캠핑장": name, "날짜": formatted_date, "상품군": group_name,
                        "객실명": "-", "상태": "매진",
                    })
    finally:
        page.close()

    if not rows:
        return pd.DataFrame(columns=RESULT_COLUMNS)

    return pd.DataFrame(rows)


def fetch_availability(campsites: list[dict], dates: list[str], progress_callback=None) -> pd.DataFrame:
    """여러 캠핑장의 예약 가능 현황을 한 번에 조회합니다.

    Playwright 브라우저를 한 번만 띄워서 캠핑장마다 새 탭(page)으로 재사용합니다.

    Args:
        campsites: config.py의 CAMPSITES 항목들
        dates: 조회할 날짜 리스트 (YYYYMMDD 형식)
        progress_callback: (완료 개수, 전체 개수, 캠핑장 dict)를 받는 콜백. 진행률 표시용.

    Returns:
        컬럼: 캠핑장, 날짜, 상품군, 객실명, 상태
    """
    frames = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            total = len(campsites)
            for idx, campsite in enumerate(campsites):
                df = fetch_campsite_availability(browser, campsite, dates)
                frames.append(df)
                if progress_callback:
                    progress_callback(idx + 1, total, campsite)
        finally:
            browser.close()

    if not frames:
        return pd.DataFrame(columns=RESULT_COLUMNS)

    return pd.concat(frames, ignore_index=True)
