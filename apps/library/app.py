"""
도서관 책 찾기 (서울시립도서관 무인예약 확인)

원본: D:\\workspace\\sblib-search (library-reservation-checker / -web)
서울시립도서관 통합검색에서 관심 도서 목록의 무인예약 가능 도서관을 확인합니다.

원본 프로젝트는 CLI + FastAPI 웹 UI(바닐라 JS)로 구성되어 있었지만, 이 앱은
Streamlit 하나로 도서 목록 관리(CRUD)와 확인 작업 실행, 결과 표시를 모두
처리합니다. 핵심 검색/파싱/재시도/속도제한 로직(apps/library/lib/)은 원본과
동일합니다.

실행: streamlit run apps/library/app.py --server.port 8501
"""

import streamlit as st
import pandas as pd
import sys
import os

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from common.config import HUB_URL
from apps.library.config import (
    BOOK_LIST_PATH,
    MAX_BOOK_COUNT,
    MAX_RETRIES,
    MIN_INTERVAL_SECONDS,
)
from apps.library.lib.check_runner import (
    CheckRunner,
    build_default_parser,
    build_default_searcher,
)
from apps.library.lib.errors import CountOutOfRangeError, InvalidEntryError
from apps.library.lib.list_loader import ListLoader
from apps.library.lib.models import BookStatus
from apps.library.lib.repository import BookNotFoundError, BookRepository

st.set_page_config(
    page_title="도서관 책 찾기",
    page_icon="📚",
    layout="wide",
)

st.title("📚 도서관 책 찾기")
st.caption("서울시립도서관 통합검색에서 관심 도서의 무인예약 가능 여부를 확인합니다.")
st.markdown("---")


# ---------------------------------------------------------------------------
# 저장소 (앱 프로세스 전체에서 공유되는 단일 인스턴스, books.txt와 동기화)
# ---------------------------------------------------------------------------
@st.cache_resource
def get_repository() -> BookRepository:
    return BookRepository(loader=ListLoader(), file_path=BOOK_LIST_PATH)


repository = get_repository()

if "library_edit_id" not in st.session_state:
    st.session_state.library_edit_id = None  # None이면 추가 모드
if "library_check_results" not in st.session_state:
    st.session_state.library_check_results = None  # list[BookResult] | None


# ---------------------------------------------------------------------------
# 도서 목록
# ---------------------------------------------------------------------------
st.subheader("📖 관심 도서 목록")

items = repository.list_all()

if not items:
    st.info("등록된 도서가 없습니다. 아래에서 도서를 추가해 주세요.")
else:
    header = st.columns([4, 3, 1, 1])
    header[0].markdown("**제목**")
    header[1].markdown("**저자**")
    header[2].markdown("**수정**")
    header[3].markdown("**삭제**")

    for item in items:
        cols = st.columns([4, 3, 1, 1])
        cols[0].write(item.entry.title)
        cols[1].write(item.entry.author or "-")

        if cols[2].button("✏️", key=f"edit_{item.id}"):
            st.session_state.library_edit_id = item.id
            st.rerun()

        if cols[3].button("🗑️", key=f"delete_{item.id}"):
            try:
                repository.delete(item.id)
                if st.session_state.library_edit_id == item.id:
                    st.session_state.library_edit_id = None
                st.rerun()
            except (BookNotFoundError, CountOutOfRangeError) as exc:
                st.error(str(exc))

st.caption(f"총 {len(items)}권 (최대 {MAX_BOOK_COUNT}권)")
st.markdown("---")

# ---------------------------------------------------------------------------
# 도서 추가 / 수정 폼
# ---------------------------------------------------------------------------
editing_item = None
if st.session_state.library_edit_id is not None:
    editing_item = next(
        (i for i in items if i.id == st.session_state.library_edit_id), None
    )

form_title = "✏️ 도서 수정" if editing_item is not None else "➕ 도서 추가"
st.subheader(form_title)

