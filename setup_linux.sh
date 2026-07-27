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
echo "[2/5] 패키지 설치..."
pip install --upgrade pip
pip install -r requirements.txt

# 3. Playwright 브라우저(Chromium) 및 시스템 의존성 설치
#    캠핑장 앱(apps/camping)이 camp.xticket.kr 예약 세션을 만들기 위해
#    headless Chromium을 사용합니다. 화면(GUI)은 뜨지 않지만 Chromium
#    바이너리(약 150~300MB)와 여러 시스템 라이브러리가 추가로 필요합니다.
#    서버 사양이 낮다면(RAM 1GB대) 이 단계가 오래 걸리거나 메모리 부족으로
#    실패할 수 있습니다. 실패 시 스왑 메모리를 늘리거나, 캠핑장 앱만 별도로
#    가벼운 서버에서 운영하는 것을 고려하세요.
echo "[3/5] Playwright 브라우저(Chromium) 설치..."
playwright install --with-deps chromium

# 4. 디렉토리 생성
echo "[4/5] 필요 디렉토리 생성..."
mkdir -p logs
mkdir -p pids

# 5. 실행 권한 부여
echo "[5/5] 스크립트 실행 권한 설정..."
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
