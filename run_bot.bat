@echo off
chcp 65001 > nul
set PYTHONIOENCODING=utf-8
title Trading Bot Auto Runner

cd /d C:\Users\ljeno\trading-bot

call venv\Scripts\activate

echo ===============================
echo Trading Bot Started %date% %time%
echo ===============================

python -u runner.py >> logs.txt 2>&1

echo ===============================
echo Bot Stopped %date% %time%
echo ===============================

pause