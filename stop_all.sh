#!/bin/bash
echo "========================================"
echo "  내 정보 대시보드 - 전체 서비스 종료"
echo "========================================"
echo ""

cd "$(dirname "$0")"

for pidfile in pids/*.pid; do
    if [ -f "$pidfile" ]; then
        pid=$(cat "$pidfile")
        name=$(basename "$pidfile" .pid)
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid"
            echo "  [종료] $name (PID: $pid)"
        else
            echo "  [이미 종료됨] $name"
        fi
        rm -f "$pidfile"
    fi
done

echo ""
echo "  모든 서비스가 종료되었습니다."
echo "========================================"
