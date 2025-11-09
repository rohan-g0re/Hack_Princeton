# 🚀 Complete Setup Guide - Grocery Super-App

This guide will walk you through setting up the complete application from scratch.

---

## 📋 Prerequisites

- **Python 3.9+** installed
- **Node.js 18+** and npm installed
- **Supabase account** (free tier works)
- **Gemini API key** from Google AI Studio
- **Git** for version control
- **iOS Simulator** (Mac only) or **Android Emulator** or **Physical device**

---

## 🔧 Part 1: Backend Setup (FastAPI)

### Step 1: Create Supabase Project

1. Go to [supabase.com/dashboard](https://supabase.com/dashboard)
2. Click "New Project"
3. Fill in:
   - **Name**: `grocery-superapp`
   - **Database Password**: Choose a strong password
   - **Region**: Select closest to you
4. Wait for project creation (~2 minutes)

### Step 2: Apply Database Schema

1. In Supabase Dashboard, go to **SQL Editor**
2. Click "New Query"
3. Copy the entire contents of `server/supabase_schema.sql`
4. Paste and click "Run"
5. Verify tables created: Go to **Table Editor** and check for:
   - `user_sessions`
   - `cart_states`
   - `cart_diffs`
   - `transactions`

### Step 3: Get Supabase API Keys

1. Go to **Settings** → **API**
2. Copy these values:
   - **Project URL** (e.g., `https://xxxxx.supabase.co`)
   - **anon / public key** (for mobile app)
   - **service_role key** (for backend - keep secret!)

### Step 4: Get Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click "Create API key"
3. Copy the key

### Step 5: Configure Backend Environment

```bash
# Navigate to project root
cd D:\STUFF\Projects\HackPton_Delivery_App

# Create server/.env from template
copy server\.env.example server\.env

# Edit server/.env with your keys:
# - SUPABASE_URL=https://xxxxx.supabase.co
# - SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
# - SUPABASE_ANON_KEY=your-anon-key
# - GEMINI_API_KEY=your-gemini-key
```

### Step 6: Install Backend Dependencies

```bash
# Activate virtual environment (already created)
venv\Scripts\activate

# Install dependencies
pip install -r server\requirements.txt
```

### Step 7: Start Backend Server

```bash
# Make sure venv is activated
cd server
python -m uvicorn server.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
✅ Supabase initialized
✅ Gemini service initialized
✅ Agent runner initialized
✨ Server ready!
```

### Step 8: Test Backend

Open a new terminal and run:

```bash
# Test health endpoint
curl http://localhost:8000/health

# Should return: {"status":"healthy","services":{"supabase":true,...}}
```

Or visit: http://localhost:8000/docs for interactive API documentation

---

## 📱 Part 2: Mobile App Setup (Expo)

### Step 9: Install Mobile Dependencies

```bash
# Open new terminal, navigate to mobile folder
cd mobile

# Install dependencies
npm install
```

### Step 10: Configure Mobile Environment

```bash
# Find your local IP address:
# Windows: ipconfig (look for IPv4 Address)
# Mac/Linux: ifconfig (look for inet)
# Example: 192.168.1.100

# Create mobile/.env
copy .env.example .env

# Edit mobile/.env:
# API_BASE_URL=http://YOUR_LOCAL_IP:8000
# SUPABASE_URL=https://xxxxx.supabase.co
# SUPABASE_ANON_KEY=your-anon-public-key
```

**⚠️ IMPORTANT**: Use your machine's IP address, NOT `localhost` or `127.0.0.1`, because your phone/emulator is a different device!

### Step 11: Start Expo

```bash
# In mobile folder
npx expo start
```

You should see:
```
› Metro waiting on exp://192.168.1.100:8081
› Scan the QR code above with Expo Go (Android) or the Camera app (iOS)
```

### Step 12: Open App on Device

**Option A: Physical Device**
1. Install **Expo Go** app from App Store (iOS) or Play Store (Android)
2. Scan the QR code from terminal
3. App will load on your device

**Option B: iOS Simulator (Mac only)**
1. Press `i` in terminal
2. iOS Simulator will open with the app

**Option C: Android Emulator**
1. Start Android Emulator
2. Press `a` in terminal
3. App will load in emulator

---

## ✅ Part 3: Verification & Testing

### Test 1: Backend Health Check

```bash
# Should return 200 OK
curl http://localhost:8000/health
```

### Test 2: Mobile App Login

1. Open the app
2. Click "Sign Up"
3. Enter email, password, name
4. Click "Sign Up"
5. Should navigate to Home screen

### Test 3: Recipe Flow

1. Click "Start Shopping"
2. Enter "caesar salad"
3. Click "Get Ingredients"
4. Should see ingredient list
5. Select ingredients and platform (Instacart)
6. Click "Start Shopping"

**Expected**: Agent progress screen shows with WebSocket updates

**Note**: Agents require Chrome/Chromium and may take time. For quick testing, they might fail if not fully configured.

### Test 4: API Tests

```bash
# Activate venv
venv\Scripts\activate

# Run backend tests
pytest server/tests/ -v

# Or run manual test script
python server/test_api.py
```

---

## 🔍 Troubleshooting

### Backend Issues

**Problem**: Server won't start
```bash
# Solution: Check if port 8000 is in use
netstat -ano | findstr :8000

# Kill process if needed
taskkill /PID <process_id> /F

# Or use different port
python -m uvicorn server.main:app --reload --port 8001
```

**Problem**: Supabase connection error
- Verify `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are correct
- Check if Supabase project is active
- Test connection in Supabase dashboard

**Problem**: Gemini API error
- Verify `GEMINI_API_KEY` is valid
- Check API quota at [Google AI Studio](https://aistudio.google.com/)

### Mobile Issues

**Problem**: Can't connect to backend
```bash
# 1. Verify backend is running on http://0.0.0.0:8000
# 2. Find your IP address:
ipconfig  # Windows
ifconfig  # Mac/Linux

# 3. Update mobile/.env with correct IP:
API_BASE_URL=http://YOUR_IP:8000

# 4. Restart Expo
npx expo start --clear
```

**Problem**: Module not found errors
```bash
# Clear cache and reinstall
cd mobile
rm -rf node_modules
npm install
npx expo start --clear
```

**Problem**: TypeScript errors
```bash
# Run type check
npx tsc --noEmit

# Fix any type errors shown
```

### Agent Issues

**Problem**: Agents fail to start
- Ensure Chrome/Chromium is installed
- Check `GEMINI_API_KEY` for weight estimation
- Verify shopping list JSON format
- Check agent logs in console

---

## 📊 Project Structure Summary

```
HackPton_Delivery_App/
├── server/                 # FastAPI Backend
│   ├── main.py            # ✅ Main API app
│   ├── models.py          # ✅ Pydantic models
│   ├── supabase_client.py # ✅ DB client
│   ├── gemini_service.py  # ✅ AI service
│   ├── agent_runner.py    # ✅ Agent orchestration
│   ├── ws_manager.py      # ✅ WebSocket manager
│   ├── .env               # 🔧 Your credentials
│   └── tests/             # ✅ Test suites
│
├── mobile/                # Expo Mobile App
│   ├── App.tsx            # ✅ Root component
│   ├── src/
│   │   ├── screens/       # ✅ All screens
│   │   ├── services/      # ✅ API & WebSocket
│   │   ├── context/       # ✅ Auth context
│   │   ├── navigation/    # ✅ Navigation
│   │   └── config/        # ✅ Configuration
│   ├── .env               # 🔧 Your config
│   └── package.json       # ✅ Dependencies
│
├── agents/                # Browser Automation
│   └── search_and_add_agents/
│       ├── instacart.py   # ✅ Instacart agent
│       └── ubereats.py    # ✅ UberEats agent
│
├── venv/                  # Python virtual environment
├── README.md              # ✅ Project overview
├── IMPLEMENTATION_PLAN.md # ✅ Detailed plan
└── SETUP_GUIDE.md         # ✅ This file
```

---

## 🎯 Quick Start Commands

### Terminal 1: Backend
```bash
venv\Scripts\activate
cd server
python -m uvicorn server.main:app --reload --host 0.0.0.0 --port 8000
```

### Terminal 2: Mobile
```bash
cd mobile
npx expo start
```

### Terminal 3: Tests (Optional)
```bash
venv\Scripts\activate
pytest server/tests/ -v
```

---

## 🎉 Next Steps

1. **Test the Complete Flow**:
   - Sign up → Enter recipe → Select ingredients → Start agents → View carts → Checkout

2. **Explore the API**:
   - Visit http://localhost:8000/docs for interactive API documentation
   - Test endpoints with Postman or curl

3. **Customize**:
   - Add more platforms (DoorDash, etc.)
   - Enhance UI with custom themes
   - Add more recipe categories

4. **Deploy** (Future):
   - Backend: Deploy to Heroku, AWS, or DigitalOcean
   - Mobile: Build with EAS and publish to App Stores

---

## 📞 Support

If you encounter issues:
1. Check this guide's Troubleshooting section
2. Review `IMPLEMENTATION_PLAN.md` for detailed specs
3. Check logs in terminal for error messages
4. Verify all environment variables are set correctly

---

**Happy Coding! 🚀**

