# Free Deployment Guide for un!mployed

This guide will help you deploy your Flask application to free hosting platforms.

## 🎯 Best Free Hosting Options

### Option 1: **Render** (Recommended - Easiest)
- ✅ Free tier available
- ✅ Automatic SSL/HTTPS
- ✅ Easy GitHub integration
- ✅ PostgreSQL database (free tier)

### Option 2: **Railway**
- ✅ Free tier with $5 credit/month
- ✅ Easy deployment
- ✅ PostgreSQL support

### Option 3: **Fly.io**
- ✅ Free tier available
- ✅ Global edge deployment
- ✅ PostgreSQL support

---

## 📋 Pre-Deployment Checklist

Before deploying, you need to make some changes to your code:

### 1. Environment Variables
Create a `.env` file (or use platform environment variables) for:
- Database paths
- Secret keys
- API keys

### 2. Database Migration
- Current: SQLite (file-based)
- Production: PostgreSQL or MySQL (cloud database)

### 3. File Storage
- Resume files need cloud storage (AWS S3, Cloudinary, etc.)
- Or use platform's file system (temporary)

### 4. Static Files
- Ensure static files are properly configured

---

## 🚀 Option 1: Deploy to Render (Step-by-Step)

### Step 1: Prepare Your Code

1. **Create a `render.yaml` file** (optional but recommended):

```yaml
services:
  - type: web
    name: un-employed
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python -m app.ui
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: PORT
        value: 5001
```

2. **Create a `Procfile`** (for Render):

```
web: python -m app.ui
```

3. **Update `app/ui.py`** to use environment variables:

```python
import os
from pathlib import Path

# At the top of ui.py, add:
PORT = int(os.environ.get('PORT', 5001))
HOST = os.environ.get('HOST', '0.0.0.0')

# Update the run_ui function:
def run_ui(host=HOST, port=PORT, debug=False):
    """Run the Flask UI server."""
    logging.basicConfig(level=logging.INFO)
    logger.info(f"Starting un!mployed UI server on {host}:{port}")
    app.run(host=host, port=port, debug=debug)
```

4. **Create `runtime.txt`** (specify Python version):

```
python-3.11.0
```

### Step 2: Push to GitHub

1. Initialize git (if not already):
```bash
cd "/Users/wasifkarim/Desktop/Job Searching/job-pulse"
git init
git add .
git commit -m "Initial commit"
```

2. Create a GitHub repository:
   - Go to https://github.com/new
   - Create a new repository (e.g., "un-employed")
   - **Don't** initialize with README

3. Push your code:
```bash
git remote add origin https://github.com/YOUR_USERNAME/un-employed.git
git branch -M main
git push -u origin main
```

### Step 3: Deploy on Render

1. **Sign up for Render:**
   - Go to https://render.com
   - Sign up with GitHub (free)

2. **Create a New Web Service:**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select your repository

3. **Configure the Service:**
   - **Name:** `un-employed` (or any name)
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python -m app.ui`
   - **Plan:** Free

4. **Add Environment Variables:**
   - Click "Environment" tab
   - Add:
     - `PORT` = `5001`
     - `PYTHON_VERSION` = `3.11.0`
     - `FLASK_ENV` = `production`

5. **Deploy:**
   - Click "Create Web Service"
   - Wait for deployment (5-10 minutes)
   - Your app will be live at: `https://un-employed.onrender.com`

### Step 4: Set Up Database (PostgreSQL)

1. **Create PostgreSQL Database:**
   - In Render dashboard, click "New +" → "PostgreSQL"
   - Name: `un-employed-db`
   - Plan: Free
   - Click "Create"

2. **Get Database URL:**
   - Copy the "Internal Database URL"
   - Add as environment variable: `DATABASE_URL`

3. **Update Code for PostgreSQL:**
   - Install: `psycopg2-binary` in requirements.txt
   - Update database connection code

---

## 🚂 Option 2: Deploy to Railway

### Step 1: Prepare Code (Same as Render)

### Step 2: Deploy

1. **Sign up:** https://railway.app (use GitHub)

2. **New Project:**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository

3. **Configure:**
   - Railway auto-detects Python
   - Add environment variables:
     - `PORT` = `5001`
   
