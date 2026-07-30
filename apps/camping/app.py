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

        # 조회 진행
        # 실제 크롤링은 별도 프로세스(crawler_worker.py)에서 한 번에 처리되므로
        # (Streamlit과 Playwright를 같은 프로세스에서 함께 쓰면 서버가 죽는
        # 문제를 피하기 위한 구조), 진행률은 시작/완료 두 단계로만 표시됩니다.
        progress_bar = st.progress(0)
        status_text = st.empty()

        def on_progress(done, total, campsite):
            status_text.text(f"{campsite['name']}... ({done}/{total})")
            progress_bar.progress(done / total if total else 0)

        with st.spinner(f"캠핑장 {len(selected_configs)}곳의 예약 현황을 조회하는 중입니다..."):
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
            col1.metric("예약가능 (개별 사이트 수)", f"{available_count}건")
            col2.metric("매진", f"{full_count}건")
            col3.metric("오류", f"{error_count}건")
            st.caption(
                "※ '예약가능 건수'는 사이트(데크/구역) 단위 개수입니다. "
                "같은 날짜·상품군에 여러 사이트가 열려있으면 그만큼 합산됩니다."
            )

            st.markdown("---")

            # 표(st.dataframe)는 셀에 긴 텍스트가 들어가면 잘려 보이는 문제가
            # 있어서, 캠핑장 > 날짜 > 상품군별로 순수 마크다운 텍스트로
            # 상세 결과를 출력합니다. 접었다 펼 필요 없이 스크롤만 하면
            # 전체 내용을 바로 볼 수 있습니다.
            st.subheader("🔎 상세 결과 (캠핑장 · 날짜 · 상품군별)")

            for camp in result_df["캠핑장"].unique():
                camp_df = result_df[result_df["캠핑장"] == camp]
                st.markdown(f"### 🏕️ {camp}")

                for date in sorted(camp_df["날짜"].unique()):
                    date_df = camp_df[camp_df["날짜"] == date]
                    st.markdown(f"**📅 {date}**")

                    for group in date_df["상품군"].unique():
                        group_df = date_df[date_df["상품군"] == group]

                        error_rows = group_df[group_df["상태"] == "오류"]
                        if not error_rows.empty:
                            st.markdown(f"- **{group}**: ⚠️ 조회 오류 — {error_rows['객실명'].iloc[0]}")
                            continue

                        total_sites = len(group_df)
                        avail_rows = group_df[group_df["상태"] == "예약가능"]
                        avail_names = avail_rows["객실명"].tolist()

                        if avail_names:
                            names_text = ", ".join(avail_names)
                            st.markdown(
                                f"- **{group}** ({len(avail_names)}/{total_sites} 예약가능): "
                                f"🟢 {names_text}"
                            )
                        else:
                            st.markdown(f"- **{group}** (0/{total_sites} 예약가능): 🔴 매진")

                st.markdown("---")
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
