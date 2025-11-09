-- Phase 3: Supabase Database Schema
-- Tables: profiles, orders, order_items
-- RLS policies for user isolation
-- Storage bucket: receipts (private)

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto"; -- for gen_random_uuid
CREATE EXTENSION IF NOT EXISTS "moddatetime"; -- for auto-updating updated_at

-- ============================================================================
-- PROFILES TABLE
-- ============================================================================
-- 1:1 relationship with auth.users
-- Stores user profile info and 5 preference keywords for recommendations

CREATE TABLE IF NOT EXISTS public.profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  first_name TEXT,
  last_name TEXT,
  preferences TEXT[] NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Auto-update updated_at timestamp
CREATE TRIGGER trg_profiles_updated
  BEFORE UPDATE ON public.profiles
  FOR EACH ROW
  EXECUTE PROCEDURE moddatetime(updated_at);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_profiles_id ON public.profiles(id);

COMMENT ON TABLE public.profiles IS 'User profiles with preference keywords';
COMMENT ON COLUMN public.profiles.preferences IS 'Array of up to 5 preference keywords for recommendations';


-- ============================================================================
-- ORDERS TABLE
-- ============================================================================
-- Stores order summaries from knot_api_jsons
-- Each order can span multiple platforms (stored in platform_subtotals)

CREATE TABLE IF NOT EXISTS public.orders (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  
  -- Order metadata
  store_name TEXT, -- Merchant name (e.g., "Instacart", "Uber Eats")
  currency TEXT NOT NULL DEFAULT 'USD',
  
  -- Pricing
  subtotal NUMERIC(12,2) NOT NULL DEFAULT 0,
  tax NUMERIC(12,2) NOT NULL DEFAULT 0,
  total NUMERIC(12,2) NOT NULL DEFAULT 0,
  
  -- Platform breakdown (if multiple platforms in one order)
  platform_subtotals JSONB, -- { "Instacart": 100.00, "Uber Eats": 50.00 }
  
  -- Original Knot API payload (preserved for receipt generation)
  knot_payload JSONB NOT NULL,
  
  -- Receipt image path in Supabase Storage
  receipt_image_path TEXT, -- e.g., "receipts/{user_id}/{order_id}.png"
  
  -- Timestamps
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON public.orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON public.orders(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_orders_user_created ON public.orders(user_id, created_at DESC);

COMMENT ON TABLE public.orders IS 'Order summaries from Knot API payloads';
COMMENT ON COLUMN public.orders.knot_payload IS 'Complete Knot API JSON for receipt generation';
COMMENT ON COLUMN public.orders.receipt_image_path IS 'Path to receipt image in Supabase Storage';


-- ============================================================================
-- ORDER_ITEMS TABLE
-- ============================================================================
-- Individual items within each order
-- Can have items from multiple platforms

CREATE TABLE IF NOT EXISTS public.order_items (
  id BIGSERIAL PRIMARY KEY,
  order_id UUID NOT NULL REFERENCES public.orders(id) ON DELETE CASCADE,
  
  -- Item metadata
  platform TEXT, -- e.g., "Instacart", "Uber Eats"
  item_name TEXT NOT NULL,
  quantity NUMERIC,
  unit TEXT, -- e.g., "ea", "lb", "oz"
  
  -- Pricing
  unit_price NUMERIC(12,2),
  total NUMERIC(12,2)
);

-- Index for fast order lookup
CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON public.order_items(order_id);

COMMENT ON TABLE public.order_items IS 'Individual items within orders';
COMMENT ON COLUMN public.order_items.platform IS 'Platform/merchant where item was purchased';


-- ============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================================================
-- Enforce user isolation: users can only access their own data

-- Enable RLS on all tables
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.order_items ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- PROFILES RLS POLICIES
-- ============================================================================

-- Users can view their own profile
CREATE POLICY profiles_select_own ON public.profiles
  FOR SELECT
  USING (auth.uid() = id);

-- Users can insert their own profile
CREATE POLICY profiles_insert_own ON public.profiles
  FOR INSERT
  WITH CHECK (auth.uid() = id);

-- Users can update their own profile
CREATE POLICY profiles_update_own ON public.profiles
  FOR UPDATE
  USING (auth.uid() = id);

-- Users can delete their own profile
CREATE POLICY profiles_delete_own ON public.profiles
  FOR DELETE
  USING (auth.uid() = id);


-- ============================================================================
-- ORDERS RLS POLICIES
-- ============================================================================

-- Users can view their own orders
CREATE POLICY orders_select_own ON public.orders
  FOR SELECT
  USING (auth.uid() = user_id);

-- Users can insert orders for themselves
CREATE POLICY orders_insert_own ON public.orders
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Users can update their own orders
CREATE POLICY orders_update_own ON public.orders
  FOR UPDATE
  USING (auth.uid() = user_id);

-- Users can delete their own orders
CREATE POLICY orders_delete_own ON public.orders
  FOR DELETE
  USING (auth.uid() = user_id);


-- ============================================================================
-- ORDER_ITEMS RLS POLICIES
-- ============================================================================

-- Users can view items from their own orders
CREATE POLICY order_items_select_own ON public.order_items
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.orders o 
      WHERE o.id = order_id AND o.user_id = auth.uid()
    )
  );

-- Users can insert items into their own orders
CREATE POLICY order_items_insert_own ON public.order_items
  FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.orders o 
      WHERE o.id = order_id AND o.user_id = auth.uid()
    )
  );

-- Users can update items in their own orders
CREATE POLICY order_items_update_own ON public.order_items
  FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM public.orders o 
      WHERE o.id = order_id AND o.user_id = auth.uid()
    )
  );

-- Users can delete items from their own orders
CREATE POLICY order_items_delete_own ON public.order_items
  FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM public.orders o 
      WHERE o.id = order_id AND o.user_id = auth.uid()
    )
  );


-- ============================================================================
-- STORAGE BUCKET SETUP NOTES
-- ============================================================================
-- The following needs to be done via Supabase Dashboard or API:
--
-- 1. Create bucket 'receipts' (private)
-- 2. Set policies:
--    - Only service role can upload (backend writes)
--    - No public access (use signed URLs via backend)
--
-- Bucket structure:
--   receipts/
--     {user_id}/
--       {order_id}.png          (full receipt image)
--       {order_id}_thumb.jpg    (optional thumbnail)
--
-- Backend generates signed URLs with 1-hour expiry for client display
-- ============================================================================

