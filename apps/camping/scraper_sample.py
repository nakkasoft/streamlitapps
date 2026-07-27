"""
캠핑장 예약 가능 여부 조회 스크립트.

camp.xticket.kr 은 예약 조회 API(GetBookProduct010001.json 등)를 호출하기 전에
반드시 브라우저 세션이 필요합니다. 세션은 다음 순서로만 만들어집니다.

    1. GET /web/main?shopEncode=<캠핑장 고유 토큰> 접속 (JSESSIONID 쿠키 발급)
    2. 그 페이지의 JS가 내부적으로 GetShopInformation.json 을 호출해서
       세션에 매장 정보(shop_code 등)를 바인딩함
    3. 그 다음부터 GetBookProductGroup.json / GetBookProduct010001.json 같은
       조회 API가 정상 동작함

즉 shop_code(숫자, 예: 210820613601) 만으로는 세션을 열 수 없고, shopEncode
(긴 해시 토큰)로 실제 예약 페이지에 먼저 접속해야 합니다. 이 흐름을 requests만으로
재현하기 어려워서(내부 상태가 서버 세션에 저장되고 클라이언트 JS 로직이 개입),
Playwright(headless 브라우저)로 페이지를 로드해 세션을 만들고, 그 세션 위에서
동일한 fetch 요청을 그대로 실행합니다.
"""

import json
from datetime import datetime

from playwright.sync_api import sync_playwright

BASE_URL = "https://camp.xticket.kr"

# 조회할 캠핑장 목록: 이름과 shopEncode(예약 페이지 URL의 shopEncode 파라미터 값)
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

TARGET_DATES = [
    "20260801",
    "20260808",
    "20260815",
    "20260822",
    "20260829",
]

BOOK_DAYS = "1"
TWO_STAY_DAYS = "0"


def fetch_json(page, path: str, params: dict) -> dict:
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


def get_product_groups(page) -> list:
    """이 캠핑장에서 조회 가능한 상품군(야영데크/글램핑 등) 목록을 가져온다."""
    result = fetch_json(
        page,
        "/Web/Book/GetBookProductGroup.json",
        {
            "start_date": TARGET_DATES[0],
            "end_date": TARGET_DATES[-1],
        },
    )
    if result.get("error"):
        raise RuntimeError(result["error"].get("message", "알 수 없는 오류"))
    return result["data"]["bookProductGroupList"]


def check_date(page, product_group_code: str, date_str: str) -> list:
    """특정 상품군, 특정 날짜에 예약 가능한 사이트(구역) 이름 목록을 반환한다."""
    result = fetch_json(
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

    available_rooms = []
    for room in result["data"]["bookProductList"]:
        if room["select_yn"] == "1":
            available_rooms.append(room["product_name"])

    return available_rooms


def check_campsite(browser, campsite: dict) -> bool:
    """캠핑장 하나에 대해 모든 대상 날짜, 모든 상품군을 조회해서 출력한다.

    반환값: 예약 가능한 곳을 하나라도 찾았으면 True.
    """
    name = campsite["name"]
    shop_encode = campsite["shop_encode"]

    print(f"\n[{name}]")

    page = browser.new_page()
    found = False

    try:
        page.goto(
            f"{BASE_URL}/web/main?shopEncode={shop_encode}",
            wait_until="networkidle",
            timeout=30000,
        )

        if "error.html" in page.url:
            print(f"  [ERROR] 접속 실패 (잘못된 shopEncode 이거나 페이지 구조 변경): {page.url}")
            return False

        try:
            product_groups = get_product_groups(page)
        except Exception as e:
            print(f"  [ERROR] 상품군 조회 실패: {e}")
            return False

        for date_str in TARGET_DATES:
            rooms_by_group = {}

            for group in product_groups:
                group_code = group["product_group_code"]
                group_name = group["product_group_name"]
                try:
                    rooms = check_date(page, group_code, date_str)
                except Exception as e:
                    print(f"  [ERROR] {date_str} ({group_name}): {e}")
                    continue

                if rooms:
                    rooms_by_group[group_name] = rooms

            if rooms_by_group:
                found = True
                print(f"  [FOUND] {date_str}")
                for group_name, rooms in rooms_by_group.items():
                    print(f"    - {group_name}: {', '.join(rooms)}")
            else:
                print(f"  [FULL ] {date_str}")

    finally:
        page.close()

    return found


def main():
    print("=" * 60)
    print(datetime.now())
    print("=" * 60)

    any_found = False

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            for campsite in CAMPSITES:
                if check_campsite(browser, campsite):
                    any_found = True
        finally:
            browser.close()

    print()
    if any_found:
        print("★★★★★ 예약 가능 객실 발견 ★★★★★")
    else:
        print("모든 대상 날짜 만석")


if __name__ == "__main__":
    main()

