@echo off
REM Build script for Easebuzz ClickHouse Docker

echo ================================================
echo  Easebuzz ClickHouse - Docker Build Script
echo ================================================
echo.

echo [1/3] Copying latest code from index.py...
copy /Y "..\index.py" "app.py"
if errorlevel 1 (
    echo ERROR: Failed to copy index.py
    pause
    exit /b 1
)
echo [OK] Code copied successfully
echo.

echo [2/3] Building Docker image...
docker-compose build --no-cache
if errorlevel 1 (
    echo ERROR: Docker build failed
    pause
    exit /b 1
)
echo [OK] Docker image built successfully
echo.

echo [3/3] Verifying SSH key...
if not exist "keys\SML_Castlecraft.pem" (
    echo WARNING: SSH key not found at keys\SML_Castlecraft.pem
    echo Please copy your SSH key to the keys directory
    pause
) else (
    echo [OK] SSH key found
)
echo.

echo ================================================
echo  Build completed successfully!
echo ================================================
echo.
echo Next steps:
echo   Single run:      docker-compose run --rm easebuzz_clickhouse
echo   Continuous mode: docker-compose run --rm easebuzz_clickhouse python app.py --continuous
echo.
pause
