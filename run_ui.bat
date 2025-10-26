@echo off
cd /d "%~dp0"
set PYTHONPATH=%cd%
python run_fixed.py
pause
