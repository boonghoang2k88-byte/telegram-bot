# 🤖 AntiScamBot - Telegram Bot

A community-driven bot for checking and reporting Crypto/OTC scams.

## 🚀 Features

✅ **Check Scammers**: Search by Telegram username, link, or Binance ID  
✅ **Report Scammers**: 5-step reporting process  
✅ **Community Statistics**: Real-time scam data  
✅ **Safety Tips**: Crypto trading safety guide  
✅ **Trusted Groups**: Verified community groups  
✅ **No Admin Approval**: Reports recorded immediately  
✅ **Rate Limiting**: 3 reports/day/user  
✅ **Multi-language**: English & Vietnamese  

## 📦 Deployment on Render

### 1. Fork/Clone this repository

### 2. Create new Web Service on Render

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure:
   - **Name**: `anticam-bot` (or any name)
   - **Environment**: `Python 3`
   - **Region**: `Singapore` (or closest to you)
   - **Branch**: `main`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`

### 3. Set Environment Variables

Add these environment variables on Render:

| Key | Value |
|-----|-------|
| `TOKEN` | Your bot token from @BotFather |

### 4. Deploy

Click **"Create Web Service"** and wait for deployment.

## 🔧 Local Development

```bash
# 1. Clone repository
git clone https://github.com/yourusername/anticam-bot.git
cd anticam-bot

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env file
echo "TOKEN=your_bot_token_here" > .env

# 4. Run bot
python main.py