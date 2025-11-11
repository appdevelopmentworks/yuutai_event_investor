@echo off
REM Windows用ビルドスクリプト
REM 使用方法: build.bat [pyinstaller|nuitka] または引数なしで対話式メニュー

setlocal

REM 引数がある場合は直接実行
if not "%1"=="" goto direct_build

REM 引数がない場合は対話式メニュー
:menu
echo.
echo ========================================
echo Yuutai Event Investor ビルドスクリプト
echo ========================================
echo.
echo ビルド方法を選択してください:
echo.
echo   1. PyInstaller  （推奨・高速ビルド）
echo   2. Nuitka       （高速実行）
echo   3. キャンセル
echo.
echo ========================================
echo.

set /p choice="番号を入力してください (1-3): "

if "%choice%"=="1" goto pyinstaller
if "%choice%"=="2" goto nuitka
if "%choice%"=="3" goto cancel

echo.
echo エラー: 無効な選択です
echo.
pause
exit /b 1

REM コマンドライン引数による直接実行
:direct_build
if /i "%1"=="pyinstaller" goto pyinstaller
if /i "%1"=="nuitka" goto nuitka

echo.
echo エラー: 不明なビルド方法 '%1'
echo.
echo 有効なオプション: pyinstaller, nuitka
echo.
pause
exit /b 1

:pyinstaller
echo.
echo ----------------------------------------
echo PyInstallerでビルドします...
echo ----------------------------------------
echo.
python build_pyinstaller.py
goto end

:nuitka
echo.
echo ----------------------------------------
echo Nuitkaでビルドします...
echo ----------------------------------------
echo.
python build_nuitka.py
goto end

:cancel
echo.
echo キャンセルしました。
echo.
pause
exit /b 0

:end
if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo [OK] ビルド完了\!
    echo ========================================
    echo.
    echo 出力先: dist\YuutaiEventInvestor
    echo.
) else (
    echo.
    echo ========================================
    echo [ERROR] ビルド失敗
    echo ========================================
    echo.
)

endlocal
pause
