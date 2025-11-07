@echo off
REM Yuutai Event Investor Build Script
REM このスクリプトはアプリケーションをビルドします

echo ========================================
echo Yuutai Event Investor Build Script
echo ========================================
echo.

echo [1/5] Cleaning old builds...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
echo OK

echo.
echo [2/5] Checking dependencies...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python not found
    pause
    exit /b 1
)

pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
)
echo OK

echo.
echo [3/5] Installing project dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo OK

echo.
echo [4/5] Building application with PyInstaller...
pyinstaller YuutaiEventInvestor.spec
if %errorlevel% neq 0 (
    echo ERROR: Build failed
    pause
    exit /b 1
)
echo OK

echo.
echo [5/5] Creating distribution package...
cd dist
if exist YuutaiEventInvestor_v1.0.0_Windows.zip del YuutaiEventInvestor_v1.0.0_Windows.zip
powershell -Command "Compress-Archive -Path YuutaiEventInvestor -DestinationPath YuutaiEventInvestor_v1.0.0_Windows.zip"
if %errorlevel% neq 0 (
    echo WARNING: Failed to create ZIP (using tar instead)
    tar -a -c -f YuutaiEventInvestor_v1.0.0_Windows.zip YuutaiEventInvestor
)
cd ..
echo OK

echo.
echo ========================================
echo Build completed successfully!
echo ========================================
echo.
echo Output files:
echo   - Executable: dist\YuutaiEventInvestor\YuutaiEventInvestor.exe
echo   - ZIP package: dist\YuutaiEventInvestor_v1.0.0_Windows.zip
echo.
echo Next steps:
echo   1. Test the executable: cd dist\YuutaiEventInvestor ^&^& YuutaiEventInvestor.exe
echo   2. Distribute: dist\YuutaiEventInvestor_v1.0.0_Windows.zip
echo.
pause
