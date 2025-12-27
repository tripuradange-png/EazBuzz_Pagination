# Quick Start Guide

## ⚠️ BEFORE YOU START - Network Connectivity Test

**IMPORTANT:** Run this command first to verify your PC can reach the server:

```powershell
Test-NetConnection -ComputerName 3.7.169.181 -Port 22
```

**Expected Result:**
```
TcpTestSucceeded : True
```

❌ **If this test FAILS**, the Docker container will NOT work.
✅ **If this test SUCCEEDS**, continue with the setup below.

### If the test fails:
1. **Connect to VPN** if your organization requires it
2. **Contact IT** to whitelist your IP address for SSH access
3. **Run from a different PC** that has network access

---

## Quick Setup (5 Steps)

### 1. Install Docker Desktop
Download: https://www.docker.com/products/docker-desktop/

### 2. Create a folder for the SSH key
```cmd
mkdir C:\easebuzz-keys
```

### 3. Copy the .pem file
Copy `SML_Castlecraft.pem` to `C:\easebuzz-keys\`

### 4. Pull the Docker image
```cmd
docker pull tripuradange15/easebuzz-clickhouse:latest
```

### 5. Run the container
```cmd
docker run --rm ^
  -e SSH_HOST=3.7.169.181 ^
  -e SSH_PORT=22 ^
  -e SSH_USER=ubuntu ^
  -e SSH_KEY_PATH=/keys/SML_Castlecraft.pem ^
  -e FETCH_INTERVAL=30 ^
  -v "C:\easebuzz-keys\SML_Castlecraft.pem:/keys/SML_Castlecraft.pem:ro" ^
  tripuradange15/easebuzz-clickhouse:latest
```

**Note:** Make sure to run this from **Command Prompt (cmd)**, NOT Git Bash or PowerShell.

---

## What You Should See

If everything works correctly:

```
Starting SSH tunnel...
SSH Tunnel established: ('127.0.0.1', 9000)
Connecting to ClickHouse database...
Connected to ClickHouse! Version: 25.6.4.12
Fetching authentication token...
Token fetched successfully
```

The container will then continuously check for new transactions every 30 seconds.

---

## Troubleshooting

### "Connection refused" error
- Your PC cannot reach the SSH server
- See the troubleshooting section above ⬆️

### "No such file" error
- The .pem file path is wrong
- Make sure you copied it to exactly: `C:\easebuzz-keys\SML_Castlecraft.pem`

### Container exits immediately
- Check logs: `docker logs easebuzz_clickhouse`
- See SETUP_EMAIL.txt or TROUBLESHOOTING.md for detailed help

---

## Stopping the Container

Press `Ctrl+C` in the terminal window where the container is running.

Or if running in background:
```cmd
docker stop easebuzz_clickhouse
```

---

## Need Help?

1. Check SETUP_EMAIL.txt for complete setup instructions
2. Check TROUBLESHOOTING.md for detailed troubleshooting
3. Contact your IT administrator for network issues
