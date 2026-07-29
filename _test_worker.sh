#!/bin/bash
cd /home/ubuntu/streamlitapp
source venv/bin/activate
CAMPSITES='[{"name": "test", "shop_encode": "5f9422e223671b122a7f2c94f4e15c6f71cd1a49141314cf19adccb98162b5b0"}]'
DATES='["20260801"]'
python3 apps/camping/crawler_worker.py "$CAMPSITES" "$DATES"
echo "EXIT: $?"
