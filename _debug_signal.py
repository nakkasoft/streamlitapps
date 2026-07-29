"""
Streamlit 실행 파일(streamlit.web.cli)을 신호 핸들러로 감싸서 실행하는
디버깅용 진입점. 프로세스가 어떤 신호로 종료되는지 기록한다.
"""
import signal
import sys
import faulthandler

faulthandler.enable()

def log_signal(signum, frame):
    with open("/tmp/signal_debug.log", "a") as f:
        f.write(f"Received signal: {signum} ({signal.Signals(signum).name})\n")
    sys.exit(1)

for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP, signal.SIGQUIT):
    signal.signal(sig, log_signal)

with open("/tmp/signal_debug.log", "a") as f:
    f.write("=== starting streamlit via debug wrapper ===\n")

sys.argv = ["streamlit", "run", "apps/camping/app.py", "--server.port", "8502", "--server.headless", "true"]

from streamlit.web.cli import main

if __name__ == "__main__":
    main()
