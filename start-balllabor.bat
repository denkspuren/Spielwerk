@echo off
cd /d "%~dp0"
java server-java/ArcadeServer.java games/balllabor/Balllabor.java %*
pause
