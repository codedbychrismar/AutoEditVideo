@echo off
title AutoEdit Long Form for CapCut
cd /d "%~dp0"
echo.
echo  AutoEdit Long Form - builds your CapCut timeline + YOUTUBE UPLOAD.txt from a content folder.
echo  Make sure CapCut is CLOSED before continuing.
echo.
if "%~1"=="" (
  python autoedit.py
) else (
  python autoedit.py "%~1"
)
echo.
pause
