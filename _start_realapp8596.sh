#!/bin/bash
pkill -f "_debug_scraper_wrap" 2>/dev/null
pkill -f "port 8596" 2>/dev/null
sleep 1
cd /home/ubuntu/streamlitapp
source venv/bin/activate
nohup streamlit run apps/camping/app.py --server.port 8596 --server.headless true > /tmp/realapp8596.log 2>&1 < /dev/null &
disown
sleep 3
ss -tlnp | grep 8596
cat /tmp/realapp8596.log
