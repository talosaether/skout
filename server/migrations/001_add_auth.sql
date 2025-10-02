-- Migration: Add authentication and user ownership
-- Date: 2025-10-02
-- Description: Add users table and link assets to users

-- Create users table
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  CONSTRAINT email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- Create index on email for login queries
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Add user_id column to assets table (nullable for backward compatibility)
ALTER TABLE assets ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;

-- Create index on user_id for filtering user's assets
CREATE INDEX IF NOT EXISTS idx_assets_user_id ON assets(user_id);

-- Optional: Create a system user for orphaned assets
-- INSERT INTO users (id, email, password_hash)
-- VALUES ('00000000-0000-0000-0000-000000000000', 'system@skout.internal', '')
-- ON CONFLICT (id) DO NOTHING;

-- Optional: Assign orphaned assets to system user
-- UPDATE assets SET user_id = '00000000-0000-0000-0000-000000000000' WHERE user_id IS NULL;
