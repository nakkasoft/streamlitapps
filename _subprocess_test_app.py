import streamlit as st
import subprocess

st.title("Subprocess Test")

if st.button("서브프로세스 실행"):
    with st.spinner("실행 중..."):
        result = subprocess.run(["echo", "hello from subprocess"], capture_output=True, text=True, timeout=30)
    st.success(f"결과: {result.stdout}")
