#!/bin/bash
# 백그라운드로 프로세스 트리를 계속 기록
(
  for i in $(seq 1 15); do
    echo "=== $i ($(date +%H:%M:%S.%N)) ==="
    ps --ppid 56799 -o pid,ppid,stat,cmd 2>/dev/null
    ps -ef | grep -E "camping|crawler_worker|chromium|headless_shell" | grep -v grep
    sleep 1
  done
) > /tmp/tree_watch.log 2>&1 &
WATCHPID=$!

cd /home/ubuntu/streamlitapp
source venv/bin/activate
python3 _final_click_test.py

sleep 3
kill $WATCHPID 2>/dev/null
echo "=== TREE LOG ==="
cat /tmp/tree_watch.log
