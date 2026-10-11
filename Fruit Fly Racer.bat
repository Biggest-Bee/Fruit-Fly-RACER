@echo off
cd "C:\Users\anngu\Downloads\Fruit fly ai"
echo ========================================
echo Fruit Fly Racer - Racing Simulation
echo ========================================
echo.
echo Launching Racing Simulation...
echo.
echo This includes:
echo - 3D Obstacle Tunnel with MuJoCo Physics
echo - Procedural Obstacle Generation
echo - Dynamic Wind Fields
echo - Neural Network Inputs
echo - Reward/Penalty System
echo - Neural Memory with Cloud Sync
echo.
echo Based on MaleCNS v1.0 Fruit Fly Connectome
echo 211,577 neurons / ~151.8M connections
echo.
echo Select option:
echo 1. RUN FULL SIMULATION (Millions of repetitions with learning)
echo 2. Test Environment Generation
echo 3. Test Agent Logic
echo 4. Test Reward System
echo 5. Test Sync Manager
echo 6. Exit
echo.
set /p choice="Enter choice (1-6): "

if "%choice%"=="1" (
    echo.
    echo ========================================
    echo STARTING FULL SIMULATION
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
) else if "%choice%"=="2" (
    echo.
    echo Testing Environment Generation...
    python environment.py
) else if "%choice%"=="3" (
    echo.
    echo Testing Agent Logic...
    python agent_logic.py
) else if "%choice%"=="4" (
    echo.
    echo Testing Reward System...
    python rewards.py
) else if "%choice%"=="5" (
    echo.
    echo Testing Sync Manager...
    python sync_manager.py
) else if "%choice%"=="6" (
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