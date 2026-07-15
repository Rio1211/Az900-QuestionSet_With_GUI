@echo off
cd /d "%~dp0"
python az900_quiz_app.py
if errorlevel 1 pause
