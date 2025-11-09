# Supabase Storage Setup for Phase 3

## Storage Bucket: `receipts`

### Setup Instructions

Execute the following in Supabase SQL Editor or via Dashboard:

```sql
-- Create private storage bucket for receipts
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
  'receipts',
  'receipts',
  false, -- private bucket
  10485760, -- 10MB limit per file
  ARRAY['image/png', 'image/jpeg']
)
ON CONFLICT (id) DO NOTHING;

-- Policy: Only service role can upload receipts
CREATE POLICY "Service role can upload receipts"
ON storage.objects FOR INSERT
WITH CHECK (
  bucket_id = 'receipts' AND
  auth.role() = 'service_role'
);

-- Policy: Users can read their own receipts via signed URLs
CREATE POLICY "Users can read own receipts"
ON storage.objects FOR SELECT
USING (
  bucket_id = 'receipts' AND
  (storage.foldername(name))[1] = auth.uid()::TEXT
);

-- Policy: Service role can update/delete receipts
CREATE POLICY "Service role can manage receipts"
ON storage.objects FOR UPDATE
USING (
  bucket_id = 'receipts' AND
  auth.role() = 'service_role'
);

CREATE POLICY "Service role can delete receipts"
ON storage.objects FOR DELETE
USING (
  bucket_id = 'receipts' AND
  auth.role() = 'service_role'
);
```

### Folder Structure

```
receipts/
  {user_id}/
    {order_id}.png          # Full receipt image (1024x1792)
    {order_id}_thumb.jpg    # Thumbnail (320x568)
```

### Access Pattern

- **Upload**: Backend uses service role key to upload images
- **Read**: Backend generates signed URLs (1-hour expiry) for frontend display
- **Security**: Private bucket; no public URLs; RLS enforces user isolation

### Verification

After setup, verify:

```sql
-- Check bucket exists
SELECT * FROM storage.buckets WHERE id = 'receipts';

-- Check policies
SELECT * FROM storage.policies WHERE bucket_id = 'receipts';
```

