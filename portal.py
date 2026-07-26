"""
앱 허브 - 내 정보 대시보드
모든 앱을 소개하고 바로가기를 제공합니다.
실행: streamlit run portal.py --server.port 8500
"""

import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common.config import build_url

st.set_page_config(
    page_title="내 정보 대시보드",
    page_icon="🏠",
    layout="wide",
)

st.title("🏠 내 정보 대시보드")
st.markdown("개인용 정보 수집 & 유틸리티 서비스를 모아둔 허브입니다.")
st.markdown("각 앱은 독립적으로 실행되며, 아래에서 바로 이동할 수 있습니다.")
st.markdown("---")

# 앱 정보 정의
apps = [
    {
        "name": "🏕️ 캠핑장 빈자리 찾기",
        "port": 8502,
        "description": "관심 캠핑장의 예약 가능 현황을 날짜별로 조회합니다.",
        "features": [
            "날짜 범위 선택하여 조회",
            "다중 캠핑장 동시 조회",
            "예약 가능 객실 하이라이트 표시",
            "예약 사이트 바로가기 링크",
        ],
        "tech": "xticket API 연동",
        "status": "🟢 운영중",
    },
    {
        "name": "🎵 유튜브 음악 다운로드",
        "port": 8503,
        "description": "유튜브 URL을 입력하면 MP3로 변환하여 서버에 저장합니다.",
        "features": [
            "여러 URL 동시 입력 가능",
            "다운로드 진행률 프로그레스 바",
            "다운로드 이력 및 파일 관리",
            "3일 경과 파일 자동 삭제",
        ],
        "tech": "yt-dlp / FFmpeg",
        "status": "🟢 운영중",
    },
    {
        "name": "📚 도서관 책 찾기",
        "port": 8501,
        "description": "관심 도서의 대여 가능 여부를 확인합니다.",
        "features": [
            "도서관별 대여 상태 조회",
            "관심 도서 목록 관리",
        ],
        "tech": "크롤링 / 공공도서관 API",
        "status": "🟡 준비중",
    },
]

# 앱 카드 표시
for app in apps:
    with st.container():
        col_info, col_action = st.columns([4, 1])

        with col_info:
            st.subheader(app["name"])
            st.write(app["description"])

            with st.expander("주요 기능"):
                for feature in app["features"]:
                    st.markdown(f"- {feature}")
                st.markdown(f"**기술 스택:** {app['tech']}")

        with col_action:
            st.markdown(f"**{app['status']}**")
            st.markdown(f"포트: `{app['port']}`")
            if "운영중" in app["status"]:
                # common/config.py의 SERVER_HOST를 기준으로 절대 URL을 생성합니다.
                # 서버를 옮기거나 도메인을 붙이면 common/config.py의 SERVER_HOST만 수정하면 됩니다.
                st.markdown(
                    f'<a href="{build_url(app["port"])}" target="_blank">'
                    f'<button style="background-color:#FF4B4B;color:white;border:none;'
                    f'padding:10px 20px;border-radius:4px;cursor:pointer;width:100%;">'
                    f'바로가기 →</button></a>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    '<button style="background-color:#ccc;color:white;border:none;'
                    'padding:10px 20px;border-radius:4px;width:100%;" disabled>'
                    '준비중</button>',
                    unsafe_allow_html=True,
                )

    st.markdown("---")

# 전체 요약
st.subheader("📊 서비스 현황")
col1, col2, col3 = st.columns(3)
col1.metric("전체 앱", f"{len(apps)}개")
col2.metric("운영중", f"{sum(1 for a in apps if '운영중' in a['status'])}개")
col3.metric("준비중", f"{sum(1 for a in apps if '준비중' in a['status'])}개")

st.markdown("---")

# 관리 안내
st.subheader("🛠️ 관리 안내")
st.code("""
# 전체 서비스 시작
./start_all.sh

# 전체 서비스 종료
./stop_all.sh

# 로그 확인
tail -f logs/*.log

# 유튜브 다운로드 파일 수동 정리
python -m apps.youtube_music.cleanup
""", language="bash")

st.caption("각 앱은 독립 프로세스로 실행됩니다. 하나가 멈춰도 나머지에 영향을 주지 않습니다.")
