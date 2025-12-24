@echo off
REM Easebuzz to ClickHouse Sync Script
REM This script runs the Docker container to sync transactions

cd /d D:\Tripura\easebuzz-clickhouse-docker

echo [%date% %time%] Starting Easebuzz sync...

REM Run the container (it will stop automatically when done)
docker-compose up

REM Clean up
docker-compose down

echo [%date% %time%] Sync completed.
