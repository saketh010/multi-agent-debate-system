@echo off
REM Convenience script to run Streamlit web interface

echo ======================================
echo Multi-Agent Debate System - Web UI
echo ======================================
echo.

REM Check if virtual environment is activated
if not defined VIRTUAL_ENV (
    echo Activating virtual environment...
    if exist venv\Scripts\activate.bat (
        call venv\Scripts\activate.bat
    ) else (
        echo Warning: Virtual environment not found at venv\
        echo Please create one with: python -m venv venv
        echo.
    )
)

REM Check if Okta authentication is needed
echo Checking AWS credentials...
if not defined AWS_SESSION_TOKEN (
    if not defined AWS_ACCESS_KEY_ID (
        echo.
        echo WARNING: No AWS credentials detected!
        echo If using Okta, run: okta-aws-cli -p sandbox
        echo.
        pause
    )
)

echo.
echo Starting Streamlit web interface...
echo.
echo The app will open in your browser at http://localhost:8501
echo Press Ctrl+C to stop the server
echo.

streamlit run streamlit_app.py

pause
