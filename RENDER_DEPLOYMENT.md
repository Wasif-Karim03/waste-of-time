# 🚀 Step-by-Step Render Deployment Guide

This guide will walk you through deploying your job-pulse application to Render.

## 📋 Prerequisites

- ✅ GitHub account
- ✅ Code already pushed to GitHub (https://github.com/Wasif-Karim03/waste-of-time.git)
- ✅ Render account (we'll create this)

---

## Step 1: Verify Your Code is Ready (2 minutes)

### 1.1 Check that all files are committed

```bash
cd /Users/wasifkarim/Desktop/unimployed
git status
```

If you see uncommitted changes, commit them:

```bash
git add .
git commit -m "Prepare for Render deployment"
git push
```

### 1.2 Verify deployment files exist

Make sure these files exist:
- ✅ `Procfile` (at root) - tells Render how to start your app
- ✅ `runtime.txt` (at root) - specifies Python version
- ✅ `job-pulse/requirements.txt` - Python dependencies

---

## Step 2: Sign Up for Render (1 minute)

1. **Go to:** https://render.com
2. **Click:** "Get Started for Free" or "Sign Up"
3. **Choose:** "Sign up with GitHub" (recommended - easiest)
4. **Authorize:** Render to access your GitHub repositories
5. **Complete:** Your profile setup

---

## Step 3: Create a New Web Service (3 minutes)

### 3.1 Start the deployment

1. In Render dashboard, click **"New +"** button (top right)
2. Select **"Web Service"**
3. You'll see "Connect a repository" - click **"Connect account"** if needed
4. Select your repository: **`waste-of-time`** (or `Wasif-Karim03/waste-of-time`)

### 3.2 Configure the service

Fill in the following settings:

| Setting | Value |
|---------|-------|
| **Name** | `un-employed` (or any name you like) |
| **Region** | Choose closest to you (e.g., `Oregon (US West)`) |
| **Branch** | `main` |
| **Root Directory** | `job-pulse` ⚠️ **IMPORTANT!** (Leave empty if using root Procfile) |
| **Environment** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `python -m app.ui` |
| **Plan** | `Free` |

**Key Points:**
- **Root Directory:** Set to `job-pulse` because your app code is in that subdirectory
- **Build Command:** Installs Python dependencies
- **Start Command:** Runs your Flask app

### 3.3 Add Environment Variables

Click on **"Advanced"** → **"Add Environment Variable"** and add these:

| Key | Value | Notes |
|-----|-------|-------|
| `PORT` | `5001` | Render will set this automatically, but we specify it |
| `FLASK_ENV` | `production` | Disables debug mode |
| `FLASK_SECRET_KEY` | `[Generate random string]` | See below |
| `PYTHON_VERSION` | `3.11.0` | Matches runtime.txt |

**Generate FLASK_SECRET_KEY:**
Run this command in your terminal:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```
Copy the output and use it as the value for `FLASK_SECRET_KEY`.

**Optional Environment Variables** (add if you need them):
- `SQLITE_PATH` = `./jobs.db`
- `MAX_AGE_HOURS` = `24`
- `USER_DB_PATH` = `./users.db`
- `ACTIVITY_DB_PATH` = `./user_activity.db`
- `LINKEDIN_RSS_URLS` = `your,comma,separated,urls`
- `INDEED_RSS_URLS` = `your,comma,separated,urls`
- `GREENHOUSE_BOARDS` = `company1,company2` (or use companies.yaml)
- `LEVER_COMPANIES` = `company1,company2`
- `GOOGLE_SHEET_ID` = `your-google-sheet-id` (if using Google Sheets)
- `GOOGLE_SERVICE_ACCOUNT_JSON` = `path/to/credentials.json` (if using Google Sheets)

### 3.4 Create the service

1. Review all settings
2. Click **"Create Web Service"**
3. Render will start building your application

---

## Step 4: Monitor the Deployment (5-10 minutes)

### 4.1 Watch the build logs

- You'll see build logs in real-time
- The build process will:
  1. Install Python 3.11.0
  2. Install dependencies from `requirements.txt`
  3. Start your Flask application

### 4.2 Common build issues and fixes

**Issue: "Module not found"**
- **Fix:** Check `requirements.txt` has all dependencies

**Issue: "Port already in use"**
- **Fix:** Make sure `PORT` environment variable is set

**Issue: "Cannot find app.ui"**
- **Fix:** Verify Root Directory is set to `job-pulse`

**Issue: "Database error"**
- **Fix:** SQLite files may not persist. Consider PostgreSQL (see Step 5)

### 4.3 Deployment success

When deployment succeeds, you'll see:
- ✅ "Your service is live"
- Your app URL: `https://un-employed.onrender.com` (or your chosen name)

---

## Step 5: (Optional) Set Up PostgreSQL Database

SQLite files may not persist on Render's free tier. For production, use PostgreSQL.

### 5.1 Create PostgreSQL database

1. In Render dashboard, click **"New +"** → **"PostgreSQL"**
2. Configure:
   - **Name:** `un-employed-db`
   - **Database:** `unemployed` (auto-generated)
   - **User:** `unemployed_user` (auto-generated)
   - **Region:** Same as your web service
   - **Plan:** `Free`
3. Click **"Create Database"**

### 5.2 Get database connection string

1. Click on your database
2. Find **"Internal Database URL"** (looks like: `postgresql://user:pass@host:5432/dbname`)
3. Copy this URL

### 5.3 Add to environment variables

1. Go back to your web service
2. **Environment** tab → **Add Environment Variable**
3. Key: `DATABASE_URL`
4. Value: Paste the Internal Database URL
5. Save

### 5.4 Update code (if needed)

Your code currently uses SQLite. To use PostgreSQL, you'd need to:
- Install `psycopg2-binary` in requirements.txt
- Update database connection code to use `DATABASE_URL`

**Note:** For now, SQLite will work for testing, but data may not persist between deployments.

---

## Step 6: Test Your Deployment

### 6.1 Visit your app

1. Open: `https://un-employed.onrender.com` (or your app URL)
2. You should see the landing page

### 6.2 Test features

- ✅ Landing page loads
- ✅ Sign up / Login works
- ✅ Job search works
- ✅ CSV export works

### 6.3 Check logs

If something doesn't work:
1. Go to Render dashboard
2. Click on your service
3. Click **"Logs"** tab
4. Look for error messages

---

## Step 7: Configure Custom Domain (Optional)

1. In your service settings, go to **"Custom Domains"**
2. Click **"Add Custom Domain"**
3. Enter your domain name
4. Follow DNS configuration instructions

---

## 🎉 Success! Your App is Live

Your application is now deployed at: `https://un-employed.onrender.com`

---

## 📝 Important Notes

### Free Tier Limitations

1. **Spins down after 15 minutes of inactivity**
   - First request after spin-down takes ~30 seconds
   - Subsequent requests are fast
   - Consider upgrading to paid plan for always-on

2. **Limited resources**
   - 512 MB RAM
   - 0.1 CPU
   - May be slow under heavy load

3. **Database**
   - SQLite files may not persist
   - Use PostgreSQL for production data

### Updating Your App

Whenever you push to GitHub:
1. Render automatically detects changes
2. Triggers a new deployment
3. Your app updates automatically

To manually deploy:
1. Go to Render dashboard
2. Click **"Manual Deploy"** → **"Deploy latest commit"**

---

## 🆘 Troubleshooting

### App won't start

1. **Check logs:**
   - Render dashboard → Your service → Logs tab
   - Look for error messages

2. **Common fixes:**
   - Verify `PORT` environment variable is set
   - Check Root Directory is `job-pulse`
   - Verify `requirements.txt` has all dependencies
   - Check Python version matches `runtime.txt`

### Database errors

1. **SQLite issues:**
   - SQLite files may not persist on free tier
   - Use PostgreSQL instead (see Step 5)

2. **Connection errors:**
   - Verify database URL is correct
   - Check database is running in Render dashboard

### Build fails

1. **Check requirements.txt:**
   ```bash
   # Make sure all dependencies are listed
   pip freeze > requirements.txt
   ```

2. **Check Python version:**
   - Verify `runtime.txt` has correct version
   - Render supports Python 3.7+

### App is slow

1. **First request slow:**
   - Normal on free tier (spins down after inactivity)
   - Consider upgrading to paid plan

2. **Always slow:**
   - Check logs for errors
   - Verify database connections
   - Check resource usage in dashboard

---

## 📚 Additional Resources

- **Render Docs:** https://render.com/docs
- **Flask Deployment:** https://flask.palletsprojects.com/en/latest/deploying/
- **Your App Logs:** Render dashboard → Your service → Logs

---

## ✅ Deployment Checklist

Before going live, make sure:

- [ ] Code is pushed to GitHub
- [ ] Procfile exists at root
- [ ] runtime.txt exists at root
- [ ] requirements.txt has all dependencies
- [ ] Environment variables are set
- [ ] FLASK_SECRET_KEY is set (not default)
- [ ] Root Directory is set to `job-pulse`
- [ ] Build command is correct
- [ ] Start command is correct
- [ ] App builds successfully
- [ ] App starts successfully
- [ ] Landing page loads
- [ ] Can sign up / login
- [ ] Job search works

---

**Need help?** Check the logs in Render dashboard or refer to Render documentation.

