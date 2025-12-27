# Easebuzz ClickHouse Sync Service - Docker

This is a production-ready Docker containerized setup for the Easebuzz transaction sync service. It connects to Easebuzz API and syncs transactions to ClickHouse database via SSH tunnel.

## ✨ Latest Updates

- ✅ Updated to latest version with all bug fixes
- ✅ Auto-pagination for fetching ALL transactions
- ✅ Intermediate status update handling (pending → success/failure)
- ✅ Token auto-refresh mechanism
- ✅ Batch insertion (50 transactions per batch)
- ✅ Duplicate detection and smart update logic
- ✅ Continuous sync mode with configurable intervals

## Project Structure

```
easebuzz-clickhouse-docker/
│
├── app.py                  # Main Python application
├── Dockerfile              # Docker image configuration
├── docker-compose.yml      # Docker Compose configuration
├── requirements.txt        # Python dependencies
├── README.md              # This file
│
└── keys/
    └── SML_Castlecraft.pem  # SSH private key (REQUIRED - add manually)
```

## Prerequisites

- Docker Desktop installed on Windows
- Docker Compose installed (comes with Docker Desktop)
- SSH private key file: `SML_Castlecraft.pem`

## Setup Instructions

### Step 1: Copy SSH Key

**IMPORTANT:** Before running the container, you MUST copy your SSH private key into the `keys/` folder.

1. Copy your SSH key file `SML_Castlecraft.pem` to the `keys/` directory
2. The final path should be: `easebuzz-clickhouse-docker/keys/SML_Castlecraft.pem`

```cmd
# From your project directory
copy "D:\ClickHouse\SML_Castlecraft.pem" "keys\SML_Castlecraft.pem"
```

### Step 2: Verify Project Structure

Make sure your folder structure looks like this:

```
easebuzz-clickhouse-docker/
├── app.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── README.md
└── keys/
    └── SML_Castlecraft.pem  ← SSH key must be here
```

## Usage Commands

### Build the Docker Image

This command builds the Docker image from the Dockerfile.

```cmd
docker-compose build
```

**What this does:**
- Creates a Docker image with Python 3.10
- Installs all required dependencies (requests, tabulate, sshtunnel, clickhouse-driver)
- Copies your application code
- Sets up SSH key with correct permissions

### Run Single Sync (One-time run)

```cmd
docker-compose run --rm easebuzz_clickhouse
```

**What this does:**
- Runs a single sync operation
- Fetches all missing transactions from Easebuzz
- Inserts them into ClickHouse
- Exits when complete

### Run Continuous Sync Mode (Recommended for Production)

```cmd
docker-compose run --rm easebuzz_clickhouse python app.py --continuous
```

**What this does:**
- Syncs transactions every 5 minutes (default)
- Updates intermediate statuses every 2 hours
- Runs indefinitely until stopped with Ctrl+C
- Auto-refreshes API tokens

### Run Continuous Sync with Custom Intervals

```cmd
# Sync every 10 minutes, status update every 120 minutes
docker-compose run --rm easebuzz_clickhouse python app.py --continuous 10 120
```

### Run Status Update Only

```cmd
# Update transactions with intermediate status (last 48 hours)
docker-compose run --rm easebuzz_clickhouse python app.py --update-status

# Update transactions from last 72 hours
docker-compose run --rm easebuzz_clickhouse python app.py --update-status 72
```

### View Container Logs

When running in background mode, use this to see the output:

```cmd
docker logs -f easebuzz_clickhouse
```

**What this does:**
- Shows all console output from the running container
- `-f` flag follows the log (like tail -f)
- Press `Ctrl+C` to stop viewing logs (container keeps running)

### Stop the Container

```cmd
docker-compose down
```

**What this does:**
- Stops the running container
- Removes the container (but keeps the image)

## Complete Workflow Example

Here's a complete example of how to use this setup:

```cmd
# 1. Navigate to the project directory
cd D:\Tripura\easebuzz-clickhouse-docker

# 2. Build the Docker image (first time only, or after changes)
docker-compose build

# 3. Run the container in background
docker-compose up -d

# 4. Watch the logs
docker logs -f easebuzz_clickhouse

# 5. When done, stop the container
docker-compose down
```

## Environment Variables

The container uses the following environment variables (all configurable in docker-compose.yml):

### SSH Configuration
- `SSH_HOST`: SSH server hostname (default: `3.7.169.181`)
- `SSH_PORT`: SSH server port (default: `22`)
- `SSH_USERNAME`: SSH username (default: `ubuntu`)
- `SSH_KEY_PATH`: Path to SSH private key inside container (default: `/keys/SML_Castlecraft.pem`)

### ClickHouse Configuration
- `CH_HOST`: ClickHouse host (default: `127.0.0.1`)
- `CH_PORT`: ClickHouse port (default: `9000`)
- `CH_USER`: ClickHouse username (default: `default`)
- `CH_PASSWORD`: ClickHouse password (default: `aSh49aVjfy8P`)
- `CH_DATABASE`: ClickHouse database name (default: `default`)

