"""
도서관 책 찾기
관심 도서의 대여 가능 여부를 확인합니다.
실행: streamlit run apps/library/app.py --server.port 8501
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from common.config import HUB_URL

st.set_page_config(
    page_title="도서관 책 찾기",
    page_icon="📚",
    layout="wide",
)

st.title("📚 도서관 책 찾기")
st.caption(f"마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.markdown("---")


# 샘플 데이터 (실제로는 도서관 API 또는 크롤링으로 대체)
@st.cache_data(ttl=300)  # 5분 캐시
def fetch_library_data():
    """도서관 데이터를 가져옵니다. 실제 구현 시 크롤링/API 호출로 대체하세요."""
    data = [
        {"도서명": "클린 코드", "저자": "로버트 마틴", "도서관": "시립도서관", "상태": "대여가능", "반납예정일": "-"},
        {"도서명": "리팩터링", "저자": "마틴 파울러", "도서관": "시립도서관", "상태": "대여중", "반납예정일": "2026-08-01"},
        {"도서명": "디자인 패턴", "저자": "GoF", "도서관": "구립도서관", "상태": "대여가능", "반납예정일": "-"},
        {"도서명": "파이썬 코딩의 기술", "저자": "브렛 슬라킨", "도서관": "구립도서관", "상태": "대여중", "반납예정일": "2026-07-30"},
        {"도서명": "데이터 중심 애플리케이션 설계", "저자": "마틴 클레프만", "도서관": "시립도서관", "상태": "대여가능", "반납예정일": "-"},
    ]
    return pd.DataFrame(data)


df = fetch_library_data()

# 필터
col1, col2 = st.columns(2)
with col1:
    library_filter = st.selectbox("도서관 선택", ["전체"] + df["도서관"].unique().tolist())
with col2:
    status_filter = st.selectbox("상태 필터", ["전체", "대여가능", "대여중"])

# 필터 적용
filtered = df.copy()
if library_filter != "전체":
    filtered = filtered[filtered["도서관"] == library_filter]
if status_filter != "전체":
    filtered = filtered[filtered["상태"] == status_filter]

# 요약 표시
col1, col2, col3 = st.columns(3)
col1.metric("전체 관심도서", f"{len(df)}권")
col2.metric("대여 가능", f"{len(df[df['상태'] == '대여가능'])}권")
col3.metric("대여 중", f"{len(df[df['상태'] == '대여중'])}권")

st.markdown("---")


# 데이터 표시 (상태에 따라 색상 구분)
def highlight_status(row):
    if row["상태"] == "대여가능":
        return ["background-color: #d4edda"] * len(row)
    elif row["상태"] == "대여중":
        return ["background-color: #f8d7da"] * len(row)
    return [""] * len(row)


st.dataframe(
    filtered.style.apply(highlight_status, axis=1),
    use_container_width=True,
    hide_index=True,
)

# 새로고침 버튼
if st.button("🔄 새로고침"):
    st.cache_data.clear()
    st.rerun()

st.markdown("---")
st.markdown(f"[← 포털로 돌아가기]({HUB_URL})")
