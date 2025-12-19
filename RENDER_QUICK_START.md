# 🚀 Quick Start: Deploy to Render (10 Minutes)

## Step 1: Push Code to GitHub ✅

Your code is already on GitHub at: `https://github.com/Wasif-Karim03/waste-of-time.git`

If you have uncommitted changes:
```bash
cd /Users/wasifkarim/Desktop/unimployed
git add .
git commit -m "Ready for Render deployment"
git push
```

## Step 2: Sign Up for Render (1 min)

1. Go to: **https://render.com**
2. Click: **"Get Started for Free"**
3. Choose: **"Sign up with GitHub"**
4. Authorize Render to access your repositories

## Step 3: Create Web Service (5 min)

1. In Render dashboard, click **"New +"** → **"Web Service"**
2. Connect repository: **`waste-of-time`**
3. Configure:

   **Basic Settings:**
   - **Name:** `un-employed` (or any name)
   - **Region:** Choose closest (e.g., `Oregon`)
   - **Branch:** `main`
   - **Root Directory:** `job-pulse` ⚠️ **IMPORTANT!**
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python -m app.ui`
   - **Plan:** `Free`

4. **Add Environment Variables:**
   
   Click "Advanced" → Add these variables:

   | Key | Value |
   |-----|-------|
   | `PORT` | `5001` |
   | `FLASK_ENV` | `production` |
   | `FLASK_SECRET_KEY` | `dd08018ed4e671c89a07d70fbac260d463085fa1d229afe947b1733dadfc5215` |
   | `PYTHON_VERSION` | `3.11.0` |

5. Click **"Create Web Service"**

## Step 4: Wait for Deployment (5-10 min)

- Watch the build logs
- Wait for "Your service is live" message
- Your app will be at: `https://un-employed.onrender.com`

## ✅ Done!

Visit your app and test it!

---

## 🔧 Optional: Add More Environment Variables

If you want to configure job sources, add these in Render dashboard → Environment:

- `LINKEDIN_RSS_URLS` = `url1,url2,url3`
- `INDEED_RSS_URLS` = `url1,url2`
- `GREENHOUSE_BOARDS` = `company1,company2` (or use companies.yaml)
- `LEVER_COMPANIES` = `company1,company2`
- `MAX_AGE_HOURS` = `24`
- `SQLITE_PATH` = `./jobs.db`
- `USER_DB_PATH` = `./users.db`
- `ACTIVITY_DB_PATH` = `./user_activity.db`

---

## ⚠️ Important Notes

1. **Free tier spins down** after 15 min inactivity (first request will be slow ~30s)
2. **SQLite databases** may not persist - use PostgreSQL for production
3. **Resume uploads** may need cloud storage (AWS S3) for production

---

## 🆘 Troubleshooting

**Build fails?**
- Check Root Directory is set to `job-pulse`
- Verify `requirements.txt` exists in `job-pulse/`
- Check logs in Render dashboard

**App won't start?**
- Verify `PORT` environment variable is set
- Check Start Command is: `python -m app.ui`
- Look at logs for error messages

**Need help?**
- See full guide: `RENDER_DEPLOYMENT.md`
- Check Render logs in dashboard
- Render docs: https://render.com/docs

