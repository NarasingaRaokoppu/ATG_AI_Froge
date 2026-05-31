create table if not exists behavior_events (
  id uuid primary key,
  user_id text not null,
  session_id text not null,
  event_type text not null,
  event_time timestamptz not null,
  attributes jsonb not null default '{}'::jsonb,
  request_id text not null
);

create table if not exists user_segments (
  user_id text primary key,
  segment_id text not null,
  segment_name text not null,
  confidence numeric not null,
  reason_codes jsonb not null default '[]'::jsonb,
  updated_at timestamptz not null
);

create table if not exists products (
  id text primary key,
  title text not null,
  category text not null,
  base_price numeric not null,
  inventory_count int not null default 0
);

create table if not exists personalization_decisions (
  id bigserial primary key,
  trace_id text unique not null,
  user_id text not null,
  page_type text not null,
  segment_payload jsonb not null,
  rec_payload jsonb not null,
  pricing_payload jsonb not null,
  content_payload jsonb not null,
  latency_ms int not null,
  error_notes jsonb not null default '[]'::jsonb,
  created_at timestamptz not null
);

create index if not exists idx_behavior_events_user_time on behavior_events(user_id, event_time);
create index if not exists idx_decisions_user_time on personalization_decisions(user_id, created_at);
