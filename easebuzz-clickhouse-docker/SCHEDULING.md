# 24/7 Scheduling Options for Easebuzz-ClickHouse Sync

## Option 1: Windows Task Scheduler (Recommended for 24/7)

Schedule the script to run automatically at regular intervals.

### Step 1: Open Task Scheduler

1. Press `Win + R`, type `taskschd.msc`, press Enter
2. Or search for "Task Scheduler" in Windows Start menu

### Step 2: Create a New Task

1. Click **"Create Basic Task"** in the right panel
2. Name: `Easebuzz ClickHouse Sync`
3. Description: `Sync Easebuzz transactions to ClickHouse database every hour`
4. Click **Next**

### Step 3: Set Trigger (When to Run)

Choose one of these schedules:

**Option A: Every Hour (Recommended)**
- Select **"Daily"**
- Set start time (e.g., 12:00 AM)
- Click **Next**
- In the next screen, check **"Repeat task every"**
- Select **1 hour**
- Duration: **1 day**

**Option B: Every 6 Hours**
- Select **"Daily"**
- Set start time (e.g., 12:00 AM)
- Click **Next**
- Check **"Repeat task every"**
- Select **6 hours**
- Duration: **1 day**

**Option C: Once Daily (Less frequent)**
- Select **"Daily"**
- Set time (e.g., 2:00 AM)
- Click **Next**

### Step 4: Set Action (What to Run)

1. Select **"Start a program"**
2. Click **Next**
3. **Program/script:** Browse to: `D:\Tripura\easebuzz-clickhouse-docker\run.bat`
4. Click **Next**

### Step 5: Finish Configuration

1. Check **"Open the Properties dialog when I click Finish"**
2. Click **Finish**

### Step 6: Advanced Settings (In Properties Dialog)

1. **General Tab:**
   - Check ☑ **"Run whether user is logged on or not"**
   - Check ☑ **"Run with highest privileges"**
   - Configure for: **Windows 10/Windows Server 2019**

2. **Conditions Tab:**
   - Uncheck ☐ **"Start the task only if the computer is on AC power"** (if laptop)
   - Check ☑ **"Wake the computer to run this task"** (optional)

3. **Settings Tab:**
   - Check ☑ **"Allow task to be run on demand"**
   - Check ☑ **"Run task as soon as possible after a scheduled start is missed"**
   - **If the task fails, restart every:** 10 minutes
   - **Attempt to restart up to:** 3 times
   - **Stop the task if it runs longer than:** 3 hours (adjust based on your data volume)

4. Click **OK**
5. Enter your Windows password when prompted

### Step 7: Test the Task

1. Right-click the task in Task Scheduler
2. Click **"Run"**
3. Check if it works correctly

### View Task History

1. In Task Scheduler, select your task
2. Click **"History"** tab at the bottom
3. View execution logs

---

## Option 2: Keep Container Running 24/7 with Auto-Restart

If you want the container to keep running and automatically restart after completion:

### Modify docker-compose.yml

Change line 22 back to:
```yaml
restart: unless-stopped
```

### Start the Container

```cmd
cd D:\Tripura\easebuzz-clickhouse-docker
docker-compose up -d
```

**How it works:**
- Container runs the script
- When script completes, container exits
- Docker automatically restarts the container
- Script runs again from the beginning

**Pros:**
- Fully automated
- No Task Scheduler needed
- Always running

**Cons:**
- Runs continuously (fetches same data repeatedly)
- More resource intensive
- Duplicate checking relies on database

---

## Option 3: Hybrid Approach (Best for Production)

Combine both approaches:

1. Use **Task Scheduler** for regular syncs (e.g., every 6 hours)
2. Keep **`restart: "no"`** in docker-compose.yml
3. Container runs, syncs data, then stops
4. Waits for next scheduled run

**Advantages:**
- Efficient (only runs when scheduled)
- Predictable execution times
- Lower resource usage
- Easy to monitor and log

---

## Monitoring and Logging

### View Logs

```cmd
# View all logs from last run
docker logs easebuzz_clickhouse

# View last 100 lines
docker logs --tail 100 easebuzz_clickhouse

# Follow logs in real-time (during execution)
docker logs -f easebuzz_clickhouse
```

### Save Logs to File

Add this to `run.bat`:

```batch
docker-compose up > "logs\sync_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%.log" 2>&1
```

---

## Recommended Setup for 24/7 Operation

1. **Schedule:** Every 1-2 hours using Task Scheduler
2. **Restart policy:** `restart: "no"`
3. **Logging:** Enable log rotation
4. **Monitoring:** Check Task Scheduler history daily

This gives you:
- Continuous operation
- Predictable execution
- Efficient resource usage
- Easy troubleshooting

---

## Troubleshooting

### Task doesn't run
- Check Task Scheduler history for errors
- Verify Docker Desktop is running
- Check Windows Event Viewer

### Task runs but fails
- Check Docker logs: `docker logs easebuzz_clickhouse`
- Verify SSH key is accessible
- Check ClickHouse connectivity

### Resource issues
- Reduce sync frequency (e.g., every 6 hours instead of every hour)
- Monitor Docker Desktop resource usage

---

## Quick Commands

```cmd
# Manually run sync
cd D:\Tripura\easebuzz-clickhouse-docker
docker-compose up

# Stop running sync
docker-compose down

# View logs
docker logs easebuzz_clickhouse

# Check container status
docker ps -a

# Force restart container
docker-compose restart
```
