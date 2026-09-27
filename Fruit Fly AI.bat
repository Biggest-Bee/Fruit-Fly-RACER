@echo off
cd "C:\Users\anngu\Downloads\Fruit fly ai"
echo ========================================
echo Fruit Fly AI - Launch Options
echo ========================================
echo.
echo Backend systems are confirmed working!
echo.
echo Available Options:
echo 1. Console Version (RECOMMENDED - Fully Working)
echo 2. Quick Status Check
echo 3. Simple GUI (Working - Basic Interface)
echo 4. Integrated Desktop App (3D + Resizable Panels + Training)
echo 5. Exit
echo.
set /p choice="Enter choice (1-5): "

if "%choice%"=="1" (
    echo.
    echo Launching Console Version...
    echo Type 'exit' to quit
    echo.
    python console_app.py
    echo.
    echo Console closed. Press any key to return to menu...
    pause
    cls
    goto :menu
) else if "%choice%"=="2" (
    echo.
    echo Running Status Check...
    echo.
    python status_check.py
    echo.
    pause
    cls
    goto :menu
) else if "%choice%"=="3" (
    echo.
    echo Launching Simple GUI Version...
    echo.
    echo Basic interface with backend loading capability.
    echo.
    python ultra_simple_app.py 2>&1
    echo.
    echo ========================================
    echo Simple GUI process ended
    echo ========================================
    echo.
    pause
    cls
    goto :menu
) else if "%choice%"=="4" (
    echo.
    echo Launching Integrated Desktop Application...
    echo.
    echo This includes:
    echo - Complete GUI with all components
    echo - Integrated 3D Environment (launch anytime)
    echo - Resizable panels (View menu)
    echo - File Explorer with code execution
    echo - Training Panel with 27 languages
    echo - Practice in 3D functionality
    echo - Status Panel
    echo.
    echo Features:
    echo - View menu: Expand/contract panels
    echo - 3D menu: Launch/control 3D environment
    echo - Training menu: Start training, practice in 3D
    echo.
    echo Backend loads in background after GUI starts.
    echo Debug output will be shown below.
    echo.
    echo Starting Integrated Desktop App...
    echo.
    python integrated_desktop_app.py 2>&1
    echo.
    echo ========================================
    echo Integrated Desktop App process ended
    echo ========================================
    echo.
    pause
    cls
    goto :menu
) else if "%choice%"=="5" (
    echo Exiting...
    exit /b
) else (
    echo Invalid choice
    pause
    cls
    goto :menu
)

:menu
goto :eof