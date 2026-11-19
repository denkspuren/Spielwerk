@echo off
cd /d "%~dp0"
py -3 server.py games/balllabor/Balllabor.java %*
pause
