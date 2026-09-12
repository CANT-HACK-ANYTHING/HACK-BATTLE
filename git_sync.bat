@echo off
title AegisOS :: GitHub Sync
cls
powershell -ExecutionPolicy Bypass -File "%~dp0git_sync.ps1" %*
pause
