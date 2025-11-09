<div align="center">
  <img src="./assets/logo.jpeg" alt="MealPilot Logo" width="200"/>
  
  # 🥘 MealPilot: AutoCart
  
  **Compare grocery costs accross popular platforms to save time and money.**

  ## [Youtube Video - Link](https://www.youtube.com/watch?v=Ezjk6Yx-GTk)
  
</div>

MealPilot is an intelligent grocery comparison platform that helps you find the best prices groceries across multiple delivery platforms. Simply enter your recipe or ingredients, and we'll automatically compare prices across Amazon, Instacart, and Uber Eats.

---

## ✨ Features

- 🔍 **Smart Recipe Search** - Enter any recipe name and get instant ingredient lists
- 📊 **Multi-Platform Price Comparison** - Compare prices across Instacart, Uber Eats, and more
- 💰 **Instant Savings Calculator** - See exactly how much you save by choosing the best deal
- 📦 **Order History** - Track all your past orders with detailed receipts
- 🎨 **Beautiful UI** - Clean, modern design with intuitive navigation
- ⚡ **Real-Time Updates** - Live price comparison updates as you shop

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+** for backend
- **Node.js 18+** for frontend
- **Supabase Account** for database

### Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Visit **http://localhost:3001** to start comparing prices!

---

## 🏗️ Tech Stack

### Frontend
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling
- **Custom Design System** - MealPilot brand colors and components

### Backend
- **Amazon Nova Act** - Web Automation Agents
- **Gemini API** - AI-powered recipe parsing
- **Supabase** - Database and authentication
- **Knot API** - E-commerce integration
- **FastAPI** - Modern Python web framework

---

## 📱 How It Works

### 1️⃣ Search for Recipe
Enter any recipe name (e.g., "Spaghetti Carbonara" or "Veggie Pizza")

### 2️⃣ Review Ingredients
AI extracts and lists all required ingredients with quantities

### 3️⃣ Compare Prices
Our automation searches across platforms and compares prices in real-time

### 4️⃣ Save Money
Choose the best deal and save on your grocery shopping!

---

## 🎯 Key Capabilities

### Automated Price Comparison
- Searches multiple platforms simultaneously
- Extracts accurate pricing data
- Calculates totals including tax
- Identifies the best deal automatically

### Smart Recipe Processing
- Uses Google Gemini AI for intelligent recipe parsing
- Extracts ingredients with quantities and units
- Handles various recipe formats
- Suggests alternatives when items aren't found

### Order Management
- Complete order history
- Detailed receipts with itemized pricing
- Order status tracking
- Receipt image generation (Phase 3)

---

## 📂 Project Structure

```
HackPton_Delivery_App/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── agents/            # Platform-specific automation agents
│   │   ├── routes/            # API endpoints
│   │   ├── services/          # Business logic
│   │   └── models/            # Data models
│   └── data/
│       ├── cart_jsons/        # Raw cart data
│       └── knot_api_jsons/    # Processed order data
├── frontend/                   # Next.js frontend
│   ├── app/                   # App router pages
│   ├── components/            # React components
│   ├── hooks/                 # Custom React hooks
│   └── lib/                   # Utilities and API clients
└── README.md
```

---

## 🏗️ System Architecture

<div align="center">
  <img src="./assets/system_architecture.jpeg" alt="System Architecture" width="800"/>
</div>

### Architecture Overview

**Frontend (Next.js)** → **Backend API (FastAPI)** → **Automation Agents (Selenium)** → **E-commerce Platforms**

1. **User Interface Layer**: React/Next.js frontend with beautiful MealPilot branding
2. **API Layer**: FastAPI backend handling requests and orchestrating operations
3. **Automation Layer**: Selenium-based agents for platform-specific interactions
4. **Data Processing Layer**: Gemini AI for recipe parsing, Knot API for order formatting
5. **Storage Layer**: Supabase for user data, orders, and statistics

---

## 🔧 Configuration

### Environment Variables

**Backend** (`.env`):
```env
GEMINI_API_KEY=your_gemini_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
JWT_SECRET=your_jwt_secret
```

**Frontend** (`.env.local`):
```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

---

## 🎨 Design System

### Color Palette
- **Primary Brown**: `#C9915C` - Buttons, accents, branding
- **Text Primary**: `#3E2723` - Headings and important text
- **Background**: `#F5F5F5` - Page background
- **Success Green**: `#4CAF50` - Confirmations and badges
- **Instacart Orange**: `#FF6B35` - Instacart branding
- **Uber Eats Green**: `#06C167` - Uber Eats branding

### Components
- Reusable card component with consistent styling
- Platform-specific color coding
- Responsive grid layouts
- Smooth animations and transitions

---

## 🚦 API Endpoints

### Recipe & Shopping
- `POST /api/recipes/ingredients` - Extract ingredients from recipe
- `POST /api/shopping/save` - Save shopping list
- `POST /api/driver/start` - Start price comparison

### Comparison
- `GET /api/comparison/{job_id}` - Get comparison results
- `GET /api/jobs/{job_id}/status` - Check job status

### Orders (Phase 3)
- `GET /api/orders` - List all orders
- `GET /api/orders/{order_id}` - Get order details
- `POST /api/orders/import-knot` - Import from Knot API

---

## 🔮 Roadmap

### Phase 3 (In Progress)
- ✅ Order history tracking
- ✅ Detailed receipt views
- ✅ Price data integration
- 🔄 Receipt image generation with AI
- 🔄 User profiling and recommendations
- 🔄 Statistics dashboard

### Future Enhancements
- More platform integrations (Amazon Fresh, Walmart+)
- Dietary preference filtering
- Meal planning calendar
- Shopping list sharing
- Price drop alerts


## 🙏 Acknowledgments

- **Amazon Nova Act** for web automation using LLMs
- **Google Gemini** for AI-powered recipe parsing
- **Knot API** for e-commerce integration
- **Supabase** for backend infrastructure
- **Hack Princeton** for the opportunity to build this project

---

**Built with ❤️ for smarter grocery shopping**

© 2025 MealPilot. All rights reserved.