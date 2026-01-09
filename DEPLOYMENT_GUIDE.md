# 🚀 Free Hosting Guide for PDF Tools

## Best Free Hosting Options

### 1. **Render** (Recommended ⭐)
- **Cost**: Free tier available
- **Features**: Auto-deploy from GitHub, 750 free compute hours/month
- **Best for**: Easy deployment, automatic updates
- **URL**: https://render.com

**Steps:**
1. Push your code to GitHub
2. Sign up at render.com with GitHub
3. Create new "Web Service"
4. Connect your GitHub repository
5. Set build command: `pip install -r requirements.txt`
6. Set start command: `gunicorn main:app`
7. Deploy!

---

### 2. **Railway** 
- **Cost**: $5/month free credits (usually lasts 1-2 months)
- **Features**: Simple deployment, good dashboard
- **Best for**: Quick setup, reliable service
- **URL**: https://railway.app

**Steps:**
1. Push code to GitHub
2. Sign up at railway.app
3. Import from GitHub
4. Connect repository
5. Add Python environment
6. Railway auto-detects Procfile
7. Deploy!

---

### 3. **PythonAnywhere**
- **Cost**: Free tier available
- **Features**: Dedicated Python hosting
- **Best for**: Simple Python apps
- **URL**: https://www.pythonanywhere.com

**Steps:**
1. Sign up at pythonanywhere.com
2. Upload your files via their web console
3. Create a new web app
4. Configure to use Flask
5. Set up virtual environment
6. Deploy!

---

### 4. **Replit**
- **Cost**: Free with limitations
- **Features**: Online IDE + hosting
- **Best for**: Quick testing
- **URL**: https://replit.com

**Steps:**
1. Create new Replit project
2. Import from GitHub
3. Run button starts server
4. Share public link
5. Deploy!

---

## 📋 Prerequisites

1. **GitHub Account** (for Render/Railway/Replit)
2. **Git installed** locally
3. **Deployment files** (already created):
   - `Procfile` - Tells hosting service how to run app
   - `runtime.txt` - Specifies Python version
   - `requirements.txt` - Python dependencies

---

## Step-by-Step: Deploy to Render (Easiest)

### Step 1: Create GitHub Repository
```bash
cd /workspaces/mergesplitPDF
git init
git add .
git commit -m "Initial commit: PDF Tools with Advanced Frontend"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/mergesplitPDF.git
git push -u origin main
```

### Step 2: Deploy to Render
1. Go to https://render.com
2. Click "New +" → "Web Service"
3. Connect GitHub account
4. Search for "mergesplitPDF" repository
5. Select it and click "Connect"

### Step 3: Configure Render
- **Name**: `pdf-tools` (or any name)
- **Runtime**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn main:app`
- **Free Plan**: Select free tier

### Step 4: Deploy
Click "Create Web Service" and wait for deployment (2-5 minutes)

Your app will be live at: `https://pdf-tools-xxxx.onrender.com`

---

## Important Notes for Free Hosting

⚠️ **Limitations to be aware of:**

1. **Render Free Tier**:
   - 750 compute hours/month (~31 hours/day average)
   - Spins down after 15 min inactivity (slow first load)
   - Good for small-medium usage

2. **Railway Free Tier**:
   - $5/month credit
   - Runs continuously (no spin-down)
   - Better for active apps

3. **PythonAnywhere Free Tier**:
   - 3-month validity, limited usage
   - Simple to set up
   - Good for learning

---

## Environment Variables (if needed)

Create `.env` file locally:
```
FLASK_ENV=production
```

For Render/Railway, add in dashboard under "Environment Variables"

---

## Troubleshooting

### "Module not found" error
- Ensure `requirements.txt` has all dependencies
- Check Python version compatibility

### "Connection timeout"
- Free tier might spin down after inactivity
- Railway doesn't spin down, use that if you need 24/7

### "File upload fails"
- Check MAX_CONTENT_LENGTH in main.py (currently 200MB)
- Reduce if hosting has storage limits

---

## Recommended Setup

**For Best Results**: Use **Render** or **Railway**
- Both are reliable
- Easy GitHub integration
- Good free tiers
- Good documentation

**Quick Comparison:**
| Feature | Render | Railway | PythonAnywhere |
|---------|--------|---------|---|
| Free Tier | ✅ Yes | ✅ $5 credit | ✅ Limited |
| Ease | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| Always On | ❌ (spins down) | ✅ | ✅ |
| Speed | Medium | Fast | Medium |

---

## After Deployment

1. **Test your app** - Visit the public URL
2. **Test merge feature** - Upload 2+ PDFs
3. **Test split feature** - Upload 1 PDF
4. **Share with friends** - Your PDF tools are live! 🎉

---

## Need Help?

- **Render Docs**: https://docs.render.com
- **Railway Docs**: https://docs.railway.app
- **PythonAnywhere Help**: https://help.pythonanywhere.com

Good luck! 🚀
