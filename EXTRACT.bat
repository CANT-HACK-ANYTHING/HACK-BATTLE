@echo off
set DEST=C:\HACK BATTLE
if not exist "%~dp0aegis-os-hackbattle.zip" (
  echo Put this EXTRACT.bat in the SAME folder as aegis-os-hackbattle.zip
  pause
  exit /b 1
)
mkdir "%DEST%" 2>nul
tar -xf "%~dp0aegis-os-hackbattle.zip" -C "%DEST%"
if not exist "%DEST%\main.py" (
  echo Extract failed. Install Python later. The zip must sit next to this bat.
  pause
  exit /b 1
)
echo OK. Files are in %DEST%
echo Next: open that folder in Antigravity.
explorer "%DEST%"
pause
