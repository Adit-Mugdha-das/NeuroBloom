@echo off
REM Quick Test Data Generator - Windows Batch Script

echo ================================
echo   NeuroBloom Dev Tools
echo ================================
echo.

if "%1"=="" (
    echo Usage:
    echo   test.bat generate [num]   - Generate test sessions
    echo   test.bat complete          - Complete current session
    echo   test.bat streak [days]     - Set streak
    echo   test.bat clear             - Clear all data
    echo.
    echo Examples:
    echo   test.bat generate 3        - Generate 3 sessions
    echo   test.bat complete          - Finish current session
    echo   test.bat streak 7          - Set 7-day streak
    echo.
    exit /b
)

D:\NeuroBloom\backend\venv\Scripts\python.exe D:\NeuroBloom\backend\dev_tools.py %*
