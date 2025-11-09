# Phase 3 Implementation Guide

## Overview

Phase 3 adds receipt generation, user authentication, order history, and personalized recommendations to the Recipe Cart Optimizer platform.

### Key Features
- **Receipt Generation**: Photorealistic receipt images using Gemini Nano Banana
- **User Authentication**: Supabase Auth with email/password
- **Order History**: View past orders with receipt images and item details
- **User Profiling**: AI-generated preference keywords based on purchase history
- **Personalized Recommendations**: Homepage displays 5 preference keywords

---

## Architecture

### Backend (FastAPI)
- **Framework**: FastAPI 0.115.5
- **Database**: Supabase (PostgreSQL with RLS)
- **Storage**: Supabase Storage (private bucket for receipts)
- **AI**: Google Gemini for receipt generation and profiling

### Frontend (Next.js)
- **Framework**: Next.js 14.1.0
- **Auth**: Supabase JS Client
- **UI**: React + Tailwind CSS

---

## Database Schema

### Tables

#### `profiles`
User profiles with preference keywords
- `id` (UUID, PK, FK to auth.users)
- `first_name`, `last_name`, `email`
- `preferences` (text[], max 5 keywords)
- `created_at`, `updated_at`

#### `orders`
Order summaries from Knot API JSONs
- `id` (UUID, PK)
- `user_id` (UUID, FK to auth.users)
- `store_name`, `currency`
- `subtotal`, `tax`, `total`
- `platform_subtotals` (JSONB)
- `knot_payload` (JSONB, complete original data)
- `receipt_image_path`, `receipt_thumbnail_path`
- `payload_hash` (for idempotent imports)
- `receipt_status`, `profiling_status`
- `created_at`, `updated_at`

#### `order_items`
Individual items within orders
- `id` (bigserial, PK)
- `order_id` (UUID, FK to orders)
- `platform`, `item_name`, `external_id`
- `quantity`, `unit`, `unit_price`, `subtotal`, `total`
- `eligibility` (text[])

#### `profiling_history`
Audit trail of preference updates
- `id` (bigserial, PK)
- `user_id` (UUID, FK to auth.users)
- `order_id` (UUID, FK to orders)
- `generated_keywords`, `final_preferences` (text[])
- `created_at`

### Row Level Security (RLS)
All tables enforce user isolation:
- Users can only access their own data
- Service role (backend) has full access

### Storage Bucket: `receipts`
- **Privacy**: Private (no public URLs)
- **Access**: Backend writes, frontend reads via signed URLs (1-hour expiry)
- **Structure**: `receipts/{user_id}/{order_id}.png`

---

## Backend API Endpoints

### Orders (`/api/orders`)

#### `POST /api/orders/import-knot`
Import Knot JSONs from `current_code/knot_api_jsons/`
- **Auth**: Required
- **Returns**: List of created order IDs
- **Background Tasks**: Receipt generation + profiling

#### `GET /api/orders`
List user's orders
- **Auth**: Required
- **Query Params**: `limit` (default 50), `offset` (default 0)
- **Returns**: Array of order summaries with thumbnail URLs

#### `GET /api/orders/{order_id}`
Get order details
- **Auth**: Required
- **Returns**: Order metadata, items, and receipt image URL

### Receipts (`/api/receipts`)

#### `POST /api/receipts/generate/{order_id}`
Trigger receipt generation for an order
- **Auth**: Required
- **Background Task**: Generates image via Gemini and uploads to storage
- **Returns**: Immediate confirmation (process runs in background)

### Profiling (`/api/profiling`)

#### `POST /api/profiling/refresh`
Refresh user preferences based on latest order
- **Auth**: Required
- **Background Task**: Extracts items, calls Gemini, updates preferences
- **Returns**: Immediate confirmation

#### `GET /api/profiling/preferences`
Get user's current preferences
- **Auth**: Required
- **Returns**: Array of up to 5 preference keywords

---

## Frontend Pages

### Authentication
- `/login` - Email/password login
- `/signup` - Registration with first/last name

### Orders
- `/orders` - List of orders with thumbnails
- `/orders/[orderId]` - Order details with receipt image and items table

### Home
- `/` - Recipe search with preference keywords displayed

---

## Setup Instructions

### 1. Database Setup

Run the SQL migration:
```bash
# Execute backend/models/tables.sql in Supabase SQL Editor
```

Create storage bucket:
```bash
# Execute backend/models/storage_setup.md instructions
```

### 2. Environment Variables

#### Backend (`.env` in `backend/`)
```env
# Existing Phase 1-2 vars...
GEMINI_API_KEY=your_key

# Phase 3: Supabase
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIs...
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIs...
SUPABASE_JWT_SECRET=your-jwt-secret

RECEIPTS_BUCKET=receipts
MAX_RECEIPT_RETRIES=3
RECEIPT_RETRY_DELAY_SECONDS=5
```

