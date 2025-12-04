-- RedditHarbor Database Schema Dump
-- Generated: 2025-12-03 19:01:41
-- Schema: All user schemas (public, auth, storage, etc.)
-- Purpose: Complete database structure backup

\c reddit_harbor

-- Create schema dump
\echo 'Creating schema dump...'

-- Dump all schemas and their objects
pg_dump \
  --schema=public \
  --schema=auth \
  --schema=storage \
  --schema=extensions \
  --schema=graphql \
  --schema=realtime \
  --schema=supabase_functions \
  --schema=vault \
  --schema=_realtime \
  --schema=net \
  --schema=app_opportunities \
  --schema=app_opportunities_staging \
  --schema=public_staging \
  --schema-only \
  --no-owner \
  --no-privileges \
  --verbose \
  --file=reddit_harbor_schema_20251203_190141.sql

\echo 'Schema dump completed: reddit_harbor_schema_20251203_190141.sql'

-- Generate individual table schemas
\echo 'Generating individual table schemas...'

-- Create detailed table definitions
SELECT
    'CREATE TABLE ' || schemaname || '.' || tablename || ' (' ||
    array_to_string(
        array_agg(
            column_name || ' ' || data_type ||
            CASE
                WHEN character_maximum_length IS NOT NULL
                THEN '(' || character_maximum_length || ')'
                ELSE ''
            END ||
            CASE
                WHEN is_nullable = 'NO' THEN ' NOT NULL'
                ELSE ' NULL'
            END ||
            CASE
                WHEN column_default IS NOT NULL
                THEN ' DEFAULT ' || column_default
                ELSE ''
            END
            ORDER BY ordinal_position
        ), E',\n    '
    ) ||
    E');' AS create_statement
FROM information_schema.columns
WHERE schemaname IN ('public', 'auth', 'storage', 'extensions')
GROUP BY schemaname, tablename
ORDER BY schemaname, tablename;

\echo 'Individual table schemas generated'

-- Create index definitions
\echo 'Generating index definitions...'

SELECT
    'CREATE ' ||
    CASE WHEN i.indisunique THEN 'UNIQUE ' ELSE '' END ||
    'INDEX ' || i.indexname || ' ON ' || n.nspname || '.' || c.relname ||
    ' USING ' || am.amname || ' (' ||
    array_to_string(
        array_agg(a.attname ORDER BY a.attnum),
        ', '
    ) || ');' AS index_definition
FROM pg_index i
JOIN pg_class c ON i.indrelid = c.oid
JOIN pg_class ic ON i.indexrelid = ic.oid
JOIN pg_namespace n ON c.relnamespace = n.oid
JOIN pg_namespace in ON ic.relnamespace = in.oid
JOIN pg_am am ON ic.relam = am.oid
JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = ANY(i.indkey)
WHERE n.nspname IN ('public', 'auth', 'storage', 'extensions')
GROUP BY n.nspname, c.relname, i.indexname, i.indisunique, am.amname
ORDER BY n.nspname, c.relname, i.indexname;

\echo 'Index definitions generated'

-- Create constraint definitions
\echo 'Generating constraint definitions...'

SELECT
    n.nspname || '.' || c.relname || ': ' ||
    con.conname || ' - ' ||
    CASE con.contype
        WHEN 'p' THEN 'PRIMARY KEY (' || array_to_string(array_agg(a.attname ORDER BY a.attnum), ', ') || ')'
        WHEN 'u' THEN 'UNIQUE (' || array_to_string(array_agg(a.attname ORDER BY a.attnum), ', ') || ')'
        WHEN 'f' THEN 'FOREIGN KEY (' || array_to_string(array_agg(a.attname ORDER BY a.attnum), ', ') || ') REFERENCES ' ||
                 fn.nspname || '.' || fc.relname || ' (' || array_to_string(array_agg(fa.attname ORDER BY fa.attnum), ', ') || ')'
        WHEN 'c' THEN 'CHECK: ' || pg_get_constraintdef(con.oid)
        ELSE con.contype::text
    END AS constraint_definition
FROM pg_constraint con
JOIN pg_class c ON con.conrelid = c.oid
JOIN pg_namespace n ON c.relnamespace = n.oid
LEFT JOIN pg_class fc ON con.confrelid = fc.oid
LEFT JOIN pg_namespace fn ON fc.relnamespace = fn.oid
LEFT JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = ANY(con.conkey)
LEFT JOIN pg_attribute fa ON fa.attrelid = fc.oid AND fa.attnum = ANY(con.confkey)
WHERE n.nspname IN ('public', 'auth', 'storage', 'extensions')
GROUP BY n.nspname, c.relname, con.conname, con.contype, con.oid, fn.nspname, fc.relname
ORDER BY n.nspname, c.relname, con.conname;

\echo 'Constraint definitions generated'
\echo 'Schema dump complete!'