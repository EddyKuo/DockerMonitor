@echo off
REM DockerMonitor - Quick start script for Windows

echo DockerMonitor - Docker Container Monitoring
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv\" (
    echo Virtual environment not found. Creating...
    python -m venv venv
    if errorlevel 1 (
        echo Error: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully.
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if dependencies are installed
python -c "import textual" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Error: Failed to install dependencies
        pause
        exit /b 1
    )
    echo Dependencies installed successfully.
)

REM Check if configuration exists
if not exist "config\hosts.yaml" (
    echo.
    echo Warning: config\hosts.yaml not found!
    echo Please copy config\hosts.yaml.example to config\hosts.yaml
    echo and configure your jump host and target servers.
    echo.
    pause
    exit /b 1
)

REM Run the application
echo.
echo Starting DockerMonitor TUI...
echo.
python -m src.main tui

deactivate
