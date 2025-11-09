# 🛒 Grocery Super-App

A multi-platform grocery ordering application with React Native Expo frontend and FastAPI backend, using browser automation agents to manage carts across Instacart, UberEats, and more.

---

## 📋 Project Structure

```
HackPton_Delivery_App/
├── server/                     # FastAPI Backend
│   ├── main.py                 # Main API application
│   ├── models.py               # Pydantic models
│   ├── supabase_client.py      # Supabase integration
│   ├── gemini_service.py       # Gemini AI service
│   ├── agent_runner.py         # Agent orchestration
│   ├── ws_manager.py           # WebSocket manager
│   ├── requirements.txt        # Python dependencies
│   ├── .env.example            # Environment template
│   └── tests/                  # Backend tests
├── mobile/                     # React Native Expo Frontend
│   ├── src/                    # Source code
│   ├── package.json            # Node dependencies
│   └── .env.example            # Mobile env template
├── agents/                     # Browser automation agents
│   ├── search_and_add_agents/  # Shopping agents
│   ├── edit_cart_agent_nova.py # Cart editing
│   └── cart_detail_agent_nova.py # Cart details
├── venv/                       # Python virtual environment
├── IMPLEMENTATION_PLAN.md      # Detailed implementation plan
└── README.md                   # This file
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- Supabase account ([sign up](https://supabase.com))
- Gemini API key ([get key](https://aistudio.google.com/app/apikey))

### Setup

#### Windows
```bash
# Run the setup script
setup_project.bat

# Or manually:
python -m venv venv
venv\Scripts\activate
pip install -r server\requirements.txt
copy server\.env.example server\.env
# Edit server\.env with your credentials
```

#### Linux/Mac
```bash
# Run the setup script
chmod +x setup_project.sh
./setup_project.sh

# Or manually:
python3 -m venv venv
source venv/bin/activate
pip install -r server/requirements.txt
cp server/.env.example server/.env
# Edit server/.env with your credentials
```

---

## 🔧 Configuration

### 1. Supabase Setup
1. Create a new project at [supabase.com](https://supabase.com/dashboard)
2. Go to SQL Editor and run `server/supabase_schema.sql`
3. Get your API keys from Settings → API
4. Add to `server/.env`:
   ```
   SUPABASE_URL=https://xxxxx.supabase.co
   SUPABASE_SERVICE_ROLE_KEY=your-key-here
   SUPABASE_ANON_KEY=your-anon-key-here
   ```

### 2. Gemini AI Setup
1. Get API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Add to `server/.env`:
   ```
   GEMINI_API_KEY=your-gemini-key-here
   ```

### 3. Mobile App Setup (Coming Soon)
```bash
cd mobile
npm install
cp .env.example .env
# Edit mobile/.env with backend URL
```

---

## 🏃 Running the Application

### Backend Server
```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate  # Windows

# Start server
cd server
python -m uvicorn server.main:app --reload --host 0.0.0.0 --port 8000

# Server will be available at: http://localhost:8000
# API docs at: http://localhost:8000/docs
```

### Run Tests
```bash
# Activate venv first
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Run all tests
pytest server/tests/ -v

# Run specific test file
pytest server/tests/test_phase1_2.py -v

# Run with coverage
pytest server/tests/ --cov=server --cov-report=html

# Run manual test script
python server/test_api.py
```

### Mobile App (Coming Soon)
```bash
cd mobile
npm start
# or
npx expo start
```

---

## 📡 API Endpoints

### Health & Status
- `GET /` - Root endpoint
- `GET /health` - Health check

### Authentication
- `POST /auth/signup` - Create new user
- `POST /auth/signin` - Sign in existing user
- `GET /auth/me` - Get current user

### Recipe & Ingredients
- `POST /api/recipe` - Convert recipe query to ingredients

### Agent Orchestration
- `POST /api/start-agents` - Start shopping agents
- `GET /api/job/{job_id}/status` - Get agent job status

### Cart Management
- `GET /api/cart-status` - Get cart status for all platforms
- `POST /api/cart-diffs` - Save cart modifications
- `POST /api/apply-diffs` - Apply cart modifications

### Checkout
- `POST /api/checkout` - Process checkout and create transaction

### WebSocket
- `WS /ws/agent-progress` - Real-time agent progress updates

Full API documentation: http://localhost:8000/docs

---

## 🧪 Testing

### Phase-by-Phase Testing
The project follows a phased implementation with comprehensive test suites. See `IMPLEMENTATION_PLAN.md` for detailed testing procedures.

#### Current Test Coverage
- ✅ Phase 1.2: FastAPI Core Setup
- ✅ Phase 1.3: Authentication Endpoints  
- ✅ Phase 1.4: Gemini Recipe Service
- ⏳ Phase 2.1: Agent Runner
- ⏳ Phase 2.2: WebSocket Manager
- ⏳ Phase 2.3: Agent Orchestration

### Test Commands
```bash
# Backend unit tests
pytest server/tests/ -v

