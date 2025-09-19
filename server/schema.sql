create extension if not exists "uuid-ossp";

create table if not exists assets (
  id uuid primary key default uuid_generate_v4(),
  created_at timestamptz not null default now(),
  filename text not null,
  mime text not null,
  size integer not null,
  data bytea not null
);

-- Basic pagination helper index
create index if not exists idx_assets_created_at on assets (created_at desc);