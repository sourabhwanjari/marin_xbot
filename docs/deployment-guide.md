# MARINEX AI — Production Deployment Guide

## Overview
This guide covers deploying **MARINEX AI** to production:
- **Frontend**: Deployed to [Vercel](https://vercel.com) (Next.js 14 App Router)
- **Backend**: Deployed to [Render](https://render.com) or [Railway](https://railway.app) (FastAPI + LangGraph + Uvicorn)

---

## Part 1: Deploying the Frontend on Vercel

### Option A: Via Vercel Web Dashboard (Recommended)

1. **Connect GitHub**:
   - Go to [vercel.com](https://vercel.com) and log in.
   - Click **"Add New..."** $\rightarrow$ **"Project"**.
   - Select repository: **`sourabhwanjari/marin_xbot`**.

2. **Project Settings**:
   - **Framework Preset**: `Next.js` (auto-detected).
   - **Root Directory**: Set to `frontend` (Click "Edit" and choose `frontend`).
   - **Build Command**: `npm run build` (default).
   - **Output Directory**: `.next` (default).
   - **Install Command**: `npm install` (default).

3. **Environment Variables**:
   Add the following under **Settings $\rightarrow$ Environment Variables**:

   | Variable | Value | Description |
   |---|---|---|
   | `NEXT_PUBLIC_API_URL` | `https://<your-backend-domain>/api` | URL of your deployed FastAPI backend |
   | `NEXT_PUBLIC_DEMO_MODE` | `false` | `false` for live data, `true` for demo fallback |

4. **Deploy**:
   - Click **Deploy**.
   - Your frontend will be live at `https://marin-xbot.vercel.app` (or custom Vercel domain).

---

### Option B: Via Vercel CLI

From the project root:
```bash
# Authorize CLI
npx vercel login

# Deploy frontend
cd frontend
npx vercel --prod
```

---

## Part 2: Deploying the Backend (FastAPI + LangGraph)

### Option A: Render (1-Click Blueprint)

1. Go to [render.com](https://render.com) and sign in with GitHub.
2. Click **"New +"** $\rightarrow$ **"Blueprint"**.
3. Select `sourabhwanjari/marin_xbot`. Render will automatically detect `render.yaml`.
4. Set the secret environment variable:
   - `LLM_API_KEY`: Your Gemini/OpenAI API key.
5. Click **"Apply"**.
6. Render will build and deploy the service. Once ready, copy your backend URL:
   `https://marinex-ai-backend.onrender.com`
7. Update `NEXT_PUBLIC_API_URL` on Vercel to:
   `https://marinex-ai-backend.onrender.com/api`

---

### Option B: Railway

1. Go to [railway.app](https://railway.app) and sign in with GitHub.
2. Click **"New Project"** $\rightarrow$ **"Deploy from GitHub repo"**.
3. Select `sourabhwanjari/marin_xbot`.
4. In Railway Settings:
   - **Root Directory**: `backend`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Under Variables, add:
   - `PORT`: `8000`
   - `ENVIRONMENT`: `production`
   - `LLM_API_KEY`: Your Gemini/OpenAI API key
   - `CORS_ORIGINS`: `https://marin-xbot.vercel.app,http://localhost:3000`
6. Click **Deploy**. Railway will provide a public HTTPS URL.

---

## Part 3: Verifying Full End-to-End Communication

1. **Backend Health Check**:
   ```bash
   curl https://<your-backend-domain>/api/health
   ```
   Expected response:
   ```json
   {
     "status": "ok",
     "service": "MARINEX AI",
     "phase": "Phase 4 - Real Marine Data Integration + Geo-spatial Intelligence Active"
   }
   ```

2. **Frontend Map & Data Feeds**:
   - Open your Vercel URL in any browser.
   - Click the **Data Feeds** popover: Weather and Ocean should display `LIVE`.
   - Toggle **PFZ Zones**, **Restricted Zones**, and **Hazards** on the Leaflet map.

3. **Multi-Agent Decision Query**:
   - Send: *"Is it safe to go fishing tomorrow morning near Mumbai?"*
   - Verify:
     - Planner decomposes task.
     - Weather & Ocean agents fetch live Open-Meteo feeds.
     - Risk Assessment agent assigns risk badge (`LOW`, `MEDIUM`, or `HIGH`).
     - Response cites conditions and regulatory recommendations.
