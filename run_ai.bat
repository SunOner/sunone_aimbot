@echo off
setlocal
cd /d "%~dp0"

set "VENV_DIR=.venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
set "VENV_ACTIVATE=%VENV_DIR%\Scripts\activate.bat"
set "PY_DEPS_STAMP=%VENV_DIR%\.ai_python_deps.stamp"

if not exist "%VENV_PYTHON%" (
    echo [INFO] Creating virtual environment...
    py -3 -m venv "%VENV_DIR%" 2>nul
    if errorlevel 1 (
        python -m venv "%VENV_DIR%"
    )
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

call "%VENV_ACTIVATE%"
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment.
    pause
    exit /b 1
)

call :check_python_deps
if errorlevel 1 goto install_python_deps
echo [INFO] Python dependencies are up to date.
goto python_deps_ready

:install_python_deps
echo [INFO] Installing dependencies...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo [ERROR] Failed to upgrade pip.
    pause
    exit /b 1
)

python -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

call :touch_python_deps_stamp
if errorlevel 1 (
    echo [ERROR] Failed to update Python dependency stamp.
    pause
    exit /b 1
)

:python_deps_ready
call :ensure_torch_cuda
if errorlevel 1 (
    pause
    exit /b 1
)

python run.py
set "AI_EXIT_CODE=%errorlevel%"

endlocal & exit /b %AI_EXIT_CODE%

:check_python_deps
if not exist "%PY_DEPS_STAMP%" exit /b 1
powershell -NoProfile -ExecutionPolicy Bypass -Command "$stampPath = '%PY_DEPS_STAMP%'; if (!(Test-Path -LiteralPath $stampPath)) { exit 1 }; $expected = (Get-Content -LiteralPath $stampPath -Raw).Trim(); $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath 'requirements.txt').Hash; if ($expected -ne $actual) { exit 1 }; exit 0"
exit /b %errorlevel%

:touch_python_deps_stamp
powershell -NoProfile -ExecutionPolicy Bypass -Command "$hash = (Get-FileHash -Algorithm SHA256 -LiteralPath 'requirements.txt').Hash; Set-Content -LiteralPath '%PY_DEPS_STAMP%' -Value $hash -NoNewline -Encoding ascii -Force"
exit /b %errorlevel%

:ensure_torch_cuda
call :check_torch_cuda
if not errorlevel 1 (
    echo [INFO] PyTorch CUDA support is available.
    exit /b 0
)

echo [INFO] PyTorch CUDA support is not available. Installing PyTorch for CUDA 12.8...
python -m pip uninstall torch torchvision torchaudio -y
if errorlevel 1 (
    echo [ERROR] Failed to uninstall existing PyTorch packages.
    exit /b 1
)

python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
if errorlevel 1 (
    echo [ERROR] Failed to install PyTorch with CUDA 12.8 support.
    exit /b 1
)

call :check_torch_cuda
if errorlevel 1 (
    echo [ERROR] PyTorch is installed, but CUDA is still not available in this environment.
    python -c "import sys; print('Python executable:', sys.executable); import torch; print('Torch version:', torch.__version__); print('Torch CUDA build:', getattr(torch.version, 'cuda', None)); print('Torch file:', getattr(torch, '__file__', 'unknown')); print('CUDA available:', torch.cuda.is_available()); print('CUDA device count:', torch.cuda.device_count())"
    exit /b 1
)

echo [INFO] PyTorch CUDA support is available.
exit /b 0

:check_torch_cuda
python -c "import sys, torch; sys.exit(0 if torch.cuda.is_available() else 1)" >nul 2>&1
exit /b %errorlevel%
