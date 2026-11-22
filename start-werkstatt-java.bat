@echo off
cd /d "%~dp0"
java server-java/ArcadeServer.java games/werkstatt_demo/SpielwerkDemo.java %*
