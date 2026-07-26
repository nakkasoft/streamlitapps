"""
캠핑장 빈자리 찾기
날짜를 선택하면 등록된 캠핑장들의 예약 가능 현황을 자동으로 조회합니다.
페이지 접속/새로고침/조건 변경 시마다 최신 데이터를 다시 가져옵니다 (캐시 없음).
실행: streamlit run apps/camping/app.py --server.port 8502
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from apps.camping.config import CAMPSITES
from apps.camping.scraper import fetch_campsite_availability
from common.config import HUB_URL

st.set_page_config(
    page_title="캠핑장 빈자리 찾기",
    page_icon="🏕️",
    layout="wide",
)

st.title("🏕️ 캠핑장 빈자리 찾기")
st.markdown("날짜와 캠핑장을 선택한 뒤 '빈자리 조회' 버튼을 누르면 최신 예약 현황을 조회합니다.")
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
        value=datetime.now().date() + timedelta(days=14),
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
    else:
        # 날짜 리스트 생성 (YYYYMMDD 형식)
        date_list = []
        current = start_date
        while current <= end_date:
            date_list.append(current.strftime("%Y%m%d"))
            current += timedelta(days=1)

        # 선택된 캠핑장만 필터
        selected_configs = [c for c in CAMPSITES if c["name"] in selected_campsites]

        # 조회 진행
        all_results = []
        progress_bar = st.progress(0)
        status_text = st.empty()

        total_steps = len(selected_configs)
        for idx, campsite in enumerate(selected_configs):
            status_text.text(f"조회 중... {campsite['name']} ({idx + 1}/{total_steps})")
            df = fetch_campsite_availability(campsite, date_list)
            all_results.append(df)
            progress_bar.progress((idx + 1) / total_steps)

        progress_bar.empty()
        status_text.empty()

        # 결과 합치기
        if all_results:
            result_df = pd.concat(all_results, ignore_index=True)

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
            available_df = result_df[result_df["상태"] == "예약가능"]
            if not available_df.empty:
                st.subheader("✅ 예약 가능 객실")
                st.dataframe(
                    available_df.style.apply(
                        lambda row: ["background-color: #d4edda"] * len(row), axis=1
                    ),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("선택한 기간에 예약 가능한 객실이 없습니다.")

            # 전체 현황
            with st.expander("📋 전체 조회 결과 보기"):
                def highlight_status(row):
                    if row["상태"] == "예약가능":
                        return ["background-color: #d4edda"] * len(row)
                    elif row["상태"] == "매진":
                        return ["background-color: #f8d7da"] * len(row)
                    return ["background-color: #fff3cd"] * len(row)

                st.dataframe(
                    result_df.style.apply(highlight_status, axis=1),
                    use_container_width=True,
                    hide_index=True,
                )

        # 캠핑장 예약 링크
        st.markdown("---")
        st.subheader("🔗 예약 사이트 바로가기")
        for campsite in selected_configs:
            st.markdown(f"- [{campsite['name']}]({campsite['web_url']})")

st.markdown("---")
st.markdown(f"[← 허브로 돌아가기]({HUB_URL})")
