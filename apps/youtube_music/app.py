"""
유튜브 음악 다운로드
유튜브 URL을 여러 개 입력하면 MP3로 변환하여 다운로드합니다.
실행: streamlit run apps/youtube_music/app.py --server.port 8503
"""

import streamlit as st
import pandas as pd
import sys
import os

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from apps.youtube_music.downloader import download_single, get_video_info, list_downloaded_files
from apps.youtube_music.config import DOWNLOAD_DIR, FILE_RETENTION_DAYS
from common.config import HUB_URL

st.set_page_config(
    page_title="유튜브 음악 다운로드",
    page_icon="🎵",
    layout="wide",
)

st.title("🎵 유튜브 음악 다운로드")
st.markdown("유튜브 URL을 입력하면 MP3로 변환하여 서버에 저장합니다.")
st.markdown(f"다운로드된 파일은 **{FILE_RETENTION_DAYS}일** 후 자동 삭제됩니다.")
st.markdown("---")

# URL 입력 (여러 줄)
st.subheader("🔗 유튜브 URL 입력")
urls_text = st.text_area(
    "URL을 한 줄에 하나씩 입력하세요",
    height=150,
    placeholder="https://www.youtube.com/watch?v=...\nhttps://www.youtube.com/watch?v=...\nhttps://www.youtube.com/watch?v=...",
)

download_btn = st.button("🎵 다운로드 시작", type="primary")

st.markdown("---")

# 다운로드 처리
if download_btn and urls_text.strip():
    urls = [u.strip() for u in urls_text.strip().split("\n") if u.strip()]

    if not urls:
        st.warning("유효한 URL을 입력해주세요.")
    else:
        st.subheader(f"⏳ 다운로드 진행 ({len(urls)}개)")

        # 전체 프로그레스 바
        overall_progress = st.progress(0)
        overall_status = st.empty()

        # 개별 결과 표시 영역
        result_container = st.container()

        results = []
        for idx, url in enumerate(urls):
            overall_status.text(f"[{idx + 1}/{len(urls)}] 다운로드 중...")

            # 개별 프로그레스
            with result_container:
                item_status = st.empty()
                item_status.info(f"⏳ ({idx + 1}/{len(urls)}) 정보 확인 중: {url[:60]}...")

            # 영상 정보 가져오기
            info = get_video_info(url)
            title = info.get("title", url) if info else url

            if info and info.get("error"):
                with result_container:
                    item_status.error(f"❌ ({idx + 1}/{len(urls)}) 실패: {info['error']}")
                results.append({"URL": url, "제목": title, "결과": "실패", "사유": info.get("error", "")})
            else:
                with result_container:
                    item_status.info(f"⏳ ({idx + 1}/{len(urls)}) 다운로드 중: {title}")

                # 다운로드 실행
                result = download_single(url)

                if result["success"]:
                    with result_container:
                        item_status.success(f"✅ ({idx + 1}/{len(urls)}) 완료: {result['title']}")
                    results.append({"URL": url, "제목": result["title"], "결과": "성공", "사유": ""})
                else:
                    with result_container:
                        item_status.error(f"❌ ({idx + 1}/{len(urls)}) 실패: {result['error']}")
                    results.append({"URL": url, "제목": title, "결과": "실패", "사유": result["error"]})

            # 전체 프로그레스 업데이트
            overall_progress.progress((idx + 1) / len(urls))

        # 완료 요약
        overall_status.empty()
        overall_progress.empty()

        success_count = sum(1 for r in results if r["결과"] == "성공")
        fail_count = sum(1 for r in results if r["결과"] == "실패")

        st.markdown("---")
        st.subheader("📊 다운로드 결과")
        col1, col2, col3 = st.columns(3)
        col1.metric("전체", f"{len(results)}개")
        col2.metric("성공", f"{success_count}개")
        col3.metric("실패", f"{fail_count}개")

        if results:
            df = pd.DataFrame(results)
            st.dataframe(df, use_container_width=True, hide_index=True)

elif download_btn and not urls_text.strip():
    st.warning("URL을 입력해주세요.")

# 다운로드된 파일 목록
st.markdown("---")
st.subheader("📂 다운로드된 파일")
st.caption(f"저장 위치: `{DOWNLOAD_DIR}` | 보관 기간: {FILE_RETENTION_DAYS}일")

files = list_downloaded_files()
if files:
    header = st.columns([4, 1, 2, 1.5])
    header[0].markdown("**파일명**")
    header[1].markdown("**크기**")
    header[2].markdown("**다운로드일시**")
    header[3].markdown("**받기**")

    @st.cache_data(show_spinner=False)
    def _read_file_bytes(path: str, mtime: float) -> bytes:
        # mtime을 캐시 키에 포함시켜, 파일이 바뀌면(재다운로드 등) 캐시를 새로 읽습니다.
        with open(path, "rb") as fp:
            return fp.read()

    for f in files:
        cols = st.columns([4, 1, 2, 1.5])
        cols[0].write(f["파일명"])
        cols[1].write(f["크기"])
        cols[2].write(f["다운로드일시"])
        try:
            file_mtime = os.path.getmtime(f["경로"])
            file_bytes = _read_file_bytes(f["경로"], file_mtime)
            cols[3].download_button(
                "⬇️ 다운로드",
                data=file_bytes,
                file_name=f["파일명"],
                mime="audio/mpeg",
                key=f"dl_{f['파일명']}",
            )
        except OSError:
            cols[3].error("읽기 실패")
else:
    st.info("아직 다운로드된 파일이 없습니다.")

st.markdown("---")
st.markdown(f"[← 허브로 돌아가기]({HUB_URL})")
