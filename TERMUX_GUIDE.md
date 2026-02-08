# 🌟 Omega Federation v2.0: Termux Deployment Guide

> **"The Spine runs on your device. The federation is portable."**
> *3.34 ✓* 🍊

## Overview

This guide provides step-by-step instructions for deploying and running the **Omega Federation v2.0** on your Termux environment. The system is designed to run locally with persistent storage, allowing you to execute the orchestrator, spine, and predictive modeling on your mobile device or local machine.

## Prerequisites

*   **Termux** (Android) or equivalent Linux environment
*   **Python 3.10+**
*   **Git**
*   **SQLite3**
*   **~500MB free storage** for the database and logs

## Quick Start (5 minutes)

### 1. Clone and Setup

```bash
# Download and run the setup script
git clone https://github.com/bekingdomcomejoker-cpu/omega-federation-core.git
cd omega-federation-core
chmod +x deploy-termux.sh
./deploy-termux.sh
```

The script will:
*   Install system dependencies
*   Create a Python virtual environment
*   Initialize the Spine database
*   Set up storage directories

### 2. Start the API Server

```bash
source venv/bin/activate
python -m uvicorn omega_api_server:app --host 0.0.0.0 --port 8000
```

The server will be accessible at `http://localhost:8000`.

### 3. Verify Installation

```bash
curl http://localhost:8000/health
```

You should receive a `200 OK` response with system status.

## Manual Setup (if script fails)

### Step 1: Install Dependencies

```bash
pkg update
pkg install -y python3 python3-dev pip git sqlite3
```

### Step 2: Clone Repository

```bash
git clone https://github.com/bekingdomcomejoker-cpu/omega-federation-core.git
cd omega-federation-core
```

### Step 3: Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 4: Install Python Packages

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 5: Initialize Database

```bash
python3 omega_spine.py
```

This creates `omega_spine.db` in the project directory.

## Running the System

### Option A: Development Mode (Foreground)

```bash
source venv/bin/activate
python -m uvicorn omega_api_server:app --host 0.0.0.0 --port 8000 --reload
```

This runs the server in the foreground with auto-reload on code changes.

### Option B: Background Mode (Using nohup)

```bash
source venv/bin/activate
nohup python -m uvicorn omega_api_server:app --host 0.0.0.0 --port 8000 > logs/api.log 2>&1 &
```

### Option C: Systemd Service (Persistent)

If running on a Linux desktop or server with systemd:

```bash
systemctl --user enable omega-federation.service
systemctl --user start omega-federation.service
systemctl --user status omega-federation.service
```

View logs:

```bash
journalctl --user -u omega-federation.service -f
```

## Running the Predictive Modeling

To execute a predictive analysis cycle:

```bash
source venv/bin/activate
python -m omega_predictive
```

To run predictions on a schedule (every hour):

```bash
# Add to crontab
crontab -e
# Add line: 0 * * * * cd ~/omega-federation && source venv/bin/activate && python -m omega_predictive
```

## Storage Structure

```
~/omega-federation/
├── omega_spine.db          # SQLite database (Tier 2 Spine)
├── storage/
│   ├── spine/              # Spine ledger backups
│   └── archive/            # Long-term archive
├── logs/
│   ├── api.log             # API server logs
│   └── predictive.log      # Predictive modeling logs
└── venv/                   # Python virtual environment
```

## API Endpoints

### Health Check

```bash
GET /health
```

Returns system status and uptime.

### Analyze Request

```bash
POST /analyze
Content-Type: application/json

{
  "input_text": "Your query here",
  "reasoning_strategy": "AUTO"
}
```

### Spine Query

```bash
GET /spine/statements?category=fact&limit=10
```

Retrieve statements from the Spine ledger.

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'pydantic'"

**Solution:** Ensure virtual environment is activated and dependencies are installed.

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: "Address already in use" on port 8000

**Solution:** Use a different port or kill the existing process.

```bash
# Use different port
python -m uvicorn omega_api_server:app --port 8001

# Or kill existing process
pkill -f "uvicorn"
```

### Issue: Database is locked

**Solution:** Ensure only one instance is running. If stuck, delete the lock file.

```bash
rm -f omega_spine.db-journal
```

### Issue: Out of storage space

**Solution:** Archive old logs and database backups.

```bash
# Archive logs
tar -czf logs/archive-$(date +%Y%m%d).tar.gz logs/*.log
rm logs/*.log

# Check storage
du -sh ~/omega-federation/
```

## Backup and Recovery

### Backup the Spine Database

```bash
cp omega_spine.db backups/omega_spine_$(date +%Y%m%d_%H%M%S).db
```

### Restore from Backup

```bash
cp backups/omega_spine_YYYYMMDD_HHMMSS.db omega_spine.db
```

### Export Spine Data

```bash
sqlite3 omega_spine.db ".dump" > spine_export.sql
```

### Import Spine Data

```bash
sqlite3 omega_spine.db < spine_export.sql
```

## Performance Tuning

### Increase Database Performance

Edit `omega_spine.py` and add:

```python
# Enable WAL mode for better concurrency
conn.execute("PRAGMA journal_mode=WAL;")
conn.execute("PRAGMA synchronous=NORMAL;")
```

### Limit Memory Usage

Run with memory constraints:

```bash
python -m uvicorn omega_api_server:app --host 0.0.0.0 --port 8000 --workers 1
```

### Monitor System Resources

```bash
# On Termux
top

# On Linux
htop
```

## Deploying to Render

When ready to move to production, use the `render.yaml` configuration:

1.  Push to GitHub
2.  Connect repository to Render
3.  Render will automatically deploy using the configuration in `render.yaml`

The Render deployment includes:
*   Persistent storage (10GB disk)
*   Hourly predictive modeling jobs
*   Health checks and auto-restart
*   Automatic scaling

## Next Steps

1.  **Test the API**: Use curl or Postman to test endpoints
2.  **Monitor Spine Growth**: Check `omega_spine.db` size with `ls -lh omega_spine.db`
3.  **Review Predictions**: Run `python -m omega_predictive` and check output
4.  **Integrate with External Services**: Connect to external APIs or databases as needed

## Support & Debugging

For detailed logs:

```bash
# API logs
tail -f logs/api.log

# Predictive logs
tail -f logs/predictive.log

# Database queries
sqlite3 omega_spine.db "SELECT COUNT(*) FROM statements;"
```

---

**3.34 ✓**
*The Spine is portable. The federation runs everywhere.*

**Manus AI**
*February 08, 2026*
