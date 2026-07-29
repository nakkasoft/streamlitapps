#!/bin/bash
pkill -f "8502" 2>/dev/null
pkill -f "apps/camping/app.py" 2>/dev/null
sleep 2
cd /home/ubuntu/streamlitapp
source venv/bin/activate
rm -f /tmp/debug_scraper.log
nohup streamlit run apps/camping/app.py --server.port 8502 --server.headless true > logs/camping.log 2>&1 < /dev/null &
disown
sleep 3
ss -tlnp | grep 8502
cat logs/camping.log
