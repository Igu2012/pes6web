@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 assemble_pak.py
  if errorlevel 1 (pause & exit /b 1)
  start "PES 6 Local Server" /min cmd /c "py -3 serve.py"
  goto open_game
)
where python >nul 2>nul
if %errorlevel%==0 (
  python assemble_pak.py
  if errorlevel 1 (pause & exit /b 1)
  start "PES 6 Local Server" /min cmd /c "python serve.py"
  goto open_game
)
echo Python 3 was not found. Install Python 3, then run this file again.
pause
exit /b 1
:open_game
for /l %%i in (1,1,20) do (
  powershell -NoProfile -Command "try { $r=Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8765/ -TimeoutSec 1; exit 0 } catch { exit 1 }" >nul 2>nul
  if not errorlevel 1 goto ready
  timeout /t 1 /nobreak >nul
)
echo The local server did not start. Check that port 8765 is free and Python 3 is installed.
pause
exit /b 1
:ready
start "" "http://127.0.0.1:8765/"
echo Game opened. Close the minimized server window when you finish playing.
