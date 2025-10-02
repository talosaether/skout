create extension if not exists "uuid-ossp";

-- Users table for authentication
create table if not exists users (
  id uuid primary key default uuid_generate_v4(),
  created_at timestamptz not null default now(),
  email text unique not null,
  password_hash text not null,
  constraint email_format check (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- Index on email for login queries
create index if not exists idx_users_email on users(email);

-- Assets table with user ownership
create table if not exists assets (
  id uuid primary key default uuid_generate_v4(),
  created_at timestamptz not null default now(),
  filename text not null,
  mime text not null,
  size integer not null,
  file_hash text not null,
  user_id uuid references users(id) on delete cascade
);

-- Basic pagination helper index
create index if not exists idx_assets_created_at on assets (created_at desc);

-- Index on user_id for filtering user's assets
create index if not exists idx_assets_user_id on assets(user_id);