4. **Deploy:**
   - Railway auto-deploys
   - Get your URL: `https://your-app.railway.app`

---

## ✈️ Option 3: Deploy to Fly.io

### Step 1: Install Fly CLI

```bash
# macOS
curl -L https://fly.io/install.sh | sh

# Or download from: https://fly.io/docs/getting-started/installing-flyctl/
```

### Step 2: Create `fly.toml`

```bash
cd "/Users/wasifkarim/Desktop/Job Searching/job-pulse"
fly launch
```

Or create manually:

```toml
app = "un-employed"
primary_region = "iad"

[build]

[env]
  PORT = "5001"

[http_service]
  internal_port = 5001
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0
  processes = ["app"]

[[services]]
  http_checks = []
  internal_port = 5001
  processes = ["app"]
  protocol = "tcp"
  script_checks = []
```

### Step 3: Deploy

```bash
fly deploy
```

---

## 🔧 Required Code Changes

### 1. Update `app/ui.py` for Production

Add at the top:

```python
import os
from pathlib import Path

# Get port from environment or default
PORT = int(os.environ.get('PORT', 5001))
HOST = os.environ.get('HOST', '0.0.0.0')
```

Update `run_ui` function:

```python
def run_ui(host=None, port=None, debug=False):
    """Run the Flask UI server."""
    # Use environment variables in production
    host = host or HOST
    port = port or PORT
    debug = debug or (os.environ.get('FLASK_ENV') != 'production')
    
    logging.basicConfig(level=logging.INFO)
    logger.info(f"Starting un!mployed UI server on {host}:{port}")
    app.run(host=host, port=port, debug=debug)
```

### 2. Update Database Paths

In `app/ui.py`, change:

```python
# Instead of:
USER_DB_PATH = "./users.db"
ACTIVITY_DB_PATH = "./user_activity.db"

# Use:
USER_DB_PATH = os.environ.get('USER_DB_PATH', './users.db')
ACTIVITY_DB_PATH = os.environ.get('ACTIVITY_DB_PATH', './user_activity.db')
```

### 3. Update Resume Storage

For cloud storage, you'll need to:
- Use AWS S3, Cloudinary, or similar
- Or use platform's persistent storage

### 4. Add `.gitignore`

Create `.gitignore`:

```
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
.venv
*.db
*.sqlite
*.sqlite3
resumes/
.env
.DS_Store
*.log
```

---

## 📝 Quick Start Commands

### For Render:
```bash
# 1. Push to GitHub
git add .
git commit -m "Ready for deployment"
git push

# 2. Go to render.com and connect repo
# 3. Deploy!
```

### For Railway:
```bash
# 1. Push to GitHub
git push

# 2. Go to railway.app and connect repo
# 3. Deploy!
```

### For Fly.io:
```bash
# 1. Install CLI
# 2. Login
fly auth login

# 3. Launch
fly launch

# 4. Deploy
fly deploy
```

---

## 🎯 Recommended: Render (Easiest)

**Why Render?**
- ✅ Free tier
- ✅ Automatic HTTPS
- ✅ Easy GitHub integration
- ✅ PostgreSQL included
- ✅ No credit card required

**Steps:**
1. Push code to GitHub
2. Sign up at render.com
3. Connect GitHub repo
4. Click "Deploy"
5. Done! 🎉

---

## ⚠️ Important Notes

1. **Free tiers have limitations:**
   - Render: Spins down after 15 min inactivity (free tier)
   - Railway: $5 credit/month
   - Fly.io: Limited resources

2. **Database:**
   - SQLite won't work well in production
   - Use PostgreSQL (free on Render/Railway)

3. **File Storage:**
   - Resume files need cloud storage
   - Or use platform's file system (may be temporary)

4. **Environment Variables:**
   - Never commit `.env` files
   - Use platform's environment variable settings

---

## 🆘 Need Help?

- Render Docs: https://render.com/docs
- Railway Docs: https://docs.railway.app
- Fly.io Docs: https://fly.io/docs

---

## 🎉 After Deployment

Your app will be live at:
- Render: `https://your-app.onrender.com`
- Railway: `https://your-app.railway.app`
- Fly.io: `https://your-app.fly.dev`

Share the URL and start using your app! 🚀