### Python Configuration
- `PYTHONDONTWRITEBYTECODE`: Prevents Python from writing .pyc files
- `PYTHONUNBUFFERED`: Ensures Python output is sent straight to terminal

**To change these values:** Edit the `environment` section in `docker-compose.yml` and restart the container (no rebuild needed!).

## How It Works

1. **Docker Build Process:**
   - Uses `python:3.10-slim` as base image
   - Installs gcc and openssh-client for SSH tunnel support
   - Installs Python dependencies from requirements.txt
   - Copies app.py and SSH keys into the container
   - Sets SSH key permissions to 600 (read-write for owner only)

2. **Docker Run Process:**
   - Container starts and runs `python app.py`
   - App reads SSH key path from `SSH_KEY_PATH` environment variable
   - Establishes SSH tunnel to remote server (3.7.169.181)
   - Connects to ClickHouse database through the tunnel
   - Fetches transactions from Easebuzz API
   - Inserts data into ClickHouse database
   - Container exits when script completes

3. **Volume Mounting:**
   - The `keys/` folder is mounted as read-only into the container
   - This allows you to update the SSH key without rebuilding the image

## Troubleshooting

### Container fails to start

Check if the SSH key exists:
```cmd
dir keys\SML_Castlecraft.pem
```

### Permission denied errors

The Dockerfile automatically sets the correct permissions (600) for the SSH key inside the container.

### Cannot connect to ClickHouse

1. Check if SSH tunnel is established (look for "SSH tunnel established" in logs)
2. Verify the SSH key is correct
3. Check network connectivity to 3.7.169.181

### View detailed logs

```cmd
# View all logs
docker logs easebuzz_clickhouse

# View last 50 lines
docker logs --tail 50 easebuzz_clickhouse

# Follow logs in real-time
docker logs -f easebuzz_clickhouse
```

### Rebuild after code changes

If you modify `app.py`:
```cmd
docker-compose down
docker-compose build
docker-compose up
```

## Security Notes

- SSH private key is mounted as read-only into the container
- SSH key permissions are automatically set to 600 (owner read-write only)
- Never commit the SSH key to version control
- Add `keys/SML_Castlecraft.pem` to `.gitignore`

## What Changed from Original Script

Only ONE line changed in the Python code:

**Before:**
```python
self.ssh_key_path = r'D:\ClickHouse\SML_Castlecraft.pem'
```

**After:**
```python
self.ssh_key_path = os.getenv("SSH_KEY_PATH", "/keys/SML_Castlecraft.pem")
```

**Added:**
```python
import os  # Added at the top of the file
```

Everything else remains exactly the same - all business logic is unchanged.

## Technical Stack

- **Base Image:** python:3.10-slim
- **Python Version:** 3.10
- **Dependencies:**
  - requests (Easebuzz API calls)
  - tabulate (Table formatting)
  - sshtunnel (SSH tunnel for ClickHouse)
  - clickhouse-driver (ClickHouse database client)
- **System Packages:**
  - gcc (Required for building Python packages)
  - openssh-client (Required for SSH tunnel)

## Running with Docker Run Command

If you prefer using `docker run` instead of docker-compose, use this command:

```cmd
docker run --rm ^
  -e SSH_HOST=3.7.169.181 ^
  -e SSH_PORT=22 ^
  -e SSH_USER=ubuntu ^
  -e SSH_KEY_PATH=/keys/SML_Castlecraft.pem ^
  -e FETCH_INTERVAL=30 ^
  -v "D:\Tripura\easebuzz-clickhouse-docker\keys\SML_Castlecraft.pem:/keys/SML_Castlecraft.pem:ro" ^
  tripuradange15/easebuzz-clickhouse
```

**Key Points:**
- Use `-v` to mount the SSH key from your local machine to the container
- The `:ro` suffix makes the mount read-only for security
- Adjust the local path if your `.pem` file is in a different location
- The `--rm` flag automatically removes the container when it exits
- `FETCH_INTERVAL=30` sets checking every 30 seconds (change to adjust frequency)

## Support

If you encounter any issues:

1. Check the logs: `docker logs -f easebuzz_clickhouse`
2. Verify SSH key is in the correct location
3. Ensure Docker Desktop is running
4. Check network connectivity
5. Make sure the SSH key has correct permissions (Docker will set it to 600 automatically)

## Quick Reference

| Command | Description |
|---------|-------------|
| `docker-compose build` | Build the Docker image |
| `docker-compose up` | Run container (foreground) |
| `docker-compose up -d` | Run container (background) |
| `docker logs -f easebuzz_clickhouse` | View logs |
| `docker-compose down` | Stop container |
| `docker ps` | List running containers |
| `docker images` | List Docker images |
