@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" "recolor_gui.py"
) else (
    python "recolor_gui.py"
)

if errorlevel 1 (
    echo.
    echo O Chromatic foi encerrado com erro.
    pause
)
endlocal

