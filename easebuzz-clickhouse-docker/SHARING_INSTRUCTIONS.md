# Instructions for Sharing This Project

## The Problem You're Experiencing

The Docker image works on your current PC but fails on another PC with this error:
```
Could not connect to gateway 3.7.169.181:22 : Connection refused
```

**Root Cause:** The other PC cannot reach the SSH server at `3.7.169.181:22` due to network restrictions (firewall, VPN, or IP whitelist).

---

## Solution

The person on the other PC must:

1. **Test network connectivity FIRST** before trying to run Docker
2. Connect to VPN if required
3. Get their IP whitelisted by the server administrator
4. Only then run the Docker container

---

## Files to Share with the Other Person

Send these files via email or secure file transfer:

### Required Files:
1. **SML_Castlecraft.pem** - SSH private key (send securely, never via regular email)
2. **SETUP_EMAIL.txt** - Complete setup instructions (this is already prepared)
3. **QUICK_START.md** - Quick reference guide
4. **TROUBLESHOOTING.md** - Detailed troubleshooting steps

### Optional (if they want to build locally):
5. The entire `easebuzz-clickhouse-docker` folder

---

## How to Share

### Method 1: Email (Recommended for Instructions)

**Subject:** Easebuzz ClickHouse Docker Setup

**Body:**
```
Hi,

Attached are the setup instructions for the Easebuzz ClickHouse Docker container.

IMPORTANT: Before running anything, you MUST verify your PC can reach the server:

1. Open PowerShell and run:
   Test-NetConnection -ComputerName 3.7.169.181 -Port 22

2. If this test FAILS, you need to:
   - Connect to VPN, OR
   - Get your IP whitelisted by IT

3. If the test SUCCEEDS, follow the instructions in SETUP_EMAIL.txt

I'll send the SSH key separately via [secure method].

Let me know if you have any questions!
```

**Attachments:**
- SETUP_EMAIL.txt
- QUICK_START.md
- TROUBLESHOOTING.md

### Method 2: Send SSH Key Securely

**DO NOT send the .pem file via regular email!**

Use one of these secure methods:
- Encrypted file sharing service (e.g., password-protected zip)
- Secure company file share
- Hand it over in person
- Secure messaging app with end-to-end encryption

---

## Docker Hub Image

The Docker image is publicly available at:
```
tripuradange15/easebuzz-clickhouse:latest
```

Anyone can pull this image without credentials:
```cmd
docker pull tripuradange15/easebuzz-clickhouse:latest
```

**However:** The image will NOT work without:
1. The SSH private key (SML_Castlecraft.pem)
2. Network access to 3.7.169.181:22

---

## Pre-Flight Checklist for the Other Person

Before they can run the Docker container, they MUST:

- [ ] Install Docker Desktop
- [ ] Have the SSH private key (SML_Castlecraft.pem)
- [ ] Test network connectivity: `Test-NetConnection -ComputerName 3.7.169.181 -Port 22`
- [ ] If test fails, connect to VPN or get IP whitelisted
- [ ] Only then proceed with Docker commands

---

## Network Requirements

The other PC needs to be able to reach:
- **SSH Server:** 3.7.169.181 on port 22 (TCP)
- **Docker Hub:** hub.docker.com (for pulling the image)

---

## If Network Access is Impossible

If the other PC absolutely cannot reach 3.7.169.181 due to network policies:

### Option A: Run on Your Current PC
- Run the container on your PC in background: `docker-compose up -d`
- The other person accesses ClickHouse database remotely (if permitted)

### Option B: Deploy to Cloud
- Deploy the container to AWS EC2, Azure VM, or Google Cloud
- Make sure the cloud VM is in the same network/VPC as the ClickHouse server

### Option C: Request Network Access
- Submit IT ticket to allow the other PC's IP to access 3.7.169.181:22
- Provide the other PC's public IP address

---

## Testing Network Access

The other person should run this diagnostic:

```powershell
# Test from Windows host
Test-NetConnection -ComputerName 3.7.169.181 -Port 22

# Find their public IP (to request whitelisting)
(Invoke-WebRequest -Uri "https://api.ipify.org").Content
```

Share the public IP with your network administrator to whitelist it.

---

## Summary

✅ **Your PC:** Can reach 3.7.169.181:22 → Docker works
❌ **Other PC:** Cannot reach 3.7.169.181:22 → Docker fails

**Solution:** Fix network connectivity first, then Docker will work automatically.

The Docker setup is correct - it's purely a network connectivity issue.