#### Frontend (`.env.local` in `frontend/`)
```env
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIs...
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

### 3. Install Dependencies

#### Backend
```bash
cd backend
pip install -r requirements.txt
```

#### Frontend
```bash
cd frontend
npm install
```

### 4. Run Services

#### Backend
```bash
cd backend
uvicorn app.main:app --reload
```

#### Frontend
```bash
cd frontend
npm run dev
```

---

## Workflow

### Order Import Flow
1. User hits submit on Phase 1-2 flow
2. `main.py` processes orders → generates Knot JSONs in `current_code/knot_api_jsons/`
3. Backend imports JSONs via `/api/orders/import-knot`
4. Background tasks triggered:
   - Receipt generation (Gemini Nano Banana)
   - User profiling (extract keywords)
5. Orders appear in `/orders` with receipt images
6. Preferences update on homepage

### Receipt Generation
1. Extract order details from `knot_payload`
2. Build comprehensive prompt for Gemini
3. Call Gemini Images API to generate 1024x1792 PNG
4. Create 320x568 thumbnail
5. Upload both to Supabase Storage
6. Update order with image paths
7. Frontend displays via signed URLs (1-hour expiry)

### User Profiling
1. Extract all item names from latest order
2. Send to Gemini with profiling prompt
3. Receive 5 keyword suggestions
4. Merge with existing preferences (dedupe)
5. Randomly select 5 final preferences
6. Update profile and log to history
7. Display on homepage as recommendations

---

## Testing

### Manual Testing
1. Sign up new user
2. Import sample Knot JSONs
3. Verify orders appear in `/orders`
4. Check receipt images load
5. Verify items table matches JSON data
6. Confirm preferences show on homepage

### API Testing
```bash
# Health check
curl http://localhost:8000/health

# Import orders (requires auth token)
curl -X POST http://localhost:8000/api/orders/import-knot \
  -H "Authorization: Bearer YOUR_TOKEN"

# List orders
curl http://localhost:8000/api/orders \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Troubleshooting

### Receipt Generation Issues
- Check `GEMINI_API_KEY` is valid
- Verify Gemini API quota/limits
- Review `orders.receipt_status` for error state
- Check backend logs for Gemini errors

### Storage Issues
- Verify `receipts` bucket exists and is private
- Check RLS policies allow backend writes
- Ensure signed URLs expire correctly (1 hour)

### Auth Issues
- Verify Supabase project URL and keys
- Check JWT secret matches Supabase config
- Confirm RLS policies are enabled

---

## File Structure

```
backend/
├── models/
│   ├── tables.sql              # Phase 3 schema
│   └── storage_setup.md        # Storage bucket setup
├── app/
│   ├── config.py               # Extended with Supabase config
│   ├── main.py                 # Phase 3 routes included
│   ├── security/
│   │   ├── __init__.py
│   │   └── jwt.py              # Supabase JWT verification
│   ├── services/
│   │   ├── supabase_service.py # Supabase client wrapper
│   │   ├── knot_importer.py    # Import Knot JSONs
│   │   ├── gemini_receipts.py  # Receipt generation
│   │   └── gemini_profiling.py # User profiling
│   ├── routes/
│   │   ├── orders.py           # Orders endpoints
│   │   ├── receipts.py         # Receipts endpoints
│   │   └── profiling.py        # Profiling endpoints
│   └── models/
│       └── phase3.py           # Pydantic models
└── requirements.txt            # Updated with Supabase, Pillow, etc.

frontend/
├── app/
│   ├── (auth)/
│   │   ├── login/page.tsx
│   │   └── signup/page.tsx
│   ├── orders/
│   │   ├── page.tsx            # Orders list
│   │   └── [orderId]/page.tsx  # Order details
│   └── page.tsx                # Home with keywords
├── components/
│   ├── KeywordChips.tsx
│   ├── OrderCard.tsx
│   ├── ReceiptImage.tsx
│   └── OrdersTable.tsx
├── lib/
│   ├── supabase.ts             # Supabase client
│   └── api.ts                  # Backend API client
├── hooks/
│   └── useAuth.ts              # Auth hook
└── package.json                # Updated with @supabase/supabase-js
```

---

## Git Commits

Phase 3 implementation is tracked across these commits:
1. Database schema and storage setup
2. Backend config, JWT auth, and Supabase service
3. Knot importer and Gemini services
4. Orders, receipts, and profiling API routes
5. Frontend auth, orders UI, and preferences display

---

## Next Steps (Phase 4)

- Statistics Module: 4 KPIs based on order history
- Profile Tab: Display KPIs in bento grid layout
- Advanced profiling with behavior analysis
- Export orders to PDF/CSV
- Multi-platform order optimization

---

## Support

For issues or questions, refer to:
- [Supabase Documentation](https://supabase.com/docs)
- [Gemini API Documentation](https://ai.google.dev/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)

