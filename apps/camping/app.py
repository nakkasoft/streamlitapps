"""
캠핑장 빈자리 찾기
날짜를 선택하면 등록된 캠핑장들의 예약 가능 현황을 자동으로 조회합니다.
Playwright(headless 브라우저)로 실제 예약 페이지 세션을 만들어 조회합니다.
실행: streamlit run apps/camping/app.py --server.port 8502
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from apps.camping.config import CAMPSITES, BASE_URL
from apps.camping.scraper import fetch_availability
from common.config import HUB_URL

st.set_page_config(
    page_title="캠핑장 빈자리 찾기",
    page_icon="🏕️",
    layout="wide",
)

st.title("🏕️ 캠핑장 빈자리 찾기")
st.markdown("날짜와 캠핑장을 선택한 뒤 '빈자리 조회' 버튼을 누르면 최신 예약 현황을 조회합니다.")
st.caption("실제 예약 페이지 세션을 통해 조회하므로 캠핑장/날짜 수에 따라 다소 시간이 걸릴 수 있습니다.")
st.markdown("---")

# 날짜 선택 UI
st.subheader("📅 조회할 날짜 선택")

col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input(
        "시작 날짜",
        value=datetime.now().date() + timedelta(days=1),
        min_value=datetime.now().date(),
    )
with col2:
    end_date = st.date_input(
        "종료 날짜",
        value=datetime.now().date() + timedelta(days=7),
        min_value=datetime.now().date(),
    )

# 캠핑장 선택
st.subheader("🏕️ 캠핑장 선택")
campsite_names = [c["name"] for c in CAMPSITES]
selected_campsites = st.multiselect(
    "조회할 캠핑장",
    campsite_names,
    default=campsite_names,
)

# 조회 버튼
search_btn = st.button("🔍 빈자리 조회", type="primary")

st.markdown("---")

if search_btn:
    if not selected_campsites:
        st.warning("캠핑장을 하나 이상 선택해주세요.")
    elif start_date > end_date:
        st.warning("시작 날짜가 종료 날짜보다 클 수 없습니다.")
    elif (end_date - start_date).days > 30:
        st.warning("조회 기간은 최대 31일까지 가능합니다. 기간을 줄여주세요.")
    else:
        # 날짜 리스트 생성 (YYYYMMDD 형식)
        date_list = []
        current = start_date
        while current <= end_date:
            date_list.append(current.strftime("%Y%m%d"))
            current += timedelta(days=1)

        # 선택된 캠핑장만 필터
        selected_configs = [c for c in CAMPSITES if c["name"] in selected_campsites]

        # 조회 진행 (Playwright 브라우저 1개를 재사용하며 캠핑장별로 순회)
        progress_bar = st.progress(0)
        status_text = st.empty()

        def on_progress(done, total, campsite):
            status_text.text(f"조회 중... {campsite['name']} ({done}/{total})")
            progress_bar.progress(done / total)

        status_text.text(f"브라우저 세션 준비 중... (0/{len(selected_configs)})")
        result_df = fetch_availability(selected_configs, date_list, progress_callback=on_progress)

        progress_bar.empty()
        status_text.empty()

        # 결과 표시
        if not result_df.empty:
            # 요약 메트릭
            available_count = len(result_df[result_df["상태"] == "예약가능"])
            full_count = len(result_df[result_df["상태"] == "매진"])
            error_count = len(result_df[result_df["상태"] == "오류"])

            col1, col2, col3 = st.columns(3)
            col1.metric("예약가능", f"{available_count}건")
            col2.metric("매진", f"{full_count}건")
            col3.metric("오류", f"{error_count}건")

            st.markdown("---")

            # 예약 가능한 것만 먼저 강조 표시
            # 참고: pandas Styler(.style.apply)를 st.dataframe에 넘기면 일부 서버
            # 환경(pyarrow 25.0.0 조합)에서 세그폴트가 발생하는 것이 확인되어,
            # 색상 강조 대신 상태를 이모지로 표시하는 방식으로 대체했습니다.
            available_df = result_df[result_df["상태"] == "예약가능"]
            if not available_df.empty:
                st.subheader("✅ 예약 가능 객실")
                st.dataframe(
                    available_df,
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("선택한 기간에 예약 가능한 객실이 없습니다.")

            # 전체 현황
            with st.expander("📋 전체 조회 결과 보기"):
                display_df = result_df.copy()
                status_emoji = {"예약가능": "🟢", "매진": "🔴"}
                display_df["상태"] = display_df["상태"].apply(
                    lambda s: f"{status_emoji.get(s, '🟡')} {s}"
                )

                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True,
                )
        else:
            st.info("조회 결과가 없습니다.")

        # 캠핑장 예약 링크
        st.markdown("---")
        st.subheader("🔗 예약 사이트 바로가기")
        for campsite in selected_configs:
            reserve_url = f"{BASE_URL}/web/main?shopEncode={campsite['shop_encode']}"
            st.markdown(f"- [{campsite['name']}]({reserve_url})")

st.markdown("---")
st.markdown(f"[← 허브로 돌아가기]({HUB_URL})")
