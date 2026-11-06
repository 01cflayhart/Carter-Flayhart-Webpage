CREATE TABLE IF NOT EXISTS page_views (
  day TEXT NOT NULL,
  area TEXT NOT NULL CHECK(area IN ('sports','professional')),
  views INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY(day, area)
);
CREATE TABLE IF NOT EXISTS rate_limits (
  key TEXT PRIMARY KEY,
  day TEXT NOT NULL,
  count INTEGER NOT NULL
);
