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
echo 1. Test Environment Generation
echo 2. Test Agent Logic
echo 3. Test Reward System
echo 4. Test Sync Manager
echo 5. Exit
echo.
set /p choice="Enter choice (1-5): "

if "%choice%"=="1" (
    echo.
    echo Testing Environment Generation...
    python environment.py
) else if "%choice%"=="2" (
    echo.
    echo Testing Agent Logic...
    python agent_logic.py
) else if "%choice%"=="3" (
    echo.
    echo Testing Reward System...
    python rewards.py
) else if "%choice%"=="4" (
    echo.
    echo Testing Sync Manager...
    python sync_manager.py
) else if "%choice%"=="5" (
    echo.
    echo Exiting...
    exit
) else (
    echo.
    echo Invalid choice. Exiting...
)

echo.
echo ========================================
echo Test completed
echo ========================================
echo.
pause