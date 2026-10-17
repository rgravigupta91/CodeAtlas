@echo off
cd /d C:\Projects\CodeAtlas
venv\Scripts\python.exe -m uvicorn Chatbot_server:app --reload --port 8000
pause