with st.form("library_book_form", clear_on_submit=(editing_item is None)):
    default_title = editing_item.entry.title if editing_item else ""
    default_author = (editing_item.entry.author or "") if editing_item else ""

    title_input = st.text_input("제목 *", value=default_title)
    author_input = st.text_input("저자 (선택)", value=default_author)

    col_submit, col_cancel = st.columns([1, 1])
    submitted = col_submit.form_submit_button(
        "수정 완료" if editing_item is not None else "추가", type="primary"
    )
    cancelled = False
    if editing_item is not None:
        cancelled = col_cancel.form_submit_button("취소")

    if submitted:
        author_value = author_input.strip() or None
        try:
            if editing_item is not None:
                repository.update(editing_item.id, title=title_input, author=author_value)
                st.session_state.library_edit_id = None
            else:
                repository.add(title=title_input, author=author_value)
            st.rerun()
        except InvalidEntryError:
            st.error("제목은 필수입니다.")
        except CountOutOfRangeError as exc:
            st.error(str(exc))
        except BookNotFoundError as exc:
            st.error(str(exc))

    if cancelled:
        st.session_state.library_edit_id = None
        st.rerun()

st.markdown("---")

# ---------------------------------------------------------------------------
# 확인 작업 실행
# ---------------------------------------------------------------------------
st.subheader("🔍 무인예약 확인 작업")
st.caption(
    f"도서 1권당 최소 {MIN_INTERVAL_SECONDS:.0f}초 간격으로 순차 조회합니다. "
    f"도서 수가 많으면 시간이 걸릴 수 있습니다 (최대 재시도 {MAX_RETRIES}회)."
)

run_disabled = len(items) == 0
run_btn = st.button("🚀 확인 작업 시작", type="primary", disabled=run_disabled)

if run_disabled:
    st.warning("확인 작업을 시작하려면 도서 항목을 먼저 추가해야 합니다.")

if run_btn:
    entries = repository.to_entries()

    searcher = build_default_searcher(
        min_interval_seconds=MIN_INTERVAL_SECONDS, max_retries=MAX_RETRIES
    )
    parser = build_default_parser()
    runner = CheckRunner(searcher=searcher, parser=parser)

    progress_bar = st.progress(0)
    status_text = st.empty()

    def on_progress(done, total, result):
        status_text.text(f"조회 중... {result.entry.title} ({done}/{total})")
        progress_bar.progress(done / total)

    results = runner.run(entries, on_progress=on_progress)

    progress_bar.empty()
    status_text.empty()

    st.session_state.library_check_results = results
    st.rerun()

st.markdown("---")

# ---------------------------------------------------------------------------
# 결과 표시
# ---------------------------------------------------------------------------
results = st.session_state.library_check_results

if results:
    st.subheader("📊 확인 결과")

    status_counts = {status: 0 for status in BookStatus}
    for r in results:
        status_counts[r.status] += 1

    cols = st.columns(len(BookStatus))
    for col, status in zip(cols, BookStatus):
        col.metric(status.value, f"{status_counts[status]}권")

    st.markdown("---")

    rows = []
    for r in results:
        library_names = (
            ", ".join(lib.name for lib in r.unmanned_libraries)
            if r.status == BookStatus.UNMANNED_AVAILABLE
            else ""
        )
        rows.append(
            {
                "제목": r.entry.title,
                "저자": r.entry.author or "-",
                "상태": r.status.value,
                "무인예약 가능 도서관": library_names or "-",
            }
        )

    result_df = pd.DataFrame(rows)

    # 참고: pandas Styler(.style.apply)를 st.dataframe에 넘기면 일부 서버 환경
    # (pyarrow 25.0.0 조합)에서 세그폴트가 발생하는 것이 확인되어, 색상 강조
    # 대신 상태를 이모지로 표시하는 방식으로 대체했습니다.
    status_emoji = {
        BookStatus.UNMANNED_AVAILABLE.value: "🟢",
        BookStatus.UNMANNED_UNAVAILABLE.value: "🟡",
        BookStatus.NO_RESULTS.value: "⚪",
        BookStatus.REQUEST_ERROR.value: "🔴",
        BookStatus.PARSE_ERROR.value: "🔴",
    }
    result_df["상태"] = result_df["상태"].apply(
        lambda s: f"{status_emoji.get(s, '⚪')} {s}"
    )

    st.dataframe(
        result_df,
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("아직 확인 작업을 실행하지 않았습니다.")

st.markdown("---")
st.markdown(f"[← 허브로 돌아가기]({HUB_URL})")
