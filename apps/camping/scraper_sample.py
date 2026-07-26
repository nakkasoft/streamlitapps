import requests
from datetime import datetime

URL = "https://camp.xticket.kr/Web/Book/GetBookProduct010001.json"

TARGET_DATES = [
    "20260801",
    "20260808",
    "20260815",
    "20260822",
    "20260829"
]


def check_date(date_str):
    payload = {
        "product_group_code": "0002",
        "start_date": date_str,
        "end_date": date_str,
        "book_days": "1",
        "two_stay_days": "0",
        "shopCode": "210820613601"
    }

    headers = {
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0"
    }

    r = requests.post(
        URL,
        data=payload,
        headers=headers,
        timeout=10
    )

    r.raise_for_status()

    data = r.json()

    available_rooms = []

    for room in data["data"]["bookProductList"]:
        if room["select_yn"] == "1":
            available_rooms.append(room["product_name"])

    return available_rooms


def main():

    print("=" * 60)
    print(datetime.now())
    print("=" * 60)

    found = False

    for date_str in TARGET_DATES:

        try:
            rooms = check_date(date_str)

            if rooms:
                found = True

                print(f"\n[FOUND] {date_str}")

                for room in rooms:
                    print(f"  - {room}")

            else:
                print(f"[FULL ] {date_str}")

        except Exception as e:
            print(f"[ERROR] {date_str}: {e}")

    print()

    if found:
        print("★★★★★ 예약 가능 객실 발견 ★★★★★")
    else:
        print("모든 대상 날짜 만석")


if __name__ == "__main__":
    main()