#!/bin/bash
pkill -f "apps/camping/app.py" 2>/dev/null
pkill -f "_minimal_test_app" 2>/dev/null
rm -rf /home/ubuntu/streamlitapp/apps/camping/__pycache__
sleep 1

cd /home/ubuntu/streamlitapp
source venv/bin/activate
setsid nohup streamlit run apps/camping/app.py --server.port 8502 --server.headless true > logs/camping.log 2>&1 < /dev/null &
sleep 3
pid=$(pgrep -f "apps/camping/app.py")
echo "pid: $pid"
echo "$pid" > pids/camping.pid
ss -tlnp | grep 8502
