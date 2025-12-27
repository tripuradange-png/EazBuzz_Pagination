# Troubleshooting Guide

## Issue: "Connection Refused" Error on Another PC

### Error Message
```
Could not connect to gateway 3.7.169.181:22 : Unable to connect to 3.7.169.181: [Errno 111] Connection refused
```

### Root Cause
The SSH server at `3.7.169.181:22` is not accessible from the other PC's network. This could be due to:

1. **Network Restrictions**: The other PC is on a different network that can't reach the server
2. **Firewall Rules**: The SSH server's firewall only allows connections from specific IPs
3. **VPN Required**: You may need to be on a VPN to access the server
4. **Docker Network Issue**: Docker's bridge network on Windows may not route to the server

### Solutions

## Solution 1: Verify Network Connectivity (FIRST STEP)

Before running the Docker container, test if the PC can reach the SSH server:

### On Windows (PowerShell):
```powershell
Test-NetConnection -ComputerName 3.7.169.181 -Port 22
```

### On Windows (Command Prompt):
```cmd
telnet 3.7.169.181 22
```

### Expected Result:
- **Success**: `TcpTestSucceeded : True` or you see SSH banner
- **Failure**: Connection timeout or refused

**If this test fails, the Docker container will also fail.** You need to fix the network connectivity first.

---

## Solution 2: Connect via VPN

If the SSH server requires VPN access:

1. Connect to your organization's VPN
2. Test connectivity again: `Test-NetConnection -ComputerName 3.7.169.181 -Port 22`
3. Once connected, run the Docker container

---

## Solution 3: Use SSH Tunnel from Host

If Docker can't reach the server but your Windows host can, create an SSH tunnel on the Windows host:

### Step 1: Install OpenSSH Client on Windows
```powershell
# Check if installed
Get-WindowsCapability -Online | Where-Object Name -like 'OpenSSH.Client*'

# Install if needed
Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0
```

### Step 2: Create SSH Tunnel on Host
```cmd
ssh -i "C:\easebuzz-keys\SML_Castlecraft.pem" -L 9000:127.0.0.1:9000 -N ubuntu@3.7.169.181
```

Leave this running in a separate terminal window.

### Step 3: Update Docker Command to Use Host Network
```cmd
docker run --rm ^
  -e SSH_HOST=host.docker.internal ^
  -e SSH_PORT=9000 ^
  -e SSH_USER=ubuntu ^
  -e FETCH_INTERVAL=30 ^
  tripuradange15/easebuzz-clickhouse:latest
```

Note: This bypasses the container's SSH tunnel and uses the host's tunnel instead.

---

## Solution 4: Whitelist the PC's IP Address

Contact your server administrator to whitelist the IP address of the PC running Docker.

### Find Your Public IP:
```powershell
(Invoke-WebRequest -Uri "https://api.ipify.org").Content
```

Provide this IP to your admin to add to the SSH server's firewall allowlist.

---

## Solution 5: Run on the Working PC

If the other PC cannot reach the server due to network restrictions:

1. Run the Docker container on the PC that currently has access (the one at `192.168.0.148`)
2. Use `docker-compose up -d` to run in background
3. Access the ClickHouse database remotely from other PCs

---

## Verifying Docker Installation

Make sure Docker is installed and running on the other PC:

```cmd
docker --version
docker ps
```

If Docker is not running, start Docker Desktop.

---

## Network Configuration Comparison

### Working PC (Current):
- Windows can reach 3.7.169.181:22 ✅
- Docker container can reach 3.7.169.181:22 ❓ (sometimes fails on Windows)

### Other PC:
- Windows can reach 3.7.169.181:22 ❓ (TEST THIS FIRST)
- Docker container can reach 3.7.169.181:22 ❓

---

## Quick Diagnostic Steps

Run these on the other PC:

### 1. Test from Windows Host
```powershell
Test-NetConnection -ComputerName 3.7.169.181 -Port 22
```

### 2. Test from Docker Container
```cmd
docker run --rm busybox telnet 3.7.169.181 22
```

### 3. Check Docker Network Mode
```cmd
docker network ls
docker network inspect bridge
```

---

## Alternative: Deploy on Cloud/Server

If network restrictions persist, consider deploying the container on:

1. **AWS EC2** - Same VPC as your ClickHouse server
2. **Azure VM** - In the same network as your server
3. **Google Cloud VM** - Close to your server
4. **On-Premises Server** - In the same datacenter

This ensures the container always has network access to the SSH server.

---

## Contact Information

If issues persist, collect this information:

1. Output of: `Test-NetConnection -ComputerName 3.7.169.181 -Port 22`
2. Output of: `docker run --rm busybox telnet 3.7.169.181 22`
3. Your public IP: `(Invoke-WebRequest -Uri "https://api.ipify.org").Content`
4. Docker version: `docker --version`
5. Full error logs from container: `docker logs easebuzz_clickhouse`

Share this with your network administrator or IT support team.
