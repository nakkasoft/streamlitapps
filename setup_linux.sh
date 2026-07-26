#!/bin/bash
echo "========================================"
echo "  내 정보 대시보드 - 리눅스 환경설정"
echo "========================================"
echo ""

cd "$(dirname "$0")"

# 1. Python 가상환경 생성
echo "[1/4] Python 가상환경 생성..."
python3 -m venv venv
source venv/bin/activate

# 2. 패키지 설치
echo "[2/4] 패키지 설치..."
pip install --upgrade pip
pip install -r requirements.txt

# 3. 디렉토리 생성
echo "[3/4] 필요 디렉토리 생성..."
mkdir -p logs
mkdir -p pids

# 4. 실행 권한 부여
echo "[4/4] 스크립트 실행 권한 설정..."
chmod +x start_all.sh
chmod +x stop_all.sh

echo ""
echo "========================================"
echo "  설정 완료!"
echo "========================================"
echo ""
echo "  시작: ./start_all.sh"
echo "  종료: ./stop_all.sh"
echo "========================================"
