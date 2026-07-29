#!/bin/bash
cd /home/ubuntu/streamlitapp
source venv/bin/activate
nohup streamlit run _subprocess_test_app.py --server.port 8597 --server.headless true > /tmp/subtest.log 2>&1 < /dev/null &
disown
sleep 3
ss -tlnp | grep 8597
