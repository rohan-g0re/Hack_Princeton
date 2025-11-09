-- Supabase Schema for Grocery Super-App
-- Users are managed by Supabase Auth automatically

-- User shopping sessions
CREATE TABLE IF NOT EXISTS user_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  recipe_query TEXT,
  ingredients JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Cart states for each platform
CREATE TABLE IF NOT EXISTS cart_states (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID REFERENCES user_sessions(id) ON DELETE CASCADE,
  platform TEXT NOT NULL, -- 'instacart', 'ubereats'
  items JSONB, -- [{name, quantity, price, size}]
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- User-made cart modifications (diffs)
CREATE TABLE IF NOT EXISTS cart_diffs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID REFERENCES user_sessions(id) ON DELETE CASCADE,
  platform TEXT NOT NULL,
  action TEXT NOT NULL, -- 'add', 'remove'
  item JSONB,
  applied BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Mock payment transactions
CREATE TABLE IF NOT EXISTS transactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID REFERENCES user_sessions(id) ON DELETE CASCADE,
  knot_transaction_id TEXT,
  total_amount NUMERIC(10, 2),
  platforms JSONB, -- [{platform, subtotal}]
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_cart_states_session_id ON cart_states(session_id);
CREATE INDEX IF NOT EXISTS idx_cart_diffs_session_id ON cart_diffs(session_id);
CREATE INDEX IF NOT EXISTS idx_transactions_session_id ON transactions(session_id);

-- Add RLS policies (optional for prototype, but good practice)
ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE cart_states ENABLE ROW LEVEL SECURITY;
ALTER TABLE cart_diffs ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;

-- Note: For prototype, backend uses service role which bypasses RLS
-- In production, add policies like:
-- CREATE POLICY "Users can view own sessions" ON user_sessions
--   FOR SELECT USING (auth.uid() = user_id);

