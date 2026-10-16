@echo off
for /f "tokens=5" %%p in ('netstat -ano ^| findstr /r /c:":8765 .*LISTENING"') do taskkill /PID %%p /F >nul 2>nul
 echo PES 6 local server stopped.
