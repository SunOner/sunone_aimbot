@echo off

python -m pip --version 2>nul
if %errorlevel% neq 0 (
    echo pip is not installed. Installing...
    python -m ensurepip --default-pip
    if %errorlevel% neq 0 (
        echo Failed to install pip automatically. Please install pip manually.
        exit /b 1
    )
)

python -c "import streamlit" 2>nul
if %errorlevel% neq 0 (
    echo Streamlit is not installed. Installing...
    pip install streamlit
    if %errorlevel% neq 0 (
        echo Failed to install streamlit. Please check your internet connection and try again.
        exit /b 1
    )
)

streamlit run helper.py --server.fileWatcherType none