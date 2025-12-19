# 🚀 Quick Deployment Guide - Render (5 Minutes)

## Step 1: Push to GitHub (2 min)

```bash
cd "/Users/wasifkarim/Desktop/Job Searching/job-pulse"

# Initialize git (if not already done)
git init
git add .
git commit -m "Ready for deployment"

# Connect to your GitHub repository:
git remote add origin https://github.com/Wasif-Karim03/waste-of-time.git
git branch -M main
git push -u origin main
```

## Step 2: Deploy on Render (3 min)

1. **Go to:** https://render.com
2. **Sign up** with GitHub (free)
3. **Click:** "New +" → "Web Service"
4. **Connect** your GitHub repository
5. **Configure:**
   - **Name:** `un-employed`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python -m app.ui`
   - **Plan:** Free
6. **Add Environment Variables:**
   - `PORT` = `5001`
   - `FLASK_ENV` = `production`
   - `FLASK_SECRET_KEY` = (generate a random string)
7. **Click:** "Create Web Service"
8. **Wait** 5-10 minutes for deployment

## ✅ Done!

Your app will be live at: `https://un-employed.onrender.com`

---

## 🔧 Optional: Add PostgreSQL Database

1. In Render dashboard: "New +" → "PostgreSQL"
2. Name: `un-employed-db`
3. Plan: Free
4. Copy the "Internal Database URL"
5. Add environment variable: `DATABASE_URL`

---

## ⚠️ Important Notes

- **Free tier spins down** after 15 min of inactivity (first request will be slow)
- **Database:** SQLite works for testing, but PostgreSQL is better for production
- **Resume files:** May need cloud storage (AWS S3, Cloudinary) for production

---

## 🆘 Troubleshooting

**Build fails?**
- Check that `requirements.txt` has all dependencies
- Check Python version in `runtime.txt`

**App won't start?**
- Check logs in Render dashboard
- Verify `PORT` environment variable is set
- Verify start command: `python -m app.ui`

**Database errors?**
- Make sure database paths are correct
- For production, use PostgreSQL instead of SQLite

---

## 📚 Full Guide

See `DEPLOYMENT_GUIDE.md` for detailed instructions and other hosting options.
