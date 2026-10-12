@echo off
cd "C:\Users\anngu\Downloads\Fruit fly ai"
echo ========================================
echo Fruit Fly Racer - Racing Simulation
echo ========================================
echo.
echo Based on MaleCNS v1.0 Fruit Fly Connectome
echo 211,577 neurons / ~151.8M connections
echo.
echo Select option:
echo 1. DESKTOP GUI APPLICATION (Recommended)
echo 2. RUN FULL SIMULATION (CLI - Millions of repetitions)
echo 3. Test Environment Generation
echo 4. Test Agent Logic
echo 5. Test Reward System
echo 6. Test Sync Manager
echo 7. Test MuJoCo Fly Model
echo 8. Exit
echo.
set /p choice="Enter choice (1-8): "

if "%choice%"=="1" (
    echo.
    echo ========================================
    echo LAUNCHING DESKTOP GUI APPLICATION
    echo ========================================
    echo.
    python desktop_gui.py
) else if "%choice%"=="2" (
    echo.
    echo ========================================
    echo STARTING FULL SIMULATION (CLI)
    echo ========================================
    echo.
    echo The fly will run through the obstacle course millions of times
    echo It will learn from each run and improve its performance
    echo The map regenerates each time with new obstacles
    echo Neural memory is saved automatically
    echo.
    echo Press Ctrl+C to stop at any time
    echo.
    pause
    python main_simulation.py
) else if "%choice%"=="3" (
    echo.
    echo Testing Environment Generation...
    python environment.py
) else if "%choice%"=="4" (
    echo.
    echo Testing Agent Logic...
    python agent_logic.py
) else if "%choice%"=="5" (
    echo.
    echo Testing Reward System...
    python rewards.py
) else if "%choice%"=="6" (
    echo.
    echo Testing Sync Manager...
    python sync_manager.py
) else if "%choice%"=="7" (
    echo.
    echo Testing MuJoCo Fly Model...
    python mujoco_fly_model.py
) else if "%choice%"=="8" (
    echo.
    echo Exiting...
    exit
) else (
    echo.
    echo Invalid choice. Exiting...
)

echo.
echo ========================================
echo Process completed
echo ========================================
echo.
pause