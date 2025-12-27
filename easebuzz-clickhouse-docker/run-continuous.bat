@echo off
REM Run Easebuzz ClickHouse in continuous sync mode

echo ================================================
echo  Easebuzz ClickHouse - Continuous Sync Mode
echo ================================================
echo.
echo Starting continuous sync service...
echo - Transaction sync: Every 5 minutes
echo - Status updates: Every 2 hours
echo.
echo Press Ctrl+C to stop
echo ================================================
echo.

docker-compose run --rm easebuzz_clickhouse python app.py --continuous

pause
