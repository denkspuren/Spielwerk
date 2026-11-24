@echo off
cd /d "%~dp0"
py -3 server.py games/space_invaders/SpaceInvaders.java %*
pause
