#!/bin/bash
echo "========================================"
echo "  내 정보 대시보드 - 전체 서비스 시작"
echo "========================================"
echo ""

# 프로젝트 디렉토리로 이동
cd "$(dirname "$0")"

# 가상환경 활성화
source venv/bin/activate

# 디렉토리 확인
mkdir -p logs pids downloads/music

echo "[1/4] 허브 시작 (port 8500)..."
nohup streamlit run portal.py --server.port 8500 --server.headless true > logs/portal.log 2>&1 &
echo $! > pids/portal.pid

echo "[2/4] 도서관 책 찾기 시작 (port 8501)..."
nohup streamlit run apps/library/app.py --server.port 8501 --server.headless true > logs/library.log 2>&1 &
echo $! > pids/library.pid

echo "[3/4] 캠핑장 시작 (port 8502)..."
nohup streamlit run apps/camping/app.py --server.port 8502 --server.headless true > logs/camping.log 2>&1 &
echo $! > pids/camping.pid

echo "[4/4] 유튜브 음악 시작 (port 8503)..."
nohup streamlit run apps/youtube_music/app.py --server.port 8503 --server.headless true > logs/youtube_music.log 2>&1 &
echo $! > pids/youtube_music.pid

echo ""
echo "========================================"
echo "  모든 서비스가 시작되었습니다!"
echo "========================================"
echo ""
echo "  허브:         http://서버IP:8500"
echo "  도서관:       http://서버IP:8501"
echo "  캠핑장:       http://서버IP:8502"
echo "  유튜브 음악:  http://서버IP:8503"
echo ""
echo "  로그 확인: tail -f logs/*.log"
echo "  전체 종료: ./stop_all.sh"
echo "========================================"
