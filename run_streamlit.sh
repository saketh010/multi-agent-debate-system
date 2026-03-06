#!/bin/bash
# Convenience script to run Streamlit web interface

echo "======================================"
echo "Multi-Agent Debate System - Web UI"
echo "======================================"
echo ""

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating virtual environment..."
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    else
        echo "Warning: Virtual environment not found at venv/"
        echo "Please create one with: python -m venv venv"
        echo ""
    fi
fi

# Check if Okta authentication is needed
echo "Checking AWS credentials..."
if [ -z "$AWS_SESSION_TOKEN" ] && [ -z "$AWS_ACCESS_KEY_ID" ]; then
    echo ""
    echo "WARNING: No AWS credentials detected!"
    echo "If using Okta, run: okta-aws-cli -p sandbox"
    echo ""
    read -p "Press Enter to continue..."
fi

echo ""
echo "Starting Streamlit web interface..."
echo ""
echo "The app will open in your browser at http://localhost:8501"
echo "Press Ctrl+C to stop the server"
echo ""

streamlit run streamlit_app.py
