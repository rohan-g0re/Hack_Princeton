# Supabase Setup Instructions

## Steps to Set Up Supabase

1. **Create a Supabase Project**
   - Go to https://supabase.com/dashboard
   - Click "New Project"
   - Enter project name: `grocery-superapp`
   - Set a strong database password
   - Choose a region close to you
   - Wait for project to be created (~2 minutes)

2. **Apply the Schema**
   - In your Supabase dashboard, go to SQL Editor
   - Click "New Query"
   - Copy and paste the contents of `server/supabase_schema.sql`
   - Click "Run" to execute the schema

3. **Get Your API Keys**
   - Go to Settings → API
   - Copy the following values:
     - Project URL (e.g., `https://xxxxx.supabase.co`)
     - `anon` / `public` key (for mobile app)
     - `service_role` key (for backend - keep secret!)

4. **Create a Test User** (Optional)
   - Go to Authentication → Users
   - Click "Add User" → "Create New User"
   - Email: `test@example.com`
   - Password: `Test123456!`
   - Click "Create User"

5. **Update Environment Files**
   - Copy the keys to `server/.env` and `mobile/.env` (see examples in those directories)

## Verification

After setup, you can verify tables were created:
```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('user_sessions', 'cart_states', 'cart_diffs', 'transactions');
```

You should see all 4 tables listed.

