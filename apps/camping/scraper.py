"""
캠핑장 크롤링 모듈
xticket API를 사용하여 캠핑장 잔여석을 조회합니다.
"""

import requests
import pandas as pd
from datetime import datetime, timedelta


def check_availability(campsite: dict, date_str: str) -> list[dict]:
    """특정 캠핑장의 특정 날짜 잔여 객실을 조회합니다.

    Args:
        campsite: config.py의 CAMPSITES 항목
        date_str: 조회할 날짜 (YYYYMMDD 형식)

    Returns:
        가용 객실 리스트 [{"객실명": str, "가능여부": str}]
    """
    payload = {
        "product_group_code": campsite["product_group_code"],
        "start_date": date_str,
        "end_date": date_str,
        "book_days": "1",
        "two_stay_days": "0",
        "shopCode": campsite["shop_code"],
    }

    headers = {
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }

    try:
        r = requests.post(
            campsite["api_url"],
            data=payload,
            headers=headers,
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()

        rooms = []
        for room in data.get("data", {}).get("bookProductList", []):
            rooms.append({
                "객실명": room.get("product_name", "알 수 없음"),
                "가능여부": "예약가능" if room.get("select_yn") == "1" else "매진",
            })

        return rooms

    except Exception as e:
        return [{"객실명": f"[조회실패] {e}", "가능여부": "오류"}]


def fetch_campsite_availability(campsite: dict, dates: list[str]) -> pd.DataFrame:
    """캠핑장의 여러 날짜에 대해 잔여석을 조회합니다.

    Args:
        campsite: config.py의 CAMPSITES 항목
        dates: 조회할 날짜 리스트 (YYYYMMDD 형식)

    Returns:
        조회 결과 DataFrame
    """
    all_results = []

    for date_str in dates:
        rooms = check_availability(campsite, date_str)
        formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"

        for room in rooms:
            all_results.append({
                "캠핑장": campsite["name"],
                "날짜": formatted_date,
                "객실명": room["객실명"],
                "상태": room["가능여부"],
            })

    if not all_results:
        return pd.DataFrame(columns=["캠핑장", "날짜", "객실명", "상태"])

    return pd.DataFrame(all_results)
