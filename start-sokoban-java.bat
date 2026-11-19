@echo off
cd /d "%~dp0"
java server-java/ArcadeServer.java games/sokoban/Sokoban.java %*
pause
