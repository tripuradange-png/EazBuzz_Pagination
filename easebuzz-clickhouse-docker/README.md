# Easebuzz ClickHouse Docker Setup

This is a production-ready Docker containerized setup for the Easebuzz transaction fetcher script that connects to a remote ClickHouse database via SSH tunnel.

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

### Run the Container (Foreground)

This runs the container in the foreground and shows all output in your terminal.

```cmd
docker-compose up
```

**What this does:**
- Starts the container
- Runs `app.py` inside the container
- Shows all console output in real-time
- Press `Ctrl+C` to stop

### Run the Container (Background/Detached Mode)

This runs the container in the background.

```cmd
docker-compose up -d
```

**What this does:**
- Starts the container in the background
- Runs `app.py` inside the container
- Returns control to your terminal immediately

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

## Support

If you encounter any issues:

1. Check the logs: `docker logs -f easebuzz_clickhouse`
2. Verify SSH key is in the correct location
3. Ensure Docker Desktop is running
4. Check network connectivity

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
