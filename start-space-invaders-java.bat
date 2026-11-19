@echo off
cd /d "%~dp0"
java server-java/ArcadeServer.java games/space_invaders/SpaceInvaders.java %*
pause