# Integration tests
python server/test_api.py

# Specific phase tests
pytest server/tests/test_phase1_*.py -v

# Mobile tests (coming soon)
cd mobile && npm test
```

---

## 🏗️ Architecture

### Backend (FastAPI + Python)
- **FastAPI**: Modern async web framework
- **Supabase**: PostgreSQL database + auth
- **Gemini AI**: Recipe to ingredients conversion
- **WebSockets**: Real-time agent progress updates
- **Browser Agents**: Nova Act for automated shopping

### Frontend (React Native + Expo)
- **Expo**: React Native development platform
- **React Navigation**: Screen navigation
- **Supabase JS**: Client-side auth
- **WebSocket**: Real-time updates from backend

### Data Flow
1. User enters recipe query
2. Gemini AI converts to ingredient list
3. User selects platforms (Instacart, UberEats)
4. Browser agents add items to carts
5. User reviews/modifies cart items
6. Checkout processes mock payment
7. Transaction stored in Supabase

---

## 📚 Documentation

- [Implementation Plan](IMPLEMENTATION_PLAN.md) - Detailed phased development plan
- [Supabase Setup](server/SUPABASE_SETUP.md) - Database setup guide
- [API Documentation](http://localhost:8000/docs) - Interactive API docs (when server running)

---

## 🛠️ Development

### Project Conventions
- Python code follows PEP 8
- Use type hints for Python
- TypeScript for mobile app
- Test every endpoint before moving forward
- Make progressive git commits (never push)

### Git Workflow
```bash
# Make changes
git add .
git commit -m "feat: description of changes"

# ⚠️ NEVER push to remote during development
# Only commit locally
```

---

## 🐛 Troubleshooting

### Server won't start
- Ensure virtual environment is activated
- Check `.env` file has all required variables
- Verify Supabase is accessible
- Check port 8000 is not in use

### Tests failing
- Verify server is running on http://localhost:8000
- Check Supabase connection
- Ensure test user credentials are valid
- Review logs in console

### Agent errors
- Check `GEMINI_API_KEY` is set
- Ensure Chrome/Chromium is installed
- Review agent logs in console
- Verify shopping list JSON format

---

## 📝 Todo List

See `IMPLEMENTATION_PLAN.md` for complete task breakdown.

### Backend
- [x] FastAPI core setup
- [x] Supabase integration
- [x] Auth endpoints
- [x] Recipe/ingredients endpoint
- [x] WebSocket manager
- [x] Agent runner
- [x] Cart management endpoints
- [x] Checkout endpoint

### Frontend
- [ ] Expo app scaffold
- [ ] Auth screens
- [ ] Navigation setup
- [ ] Recipe input screen
- [ ] Ingredients selection
- [ ] Agent progress screen
- [ ] Cart status screen
- [ ] Checkout screen

### Testing & Polish
- [ ] Complete E2E tests
- [ ] Error handling
- [ ] UI polish
- [ ] Documentation
- [ ] Deployment prep

---

## 👥 Contributors

- Backend: FastAPI + Supabase + Gemini
- Frontend: React Native + Expo
- Agents: Nova Act automation

---

## 📄 License

This project is for educational/demonstration purposes.

---

## 🙏 Acknowledgments

- [Supabase](https://supabase.com) - Backend as a Service
- [Google Gemini](https://ai.google.dev) - AI/ML API
- [Expo](https://expo.dev) - React Native platform
- [FastAPI](https://fastapi.tiangolo.com) - Web framework
- [Nova Act](https://www.novaact.ai) - Browser automation

---

**Made with ❤️ for hackathon**
