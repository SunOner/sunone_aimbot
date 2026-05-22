@echo off
setlocal
cd /d "%~dp0"

set "VENV_DIR=.venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
set "VENV_ACTIVATE=%VENV_DIR%\Scripts\activate.bat"
set "PY_DEPS_STAMP=%VENV_DIR%\.helper_python_deps.stamp"
set "UI_DIR=helper_ui"
set "UI_NODE_MODULES=%UI_DIR%\node_modules"
set "UI_DEPS_STAMP=%UI_NODE_MODULES%\.helper_deps.stamp"
set "UI_DIST_INDEX=%UI_DIR%\dist\index.html"
set "UI_BUILD_STAMP=%UI_DIR%\dist\.build.stamp"
set "API_PORT=8501"

if not exist "%VENV_PYTHON%" (
    echo [INFO] Creating virtual environment...
    py -3 -m venv "%VENV_DIR%" 2>nul
    if errorlevel 1 (
        python -m venv "%VENV_DIR%"
    )
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        exit /b 1
    )
)

call "%VENV_ACTIVATE%"
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment.
    exit /b 1
)

call :check_python_deps
if errorlevel 1 goto install_python_deps
echo [INFO] Python dependencies are up to date.
goto python_deps_ready

:install_python_deps
echo [INFO] Installing Python dependencies...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo [ERROR] Failed to upgrade pip.
    exit /b 1
)

python -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install requirements from requirements.txt.
    exit /b 1
)

call :touch_python_deps_stamp
if errorlevel 1 (
    echo [ERROR] Failed to update Python dependency stamp.
    exit /b 1
)

:python_deps_ready
where npm >nul 2>&1
if errorlevel 1 (
    echo [ERROR] npm not found. Install Node.js LTS and run this file again.
    exit /b 1
)

call :check_frontend_deps
if errorlevel 1 goto install_frontend_deps
echo [INFO] Frontend dependencies are up to date.
goto frontend_deps_ready

:install_frontend_deps
echo [INFO] Installing frontend dependencies...
pushd "%UI_DIR%"
call npm install
if errorlevel 1 (
    popd
    echo [ERROR] Failed to install frontend dependencies.
    exit /b 1
)
popd

call :touch_frontend_deps_stamp
if errorlevel 1 (
    echo [ERROR] Failed to update frontend dependency stamp.
    exit /b 1
)

:frontend_deps_ready
call :check_ui_build
if errorlevel 1 goto build_ui
echo [INFO] React UI build is up to date.
goto ui_build_ready

:build_ui
echo [INFO] Building React UI...
pushd "%UI_DIR%"
call npm run build
if errorlevel 1 (
    popd
    echo [ERROR] Failed to build React UI.
    exit /b 1
)
popd

call :touch_ui_build_stamp
if errorlevel 1 (
    echo [ERROR] Failed to update React UI build stamp.
    exit /b 1
)

:ui_build_ready
echo [INFO] Starting helper API and UI on http://127.0.0.1:%API_PORT%
start "" powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 2; Start-Process 'http://127.0.0.1:%API_PORT%'"
python -m uvicorn helper_api:app --host 127.0.0.1 --port %API_PORT%
set "HELPER_EXIT_CODE=%errorlevel%"

endlocal & exit /b %HELPER_EXIT_CODE%

:check_python_deps
if not exist "%PY_DEPS_STAMP%" exit /b 1
powershell -NoProfile -ExecutionPolicy Bypass -Command "$stampPath = '%PY_DEPS_STAMP%'; if (!(Test-Path -LiteralPath $stampPath)) { exit 1 }; $expected = (Get-Content -LiteralPath $stampPath -Raw).Trim(); $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath 'requirements.txt').Hash; if ($expected -ne $actual) { exit 1 }; exit 0"
exit /b %errorlevel%

:touch_python_deps_stamp
powershell -NoProfile -ExecutionPolicy Bypass -Command "$hash = (Get-FileHash -Algorithm SHA256 -LiteralPath 'requirements.txt').Hash; Set-Content -LiteralPath '%PY_DEPS_STAMP%' -Value $hash -NoNewline -Encoding ascii -Force"
exit /b %errorlevel%

:check_frontend_deps
if not exist "%UI_NODE_MODULES%" exit /b 1
if not exist "%UI_DEPS_STAMP%" exit /b 1
powershell -NoProfile -ExecutionPolicy Bypass -Command "$stamp = (Get-Item -LiteralPath '%UI_DEPS_STAMP%').LastWriteTimeUtc; foreach ($inputPath in @('%UI_DIR%\package.json', '%UI_DIR%\package-lock.json')) { if ((Test-Path -LiteralPath $inputPath) -and ((Get-Item -LiteralPath $inputPath).LastWriteTimeUtc -gt $stamp)) { exit 1 } }; exit 0"
exit /b %errorlevel%

:touch_frontend_deps_stamp
powershell -NoProfile -ExecutionPolicy Bypass -Command "Set-Content -LiteralPath '%UI_DEPS_STAMP%' -Value '' -NoNewline -Encoding ascii -Force"
exit /b %errorlevel%

:check_ui_build
if not exist "%UI_DIST_INDEX%" exit /b 1
if not exist "%UI_BUILD_STAMP%" exit /b 1
powershell -NoProfile -ExecutionPolicy Bypass -Command "$stamp = (Get-Item -LiteralPath '%UI_BUILD_STAMP%').LastWriteTimeUtc; $files = @(); foreach ($inputPath in @('%UI_DIR%\package.json', '%UI_DIR%\package-lock.json', '%UI_DIR%\vite.config.js', '%UI_DIR%\index.html')) { if (Test-Path -LiteralPath $inputPath) { $files += Get-Item -LiteralPath $inputPath } }; if (Test-Path -LiteralPath '%UI_DIR%\src') { $files += Get-ChildItem -LiteralPath '%UI_DIR%\src' -Recurse -File }; foreach ($file in $files) { if ($file.LastWriteTimeUtc -gt $stamp) { exit 1 } }; exit 0"
exit /b %errorlevel%

:touch_ui_build_stamp
powershell -NoProfile -ExecutionPolicy Bypass -Command "Set-Content -LiteralPath '%UI_BUILD_STAMP%' -Value '' -NoNewline -Encoding ascii -Force"
exit /b %errorlevel%
