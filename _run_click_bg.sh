#!/bin/bash
cd /home/ubuntu/streamlitapp
source venv/bin/activate
nohup python3 _final_click_test.py > /tmp/finaltest.log 2>&1 < /dev/null &
disown
echo "test started, will check in 40s"
