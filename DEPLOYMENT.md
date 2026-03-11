# Deployment Guide

Complete instructions to deploy your AI BI Data Analyst to production using GitHub, Vercel, and Render.

---

## 📋 Pre-Deployment Checklist

- [ ] GitHub account created (https://github.com)
- [ ] Vercel account created (https://vercel.com) - sign in with GitHub
- [ ] Render account created (https://render.com) - sign in with GitHub
- [ ] Neon PostgreSQL database created (https://neon.tech)
- [ ] OpenAI API key obtained (https://platform.openai.com/api-keys)

---

## 🚀 Step 1: Push to GitHub

### 1a. Create GitHub Repository

1. Go to https://github.com/new
2. Create repository name: `bi-analytics-bot`
3. Choose "Public" (for portfolio) or "Private"
4. Skip "Add .gitignore" (already created)
5. Skip "Add a license" (MIT is in repo)
6. Click "Create repository"

You'll see instructions. Copy the commands below.

### 1b. Initialize & Push Code

```bash
cd /Users/juma/Desktop/job/bi-analytics-bot

# Initialize git
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: AI BI Data Analyst platform with production-grade ETL, Next.js frontend, and FastAPI backend"

# Add remote (replace YOUR-USERNAME)
git remote add origin https://github.com/YOUR-USERNAME/bi-analytics-bot.git

# Rename branch to main
git branch -M main

# Push to GitHub
git push -u origin main
```

---

## 🌐 Step 2: Deploy Frontend to Vercel

### 2a. Create Vercel Project

1. Go to https://vercel.com/dashboard
2. Click "Add New" → "Project"
3. Select "Import Git Repository"
4. Search and select "bi-analytics-bot"
5. Click "Import"

### 2b. Configure Project

**Build Settings**:
- Framework: Next.js (auto-detected)
- Root Directory: `./frontend`
- Build Command: `npm run build`
- Output Directory: `.next`
- Install Command: `npm install`

**Environment Variables**:
```
NEXT_PUBLIC_API_URL = https://bi-analytics-bot-api.onrender.com
```

### 2c. Deploy

Click "Deploy" - build takes 2-3 minutes.

Frontend URL: https://bi-analytics-bot.vercel.app

---

## ⚙️ Step 3: Deploy Backend to Render

### 3a. Create Render Service

1. Go to https://dashboard.render.com
2. Click "New" → "Web Service"
3. Connect GitHub and select repository
4. Search for "bi-analytics-bot"

### 3b. Configure Web Service

| Field | Value |
|-------|-------|
| **Name** | `bi-analytics-bot-api` |
| **Environment** | `Python 3` |
| **Build Command** | `cd backend && pip install -q uv && uv sync` |
| **Start Command** | `cd backend && uvicorn app.main:app --host 0.0.0.0 --port 10000` |

### 3c. Add Environment Variables

Click "Advanced" → "Environment Variables"

```
NEON_DATABASE_URL = postgresql+psycopg://user:password@host/dbname
OPENAI_API_KEY = sk-your-openai-key-here
```

### 3d. Deploy

Click "Create Web Service" - deployment takes 5-10 minutes.

Backend URL: https://bi-analytics-bot-api.onrender.com

---

## ✅ Verify Deployment Works

### Test Health Check
```bash
curl https://bi-analytics-bot-api.onrender.com/health
# Should return: {"status":"ok","service":"AI BI Data Analyst"}
```

### Test Frontend
1. Visit https://bi-analytics-bot.vercel.app
2. Try uploading a CSV file
3. Try asking a question in chat

---

## 🔄 Auto-Deploy Setup

With GitHub + Vercel + Render connected:

```bash
# To deploy new version, just push:
git add .
git commit -m "Your changes"
git push origin main

# Vercel and Render will auto-deploy!
```

---

## 📊 Live URLs After Deployment

```
Frontend:  https://bi-analytics-bot.vercel.app
Backend:   https://bi-analytics-bot-api.onrender.com
```

Share these URLs in your portfolio!

