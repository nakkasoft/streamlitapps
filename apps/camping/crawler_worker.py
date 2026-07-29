"""
캠핑장 크롤링 워커 (독립 프로세스로 실행)

Streamlit(Tornado 이벤트 루프 기반)과 Playwright의 동기(sync) API는 같은
프로세스 안에서 함께 쓰면 이벤트 루프 충돌로 서버 프로세스 자체가 조용히
죽는 문제가 있다(에러 로그도 남기지 않고 종료됨). 이를 피하기 위해 실제
Playwright 크롤링은 이 스크립트를 완전히 별도의 OS 프로세스로 실행해서
수행하고, 결과만 표준출력(stdout)으로 JSON 직렬화하여 부모(Streamlit)
프로세스에 전달한다.

사용법 (커맨드라인):
    python crawler_worker.py '<campsites_json>' '<dates_json>'

- campsites_json: [{"name": ..., "shop_encode": ...}, ...] 형태의 JSON 문자열
- dates_json: ["20260801", "20260808", ...] 형태의 JSON 문자열

표준출력으로 결과 rows(JSON 배열)를 출력한다. 각 row는
{"캠핑장":..., "날짜":..., "상품군":..., "객실명":..., "상태":...} 형태.

참고: apps/camping/scraper_sample.py (콘솔 출력 버전 원본)
"""

from __future__ import annotations

import json
import sys

from playwright.sync_api import sync_playwright, Browser

# 이 파일은 단독 프로세스로 실행되므로 패키지 상대 임포트를 쓸 수 없다.
# 같은 폴더의 config.py를 직접 임포트한다.
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import BASE_URL, BOOK_DAYS, TWO_STAY_DAYS  # noqa: E402


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


def fetch_campsite_availability(browser: Browser, campsite: dict, dates: list[str]) -> list[dict]:
    """캠핑장 하나에 대해 지정한 날짜들의 예약 가능 현황을 조회합니다.

    Returns:
        row 딕셔너리 리스트. 컬럼: 캠핑장, 날짜, 상품군, 객실명, 상태(예약가능/매진/오류)
    """
    name = campsite["name"]
    shop_encode = campsite["shop_encode"]
    rows: list[dict] = []

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
            return rows

        try:
            product_groups = _get_product_groups(page, dates)
        except Exception as e:
            rows.append({
                "캠핑장": name, "날짜": "-", "상품군": "-",
                "객실명": f"상품군 조회 실패: {e}", "상태": "오류",
            })
            return rows

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

    return rows


def main() -> None:
    campsites: list[dict] = json.loads(sys.argv[1])
    dates: list[str] = json.loads(sys.argv[2])

    launch_args = [
        "--disable-gpu",
        "--disable-dev-shm-usage",
        "--disable-setuid-sandbox",
        "--no-sandbox",
    ]

    all_rows: list[dict] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=launch_args)
        try:
            for campsite in campsites:
                all_rows.extend(fetch_campsite_availability(browser, campsite, dates))
        finally:
            browser.close()

    # 결과를 stdout으로 JSON 직렬화하여 출력한다 (부모 프로세스가 읽음).
    print(json.dumps(all_rows, ensure_ascii=False))


if __name__ == "__main__":
    main()
