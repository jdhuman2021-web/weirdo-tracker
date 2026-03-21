@echo off
echo ========================================
echo GMGN WebSocket Agent
echo ========================================
echo.
echo Starting real-time token data stream...
echo.
echo Tracking: All active tokens
echo Update interval: 30 seconds
echo Auto-discover: Enabled
echo.
echo Press Ctrl+C to stop
echo ========================================
echo.

REM Activate virtual environment if exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Run the WebSocket client
python agents\gmgn_websocket.py

pause