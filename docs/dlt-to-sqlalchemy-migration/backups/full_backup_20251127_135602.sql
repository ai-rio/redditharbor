--
-- PostgreSQL database dump
--

\restrict DbRlBskkgDqhWaSufMi9OJFSv4edAh3SxjPpyzrbh9N2thhjWEFDvrBawtqrbZT

-- Dumped from database version 15.8
-- Dumped by pg_dump version 16.10 (Ubuntu 16.10-0ubuntu0.24.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: _realtime; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA _realtime;


ALTER SCHEMA _realtime OWNER TO postgres;

--
-- Name: app_opportunities; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA app_opportunities;


ALTER SCHEMA app_opportunities OWNER TO postgres;

--
-- Name: app_opportunities_staging; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA app_opportunities_staging;


ALTER SCHEMA app_opportunities_staging OWNER TO postgres;

--
-- Name: auth; Type: SCHEMA; Schema: -; Owner: supabase_admin
--

CREATE SCHEMA auth;


ALTER SCHEMA auth OWNER TO supabase_admin;

--
-- Name: extensions; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA extensions;


ALTER SCHEMA extensions OWNER TO postgres;

--
-- Name: graphql; Type: SCHEMA; Schema: -; Owner: supabase_admin
--

CREATE SCHEMA graphql;


ALTER SCHEMA graphql OWNER TO supabase_admin;

--
-- Name: graphql_public; Type: SCHEMA; Schema: -; Owner: supabase_admin
--

CREATE SCHEMA graphql_public;


ALTER SCHEMA graphql_public OWNER TO supabase_admin;

--
-- Name: pg_net; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_net WITH SCHEMA extensions;


--
-- Name: EXTENSION pg_net; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pg_net IS 'Async HTTP';


--
-- Name: pgbouncer; Type: SCHEMA; Schema: -; Owner: pgbouncer
--

CREATE SCHEMA pgbouncer;


ALTER SCHEMA pgbouncer OWNER TO pgbouncer;

--
-- Name: public_staging; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA public_staging;


ALTER SCHEMA public_staging OWNER TO postgres;

--
-- Name: realtime; Type: SCHEMA; Schema: -; Owner: supabase_admin
--

CREATE SCHEMA realtime;


ALTER SCHEMA realtime OWNER TO supabase_admin;

--
-- Name: storage; Type: SCHEMA; Schema: -; Owner: supabase_admin
--

CREATE SCHEMA storage;


ALTER SCHEMA storage OWNER TO supabase_admin;

--
-- Name: supabase_functions; Type: SCHEMA; Schema: -; Owner: supabase_admin
--

CREATE SCHEMA supabase_functions;


ALTER SCHEMA supabase_functions OWNER TO supabase_admin;

--
-- Name: vault; Type: SCHEMA; Schema: -; Owner: supabase_admin
--

CREATE SCHEMA vault;


ALTER SCHEMA vault OWNER TO supabase_admin;

--
-- Name: pg_graphql; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_graphql WITH SCHEMA graphql;


--
-- Name: EXTENSION pg_graphql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pg_graphql IS 'pg_graphql: GraphQL support';


--
-- Name: pg_stat_statements; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_stat_statements WITH SCHEMA extensions;


--
-- Name: EXTENSION pg_stat_statements; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pg_stat_statements IS 'track planning and execution statistics of all SQL statements executed';


--
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA extensions;


--
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';


--
-- Name: pgjwt; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgjwt WITH SCHEMA extensions;


--
-- Name: EXTENSION pgjwt; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pgjwt IS 'JSON Web Token API for Postgresql';


--
-- Name: supabase_vault; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS supabase_vault WITH SCHEMA vault;


--
-- Name: EXTENSION supabase_vault; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION supabase_vault IS 'Supabase Vault Extension';


--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA extensions;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- Name: aal_level; Type: TYPE; Schema: auth; Owner: supabase_auth_admin
--

CREATE TYPE auth.aal_level AS ENUM (
    'aal1',
    'aal2',
    'aal3'
);


ALTER TYPE auth.aal_level OWNER TO supabase_auth_admin;

--
-- Name: code_challenge_method; Type: TYPE; Schema: auth; Owner: supabase_auth_admin
--

CREATE TYPE auth.code_challenge_method AS ENUM (
    's256',
    'plain'
);


ALTER TYPE auth.code_challenge_method OWNER TO supabase_auth_admin;

--
-- Name: factor_status; Type: TYPE; Schema: auth; Owner: supabase_auth_admin
--

CREATE TYPE auth.factor_status AS ENUM (
    'unverified',
    'verified'
);


ALTER TYPE auth.factor_status OWNER TO supabase_auth_admin;

--
-- Name: factor_type; Type: TYPE; Schema: auth; Owner: supabase_auth_admin
--

CREATE TYPE auth.factor_type AS ENUM (
    'totp',
    'webauthn',
    'phone'
);


ALTER TYPE auth.factor_type OWNER TO supabase_auth_admin;

--
-- Name: one_time_token_type; Type: TYPE; Schema: auth; Owner: supabase_auth_admin
--

CREATE TYPE auth.one_time_token_type AS ENUM (
    'confirmation_token',
    'reauthentication_token',
    'recovery_token',
    'email_change_token_new',
    'email_change_token_current',
    'phone_change_token'
);


ALTER TYPE auth.one_time_token_type OWNER TO supabase_auth_admin;

--
-- Name: buckettype; Type: TYPE; Schema: storage; Owner: supabase_storage_admin
--

CREATE TYPE storage.buckettype AS ENUM (
    'STANDARD',
    'ANALYTICS'
);


ALTER TYPE storage.buckettype OWNER TO supabase_storage_admin;

--
-- Name: email(); Type: FUNCTION; Schema: auth; Owner: supabase_auth_admin
--

CREATE FUNCTION auth.email() RETURNS text
    LANGUAGE sql STABLE
    AS $$
  select 
  coalesce(
    nullif(current_setting('request.jwt.claim.email', true), ''),
    (nullif(current_setting('request.jwt.claims', true), '')::jsonb ->> 'email')
  )::text
$$;


ALTER FUNCTION auth.email() OWNER TO supabase_auth_admin;

--
-- Name: FUNCTION email(); Type: COMMENT; Schema: auth; Owner: supabase_auth_admin
--

COMMENT ON FUNCTION auth.email() IS 'Deprecated. Use auth.jwt() -> ''email'' instead.';


--
-- Name: jwt(); Type: FUNCTION; Schema: auth; Owner: supabase_auth_admin
--

CREATE FUNCTION auth.jwt() RETURNS jsonb
    LANGUAGE sql STABLE
    AS $$
  select 
    coalesce(
        nullif(current_setting('request.jwt.claim', true), ''),
        nullif(current_setting('request.jwt.claims', true), '')
    )::jsonb
$$;


ALTER FUNCTION auth.jwt() OWNER TO supabase_auth_admin;

--
-- Name: role(); Type: FUNCTION; Schema: auth; Owner: supabase_auth_admin
--

CREATE FUNCTION auth.role() RETURNS text
    LANGUAGE sql STABLE
    AS $$
  select 
  coalesce(
    nullif(current_setting('request.jwt.claim.role', true), ''),
    (nullif(current_setting('request.jwt.claims', true), '')::jsonb ->> 'role')
  )::text
$$;


ALTER FUNCTION auth.role() OWNER TO supabase_auth_admin;

--
-- Name: FUNCTION role(); Type: COMMENT; Schema: auth; Owner: supabase_auth_admin
--

COMMENT ON FUNCTION auth.role() IS 'Deprecated. Use auth.jwt() -> ''role'' instead.';


--
-- Name: uid(); Type: FUNCTION; Schema: auth; Owner: supabase_auth_admin
--

CREATE FUNCTION auth.uid() RETURNS uuid
    LANGUAGE sql STABLE
    AS $$
  select 
  coalesce(
    nullif(current_setting('request.jwt.claim.sub', true), ''),
    (nullif(current_setting('request.jwt.claims', true), '')::jsonb ->> 'sub')
  )::uuid
$$;


ALTER FUNCTION auth.uid() OWNER TO supabase_auth_admin;

--
-- Name: FUNCTION uid(); Type: COMMENT; Schema: auth; Owner: supabase_auth_admin
--

COMMENT ON FUNCTION auth.uid() IS 'Deprecated. Use auth.jwt() -> ''sub'' instead.';


--
-- Name: grant_pg_cron_access(); Type: FUNCTION; Schema: extensions; Owner: supabase_admin
--

CREATE FUNCTION extensions.grant_pg_cron_access() RETURNS event_trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  IF EXISTS (
    SELECT
    FROM pg_event_trigger_ddl_commands() AS ev
    JOIN pg_extension AS ext
    ON ev.objid = ext.oid
    WHERE ext.extname = 'pg_cron'
  )
  THEN
    grant usage on schema cron to postgres with grant option;

    alter default privileges in schema cron grant all on tables to postgres with grant option;
    alter default privileges in schema cron grant all on functions to postgres with grant option;
    alter default privileges in schema cron grant all on sequences to postgres with grant option;

    alter default privileges for user supabase_admin in schema cron grant all
        on sequences to postgres with grant option;
    alter default privileges for user supabase_admin in schema cron grant all
        on tables to postgres with grant option;
    alter default privileges for user supabase_admin in schema cron grant all
        on functions to postgres with grant option;

    grant all privileges on all tables in schema cron to postgres with grant option;
    revoke all on table cron.job from postgres;
    grant select on table cron.job to postgres with grant option;
  END IF;
END;
$$;


ALTER FUNCTION extensions.grant_pg_cron_access() OWNER TO supabase_admin;

--
-- Name: FUNCTION grant_pg_cron_access(); Type: COMMENT; Schema: extensions; Owner: supabase_admin
--

COMMENT ON FUNCTION extensions.grant_pg_cron_access() IS 'Grants access to pg_cron';


--
-- Name: grant_pg_graphql_access(); Type: FUNCTION; Schema: extensions; Owner: supabase_admin
--

CREATE FUNCTION extensions.grant_pg_graphql_access() RETURNS event_trigger
    LANGUAGE plpgsql
    AS $_$
DECLARE
    func_is_graphql_resolve bool;
BEGIN
    func_is_graphql_resolve = (
        SELECT n.proname = 'resolve'
        FROM pg_event_trigger_ddl_commands() AS ev
        LEFT JOIN pg_catalog.pg_proc AS n
        ON ev.objid = n.oid
    );

    IF func_is_graphql_resolve
    THEN
        -- Update public wrapper to pass all arguments through to the pg_graphql resolve func
        DROP FUNCTION IF EXISTS graphql_public.graphql;
        create or replace function graphql_public.graphql(
            "operationName" text default null,
            query text default null,
            variables jsonb default null,
            extensions jsonb default null
        )
            returns jsonb
            language sql
        as $$
            select graphql.resolve(
                query := query,
                variables := coalesce(variables, '{}'),
                "operationName" := "operationName",
                extensions := extensions
            );
        $$;

        -- This hook executes when `graphql.resolve` is created. That is not necessarily the last
        -- function in the extension so we need to grant permissions on existing entities AND
        -- update default permissions to any others that are created after `graphql.resolve`
        grant usage on schema graphql to postgres, anon, authenticated, service_role;
        grant select on all tables in schema graphql to postgres, anon, authenticated, service_role;
        grant execute on all functions in schema graphql to postgres, anon, authenticated, service_role;
        grant all on all sequences in schema graphql to postgres, anon, authenticated, service_role;
        alter default privileges in schema graphql grant all on tables to postgres, anon, authenticated, service_role;
        alter default privileges in schema graphql grant all on functions to postgres, anon, authenticated, service_role;
        alter default privileges in schema graphql grant all on sequences to postgres, anon, authenticated, service_role;

        -- Allow postgres role to allow granting usage on graphql and graphql_public schemas to custom roles
        grant usage on schema graphql_public to postgres with grant option;
        grant usage on schema graphql to postgres with grant option;
    END IF;

END;
$_$;


ALTER FUNCTION extensions.grant_pg_graphql_access() OWNER TO supabase_admin;

--
-- Name: FUNCTION grant_pg_graphql_access(); Type: COMMENT; Schema: extensions; Owner: supabase_admin
--

COMMENT ON FUNCTION extensions.grant_pg_graphql_access() IS 'Grants access to pg_graphql';


--
-- Name: grant_pg_net_access(); Type: FUNCTION; Schema: extensions; Owner: supabase_admin
--

CREATE FUNCTION extensions.grant_pg_net_access() RETURNS event_trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM pg_event_trigger_ddl_commands() AS ev
    JOIN pg_extension AS ext
    ON ev.objid = ext.oid
    WHERE ext.extname = 'pg_net'
  )
  THEN
    GRANT USAGE ON SCHEMA net TO supabase_functions_admin, postgres, anon, authenticated, service_role;

    ALTER function net.http_get(url text, params jsonb, headers jsonb, timeout_milliseconds integer) SECURITY DEFINER;
    ALTER function net.http_post(url text, body jsonb, params jsonb, headers jsonb, timeout_milliseconds integer) SECURITY DEFINER;

    ALTER function net.http_get(url text, params jsonb, headers jsonb, timeout_milliseconds integer) SET search_path = net;
    ALTER function net.http_post(url text, body jsonb, params jsonb, headers jsonb, timeout_milliseconds integer) SET search_path = net;

    REVOKE ALL ON FUNCTION net.http_get(url text, params jsonb, headers jsonb, timeout_milliseconds integer) FROM PUBLIC;
    REVOKE ALL ON FUNCTION net.http_post(url text, body jsonb, params jsonb, headers jsonb, timeout_milliseconds integer) FROM PUBLIC;

    GRANT EXECUTE ON FUNCTION net.http_get(url text, params jsonb, headers jsonb, timeout_milliseconds integer) TO supabase_functions_admin, postgres, anon, authenticated, service_role;
    GRANT EXECUTE ON FUNCTION net.http_post(url text, body jsonb, params jsonb, headers jsonb, timeout_milliseconds integer) TO supabase_functions_admin, postgres, anon, authenticated, service_role;
  END IF;
END;
$$;


ALTER FUNCTION extensions.grant_pg_net_access() OWNER TO supabase_admin;

--
-- Name: FUNCTION grant_pg_net_access(); Type: COMMENT; Schema: extensions; Owner: supabase_admin
--

COMMENT ON FUNCTION extensions.grant_pg_net_access() IS 'Grants access to pg_net';


--
-- Name: pgrst_ddl_watch(); Type: FUNCTION; Schema: extensions; Owner: supabase_admin
--

CREATE FUNCTION extensions.pgrst_ddl_watch() RETURNS event_trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
  cmd record;
BEGIN
  FOR cmd IN SELECT * FROM pg_event_trigger_ddl_commands()
  LOOP
    IF cmd.command_tag IN (
      'CREATE SCHEMA', 'ALTER SCHEMA'
    , 'CREATE TABLE', 'CREATE TABLE AS', 'SELECT INTO', 'ALTER TABLE'
    , 'CREATE FOREIGN TABLE', 'ALTER FOREIGN TABLE'
    , 'CREATE VIEW', 'ALTER VIEW'
    , 'CREATE MATERIALIZED VIEW', 'ALTER MATERIALIZED VIEW'
    , 'CREATE FUNCTION', 'ALTER FUNCTION'
    , 'CREATE TRIGGER'
    , 'CREATE TYPE', 'ALTER TYPE'
    , 'CREATE RULE'
    , 'COMMENT'
    )
    -- don't notify in case of CREATE TEMP table or other objects created on pg_temp
    AND cmd.schema_name is distinct from 'pg_temp'
    THEN
      NOTIFY pgrst, 'reload schema';
    END IF;
  END LOOP;
END; $$;


ALTER FUNCTION extensions.pgrst_ddl_watch() OWNER TO supabase_admin;

--
-- Name: pgrst_drop_watch(); Type: FUNCTION; Schema: extensions; Owner: supabase_admin
--

CREATE FUNCTION extensions.pgrst_drop_watch() RETURNS event_trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
  obj record;
BEGIN
  FOR obj IN SELECT * FROM pg_event_trigger_dropped_objects()
  LOOP
    IF obj.object_type IN (
      'schema'
    , 'table'
    , 'foreign table'
    , 'view'
    , 'materialized view'
    , 'function'
    , 'trigger'
    , 'type'
    , 'rule'
    )
    AND obj.is_temporary IS false -- no pg_temp objects
    THEN
      NOTIFY pgrst, 'reload schema';
    END IF;
  END LOOP;
END; $$;


ALTER FUNCTION extensions.pgrst_drop_watch() OWNER TO supabase_admin;

--
-- Name: set_graphql_placeholder(); Type: FUNCTION; Schema: extensions; Owner: supabase_admin
--

CREATE FUNCTION extensions.set_graphql_placeholder() RETURNS event_trigger
    LANGUAGE plpgsql
    AS $_$
    DECLARE
    graphql_is_dropped bool;
    BEGIN
    graphql_is_dropped = (
        SELECT ev.schema_name = 'graphql_public'
        FROM pg_event_trigger_dropped_objects() AS ev
        WHERE ev.schema_name = 'graphql_public'
    );

    IF graphql_is_dropped
    THEN
        create or replace function graphql_public.graphql(
            "operationName" text default null,
            query text default null,
            variables jsonb default null,
            extensions jsonb default null
        )
            returns jsonb
            language plpgsql
        as $$
            DECLARE
                server_version float;
            BEGIN
                server_version = (SELECT (SPLIT_PART((select version()), ' ', 2))::float);

                IF server_version >= 14 THEN
                    RETURN jsonb_build_object(
                        'errors', jsonb_build_array(
                            jsonb_build_object(
                                'message', 'pg_graphql extension is not enabled.'
                            )
                        )
                    );
                ELSE
                    RETURN jsonb_build_object(
                        'errors', jsonb_build_array(
                            jsonb_build_object(
                                'message', 'pg_graphql is only available on projects running Postgres 14 onwards.'
                            )
                        )
                    );
                END IF;
            END;
        $$;
    END IF;

    END;
$_$;


ALTER FUNCTION extensions.set_graphql_placeholder() OWNER TO supabase_admin;

--
-- Name: FUNCTION set_graphql_placeholder(); Type: COMMENT; Schema: extensions; Owner: supabase_admin
--

COMMENT ON FUNCTION extensions.set_graphql_placeholder() IS 'Reintroduces placeholder function for graphql_public.graphql';


--
-- Name: get_auth(text); Type: FUNCTION; Schema: pgbouncer; Owner: supabase_admin
--

CREATE FUNCTION pgbouncer.get_auth(p_usename text) RETURNS TABLE(username text, password text)
    LANGUAGE plpgsql SECURITY DEFINER
    AS $_$
begin
    raise debug 'PgBouncer auth request: %', p_usename;

    return query
    select 
        rolname::text, 
        case when rolvaliduntil < now() 
            then null 
            else rolpassword::text 
        end 
    from pg_authid 
    where rolname=$1 and rolcanlogin;
end;
$_$;


ALTER FUNCTION pgbouncer.get_auth(p_usename text) OWNER TO supabase_admin;

--
-- Name: normalize_app_opportunities_submission_id(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.normalize_app_opportunities_submission_id() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Process submission_id if it's being set or changed
    IF NEW.submission_id IS DISTINCT FROM OLD.submission_id THEN
        -- Normalize the submission_id using the resolver logic
        NEW.submission_id := normalize_submission_id(NEW.submission_id);
    END IF;

    RETURN NEW;
END;
$$;


ALTER FUNCTION public.normalize_app_opportunities_submission_id() OWNER TO postgres;

--
-- Name: normalize_submission_id(text); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.normalize_submission_id(input_id text) RETURNS uuid
    LANGUAGE plpgsql IMMUTABLE
    AS $_$
DECLARE
    trimmed_input TEXT;
    uuid_pattern TEXT;
    reddit_url_pattern TEXT;
BEGIN
    -- 1. NULL/Empty check
    IF input_id IS NULL OR input_id = '' THEN
        RETURN NULL;
    END IF;

    -- Trim whitespace
    trimmed_input := TRIM(input_id);

    -- Return NULL for empty after trimming
    IF trimmed_input = '' THEN
        RETURN NULL;
    END IF;

    -- 2. UUID validation using regex pattern
    -- Pattern: /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
    uuid_pattern := '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$';
    IF trimmed_input ~* uuid_pattern THEN
        -- Passthrough valid UUID (lowercase normalization)
        RETURN trimmed_input::UUID;
    END IF;

    -- 3. Reddit URL extraction
    -- Use SUBSTRING to extract the Reddit ID from URLs
    -- This handles URLs like: https://reddit.com/r/subreddit/comments/abc123/title
    -- and: https://reddit.com/comments/abc123/title
    IF trimmed_input ~ 'reddit\.com.*comments/([a-zA-Z0-9]{6,})' THEN
        -- Extract using SUBSTRING which is more reliable than REGEXP_REPLACE
        RETURN uuid5_generate(redditharbor_namespace(), SUBSTRING(trimmed_input FROM 'reddit\.com.*comments/([a-zA-Z0-9]{6,})'));
    END IF;

    -- 4. Generate deterministic UUID for all other valid inputs
    -- This handles direct Reddit IDs and other string formats
    RETURN uuid5_generate(redditharbor_namespace(), trimmed_input);
END;
$_$;


ALTER FUNCTION public.normalize_submission_id(input_id text) OWNER TO postgres;

--
-- Name: redditharbor_namespace(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.redditharbor_namespace() RETURNS uuid
    LANGUAGE sql IMMUTABLE
    AS $$
    SELECT '67959699-bbd7-5213-8934-bbfccb37697b'::UUID;
$$;


ALTER FUNCTION public.redditharbor_namespace() OWNER TO postgres;

--
-- Name: uuid5_generate(uuid, text); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.uuid5_generate(namespace_uuid uuid, name_string text) RETURNS uuid
    LANGUAGE sql IMMUTABLE
    AS $$
    -- Use PostgreSQL's built-in uuid_generate_v5 function for RFC 4122 compliance
    SELECT CASE
        WHEN name_string IS NULL OR name_string = '' THEN NULL
        ELSE uuid_generate_v5(namespace_uuid, name_string)
    END;
$$;


ALTER FUNCTION public.uuid5_generate(namespace_uuid uuid, name_string text) OWNER TO postgres;

--
-- Name: add_prefixes(text, text); Type: FUNCTION; Schema: storage; Owner: supabase_storage_admin
--

CREATE FUNCTION storage.add_prefixes(_bucket_id text, _name text) RETURNS void
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
DECLARE
    prefixes text[];
BEGIN
    prefixes := "storage"."get_prefixes"("_name");

    IF array_length(prefixes, 1) > 0 THEN
        INSERT INTO storage.prefixes (name, bucket_id)
        SELECT UNNEST(prefixes) as name, "_bucket_id" ON CONFLICT DO NOTHING;
    END IF;
END;
$$;


ALTER FUNCTION storage.add_prefixes(_bucket_id text, _name text) OWNER TO supabase_storage_admin;

--
-- Name: can_insert_object(text, text, uuid, jsonb); Type: FUNCTION; Schema: storage; Owner: supabase_storage_admin
--

CREATE FUNCTION storage.can_insert_object(bucketid text, name text, owner uuid, metadata jsonb) RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
  INSERT INTO "storage"."objects" ("bucket_id", "name", "owner", "metadata") VALUES (bucketid, name, owner, metadata);
  -- hack to rollback the successful insert
  RAISE sqlstate 'PT200' using
  message = 'ROLLBACK',
  detail = 'rollback successful insert';
END
$$;


ALTER FUNCTION storage.can_insert_object(bucketid text, name text, owner uuid, metadata jsonb) OWNER TO supabase_storage_admin;

--
-- Name: delete_prefix(text, text); Type: FUNCTION; Schema: storage; Owner: supabase_storage_admin
--

CREATE FUNCTION storage.delete_prefix(_bucket_id text, _name text) RETURNS boolean
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
BEGIN
    -- Check if we can delete the prefix
    IF EXISTS(
        SELECT FROM "storage"."prefixes"
        WHERE "prefixes"."bucket_id" = "_bucket_id"
          AND level = "storage"."get_level"("_name") + 1
          AND "prefixes"."name" COLLATE "C" LIKE "_name" || '/%'
        LIMIT 1
    )
    OR EXISTS(
        SELECT FROM "storage"."objects"
        WHERE "objects"."bucket_id" = "_bucket_id"
          AND "storage"."get_level"("objects"."name") = "storage"."get_level"("_name") + 1
          AND "objects"."name" COLLATE "C" LIKE "_name" || '/%'
        LIMIT 1
    ) THEN
    -- There are sub-objects, skip deletion
    RETURN false;
    ELSE
        DELETE FROM "storage"."prefixes"
        WHERE "prefixes"."bucket_id" = "_bucket_id"
          AND level = "storage"."get_level"("_name")
          AND "prefixes"."name" = "_name";
        RETURN true;
    END IF;
END;
$$;


ALTER FUNCTION storage.delete_prefix(_bucket_id text, _name text) OWNER TO supabase_storage_admin;

--
-- Name: delete_prefix_hierarchy_trigger(); Type: FUNCTION; Schema: storage; Owner: supabase_storage_admin
--

CREATE FUNCTION storage.delete_prefix_hierarchy_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
    prefix text;
BEGIN
    prefix := "storage"."get_prefix"(OLD."name");

    IF coalesce(prefix, '') != '' THEN
        PERFORM "storage"."delete_prefix"(OLD."bucket_id", prefix);
    END IF;

    RETURN OLD;
END;
$$;


ALTER FUNCTION storage.delete_prefix_hierarchy_trigger() OWNER TO supabase_storage_admin;

--
-- Name: enforce_bucket_name_length(); Type: FUNCTION; Schema: storage; Owner: supabase_storage_admin
--

CREATE FUNCTION storage.enforce_bucket_name_length() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
begin
    if length(new.name) > 100 then
        raise exception 'bucket name "%" is too long (% characters). Max is 100.', new.name, length(new.name);
    end if;
    return new;
end;
$$;


ALTER FUNCTION storage.enforce_bucket_name_length() OWNER TO supabase_storage_admin;

--
-- Name: extension(text); Type: FUNCTION; Schema: storage; Owner: supabase_storage_admin
--

CREATE FUNCTION storage.extension(name text) RETURNS text
    LANGUAGE plpgsql IMMUTABLE
    AS $$
DECLARE
    _parts text[];
    _filename text;
BEGIN
    SELECT string_to_array(name, '/') INTO _parts;
    SELECT _parts[array_length(_parts,1)] INTO _filename;
    RETURN reverse(split_part(reverse(_filename), '.', 1));
END
$$;


ALTER FUNCTION storage.extension(name text) OWNER TO supabase_storage_admin;

--
-- Name: filename(text); Type: FUNCTION; Schema: storage; Owner: supabase_storage_admin
--

CREATE FUNCTION storage.filename(name text) RETURNS text
    LANGUAGE plpgsql
    AS $$
DECLARE
_parts text[];
BEGIN
	select string_to_array(name, '/') into _parts;
	return _parts[array_length(_parts,1)];
END
$$;


ALTER FUNCTION storage.filename(name text) OWNER TO supabase_storage_admin;

--
-- Name: foldername(text); Type: FUNCTION; Schema: storage; Owner: supabase_storage_admin
--

CREATE FUNCTION storage.foldername(name text) RETURNS text[]
    LANGUAGE plpgsql IMMUTABLE
    AS $$
DECLARE
    _parts text[];
BEGIN
    -- Split on "/" to get path segments
    SELECT string_to_array(name, '/') INTO _parts;
    -- Return everything except the last segment
    RETURN _parts[1 : array_length(_parts,1) - 1];
END
$$;


ALTER FUNCTION storage.foldername(name text) OWNER TO supabase_storage_admin;

--
-- Name: get_level(text); Type: FUNCTION; Schema: storage; Owner: supabase_storage_admin
--

CREATE FUNCTION storage.get_level(name text) RETURNS integer
    LANGUAGE sql IMMUTABLE STRICT
    AS $$
SELECT array_length(string_to_array("name", '/'), 1);
$$;


ALTER FUNCTION storage.get_level(name text) OWNER TO supabase_storage_admin;

--
-- Name: get_prefix(text); Type: FUNCTION; Schema: storage; Owner: supabase_storage_admin
--

CREATE FUNCTION storage.get_prefix(name text) RETURNS text
    LANGUAGE sql IMMUTABLE STRICT
    AS $_$
SELECT
    CASE WHEN strpos("name", '/') > 0 THEN
             regexp_replace("name", '[\/]{1}[^\/]+\/?$', '')
         ELSE
             ''
        END;
$_$;


ALTER FUNCTION storage.get_prefix(name text) OWNER TO supabase_storage_admin;

--
-- Name: get_prefixes(text); Type: FUNCTION; Schema: storage; Owner: supabase_storage_admin
--

CREATE FUNCTION storage.get_prefixes(name text) RETURNS text[]
    LANGUAGE plpgsql IMMUTABLE STRICT
    AS $$
DECLARE
    parts text[];
    prefixes text[];
    prefix text;
BEGIN
    -- Split the name into parts by '/'
    parts := string_to_array("name", '/');
    prefixes := '{}';

    -- Construct the prefixes, stopping one level below the last part
    FOR i IN 1..array_length(parts, 1) - 1 LOOP
            prefix := array_to_string(parts[1:i], '/');
            prefixes := array_append(prefixes, prefix);
    END LOOP;

    RETURN prefixes;
END;
$$;


ALTER FUNCTION storage.get_prefixes(name text) OWNER TO supabase_storage_admin;

--
-- Name: get_size_by_bucket(); Type: FUNCTION; Schema: storage; Owner: supabase_storage_admin
--

CREATE FUNCTION storage.get_size_by_bucket() RETURNS TABLE(size bigint, bucket_id text)
    LANGUAGE plpgsql STABLE
    AS $$
BEGIN
    return query
        select sum((metadata->>'size')::bigint) as size, obj.bucket_id
        from "storage".objects as obj
        group by obj.bucket_id;
END
$$;


ALTER FUNCTION storage.get_size_by_bucket() OWNER TO supabase_storage_admin;

--
-- Name: list_multipart_uploads_with_delimiter(text, text, text, integer, text, text); Type: FUNCTION; Schema: storage; Owner: supabase_storage_admin
--

CREATE FUNCTION storage.list_multipart_uploads_with_delimiter(bucket_id text, prefix_param text, delimiter_param text, max_keys integer DEFAULT 100, next_key_token text DEFAULT ''::text, next_upload_token text DEFAULT ''::text) RETURNS TABLE(key text, id text, created_at timestamp with time zone)
    LANGUAGE plpgsql
    AS $_$
BEGIN
    RETURN QUERY EXECUTE
        'SELECT DISTINCT ON(key COLLATE "C") * from (
            SELECT
                CASE
                    WHEN position($2 IN substring(key from length($1) + 1)) > 0 THEN
                        substring(key from 1 for length($1) + position($2 IN substring(key from length($1) + 1)))
                    ELSE
                        key
                END AS key, id, created_at
            FROM
                storage.s3_multipart_uploads
            WHERE
                bucket_id = $5 AND
                key ILIKE $1 || ''%'' AND
                CASE
                    WHEN $4 != '''' AND $6 = '''' THEN
                        CASE
                            WHEN position($2 IN substring(key from length($1) + 1)) > 0 THEN
                                substring(key from 1 for length($1) + position($2 IN substring(key from length($1) + 1))) COLLATE "C" > $4
                            ELSE
                                key COLLATE "C" > $4
                            END
                    ELSE
                        true
                END AND
                CASE
                    WHEN $6 != '''' THEN
                        id COLLATE "C" > $6
                    ELSE
                        true
                    END
            ORDER BY
                key COLLATE "C" ASC, created_at ASC) as e order by key COLLATE "C" LIMIT $3'
        USING prefix_param, delimiter_param, max_keys, next_key_token, bucket_id, next_upload_token;
END;
$_$;


ALTER FUNCTION storage.list_multipart_uploads_with_delimiter(bucket_id text, prefix_param text, delimiter_param text, max_keys integer, next_key_token text, next_upload_token text) OWNER TO supabase_storage_admin;

--
-- Name: list_objects_with_delimiter(text, text, text, integer, text, text); Type: FUNCTION; Schema: storage; Owner: supabase_storage_admin
--

CREATE FUNCTION storage.list_objects_with_delimiter(bucket_id text, prefix_param text, delimiter_param text, max_keys integer DEFAULT 100, start_after text DEFAULT ''::text, next_token text DEFAULT ''::text) RETURNS TABLE(name text, id uuid, metadata jsonb, updated_at timestamp with time zone)
    LANGUAGE plpgsql
    AS $_$
BEGIN
    RETURN QUERY EXECUTE
        'SELECT DISTINCT ON(name COLLATE "C") * from (
            SELECT
                CASE
                    WHEN position($2 IN substring(name from length($1) + 1)) > 0 THEN
                        substring(name from 1 for length($1) + position($2 IN substring(name from length($1) + 1)))
                    ELSE
                        name
                END AS name, id, metadata, updated_at
            FROM
                storage.objects
            WHERE
                bucket_id = $5 AND
                name ILIKE $1 || ''%'' AND
                CASE
                    WHEN $6 != '''' THEN
                    name COLLATE "C" > $6
                ELSE true END
                AND CASE
                    WHEN $4 != '''' THEN
                        CASE
                            WHEN position($2 IN substring(name from length($1) + 1)) > 0 THEN
                                substring(name from 1 for length($1) + position($2 IN substring(name from length($1) + 1))) COLLATE "C" > $4
                            ELSE
                                name COLLATE "C" > $4
                            END
                    ELSE
                        true
                END
            ORDER BY
                name COLLATE "C" ASC) as e order by name COLLATE "C" LIMIT $3'
        USING prefix_param, delimiter_param, max_keys, next_token, bucket_id, start_after;
END;
$_$;


ALTER FUNCTION storage.list_objects_with_delimiter(bucket_id text, prefix_param text, delimiter_param text, max_keys integer, start_after text, next_token text) OWNER TO supabase_storage_admin;

--
-- Name: objects_insert_prefix_trigger(); Type: FUNCTION; Schema: storage; Owner: supabase_storage_admin
--

CREATE FUNCTION storage.objects_insert_prefix_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    PERFORM "storage"."add_prefixes"(NEW."bucket_id", NEW."name");
    NEW.level := "storage"."get_level"(NEW."name");

    RETURN NEW;
END;
$$;


ALTER FUNCTION storage.objects_insert_prefix_trigger() OWNER TO supabase_storage_admin;

--
-- Name: objects_update_prefix_trigger(); Type: FUNCTION; Schema: storage; Owner: supabase_storage_admin
--

CREATE FUNCTION storage.objects_update_prefix_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
    old_prefixes TEXT[];
BEGIN
    -- Ensure this is an update operation and the name has changed
    IF TG_OP = 'UPDATE' AND (NEW."name" <> OLD."name" OR NEW."bucket_id" <> OLD."bucket_id") THEN
        -- Retrieve old prefixes
        old_prefixes := "storage"."get_prefixes"(OLD."name");

        -- Remove old prefixes that are only used by this object
        WITH all_prefixes as (
            SELECT unnest(old_prefixes) as prefix
        ),
        can_delete_prefixes as (
             SELECT prefix
             FROM all_prefixes
             WHERE NOT EXISTS (
                 SELECT 1 FROM "storage"."objects"
                 WHERE "bucket_id" = OLD."bucket_id"
                   AND "name" <> OLD."name"
                   AND "name" LIKE (prefix || '%')
             )
         )
        DELETE FROM "storage"."prefixes" WHERE name IN (SELECT prefix FROM can_delete_prefixes);

        -- Add new prefixes
        PERFORM "storage"."add_prefixes"(NEW."bucket_id", NEW."name");
    END IF;
    -- Set the new level
    NEW."level" := "storage"."get_level"(NEW."name");

    RETURN NEW;
END;
$$;


ALTER FUNCTION storage.objects_update_prefix_trigger() OWNER TO supabase_storage_admin;

--
-- Name: operation(); Type: FUNCTION; Schema: storage; Owner: supabase_storage_admin
--

CREATE FUNCTION storage.operation() RETURNS text
    LANGUAGE plpgsql STABLE
    AS $$
BEGIN
    RETURN current_setting('storage.operation', true);
END;
$$;


ALTER FUNCTION storage.operation() OWNER TO supabase_storage_admin;

--
-- Name: prefixes_insert_trigger(); Type: FUNCTION; Schema: storage; Owner: supabase_storage_admin
--

CREATE FUNCTION storage.prefixes_insert_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    PERFORM "storage"."add_prefixes"(NEW."bucket_id", NEW."name");
    RETURN NEW;
END;
$$;


ALTER FUNCTION storage.prefixes_insert_trigger() OWNER TO supabase_storage_admin;

--
-- Name: search(text, text, integer, integer, integer, text, text, text); Type: FUNCTION; Schema: storage; Owner: supabase_storage_admin
--

CREATE FUNCTION storage.search(prefix text, bucketname text, limits integer DEFAULT 100, levels integer DEFAULT 1, offsets integer DEFAULT 0, search text DEFAULT ''::text, sortcolumn text DEFAULT 'name'::text, sortorder text DEFAULT 'asc'::text) RETURNS TABLE(name text, id uuid, updated_at timestamp with time zone, created_at timestamp with time zone, last_accessed_at timestamp with time zone, metadata jsonb)
    LANGUAGE plpgsql
    AS $$
declare
    can_bypass_rls BOOLEAN;
begin
    SELECT rolbypassrls
    INTO can_bypass_rls
    FROM pg_roles
    WHERE rolname = coalesce(nullif(current_setting('role', true), 'none'), current_user);

    IF can_bypass_rls THEN
        RETURN QUERY SELECT * FROM storage.search_v1_optimised(prefix, bucketname, limits, levels, offsets, search, sortcolumn, sortorder);
    ELSE
        RETURN QUERY SELECT * FROM storage.search_legacy_v1(prefix, bucketname, limits, levels, offsets, search, sortcolumn, sortorder);
    END IF;
end;
$$;


ALTER FUNCTION storage.search(prefix text, bucketname text, limits integer, levels integer, offsets integer, search text, sortcolumn text, sortorder text) OWNER TO supabase_storage_admin;

--
-- Name: search_legacy_v1(text, text, integer, integer, integer, text, text, text); Type: FUNCTION; Schema: storage; Owner: supabase_storage_admin
--

CREATE FUNCTION storage.search_legacy_v1(prefix text, bucketname text, limits integer DEFAULT 100, levels integer DEFAULT 1, offsets integer DEFAULT 0, search text DEFAULT ''::text, sortcolumn text DEFAULT 'name'::text, sortorder text DEFAULT 'asc'::text) RETURNS TABLE(name text, id uuid, updated_at timestamp with time zone, created_at timestamp with time zone, last_accessed_at timestamp with time zone, metadata jsonb)
    LANGUAGE plpgsql STABLE
    AS $_$
declare
    v_order_by text;
    v_sort_order text;
begin
    case
        when sortcolumn = 'name' then
            v_order_by = 'name';
        when sortcolumn = 'updated_at' then
            v_order_by = 'updated_at';
        when sortcolumn = 'created_at' then
            v_order_by = 'created_at';
        when sortcolumn = 'last_accessed_at' then
            v_order_by = 'last_accessed_at';
        else
            v_order_by = 'name';
        end case;

    case
        when sortorder = 'asc' then
            v_sort_order = 'asc';
        when sortorder = 'desc' then
            v_sort_order = 'desc';
        else
            v_sort_order = 'asc';
        end case;

    v_order_by = v_order_by || ' ' || v_sort_order;

    return query execute
        'with folders as (
           select path_tokens[$1] as folder
           from storage.objects
             where objects.name ilike $2 || $3 || ''%''
               and bucket_id = $4
               and array_length(objects.path_tokens, 1) <> $1
           group by folder
           order by folder ' || v_sort_order || '
     )
     (select folder as "name",
            null as id,
            null as updated_at,
            null as created_at,
            null as last_accessed_at,
            null as metadata from folders)
     union all
     (select path_tokens[$1] as "name",
            id,
            updated_at,
            created_at,
            last_accessed_at,
            metadata
     from storage.objects
     where objects.name ilike $2 || $3 || ''%''
       and bucket_id = $4
       and array_length(objects.path_tokens, 1) = $1
     order by ' || v_order_by || ')
     limit $5
     offset $6' using levels, prefix, search, bucketname, limits, offsets;
end;
$_$;


ALTER FUNCTION storage.search_legacy_v1(prefix text, bucketname text, limits integer, levels integer, offsets integer, search text, sortcolumn text, sortorder text) OWNER TO supabase_storage_admin;

--
-- Name: search_v1_optimised(text, text, integer, integer, integer, text, text, text); Type: FUNCTION; Schema: storage; Owner: supabase_storage_admin
--

CREATE FUNCTION storage.search_v1_optimised(prefix text, bucketname text, limits integer DEFAULT 100, levels integer DEFAULT 1, offsets integer DEFAULT 0, search text DEFAULT ''::text, sortcolumn text DEFAULT 'name'::text, sortorder text DEFAULT 'asc'::text) RETURNS TABLE(name text, id uuid, updated_at timestamp with time zone, created_at timestamp with time zone, last_accessed_at timestamp with time zone, metadata jsonb)
    LANGUAGE plpgsql STABLE
    AS $_$
declare
    v_order_by text;
    v_sort_order text;
begin
    case
        when sortcolumn = 'name' then
            v_order_by = 'name';
        when sortcolumn = 'updated_at' then
            v_order_by = 'updated_at';
        when sortcolumn = 'created_at' then
            v_order_by = 'created_at';
        when sortcolumn = 'last_accessed_at' then
            v_order_by = 'last_accessed_at';
        else
            v_order_by = 'name';
        end case;

    case
        when sortorder = 'asc' then
            v_sort_order = 'asc';
        when sortorder = 'desc' then
            v_sort_order = 'desc';
        else
            v_sort_order = 'asc';
        end case;

    v_order_by = v_order_by || ' ' || v_sort_order;

    return query execute
        'with folders as (
           select (string_to_array(name, ''/''))[level] as name
           from storage.prefixes
             where lower(prefixes.name) like lower($2 || $3) || ''%''
               and bucket_id = $4
               and level = $1
           order by name ' || v_sort_order || '
     )
     (select name,
            null as id,
            null as updated_at,
            null as created_at,
            null as last_accessed_at,
            null as metadata from folders)
     union all
     (select path_tokens[level] as "name",
            id,
            updated_at,
            created_at,
            last_accessed_at,
            metadata
     from storage.objects
     where lower(objects.name) like lower($2 || $3) || ''%''
       and bucket_id = $4
       and level = $1
     order by ' || v_order_by || ')
     limit $5
     offset $6' using levels, prefix, search, bucketname, limits, offsets;
end;
$_$;


ALTER FUNCTION storage.search_v1_optimised(prefix text, bucketname text, limits integer, levels integer, offsets integer, search text, sortcolumn text, sortorder text) OWNER TO supabase_storage_admin;

--
-- Name: search_v2(text, text, integer, integer, text); Type: FUNCTION; Schema: storage; Owner: supabase_storage_admin
--

CREATE FUNCTION storage.search_v2(prefix text, bucket_name text, limits integer DEFAULT 100, levels integer DEFAULT 1, start_after text DEFAULT ''::text) RETURNS TABLE(key text, name text, id uuid, updated_at timestamp with time zone, created_at timestamp with time zone, metadata jsonb)
    LANGUAGE plpgsql STABLE
    AS $_$
BEGIN
    RETURN query EXECUTE
        $sql$
        SELECT * FROM (
            (
                SELECT
                    split_part(name, '/', $4) AS key,
                    name || '/' AS name,
                    NULL::uuid AS id,
                    NULL::timestamptz AS updated_at,
                    NULL::timestamptz AS created_at,
                    NULL::jsonb AS metadata
                FROM storage.prefixes
                WHERE name COLLATE "C" LIKE $1 || '%'
                AND bucket_id = $2
                AND level = $4
                AND name COLLATE "C" > $5
                ORDER BY prefixes.name COLLATE "C" LIMIT $3
            )
            UNION ALL
            (SELECT split_part(name, '/', $4) AS key,
                name,
                id,
                updated_at,
                created_at,
                metadata
            FROM storage.objects
            WHERE name COLLATE "C" LIKE $1 || '%'
                AND bucket_id = $2
                AND level = $4
                AND name COLLATE "C" > $5
            ORDER BY name COLLATE "C" LIMIT $3)
        ) obj
        ORDER BY name COLLATE "C" LIMIT $3;
        $sql$
        USING prefix, bucket_name, limits, levels, start_after;
END;
$_$;


ALTER FUNCTION storage.search_v2(prefix text, bucket_name text, limits integer, levels integer, start_after text) OWNER TO supabase_storage_admin;

--
-- Name: update_updated_at_column(); Type: FUNCTION; Schema: storage; Owner: supabase_storage_admin
--

CREATE FUNCTION storage.update_updated_at_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW; 
END;
$$;


ALTER FUNCTION storage.update_updated_at_column() OWNER TO supabase_storage_admin;

--
-- Name: http_request(); Type: FUNCTION; Schema: supabase_functions; Owner: supabase_functions_admin
--

CREATE FUNCTION supabase_functions.http_request() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'supabase_functions'
    AS $$
  DECLARE
    request_id bigint;
    payload jsonb;
    url text := TG_ARGV[0]::text;
    method text := TG_ARGV[1]::text;
    headers jsonb DEFAULT '{}'::jsonb;
    params jsonb DEFAULT '{}'::jsonb;
    timeout_ms integer DEFAULT 1000;
  BEGIN
    IF url IS NULL OR url = 'null' THEN
      RAISE EXCEPTION 'url argument is missing';
    END IF;

    IF method IS NULL OR method = 'null' THEN
      RAISE EXCEPTION 'method argument is missing';
    END IF;

    IF TG_ARGV[2] IS NULL OR TG_ARGV[2] = 'null' THEN
      headers = '{"Content-Type": "application/json"}'::jsonb;
    ELSE
      headers = TG_ARGV[2]::jsonb;
    END IF;

    IF TG_ARGV[3] IS NULL OR TG_ARGV[3] = 'null' THEN
      params = '{}'::jsonb;
    ELSE
      params = TG_ARGV[3]::jsonb;
    END IF;

    IF TG_ARGV[4] IS NULL OR TG_ARGV[4] = 'null' THEN
      timeout_ms = 1000;
    ELSE
      timeout_ms = TG_ARGV[4]::integer;
    END IF;

    CASE
      WHEN method = 'GET' THEN
        SELECT http_get INTO request_id FROM net.http_get(
          url,
          params,
          headers,
          timeout_ms
        );
      WHEN method = 'POST' THEN
        payload = jsonb_build_object(
          'old_record', OLD,
          'record', NEW,
          'type', TG_OP,
          'table', TG_TABLE_NAME,
          'schema', TG_TABLE_SCHEMA
        );

        SELECT http_post INTO request_id FROM net.http_post(
          url,
          payload,
          params,
          headers,
          timeout_ms
        );
      ELSE
        RAISE EXCEPTION 'method argument % is invalid', method;
    END CASE;

    INSERT INTO supabase_functions.hooks
      (hook_table_id, hook_name, request_id)
    VALUES
      (TG_RELID, TG_NAME, request_id);

    RETURN NEW;
  END
$$;


ALTER FUNCTION supabase_functions.http_request() OWNER TO supabase_functions_admin;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: _dlt_loads; Type: TABLE; Schema: app_opportunities; Owner: postgres
--

CREATE TABLE app_opportunities._dlt_loads (
    load_id character varying(64) NOT NULL,
    schema_name character varying,
    status bigint NOT NULL,
    inserted_at timestamp with time zone NOT NULL,
    schema_version_hash character varying
);


ALTER TABLE app_opportunities._dlt_loads OWNER TO postgres;

--
-- Name: _dlt_pipeline_state; Type: TABLE; Schema: app_opportunities; Owner: postgres
--

CREATE TABLE app_opportunities._dlt_pipeline_state (
    version bigint NOT NULL,
    engine_version bigint NOT NULL,
    pipeline_name character varying NOT NULL,
    state character varying NOT NULL,
    created_at timestamp with time zone NOT NULL,
    version_hash character varying,
    _dlt_load_id character varying(64) NOT NULL,
    _dlt_id character varying NOT NULL
);


ALTER TABLE app_opportunities._dlt_pipeline_state OWNER TO postgres;

--
-- Name: _dlt_version; Type: TABLE; Schema: app_opportunities; Owner: postgres
--

CREATE TABLE app_opportunities._dlt_version (
    version bigint NOT NULL,
    engine_version bigint NOT NULL,
    inserted_at timestamp with time zone NOT NULL,
    schema_name character varying NOT NULL,
    version_hash character varying NOT NULL,
    schema character varying NOT NULL
);


ALTER TABLE app_opportunities._dlt_version OWNER TO postgres;

--
-- Name: app_opportunities; Type: TABLE; Schema: app_opportunities; Owner: postgres
--

CREATE TABLE app_opportunities.app_opportunities (
    submission_id character varying NOT NULL,
    title character varying,
    text character varying,
    subreddit character varying,
    upvotes bigint,
    comments_count bigint,
    score double precision,
    created_utc timestamp with time zone,
    quality_score double precision,
    trust_score double precision,
    processed_at timestamp with time zone,
    pipeline_version character varying,
    _dlt_load_id character varying NOT NULL,
    _dlt_id character varying NOT NULL
);


ALTER TABLE app_opportunities.app_opportunities OWNER TO postgres;

--
-- Name: _dlt_version; Type: TABLE; Schema: app_opportunities_staging; Owner: postgres
--

CREATE TABLE app_opportunities_staging._dlt_version (
    version bigint NOT NULL,
    engine_version bigint NOT NULL,
    inserted_at timestamp with time zone NOT NULL,
    schema_name character varying NOT NULL,
    version_hash character varying NOT NULL,
    schema character varying NOT NULL
);


ALTER TABLE app_opportunities_staging._dlt_version OWNER TO postgres;

--
-- Name: app_opportunities; Type: TABLE; Schema: app_opportunities_staging; Owner: postgres
--

CREATE TABLE app_opportunities_staging.app_opportunities (
    submission_id character varying NOT NULL,
    title character varying,
    text character varying,
    subreddit character varying,
    upvotes bigint,
    comments_count bigint,
    score double precision,
    created_utc timestamp with time zone,
    quality_score double precision,
    trust_score double precision,
    processed_at timestamp with time zone,
    pipeline_version character varying,
    _dlt_load_id character varying NOT NULL,
    _dlt_id character varying NOT NULL
);


ALTER TABLE app_opportunities_staging.app_opportunities OWNER TO postgres;

--
-- Name: audit_log_entries; Type: TABLE; Schema: auth; Owner: supabase_auth_admin
--

CREATE TABLE auth.audit_log_entries (
    instance_id uuid,
    id uuid NOT NULL,
    payload json,
    created_at timestamp with time zone,
    ip_address character varying(64) DEFAULT ''::character varying NOT NULL
);


ALTER TABLE auth.audit_log_entries OWNER TO supabase_auth_admin;

--
-- Name: TABLE audit_log_entries; Type: COMMENT; Schema: auth; Owner: supabase_auth_admin
--

COMMENT ON TABLE auth.audit_log_entries IS 'Auth: Audit trail for user actions.';


--
-- Name: flow_state; Type: TABLE; Schema: auth; Owner: supabase_auth_admin
--

CREATE TABLE auth.flow_state (
    id uuid NOT NULL,
    user_id uuid,
    auth_code text NOT NULL,
    code_challenge_method auth.code_challenge_method NOT NULL,
    code_challenge text NOT NULL,
    provider_type text NOT NULL,
    provider_access_token text,
    provider_refresh_token text,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    authentication_method text NOT NULL,
    auth_code_issued_at timestamp with time zone
);


ALTER TABLE auth.flow_state OWNER TO supabase_auth_admin;

--
-- Name: TABLE flow_state; Type: COMMENT; Schema: auth; Owner: supabase_auth_admin
--

COMMENT ON TABLE auth.flow_state IS 'stores metadata for pkce logins';


--
-- Name: identities; Type: TABLE; Schema: auth; Owner: supabase_auth_admin
--

CREATE TABLE auth.identities (
    provider_id text NOT NULL,
    user_id uuid NOT NULL,
    identity_data jsonb NOT NULL,
    provider text NOT NULL,
    last_sign_in_at timestamp with time zone,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    email text GENERATED ALWAYS AS (lower((identity_data ->> 'email'::text))) STORED,
    id uuid DEFAULT gen_random_uuid() NOT NULL
);


ALTER TABLE auth.identities OWNER TO supabase_auth_admin;

--
-- Name: TABLE identities; Type: COMMENT; Schema: auth; Owner: supabase_auth_admin
--

COMMENT ON TABLE auth.identities IS 'Auth: Stores identities associated to a user.';


--
-- Name: COLUMN identities.email; Type: COMMENT; Schema: auth; Owner: supabase_auth_admin
--

COMMENT ON COLUMN auth.identities.email IS 'Auth: Email is a generated column that references the optional email property in the identity_data';


--
-- Name: instances; Type: TABLE; Schema: auth; Owner: supabase_auth_admin
--

CREATE TABLE auth.instances (
    id uuid NOT NULL,
    uuid uuid,
    raw_base_config text,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


ALTER TABLE auth.instances OWNER TO supabase_auth_admin;

--
-- Name: TABLE instances; Type: COMMENT; Schema: auth; Owner: supabase_auth_admin
--

COMMENT ON TABLE auth.instances IS 'Auth: Manages users across multiple sites.';


--
-- Name: mfa_amr_claims; Type: TABLE; Schema: auth; Owner: supabase_auth_admin
--

CREATE TABLE auth.mfa_amr_claims (
    session_id uuid NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    authentication_method text NOT NULL,
    id uuid NOT NULL
);


ALTER TABLE auth.mfa_amr_claims OWNER TO supabase_auth_admin;

--
-- Name: TABLE mfa_amr_claims; Type: COMMENT; Schema: auth; Owner: supabase_auth_admin
--

COMMENT ON TABLE auth.mfa_amr_claims IS 'auth: stores authenticator method reference claims for multi factor authentication';


--
-- Name: mfa_challenges; Type: TABLE; Schema: auth; Owner: supabase_auth_admin
--

CREATE TABLE auth.mfa_challenges (
    id uuid NOT NULL,
    factor_id uuid NOT NULL,
    created_at timestamp with time zone NOT NULL,
    verified_at timestamp with time zone,
    ip_address inet NOT NULL,
    otp_code text,
    web_authn_session_data jsonb
);


ALTER TABLE auth.mfa_challenges OWNER TO supabase_auth_admin;

--
-- Name: TABLE mfa_challenges; Type: COMMENT; Schema: auth; Owner: supabase_auth_admin
--

COMMENT ON TABLE auth.mfa_challenges IS 'auth: stores metadata about challenge requests made';


--
-- Name: mfa_factors; Type: TABLE; Schema: auth; Owner: supabase_auth_admin
--

CREATE TABLE auth.mfa_factors (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    friendly_name text,
    factor_type auth.factor_type NOT NULL,
    status auth.factor_status NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    secret text,
    phone text,
    last_challenged_at timestamp with time zone,
    web_authn_credential jsonb,
    web_authn_aaguid uuid
);


ALTER TABLE auth.mfa_factors OWNER TO supabase_auth_admin;

--
-- Name: TABLE mfa_factors; Type: COMMENT; Schema: auth; Owner: supabase_auth_admin
--

COMMENT ON TABLE auth.mfa_factors IS 'auth: stores metadata about factors';


--
-- Name: one_time_tokens; Type: TABLE; Schema: auth; Owner: supabase_auth_admin
--

CREATE TABLE auth.one_time_tokens (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    token_type auth.one_time_token_type NOT NULL,
    token_hash text NOT NULL,
    relates_to text NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    CONSTRAINT one_time_tokens_token_hash_check CHECK ((char_length(token_hash) > 0))
);


ALTER TABLE auth.one_time_tokens OWNER TO supabase_auth_admin;

--
-- Name: refresh_tokens; Type: TABLE; Schema: auth; Owner: supabase_auth_admin
--

CREATE TABLE auth.refresh_tokens (
    instance_id uuid,
    id bigint NOT NULL,
    token character varying(255),
    user_id character varying(255),
    revoked boolean,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    parent character varying(255),
    session_id uuid
);


ALTER TABLE auth.refresh_tokens OWNER TO supabase_auth_admin;

--
-- Name: TABLE refresh_tokens; Type: COMMENT; Schema: auth; Owner: supabase_auth_admin
--

COMMENT ON TABLE auth.refresh_tokens IS 'Auth: Store of tokens used to refresh JWT tokens once they expire.';


--
-- Name: refresh_tokens_id_seq; Type: SEQUENCE; Schema: auth; Owner: supabase_auth_admin
--

CREATE SEQUENCE auth.refresh_tokens_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE auth.refresh_tokens_id_seq OWNER TO supabase_auth_admin;

--
-- Name: refresh_tokens_id_seq; Type: SEQUENCE OWNED BY; Schema: auth; Owner: supabase_auth_admin
--

ALTER SEQUENCE auth.refresh_tokens_id_seq OWNED BY auth.refresh_tokens.id;


--
-- Name: saml_providers; Type: TABLE; Schema: auth; Owner: supabase_auth_admin
--

CREATE TABLE auth.saml_providers (
    id uuid NOT NULL,
    sso_provider_id uuid NOT NULL,
    entity_id text NOT NULL,
    metadata_xml text NOT NULL,
    metadata_url text,
    attribute_mapping jsonb,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    name_id_format text,
    CONSTRAINT "entity_id not empty" CHECK ((char_length(entity_id) > 0)),
    CONSTRAINT "metadata_url not empty" CHECK (((metadata_url = NULL::text) OR (char_length(metadata_url) > 0))),
    CONSTRAINT "metadata_xml not empty" CHECK ((char_length(metadata_xml) > 0))
);


ALTER TABLE auth.saml_providers OWNER TO supabase_auth_admin;

--
-- Name: TABLE saml_providers; Type: COMMENT; Schema: auth; Owner: supabase_auth_admin
--

COMMENT ON TABLE auth.saml_providers IS 'Auth: Manages SAML Identity Provider connections.';


--
-- Name: saml_relay_states; Type: TABLE; Schema: auth; Owner: supabase_auth_admin
--

CREATE TABLE auth.saml_relay_states (
    id uuid NOT NULL,
    sso_provider_id uuid NOT NULL,
    request_id text NOT NULL,
    for_email text,
    redirect_to text,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    flow_state_id uuid,
    CONSTRAINT "request_id not empty" CHECK ((char_length(request_id) > 0))
);


ALTER TABLE auth.saml_relay_states OWNER TO supabase_auth_admin;

--
-- Name: TABLE saml_relay_states; Type: COMMENT; Schema: auth; Owner: supabase_auth_admin
--

COMMENT ON TABLE auth.saml_relay_states IS 'Auth: Contains SAML Relay State information for each Service Provider initiated login.';


--
-- Name: schema_migrations; Type: TABLE; Schema: auth; Owner: supabase_auth_admin
--

CREATE TABLE auth.schema_migrations (
    version character varying(255) NOT NULL
);


ALTER TABLE auth.schema_migrations OWNER TO supabase_auth_admin;

--
-- Name: TABLE schema_migrations; Type: COMMENT; Schema: auth; Owner: supabase_auth_admin
--

COMMENT ON TABLE auth.schema_migrations IS 'Auth: Manages updates to the auth system.';


--
-- Name: sessions; Type: TABLE; Schema: auth; Owner: supabase_auth_admin
--

CREATE TABLE auth.sessions (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    factor_id uuid,
    aal auth.aal_level,
    not_after timestamp with time zone,
    refreshed_at timestamp without time zone,
    user_agent text,
    ip inet,
    tag text
);


ALTER TABLE auth.sessions OWNER TO supabase_auth_admin;

--
-- Name: TABLE sessions; Type: COMMENT; Schema: auth; Owner: supabase_auth_admin
--

COMMENT ON TABLE auth.sessions IS 'Auth: Stores session data associated to a user.';


--
-- Name: COLUMN sessions.not_after; Type: COMMENT; Schema: auth; Owner: supabase_auth_admin
--

COMMENT ON COLUMN auth.sessions.not_after IS 'Auth: Not after is a nullable column that contains a timestamp after which the session should be regarded as expired.';


--
-- Name: sso_domains; Type: TABLE; Schema: auth; Owner: supabase_auth_admin
--

CREATE TABLE auth.sso_domains (
    id uuid NOT NULL,
    sso_provider_id uuid NOT NULL,
    domain text NOT NULL,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    CONSTRAINT "domain not empty" CHECK ((char_length(domain) > 0))
);


ALTER TABLE auth.sso_domains OWNER TO supabase_auth_admin;

--
-- Name: TABLE sso_domains; Type: COMMENT; Schema: auth; Owner: supabase_auth_admin
--

COMMENT ON TABLE auth.sso_domains IS 'Auth: Manages SSO email address domain mapping to an SSO Identity Provider.';


--
-- Name: sso_providers; Type: TABLE; Schema: auth; Owner: supabase_auth_admin
--

CREATE TABLE auth.sso_providers (
    id uuid NOT NULL,
    resource_id text,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    disabled boolean,
    CONSTRAINT "resource_id not empty" CHECK (((resource_id = NULL::text) OR (char_length(resource_id) > 0)))
);


ALTER TABLE auth.sso_providers OWNER TO supabase_auth_admin;

--
-- Name: TABLE sso_providers; Type: COMMENT; Schema: auth; Owner: supabase_auth_admin
--

COMMENT ON TABLE auth.sso_providers IS 'Auth: Manages SSO identity provider information; see saml_providers for SAML.';


--
-- Name: COLUMN sso_providers.resource_id; Type: COMMENT; Schema: auth; Owner: supabase_auth_admin
--

COMMENT ON COLUMN auth.sso_providers.resource_id IS 'Auth: Uniquely identifies a SSO provider according to a user-chosen resource ID (case insensitive), useful in infrastructure as code.';


--
-- Name: users; Type: TABLE; Schema: auth; Owner: supabase_auth_admin
--

CREATE TABLE auth.users (
    instance_id uuid,
    id uuid NOT NULL,
    aud character varying(255),
    role character varying(255),
    email character varying(255),
    encrypted_password character varying(255),
    email_confirmed_at timestamp with time zone,
    invited_at timestamp with time zone,
    confirmation_token character varying(255),
    confirmation_sent_at timestamp with time zone,
    recovery_token character varying(255),
    recovery_sent_at timestamp with time zone,
    email_change_token_new character varying(255),
    email_change character varying(255),
    email_change_sent_at timestamp with time zone,
    last_sign_in_at timestamp with time zone,
    raw_app_meta_data jsonb,
    raw_user_meta_data jsonb,
    is_super_admin boolean,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    phone text DEFAULT NULL::character varying,
    phone_confirmed_at timestamp with time zone,
    phone_change text DEFAULT ''::character varying,
    phone_change_token character varying(255) DEFAULT ''::character varying,
    phone_change_sent_at timestamp with time zone,
    confirmed_at timestamp with time zone GENERATED ALWAYS AS (LEAST(email_confirmed_at, phone_confirmed_at)) STORED,
    email_change_token_current character varying(255) DEFAULT ''::character varying,
    email_change_confirm_status smallint DEFAULT 0,
    banned_until timestamp with time zone,
    reauthentication_token character varying(255) DEFAULT ''::character varying,
    reauthentication_sent_at timestamp with time zone,
    is_sso_user boolean DEFAULT false NOT NULL,
    deleted_at timestamp with time zone,
    is_anonymous boolean DEFAULT false NOT NULL,
    CONSTRAINT users_email_change_confirm_status_check CHECK (((email_change_confirm_status >= 0) AND (email_change_confirm_status <= 2)))
);


ALTER TABLE auth.users OWNER TO supabase_auth_admin;

--
-- Name: TABLE users; Type: COMMENT; Schema: auth; Owner: supabase_auth_admin
--

COMMENT ON TABLE auth.users IS 'Auth: Stores user login data within a secure schema.';


--
-- Name: COLUMN users.is_sso_user; Type: COMMENT; Schema: auth; Owner: supabase_auth_admin
--

COMMENT ON COLUMN auth.users.is_sso_user IS 'Auth: Set this column to true when the account comes from SSO. These accounts can have duplicate emails.';


--
-- Name: _dlt_loads; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public._dlt_loads (
    load_id character varying(64) NOT NULL,
    schema_name character varying,
    status bigint NOT NULL,
    inserted_at timestamp with time zone NOT NULL,
    schema_version_hash character varying
);


ALTER TABLE public._dlt_loads OWNER TO postgres;

--
-- Name: _dlt_pipeline_state; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public._dlt_pipeline_state (
    version bigint NOT NULL,
    engine_version bigint NOT NULL,
    pipeline_name character varying NOT NULL,
    state character varying NOT NULL,
    created_at timestamp with time zone NOT NULL,
    version_hash character varying,
    _dlt_load_id character varying(64) NOT NULL,
    _dlt_id character varying NOT NULL
);


ALTER TABLE public._dlt_pipeline_state OWNER TO postgres;

--
-- Name: _dlt_version; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public._dlt_version (
    version bigint NOT NULL,
    engine_version bigint NOT NULL,
    inserted_at timestamp with time zone NOT NULL,
    schema_name character varying NOT NULL,
    version_hash character varying NOT NULL,
    schema character varying NOT NULL
);


ALTER TABLE public._dlt_version OWNER TO postgres;

--
-- Name: app_opportunities; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.app_opportunities (
    submission_id character varying NOT NULL,
    problem_description character varying,
    app_concept character varying,
    core_functions character varying,
    value_proposition character varying,
    target_user character varying,
    monetization_model character varying,
    opportunity_score double precision,
    final_score double precision,
    status character varying,
    ai_profile jsonb,
    app_name character varying,
    app_category character varying,
    profession character varying,
    core_problems jsonb,
    dimension_scores jsonb,
    priority character varying,
    confidence numeric(38,9),
    evidence_based boolean,
    trust_score double precision,
    trust_badge character varying,
    activity_score double precision,
    trust_level character varying,
    trust_badges jsonb,
    monetization_score numeric(38,9),
    market_validation_score numeric(38,9),
    analyzed_at timestamp with time zone,
    enrichment_version character varying,
    pipeline_source character varying,
    title character varying,
    subreddit character varying,
    reddit_score bigint,
    _dlt_load_id character varying NOT NULL,
    _dlt_id character varying NOT NULL
);


ALTER TABLE public.app_opportunities OWNER TO postgres;

--
-- Name: app_opportunities_test; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.app_opportunities_test (
    id character varying NOT NULL,
    problem_description character varying,
    app_concept character varying,
    core_functions jsonb,
    value_proposition character varying,
    target_user character varying,
    monetization_model character varying,
    opportunity_score double precision,
    final_score double precision,
    status character varying,
    title character varying,
    subreddit character varying,
    reddit_score bigint,
    analyzed_at timestamp with time zone,
    enrichment_version character varying,
    pipeline_source character varying,
    _dlt_load_id character varying NOT NULL,
    _dlt_id character varying NOT NULL
);


ALTER TABLE public.app_opportunities_test OWNER TO postgres;

--
-- Name: app_opportunities_test_20251124_202640; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.app_opportunities_test_20251124_202640 (
    id character varying NOT NULL,
    problem_description character varying,
    app_concept character varying,
    core_functions jsonb,
    value_proposition character varying,
    target_user character varying,
    monetization_model character varying,
    opportunity_score double precision,
    final_score double precision,
    status character varying,
    title character varying,
    subreddit character varying,
    reddit_score bigint,
    _dlt_load_id character varying NOT NULL,
    _dlt_id character varying NOT NULL
);


ALTER TABLE public.app_opportunities_test_20251124_202640 OWNER TO postgres;

--
-- Name: app_opportunities_test_20251124_203609; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.app_opportunities_test_20251124_203609 (
    id character varying NOT NULL,
    problem_description character varying,
    app_concept character varying,
    core_functions jsonb,
    value_proposition character varying,
    target_user character varying,
    monetization_model character varying,
    opportunity_score double precision,
    final_score double precision,
    status character varying,
    title character varying,
    subreddit character varying,
    reddit_score bigint,
    _dlt_load_id character varying NOT NULL,
    _dlt_id character varying NOT NULL
);


ALTER TABLE public.app_opportunities_test_20251124_203609 OWNER TO postgres;

--
-- Name: competitive_landscape; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.competitive_landscape (
    opportunity_id character varying NOT NULL,
    competitor_name character varying NOT NULL,
    competitor_features jsonb,
    competitive_analysis character varying,
    market_share double precision,
    pricing_model character varying,
    target_market character varying,
    source_url character varying,
    confidence double precision,
    extracted_at timestamp with time zone,
    created_at timestamp with time zone,
    _dlt_load_id character varying NOT NULL,
    _dlt_id character varying NOT NULL
);


ALTER TABLE public.competitive_landscape OWNER TO postgres;

--
-- Name: market_validations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.market_validations (
    opportunity_id character varying NOT NULL,
    validation_type character varying NOT NULL,
    validation_source character varying,
    validation_date timestamp with time zone,
    validation_result jsonb,
    confidence_score double precision,
    notes character varying,
    status character varying,
    evidence_url character varying,
    market_validation_score double precision,
    market_data_quality_score double precision,
    market_validation_reasoning character varying,
    market_competitors_found jsonb,
    market_size_tam double precision,
    market_size_sam double precision,
    market_size_growth double precision,
    market_similar_launches bigint,
    market_validation_cost_usd double precision,
    search_queries_used jsonb,
    urls_fetched jsonb,
    extraction_stats jsonb,
    jina_api_calls_count bigint,
    jina_cache_hit_rate double precision,
    _dlt_load_id character varying NOT NULL,
    _dlt_id character varying NOT NULL
);


ALTER TABLE public.market_validations OWNER TO postgres;

--
-- Name: monetization_patterns; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.monetization_patterns (
    opportunity_id character varying NOT NULL,
    pattern_type character varying NOT NULL,
    revenue_model character varying,
    target_pricing double precision,
    market_size double precision,
    willingness_to_pay_score double precision,
    customer_segment character varying,
    price_sensitivity_score double precision,
    revenue_potential_score double precision,
    mentioned_price_points jsonb,
    existing_payment_behavior character varying,
    urgency_level character varying,
    sentiment_toward_payment character varying,
    payment_friction_indicators jsonb,
    llm_monetization_score double precision,
    confidence double precision,
    reasoning character varying,
    created_at timestamp with time zone,
    _dlt_load_id character varying NOT NULL,
    _dlt_id character varying NOT NULL
);


ALTER TABLE public.monetization_patterns OWNER TO postgres;

--
-- Name: opportunities; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.opportunities (
    id character varying,
    title character varying,
    description character varying,
    problem_statement character varying,
    target_audience character varying,
    submission_id character varying,
    _dlt_load_id character varying NOT NULL,
    _dlt_id character varying NOT NULL
);


ALTER TABLE public.opportunities OWNER TO postgres;

--
-- Name: opportunities_test_02_scaled; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.opportunities_test_02_scaled (
    id character varying,
    title character varying,
    description character varying,
    problem_statement character varying,
    target_audience character varying,
    _dlt_load_id character varying NOT NULL,
    _dlt_id character varying NOT NULL
);


ALTER TABLE public.opportunities_test_02_scaled OWNER TO postgres;

--
-- Name: opportunity_scores; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.opportunity_scores (
    opportunity_id character varying NOT NULL,
    market_demand double precision NOT NULL,
    pain_intensity double precision NOT NULL,
    competition_level double precision NOT NULL,
    technical_feasibility double precision NOT NULL,
    monetization_potential double precision NOT NULL,
    simplicity_score double precision NOT NULL,
    total_score double precision,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    _dlt_load_id character varying NOT NULL,
    _dlt_id character varying NOT NULL
);


ALTER TABLE public.opportunity_scores OWNER TO postgres;

--
-- Name: submissions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.submissions (
    submission_id character varying NOT NULL,
    title character varying,
    selftext character varying,
    author character varying,
    subreddit character varying,
    trust_score double precision,
    trust_level character varying,
    market_validation_score double precision,
    opportunity_score double precision,
    created_utc double precision,
    reddit_score bigint,
    _dlt_load_id character varying NOT NULL,
    _dlt_id character varying NOT NULL,
    reddit_id character varying,
    text character varying,
    content character varying,
    upvotes bigint,
    comments_count bigint,
    url character varying,
    created_at timestamp with time zone,
    id character varying,
    score bigint,
    num_comments bigint
);


ALTER TABLE public.submissions OWNER TO postgres;

--
-- Name: _dlt_version; Type: TABLE; Schema: public_staging; Owner: postgres
--

CREATE TABLE public_staging._dlt_version (
    version bigint NOT NULL,
    engine_version bigint NOT NULL,
    inserted_at timestamp with time zone NOT NULL,
    schema_name character varying NOT NULL,
    version_hash character varying NOT NULL,
    schema character varying NOT NULL
);


ALTER TABLE public_staging._dlt_version OWNER TO postgres;

--
-- Name: app_opportunities; Type: TABLE; Schema: public_staging; Owner: postgres
--

CREATE TABLE public_staging.app_opportunities (
    submission_id character varying NOT NULL,
    problem_description character varying,
    app_concept character varying,
    value_proposition character varying,
    target_user character varying,
    monetization_model character varying,
    opportunity_score double precision,
    title character varying,
    subreddit character varying,
    reddit_score bigint,
    status character varying,
    _dlt_load_id character varying NOT NULL,
    _dlt_id character varying NOT NULL,
    final_score double precision,
    app_name character varying,
    dimension_scores__market_demand double precision,
    dimension_scores__pain_intensity bigint,
    dimension_scores__monetization_potential bigint,
    dimension_scores__market_gap bigint,
    dimension_scores__technical_feasibility bigint,
    dimension_scores__simplicity_score double precision,
    priority character varying,
    confidence double precision,
    evidence_based boolean,
    trust_level character varying,
    enrichment_version character varying,
    pipeline_source character varying,
    market_validation_score double precision,
    ai_profile__analysis_summary__app_name character varying,
    ai_profile__analysis_summary__app_category character varying,
    ai_profile__analysis_summary__target_profession character varying,
    ai_profile__analysis_summary__core_problem_solved character varying,
    ai_profile__analysis_summary__unique_value_prop character varying,
    ai_profile__analysis_summary__primary_target_user character varying,
    ai_profile__analysis_summary__monetization_approach character varying,
    ai_profile__technical_feasibility__estimated_complexity character varying,
    ai_profile__technical_feasibility__core_function_count bigint,
    ai_profile__market_analysis__target_market_segment character varying,
    ai_profile__market_analysis__app_category character varying,
    ai_profile__market_analysis__evidence_based boolean,
    ai_profile__market_analysis__opportunity_score bigint,
    ai_profile__generation_metadata__model_used character varying,
    ai_profile__generation_metadata__analysis_timestamp timestamp with time zone,
    ai_profile__generation_metadata__evidence_available boolean,
    ai_profile__generation_metadata__cost_tracking__model_used character varying,
    ai_profile__generation_metadata__cost_tracking__provider character varying,
    ai_profile__generation_metadata__cost_tracking__prompt_tokens bigint,
    ai_profile__generation_metadagfa09q_tracking__completion_tokens bigint,
    ai_profile__generation_metadata__cost_tracking__total_tokens bigint,
    ai_profile__generation_metadata__cost_tracking__input_cost_usd double precision,
    ai_profile__generation_metadata__cost_tracking__output_cost_usd double precision,
    ai_profile__generation_metadata__cost_tracking__total_cost_usd double precision,
    ai_profile__generation_metadata__cost_tracking__latency_seconds double precision,
    ai_profile__generation_metadapa0rsgracking__prompt_length_chars bigint,
    ai_profile__generation_metadata__cost_tracking__timestamp timestamp with time zone,
    ai_profile__generation_metadaovvxfg_pricing_per_m_tokens__input double precision,
    ai_profile__generation_metadai9kwcgpricing_per_m_tokens__output double precision,
    app_category character varying,
    profession character varying,
    monetization_score double precision,
    core_functions character varying,
    ai_profile jsonb,
    core_problems jsonb,
    dimension_scores jsonb,
    trust_badges jsonb,
    analyzed_at timestamp with time zone,
    trust_score double precision,
    trust_badge character varying,
    activity_score double precision
);


ALTER TABLE public_staging.app_opportunities OWNER TO postgres;

--
-- Name: app_opportunities__ai_profile6devwwfeasibility__target_problems; Type: TABLE; Schema: public_staging; Owner: postgres
--

CREATE TABLE public_staging.app_opportunities__ai_profile6devwwfeasibility__target_problems (
    value character varying,
    _dlt_root_id character varying NOT NULL,
    _dlt_parent_id character varying NOT NULL,
    _dlt_list_idx bigint NOT NULL,
    _dlt_id character varying NOT NULL
);


ALTER TABLE public_staging.app_opportunities__ai_profile6devwwfeasibility__target_problems OWNER TO postgres;

--
-- Name: app_opportunities__ai_profile__technical_feasibility__functions; Type: TABLE; Schema: public_staging; Owner: postgres
--

CREATE TABLE public_staging.app_opportunities__ai_profile__technical_feasibility__functions (
    value character varying,
    _dlt_root_id character varying NOT NULL,
    _dlt_parent_id character varying NOT NULL,
    _dlt_list_idx bigint NOT NULL,
    _dlt_id character varying NOT NULL
);


ALTER TABLE public_staging.app_opportunities__ai_profile__technical_feasibility__functions OWNER TO postgres;

--
-- Name: app_opportunities__core_functions; Type: TABLE; Schema: public_staging; Owner: postgres
--

CREATE TABLE public_staging.app_opportunities__core_functions (
    value character varying,
    _dlt_root_id character varying NOT NULL,
    _dlt_parent_id character varying NOT NULL,
    _dlt_list_idx bigint NOT NULL,
    _dlt_id character varying NOT NULL
);


ALTER TABLE public_staging.app_opportunities__core_functions OWNER TO postgres;

--
-- Name: app_opportunities__core_problems; Type: TABLE; Schema: public_staging; Owner: postgres
--

CREATE TABLE public_staging.app_opportunities__core_problems (
    value character varying,
    _dlt_root_id character varying NOT NULL,
    _dlt_parent_id character varying NOT NULL,
    _dlt_list_idx bigint NOT NULL,
    _dlt_id character varying NOT NULL
);


ALTER TABLE public_staging.app_opportunities__core_problems OWNER TO postgres;

--
-- Name: app_opportunities__trust_badges; Type: TABLE; Schema: public_staging; Owner: postgres
--

CREATE TABLE public_staging.app_opportunities__trust_badges (
    value character varying,
    _dlt_root_id character varying NOT NULL,
    _dlt_parent_id character varying NOT NULL,
    _dlt_list_idx bigint NOT NULL,
    _dlt_id character varying NOT NULL
);


ALTER TABLE public_staging.app_opportunities__trust_badges OWNER TO postgres;

--
-- Name: app_opportunities_test_20251124_202640; Type: TABLE; Schema: public_staging; Owner: postgres
--

CREATE TABLE public_staging.app_opportunities_test_20251124_202640 (
    id character varying NOT NULL,
    problem_description character varying,
    app_concept character varying,
    core_functions jsonb,
    value_proposition character varying,
    target_user character varying,
    monetization_model character varying,
    opportunity_score double precision,
    final_score double precision,
    status character varying,
    title character varying,
    subreddit character varying,
    reddit_score bigint,
    _dlt_load_id character varying NOT NULL,
    _dlt_id character varying NOT NULL
);


ALTER TABLE public_staging.app_opportunities_test_20251124_202640 OWNER TO postgres;

--
-- Name: app_opportunities_test_20251124_203609; Type: TABLE; Schema: public_staging; Owner: postgres
--

CREATE TABLE public_staging.app_opportunities_test_20251124_203609 (
    id character varying NOT NULL,
    problem_description character varying,
    app_concept character varying,
    core_functions jsonb,
    value_proposition character varying,
    target_user character varying,
    monetization_model character varying,
    opportunity_score double precision,
    final_score double precision,
    status character varying,
    title character varying,
    subreddit character varying,
    reddit_score bigint,
    _dlt_load_id character varying NOT NULL,
    _dlt_id character varying NOT NULL
);


ALTER TABLE public_staging.app_opportunities_test_20251124_203609 OWNER TO postgres;

--
-- Name: competitive_landscape; Type: TABLE; Schema: public_staging; Owner: postgres
--

CREATE TABLE public_staging.competitive_landscape (
    opportunity_id character varying NOT NULL,
    competitor_name character varying NOT NULL,
    competitor_features jsonb,
    competitive_analysis character varying,
    market_share double precision,
    pricing_model character varying,
    target_market character varying,
    source_url character varying,
    confidence double precision,
    extracted_at timestamp with time zone,
    created_at timestamp with time zone,
    _dlt_load_id character varying NOT NULL,
    _dlt_id character varying NOT NULL
);


ALTER TABLE public_staging.competitive_landscape OWNER TO postgres;

--
-- Name: market_validations; Type: TABLE; Schema: public_staging; Owner: postgres
--

CREATE TABLE public_staging.market_validations (
    opportunity_id character varying NOT NULL,
    validation_type character varying NOT NULL,
    validation_source character varying,
    validation_date timestamp with time zone,
    validation_result jsonb,
    confidence_score double precision,
    notes character varying,
    status character varying,
    evidence_url character varying,
    market_validation_score double precision,
    market_data_quality_score double precision,
    market_validation_reasoning character varying,
    market_competitors_found jsonb,
    market_size_tam double precision,
    market_size_sam double precision,
    market_size_growth double precision,
    market_similar_launches bigint,
    market_validation_cost_usd double precision,
    search_queries_used jsonb,
    urls_fetched jsonb,
    extraction_stats jsonb,
    jina_api_calls_count bigint,
    jina_cache_hit_rate double precision,
    _dlt_load_id character varying NOT NULL,
    _dlt_id character varying NOT NULL
);


ALTER TABLE public_staging.market_validations OWNER TO postgres;

--
-- Name: monetization_patterns; Type: TABLE; Schema: public_staging; Owner: postgres
--

CREATE TABLE public_staging.monetization_patterns (
    opportunity_id character varying NOT NULL,
    pattern_type character varying NOT NULL,
    revenue_model character varying,
    target_pricing double precision,
    market_size double precision,
    willingness_to_pay_score double precision,
    customer_segment character varying,
    price_sensitivity_score double precision,
    revenue_potential_score double precision,
    mentioned_price_points jsonb,
    existing_payment_behavior character varying,
    urgency_level character varying,
    sentiment_toward_payment character varying,
    payment_friction_indicators jsonb,
    llm_monetization_score double precision,
    confidence double precision,
    reasoning character varying,
    created_at timestamp with time zone,
    _dlt_load_id character varying NOT NULL,
    _dlt_id character varying NOT NULL
);


ALTER TABLE public_staging.monetization_patterns OWNER TO postgres;

--
-- Name: opportunity_scores; Type: TABLE; Schema: public_staging; Owner: postgres
--

CREATE TABLE public_staging.opportunity_scores (
    opportunity_id character varying NOT NULL,
    market_demand double precision NOT NULL,
    pain_intensity double precision NOT NULL,
    competition_level double precision NOT NULL,
    technical_feasibility double precision NOT NULL,
    monetization_potential double precision NOT NULL,
    simplicity_score double precision NOT NULL,
    total_score double precision,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    _dlt_load_id character varying NOT NULL,
    _dlt_id character varying NOT NULL
);


ALTER TABLE public_staging.opportunity_scores OWNER TO postgres;

--
-- Name: submissions; Type: TABLE; Schema: public_staging; Owner: postgres
--

CREATE TABLE public_staging.submissions (
    submission_id character varying NOT NULL,
    title character varying,
    selftext character varying,
    author character varying,
    subreddit character varying,
    trust_score double precision,
    trust_level character varying,
    market_validation_score double precision,
    opportunity_score double precision,
    created_utc double precision,
    reddit_score bigint,
    _dlt_load_id character varying NOT NULL,
    _dlt_id character varying NOT NULL,
    reddit_id character varying,
    text character varying,
    content character varying,
    upvotes bigint,
    comments_count bigint,
    url character varying,
    created_at timestamp with time zone,
    id character varying,
    score bigint,
    num_comments bigint
);


ALTER TABLE public_staging.submissions OWNER TO postgres;

--
-- Name: buckets; Type: TABLE; Schema: storage; Owner: supabase_storage_admin
--

CREATE TABLE storage.buckets (
    id text NOT NULL,
    name text NOT NULL,
    owner uuid,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    public boolean DEFAULT false,
    avif_autodetection boolean DEFAULT false,
    file_size_limit bigint,
    allowed_mime_types text[],
    owner_id text,
    type storage.buckettype DEFAULT 'STANDARD'::storage.buckettype NOT NULL
);


ALTER TABLE storage.buckets OWNER TO supabase_storage_admin;

--
-- Name: COLUMN buckets.owner; Type: COMMENT; Schema: storage; Owner: supabase_storage_admin
--

COMMENT ON COLUMN storage.buckets.owner IS 'Field is deprecated, use owner_id instead';


--
-- Name: buckets_analytics; Type: TABLE; Schema: storage; Owner: supabase_storage_admin
--

CREATE TABLE storage.buckets_analytics (
    id text NOT NULL,
    type storage.buckettype DEFAULT 'ANALYTICS'::storage.buckettype NOT NULL,
    format text DEFAULT 'ICEBERG'::text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE storage.buckets_analytics OWNER TO supabase_storage_admin;

--
-- Name: iceberg_namespaces; Type: TABLE; Schema: storage; Owner: supabase_storage_admin
--

CREATE TABLE storage.iceberg_namespaces (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    bucket_id text NOT NULL,
    name text NOT NULL COLLATE pg_catalog."C",
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE storage.iceberg_namespaces OWNER TO supabase_storage_admin;

--
-- Name: iceberg_tables; Type: TABLE; Schema: storage; Owner: supabase_storage_admin
--

CREATE TABLE storage.iceberg_tables (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    namespace_id uuid NOT NULL,
    bucket_id text NOT NULL,
    name text NOT NULL COLLATE pg_catalog."C",
    location text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE storage.iceberg_tables OWNER TO supabase_storage_admin;

--
-- Name: migrations; Type: TABLE; Schema: storage; Owner: supabase_storage_admin
--

CREATE TABLE storage.migrations (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    hash character varying(40) NOT NULL,
    executed_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE storage.migrations OWNER TO supabase_storage_admin;

--
-- Name: objects; Type: TABLE; Schema: storage; Owner: supabase_storage_admin
--

CREATE TABLE storage.objects (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    bucket_id text,
    name text,
    owner uuid,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    last_accessed_at timestamp with time zone DEFAULT now(),
    metadata jsonb,
    path_tokens text[] GENERATED ALWAYS AS (string_to_array(name, '/'::text)) STORED,
    version text,
    owner_id text,
    user_metadata jsonb,
    level integer
);


ALTER TABLE storage.objects OWNER TO supabase_storage_admin;

--
-- Name: COLUMN objects.owner; Type: COMMENT; Schema: storage; Owner: supabase_storage_admin
--

COMMENT ON COLUMN storage.objects.owner IS 'Field is deprecated, use owner_id instead';


--
-- Name: prefixes; Type: TABLE; Schema: storage; Owner: supabase_storage_admin
--

CREATE TABLE storage.prefixes (
    bucket_id text NOT NULL,
    name text NOT NULL COLLATE pg_catalog."C",
    level integer GENERATED ALWAYS AS (storage.get_level(name)) STORED NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE storage.prefixes OWNER TO supabase_storage_admin;

--
-- Name: s3_multipart_uploads; Type: TABLE; Schema: storage; Owner: supabase_storage_admin
--

CREATE TABLE storage.s3_multipart_uploads (
    id text NOT NULL,
    in_progress_size bigint DEFAULT 0 NOT NULL,
    upload_signature text NOT NULL,
    bucket_id text NOT NULL,
    key text NOT NULL COLLATE pg_catalog."C",
    version text NOT NULL,
    owner_id text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    user_metadata jsonb
);


ALTER TABLE storage.s3_multipart_uploads OWNER TO supabase_storage_admin;

--
-- Name: s3_multipart_uploads_parts; Type: TABLE; Schema: storage; Owner: supabase_storage_admin
--

CREATE TABLE storage.s3_multipart_uploads_parts (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    upload_id text NOT NULL,
    size bigint DEFAULT 0 NOT NULL,
    part_number integer NOT NULL,
    bucket_id text NOT NULL,
    key text NOT NULL COLLATE pg_catalog."C",
    etag text NOT NULL,
    owner_id text,
    version text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE storage.s3_multipart_uploads_parts OWNER TO supabase_storage_admin;

--
-- Name: hooks; Type: TABLE; Schema: supabase_functions; Owner: supabase_functions_admin
--

CREATE TABLE supabase_functions.hooks (
    id bigint NOT NULL,
    hook_table_id integer NOT NULL,
    hook_name text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    request_id bigint
);


ALTER TABLE supabase_functions.hooks OWNER TO supabase_functions_admin;

--
-- Name: TABLE hooks; Type: COMMENT; Schema: supabase_functions; Owner: supabase_functions_admin
--

COMMENT ON TABLE supabase_functions.hooks IS 'Supabase Functions Hooks: Audit trail for triggered hooks.';


--
-- Name: hooks_id_seq; Type: SEQUENCE; Schema: supabase_functions; Owner: supabase_functions_admin
--

CREATE SEQUENCE supabase_functions.hooks_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE supabase_functions.hooks_id_seq OWNER TO supabase_functions_admin;

--
-- Name: hooks_id_seq; Type: SEQUENCE OWNED BY; Schema: supabase_functions; Owner: supabase_functions_admin
--

ALTER SEQUENCE supabase_functions.hooks_id_seq OWNED BY supabase_functions.hooks.id;


--
-- Name: migrations; Type: TABLE; Schema: supabase_functions; Owner: supabase_functions_admin
--

CREATE TABLE supabase_functions.migrations (
    version text NOT NULL,
    inserted_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE supabase_functions.migrations OWNER TO supabase_functions_admin;

--
-- Name: refresh_tokens id; Type: DEFAULT; Schema: auth; Owner: supabase_auth_admin
--

ALTER TABLE ONLY auth.refresh_tokens ALTER COLUMN id SET DEFAULT nextval('auth.refresh_tokens_id_seq'::regclass);


--
-- Name: hooks id; Type: DEFAULT; Schema: supabase_functions; Owner: supabase_functions_admin
--

ALTER TABLE ONLY supabase_functions.hooks ALTER COLUMN id SET DEFAULT nextval('supabase_functions.hooks_id_seq'::regclass);


--
-- Data for Name: _dlt_loads; Type: TABLE DATA; Schema: app_opportunities; Owner: postgres
--

COPY app_opportunities._dlt_loads (load_id, schema_name, status, inserted_at, schema_version_hash) FROM stdin;
1764180852.3568244	final_dlt_test	0	2025-11-26 18:14:12.937597+00	JX2B0fCaY4bTG4H9qNHxzJtuReU+gGUg6I1JH5x34Qw=
\.


--
-- Data for Name: _dlt_pipeline_state; Type: TABLE DATA; Schema: app_opportunities; Owner: postgres
--

COPY app_opportunities._dlt_pipeline_state (version, engine_version, pipeline_name, state, created_at, version_hash, _dlt_load_id, _dlt_id) FROM stdin;
1	4	final_dlt_test_pipeline	eNptj8FqwlAQRf9ltg1Si4oNdOGi4saItNA2RYaxGc3T58uQmRSk9N/7QhsI1e29Zw53vgDVyBg/uVZXBUiHSRdx2LvQa0YJFLyjxhvqR8knwkAnhhR2LpDHIubGapBAr1ZI3/8DmwTECfvWflWBXR1dBRkpWweSCFYiVW1NcOaiv12lFu8trkQ7S4tF06AX60AqtX19gf9aQ+N9fPvvUyxJy+h4vbE8X7I8T7K78ezpZb3YPs5W09Xt/C3Lz1l94PvjYeinzWT0AN8/zUx3zg==	2025-11-26 18:14:12.374999+00	X+tZZMepT6N25ASWQHbEAO8O0FYNZyNrje9kj1l8u64=	1764180852.3568244	OGPYTu8P74eDbg
\.


--
-- Data for Name: _dlt_version; Type: TABLE DATA; Schema: app_opportunities; Owner: postgres
--

COPY app_opportunities._dlt_version (version, engine_version, inserted_at, schema_name, version_hash, schema) FROM stdin;
2	11	2025-11-26 18:14:12.765653+00	final_dlt_test	JX2B0fCaY4bTG4H9qNHxzJtuReU+gGUg6I1JH5x34Qw=	{"version":2,"version_hash":"JX2B0fCaY4bTG4H9qNHxzJtuReU+gGUg6I1JH5x34Qw=","engine_version":11,"name":"final_dlt_test","tables":{"_dlt_version":{"name":"_dlt_version","columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_name":{"name":"schema_name","data_type":"text","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":false},"schema":{"name":"schema","data_type":"text","nullable":false}},"write_disposition":"skip","resource":"_dlt_version","description":"Created by DLT. Tracks schema updates"},"_dlt_loads":{"name":"_dlt_loads","columns":{"load_id":{"name":"load_id","data_type":"text","nullable":false,"precision":64},"schema_name":{"name":"schema_name","data_type":"text","nullable":true},"status":{"name":"status","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_version_hash":{"name":"schema_version_hash","data_type":"text","nullable":true}},"write_disposition":"skip","resource":"_dlt_loads","description":"Created by DLT. Tracks completed loads"},"app_opportunities":{"columns":{"submission_id":{"name":"submission_id","nullable":false,"primary_key":true,"data_type":"text"},"title":{"name":"title","data_type":"text","nullable":true},"text":{"name":"text","data_type":"text","nullable":true},"subreddit":{"name":"subreddit","data_type":"text","nullable":true},"upvotes":{"name":"upvotes","data_type":"bigint","nullable":true},"comments_count":{"name":"comments_count","data_type":"bigint","nullable":true},"score":{"name":"score","data_type":"double","nullable":true},"created_utc":{"name":"created_utc","data_type":"timestamp","nullable":true},"quality_score":{"name":"quality_score","data_type":"double","nullable":true},"trust_score":{"name":"trust_score","data_type":"double","nullable":true},"processed_at":{"name":"processed_at","data_type":"timestamp","nullable":true},"pipeline_version":{"name":"pipeline_version","data_type":"text","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"merge","name":"app_opportunities","resource":"app_opportunities","x-normalizer":{"seen-data":true}},"_dlt_pipeline_state":{"columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"pipeline_name":{"name":"pipeline_name","data_type":"text","nullable":false},"state":{"name":"state","data_type":"text","nullable":false},"created_at":{"name":"created_at","data_type":"timestamp","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false,"precision":64},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"append","file_format":"preferred","name":"_dlt_pipeline_state","resource":"_dlt_pipeline_state","x-normalizer":{"seen-data":true}}},"settings":{"detections":["iso_timestamp"],"default_hints":{"not_null":["_dlt_id","_dlt_root_id","_dlt_parent_id","_dlt_list_idx","_dlt_load_id"],"parent_key":["_dlt_parent_id"],"root_key":["_dlt_root_id"],"unique":["_dlt_id"],"row_key":["_dlt_id"]}},"normalizers":{"names":"snake_case","json":{"module":"dlt.common.normalizers.json.relational","config":{"propagation":{"tables":{"app_opportunities":{"_dlt_id":"_dlt_root_id"}}}}}},"previous_hashes":["WBMJinPgOx365XiE1bEK7pb9YrhE+OmVbVLKFNJeNb0=","f9Mtc8s4msk0vJbIUGXpsGd+pgk2TIcWzcjj4WloZoc="]}
\.


--
-- Data for Name: app_opportunities; Type: TABLE DATA; Schema: app_opportunities; Owner: postgres
--

COPY app_opportunities.app_opportunities (submission_id, title, text, subreddit, upvotes, comments_count, score, created_utc, quality_score, trust_score, processed_at, pipeline_version, _dlt_load_id, _dlt_id) FROM stdin;
final_test_opportunity	Final test opportunity for DLT loading	This is a test record to validate DLT loading functionality.	test	100	10	100	2025-11-26 18:14:12.209197+00	85	80	2025-11-26 18:14:12.209219+00	pipeline_v2_final_test	1764180852.3568244	XOh5gT/L7hTLvQ
\.


--
-- Data for Name: _dlt_version; Type: TABLE DATA; Schema: app_opportunities_staging; Owner: postgres
--

COPY app_opportunities_staging._dlt_version (version, engine_version, inserted_at, schema_name, version_hash, schema) FROM stdin;
2	11	2025-11-26 18:14:12.8119+00	final_dlt_test	JX2B0fCaY4bTG4H9qNHxzJtuReU+gGUg6I1JH5x34Qw=	{"version":2,"version_hash":"JX2B0fCaY4bTG4H9qNHxzJtuReU+gGUg6I1JH5x34Qw=","engine_version":11,"name":"final_dlt_test","tables":{"_dlt_version":{"name":"_dlt_version","columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_name":{"name":"schema_name","data_type":"text","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":false},"schema":{"name":"schema","data_type":"text","nullable":false}},"write_disposition":"skip","resource":"_dlt_version","description":"Created by DLT. Tracks schema updates"},"_dlt_loads":{"name":"_dlt_loads","columns":{"load_id":{"name":"load_id","data_type":"text","nullable":false,"precision":64},"schema_name":{"name":"schema_name","data_type":"text","nullable":true},"status":{"name":"status","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_version_hash":{"name":"schema_version_hash","data_type":"text","nullable":true}},"write_disposition":"skip","resource":"_dlt_loads","description":"Created by DLT. Tracks completed loads"},"app_opportunities":{"columns":{"submission_id":{"name":"submission_id","nullable":false,"primary_key":true,"data_type":"text"},"title":{"name":"title","data_type":"text","nullable":true},"text":{"name":"text","data_type":"text","nullable":true},"subreddit":{"name":"subreddit","data_type":"text","nullable":true},"upvotes":{"name":"upvotes","data_type":"bigint","nullable":true},"comments_count":{"name":"comments_count","data_type":"bigint","nullable":true},"score":{"name":"score","data_type":"double","nullable":true},"created_utc":{"name":"created_utc","data_type":"timestamp","nullable":true},"quality_score":{"name":"quality_score","data_type":"double","nullable":true},"trust_score":{"name":"trust_score","data_type":"double","nullable":true},"processed_at":{"name":"processed_at","data_type":"timestamp","nullable":true},"pipeline_version":{"name":"pipeline_version","data_type":"text","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"merge","name":"app_opportunities","resource":"app_opportunities","x-normalizer":{"seen-data":true}},"_dlt_pipeline_state":{"columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"pipeline_name":{"name":"pipeline_name","data_type":"text","nullable":false},"state":{"name":"state","data_type":"text","nullable":false},"created_at":{"name":"created_at","data_type":"timestamp","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false,"precision":64},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"append","file_format":"preferred","name":"_dlt_pipeline_state","resource":"_dlt_pipeline_state","x-normalizer":{"seen-data":true}}},"settings":{"detections":["iso_timestamp"],"default_hints":{"not_null":["_dlt_id","_dlt_root_id","_dlt_parent_id","_dlt_list_idx","_dlt_load_id"],"parent_key":["_dlt_parent_id"],"root_key":["_dlt_root_id"],"unique":["_dlt_id"],"row_key":["_dlt_id"]}},"normalizers":{"names":"snake_case","json":{"module":"dlt.common.normalizers.json.relational","config":{"propagation":{"tables":{"app_opportunities":{"_dlt_id":"_dlt_root_id"}}}}}},"previous_hashes":["WBMJinPgOx365XiE1bEK7pb9YrhE+OmVbVLKFNJeNb0=","f9Mtc8s4msk0vJbIUGXpsGd+pgk2TIcWzcjj4WloZoc="]}
\.


--
-- Data for Name: app_opportunities; Type: TABLE DATA; Schema: app_opportunities_staging; Owner: postgres
--

COPY app_opportunities_staging.app_opportunities (submission_id, title, text, subreddit, upvotes, comments_count, score, created_utc, quality_score, trust_score, processed_at, pipeline_version, _dlt_load_id, _dlt_id) FROM stdin;
final_test_opportunity	Final test opportunity for DLT loading	This is a test record to validate DLT loading functionality.	test	100	10	100	2025-11-26 18:14:12.209197+00	85	80	2025-11-26 18:14:12.209219+00	pipeline_v2_final_test	1764180852.3568244	XOh5gT/L7hTLvQ
\.


--
-- Data for Name: audit_log_entries; Type: TABLE DATA; Schema: auth; Owner: supabase_auth_admin
--

COPY auth.audit_log_entries (instance_id, id, payload, created_at, ip_address) FROM stdin;
\.


--
-- Data for Name: flow_state; Type: TABLE DATA; Schema: auth; Owner: supabase_auth_admin
--

COPY auth.flow_state (id, user_id, auth_code, code_challenge_method, code_challenge, provider_type, provider_access_token, provider_refresh_token, created_at, updated_at, authentication_method, auth_code_issued_at) FROM stdin;
\.


--
-- Data for Name: identities; Type: TABLE DATA; Schema: auth; Owner: supabase_auth_admin
--

COPY auth.identities (provider_id, user_id, identity_data, provider, last_sign_in_at, created_at, updated_at, id) FROM stdin;
\.


--
-- Data for Name: instances; Type: TABLE DATA; Schema: auth; Owner: supabase_auth_admin
--

COPY auth.instances (id, uuid, raw_base_config, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: mfa_amr_claims; Type: TABLE DATA; Schema: auth; Owner: supabase_auth_admin
--

COPY auth.mfa_amr_claims (session_id, created_at, updated_at, authentication_method, id) FROM stdin;
\.


--
-- Data for Name: mfa_challenges; Type: TABLE DATA; Schema: auth; Owner: supabase_auth_admin
--

COPY auth.mfa_challenges (id, factor_id, created_at, verified_at, ip_address, otp_code, web_authn_session_data) FROM stdin;
\.


--
-- Data for Name: mfa_factors; Type: TABLE DATA; Schema: auth; Owner: supabase_auth_admin
--

COPY auth.mfa_factors (id, user_id, friendly_name, factor_type, status, created_at, updated_at, secret, phone, last_challenged_at, web_authn_credential, web_authn_aaguid) FROM stdin;
\.


--
-- Data for Name: one_time_tokens; Type: TABLE DATA; Schema: auth; Owner: supabase_auth_admin
--

COPY auth.one_time_tokens (id, user_id, token_type, token_hash, relates_to, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: refresh_tokens; Type: TABLE DATA; Schema: auth; Owner: supabase_auth_admin
--

COPY auth.refresh_tokens (instance_id, id, token, user_id, revoked, created_at, updated_at, parent, session_id) FROM stdin;
\.


--
-- Data for Name: saml_providers; Type: TABLE DATA; Schema: auth; Owner: supabase_auth_admin
--

COPY auth.saml_providers (id, sso_provider_id, entity_id, metadata_xml, metadata_url, attribute_mapping, created_at, updated_at, name_id_format) FROM stdin;
\.


--
-- Data for Name: saml_relay_states; Type: TABLE DATA; Schema: auth; Owner: supabase_auth_admin
--

COPY auth.saml_relay_states (id, sso_provider_id, request_id, for_email, redirect_to, created_at, updated_at, flow_state_id) FROM stdin;
\.


--
-- Data for Name: schema_migrations; Type: TABLE DATA; Schema: auth; Owner: supabase_auth_admin
--

COPY auth.schema_migrations (version) FROM stdin;
20171026211738
20171026211808
20171026211834
20180103212743
20180108183307
20180119214651
20180125194653
00
20210710035447
20210722035447
20210730183235
20210909172000
20210927181326
20211122151130
20211124214934
20211202183645
20220114185221
20220114185340
20220224000811
20220323170000
20220429102000
20220531120530
20220614074223
20220811173540
20221003041349
20221003041400
20221011041400
20221020193600
20221021073300
20221021082433
20221027105023
20221114143122
20221114143410
20221125140132
20221208132122
20221215195500
20221215195800
20221215195900
20230116124310
20230116124412
20230131181311
20230322519590
20230402418590
20230411005111
20230508135423
20230523124323
20230818113222
20230914180801
20231027141322
20231114161723
20231117164230
20240115144230
20240214120130
20240306115329
20240314092811
20240427152123
20240612123726
20240729123726
20240802193726
20240806073726
20241009103726
20250717082212
\.


--
-- Data for Name: sessions; Type: TABLE DATA; Schema: auth; Owner: supabase_auth_admin
--

COPY auth.sessions (id, user_id, created_at, updated_at, factor_id, aal, not_after, refreshed_at, user_agent, ip, tag) FROM stdin;
\.


--
-- Data for Name: sso_domains; Type: TABLE DATA; Schema: auth; Owner: supabase_auth_admin
--

COPY auth.sso_domains (id, sso_provider_id, domain, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: sso_providers; Type: TABLE DATA; Schema: auth; Owner: supabase_auth_admin
--

COPY auth.sso_providers (id, resource_id, created_at, updated_at, disabled) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: auth; Owner: supabase_auth_admin
--

COPY auth.users (instance_id, id, aud, role, email, encrypted_password, email_confirmed_at, invited_at, confirmation_token, confirmation_sent_at, recovery_token, recovery_sent_at, email_change_token_new, email_change, email_change_sent_at, last_sign_in_at, raw_app_meta_data, raw_user_meta_data, is_super_admin, created_at, updated_at, phone, phone_confirmed_at, phone_change, phone_change_token, phone_change_sent_at, email_change_token_current, email_change_confirm_status, banned_until, reauthentication_token, reauthentication_sent_at, is_sso_user, deleted_at, is_anonymous) FROM stdin;
\.


--
-- Data for Name: _dlt_loads; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public._dlt_loads (load_id, schema_name, status, inserted_at, schema_version_hash) FROM stdin;
1763945243.9732513	app_opportunities_loader	0	2025-11-24 00:47:24.271318+00	yuJ75xKwP3h5zR0FZqgtT9dyngWlP0ofPUwss+mV+Vg=
1763946993.1489778	app_opportunities_loader	0	2025-11-24 01:16:33.326239+00	yuJ75xKwP3h5zR0FZqgtT9dyngWlP0ofPUwss+mV+Vg=
1764018105.1331246	reddit_harbor_problem_collection	0	2025-11-24 21:01:45.555838+00	NS4LPU4+tZlvO6LZkSMS3fknOeZhF6u9I8iK2Eth4yY=
1764026662.6875854	app_opportunities_test_loader	0	2025-11-24 23:24:22.935143+00	wsCtuhTqV8A053UkyYqy+4m2mZvO6o/soZeiqiSOK6E=
1764026800.5946286	app_opportunities_test_20251124_202640_loader	0	2025-11-24 23:26:40.844988+00	k3trREG7jTIGBhx2Wu9qRSsahChfj39gnnicgNrat5g=
1764027363.4295378	app_opportunities_test_loader	0	2025-11-24 23:36:03.637848+00	wsCtuhTqV8A053UkyYqy+4m2mZvO6o/soZeiqiSOK6E=
1764027370.1243253	app_opportunities_test_20251124_203609_loader	0	2025-11-24 23:36:10.368457+00	BQ95pMDguFCyoBTC4UeGoYttu3g/xBMjxFuXBrcEj1c=
1764028678.981518	opportunities_loader	0	2025-11-24 23:57:59.219573+00	EAGvk3giyJEmhmpx3CaLjlV41JtuHf08JSpYGFfodGg=
1764029549.2952976	opportunities_loader	0	2025-11-25 00:12:29.536032+00	EAGvk3giyJEmhmpx3CaLjlV41JtuHf08JSpYGFfodGg=
1764029629.26987	opportunities_loader	0	2025-11-25 00:13:49.427177+00	p45PMIDkaCQ1NUiYjqTf2bnZ3mY1+apIEqJUHc7d1+A=
1764029669.703498	opportunities_loader	0	2025-11-25 00:14:29.862664+00	p45PMIDkaCQ1NUiYjqTf2bnZ3mY1+apIEqJUHc7d1+A=
1764029987.5142696	opportunities_loader	0	2025-11-25 00:19:47.632456+00	p45PMIDkaCQ1NUiYjqTf2bnZ3mY1+apIEqJUHc7d1+A=
1764031135.058126	opportunities_loader	0	2025-11-25 00:38:55.177535+00	p45PMIDkaCQ1NUiYjqTf2bnZ3mY1+apIEqJUHc7d1+A=
1764031305.5583394	opportunities_loader	0	2025-11-25 00:41:45.703796+00	p45PMIDkaCQ1NUiYjqTf2bnZ3mY1+apIEqJUHc7d1+A=
\.


--
-- Data for Name: _dlt_pipeline_state; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public._dlt_pipeline_state (version, engine_version, pipeline_name, state, created_at, version_hash, _dlt_load_id, _dlt_id) FROM stdin;
1	4	app_opportunities_loader	eNqFkMFqwkAQht9lzkFRgodAD0KxIu2hwaJUZBnNaFbW3WFnEltK391EK8SD9Dr/Nx//zA8YUVQyNUWxwUM2SG4j8nvrO0magGxLOqLxeCSBbAXIbAJziFp5q5bEuIAFRVgnwJbJtYKWhuwxm0BBO6ycmo7+nwVUFNIbydXG2e1FJGo9atPX6De3WeG01xlLj4PoPjb97/GrylfONQ/4u9mUKGXjWKT5jofj/P0w/Hyd51++Po1GL88fYTKolxpny3E6fXOzfnFIn+D3DJIMfK4=	2025-11-24 00:47:23.999675+00	W4Rfp2ARQj2ZLTRxnvw66GDUoF1vXtrJXA4HMlJ/dj4=	1763945243.9732513	RN1nlFQVJmntTw
1	4	reddit_harbor_problem_collection	eNqNUE1Lw0AQ/S9zbSgNaMGAB+tHsYX2YA+iyDLJjsnCZHfZmSgq/nezaCGe9DjvzfvgfYARRSXzQklc8FCVxREi3zo/YU4KsKgopMZjT1BBHGp2DYw4PePAaqTpqMcjnchap6bDVIdkYgo1U2+awEyNZssCoovEOeX/kkmGQPX4t+Qp9xN1HvNp9C3mJMs6n8Ayj0G0TaPn7/fvYn5gHof52WIMky57rP192e/eD+vX1XIj6fZuccDrU3t5cbUNq3bYn5XkljcPm9niHD6/AML3hY0=	2025-11-24 21:17:49.547483+00	dGnX1mNzTGwB6JsrIS0TaE5dCADKoBguO91ei6FZJ+0=	1764019069.5274184	MLHwK9UDD0s85Q
1	4	reddit_harbor_problem_collection	eNqVkEFrwkAQhf/LXg1ioAoNeKitlSroQQ+lpSyT7DRZmOwuO5MWFf97s7RCeio9zpt53xveWWkWENQfGNl6p4o8u0roausGm5tMBRuQkuigRVWoiMZY0Q3E0kcdoi8JW115IqwkmTJl8B06Es1Vgy38xwgCjHJ1hK4kW/X6AMSqeP0b9ZaeYLEO0qjlGBLPkIwHMo+DZ6ljz/x9/h3vOqK+mJ8u+jBuEmPlnvN2ezqsPhezNcen/eQAy6m5v3vY+EXd7W5ztLPHl/VoMleXLxtNhY0=	2025-11-24 21:53:49.628948+00	dGnX1mNzTGwB6JsrIS0TaE5dCADKoBguO91ei6FZJ+0=	1764021229.606076	XSZVN/7dBJtQXQ
1	4	app_opportunities_test_loader	eNqNUMFOwzAM/ZdcqTZ1DFgrcdgFaQcOqNMOIBR5rVkjZYmJHSao+u8kgknlNI5+fu/5+Q1Ks4Cg/sDAxjtVl8UZQncwbrJZForbHo+gHRyRVf2igEh7Ih8kOiMGWQuyaOuhw6BeC0WG0GaXLFH1BUGhOhBglDOd4t6aNuP4BtGKngT4j1uajANJ8bV8UpZ0VmYTmGfkWQ4hvfOX/nPBRWtTH78V6B64Tx7z9/VqV92Uodr1p+auappy7Yz7Wjxvw9NqfnrYLPbXt1vurh7vky37GNrc13AhcD2M4/gNJu2UnA==	2025-11-24 23:24:22.710207+00	/qA8V951r9VhwS79SS1Aninz2ZTrQ8/wFI2b36Tsd+M=	1764026662.6875854	/zYtl2vbmPSkXQ
1	4	app_opportunities_test_20251124_202640_loader	eNqdkEFrwzAMhf+Lrw2l8dIMAjsMSkc3KC0MRhnDqIkau3VtY8mFMfbf57AVsuN2E0/Sp6f3IRQxMKoLRjLeiaYsrhK63rhRpypEMAHtIDo4o2gEhKB8CD5ycoYNkmIkVnIm52Upq6Goq5myHjqMohAdHiBZVtRqPMO/KcBAyNf1kPbWtFkfUUk0r3/kvg32iI0Dzu8qfg8DvLM8Hck0DZ64j/nA7/FvLy5Zm/P7iUxpIJ0ZDy9HaQ8rvesf5087iYtNnFQ3fbdd69Pl2OJynWpzWz/r7f2d+PwCrgONnA==	2025-11-24 23:26:40.614152+00	GWj2lfIhYgJ5KY2eDPr+43gdQNhkvjceFNu6i76ThQA=	1764026800.5946286	RD/NjoWRwiAbww
1	4	app_opportunities_test_20251124_203609_loader	eNqdUE1Lw0AQ/S97bWiT2AgJeLB4KB6lgigyTLNjdmG7u+xMWqL4392ihXjU2zBv3se8DwUsKARHSmyDV11VXFbkB+tnyLpQmt5wdALcGzogeDyQ6hTGCCHGkGT0ViwxCLFAXdZNVdXrPFxdly24gJqSKtSMzap7+SP/NcdAQSa5+Mdx72yfhaON5M6Z/xlMZ9R6lPwuyBTPEtrJcrbmZQwsQ8rBf59/O/rRudzfT2VgkE3WeNyaoT2m5+1uhytzL3XzvghVah/kad9O/UkvVtOmubs9bcob9fkF0s+Now==	2025-11-24 23:36:10.146822+00	UHhg9vrZHTTa/hJt25z+o1r9RtXb9ycwd+/yB5DAwB0=	1764027370.1243253	X2ml3ftrBTESFg
1	4	opportunities_loader	eNp9j09rAjEQxb/LXF1Eq6cFDy09eKhaKoJQSpiaaTY6JmFnIqj43d1FhS2UXt/78f6cwYiikjlQLT4GKIfFQ6LgfOg44wJkU9EeTcA9CZSfEFOKtebg1ZMYjmiphq8CLP1gZjUdHsq/6QKST8Rt0/+YRUUhfVApf7PftDqJ+oDabDR6TK1nWfsdWfopirq62fwbv0WFzNycvv80FUrVZDAtdnk2XL+8rafjlXNTNzrN7Xb3QUedPb32Ds/4vuS5H2xXE7hcAXb9eG4=	2025-11-24 23:57:59.001097+00	leOkuM1XBLXH4UggHg3zNdjkReytM2D+vAaPSlNi0jU=	1764028678.981518	fuuEGh24UkSvgA
1	4	reddit_harbor_problem_collection	eNqNkEFrwkAQhf/LXg1ioAoNeKitlSroQQ+lpSyT7DRZmOwuO5MWFf97s7RCemqP82be94Z3VpoFBPUHRrbeqSLPrhK62rrB5iZTBt+hI9FcNdiCdtCiKlREY6zoBmLpow7Rl4StrjwRVpKsmQo2ICXa/y0GBBjl6ghdSbbq9UE2q+L1b9Rb+pvFOkijlmNIPEMyHsg8Dp6ljj3z9/l3vOuI+mJ+uujDuEmMlXvO2+3psPpczNYcn/aTAyyn5v7uYeMXdbe7zdHOHl/Wo8lcXb4AH2qFjQ==	2025-11-25 01:50:10.294689+00	dGnX1mNzTGwB6JsrIS0TaE5dCADKoBguO91ei6FZJ+0=	1764035410.2761052	yvOvyVD8s1Jzfw
1	4	reddit_harbor_problem_collection	eNqNkEFrwkAQhf/LXg1ioAoNeKitlSroQQ+lpSyT7DRZmOwuO5MWFf97s7RCemqP82be94Z3VpoFBPUHRrbeqSLPrhK62rrB5iZTBt+hI9FcNdiCdtCiKlREY6zoBmLpow7Rl4StrjwRVpKsmQo2ICXa/y0GBBjl6ghdSbbq9UE2q+L1b9Rb+pvFOkijlmNIPEMyHsg8Dp6ljj3z9/l3vOuI+mJ+uujDuEmMlXvO2+3psPpczNYcn/aTAyyn5v7uYeMXdbe7zdHOHl/Wo8lcXb4AH2qFjQ==	2025-11-25 01:56:05.551322+00	dGnX1mNzTGwB6JsrIS0TaE5dCADKoBguO91ei6FZJ+0=	1764035765.5341733	1HYcNk+DUZJaEQ
1	4	submissions_loader	eNp9j91qg0AQRt9lriVEENoIuQqlEcwPCIG2lGXUqS5Z18WZFULpu2elFSyU3n7fmTMzn6BYUEiNNLDuLaRxNEdkG20XTRJBTR/ojSiuWupQWewIUmBfdponiJXpsaYBInDakZnm/4MWHob07S/oPWxFQSaZTc6XRlcwXcOiLUrAldzc1NVGVouYV65naYZg/41/q6w3Jrz786FqkdvgKMZ9vhEukuSpeizyuCvG8nh4OR/We9n59vXBXU/P2eXcZMkWvu431XUR	2025-11-25 21:57:59.998417+00	SvHL9tsS44Ec8SL1mSvbNMYPM0HtCuhZ7pkOGIVPgI4=	1764107879.978241	/Yrr4Gm0QXRHRQ
\.


--
-- Data for Name: _dlt_version; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public._dlt_version (version, engine_version, inserted_at, schema_name, version_hash, schema) FROM stdin;
4	11	2025-11-24 00:46:57.367101+00	app_opportunities_loader	arbeBJe3bDZdsPHsb4+PfhEh5R/dFCCbFDjZjur5Sh0=	{"version":4,"version_hash":"arbeBJe3bDZdsPHsb4+PfhEh5R/dFCCbFDjZjur5Sh0=","engine_version":11,"name":"app_opportunities_loader","tables":{"_dlt_version":{"name":"_dlt_version","columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_name":{"name":"schema_name","data_type":"text","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":false},"schema":{"name":"schema","data_type":"text","nullable":false}},"write_disposition":"skip","resource":"_dlt_version","description":"Created by DLT. Tracks schema updates"},"_dlt_loads":{"name":"_dlt_loads","columns":{"load_id":{"name":"load_id","data_type":"text","nullable":false,"precision":64},"schema_name":{"name":"schema_name","data_type":"text","nullable":true},"status":{"name":"status","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_version_hash":{"name":"schema_version_hash","data_type":"text","nullable":true}},"write_disposition":"skip","resource":"_dlt_loads","description":"Created by DLT. Tracks completed loads"},"app_opportunities":{"columns":{"submission_id":{"data_type":"text","nullable":false,"name":"submission_id","primary_key":true},"problem_description":{"data_type":"text","name":"problem_description"},"app_concept":{"data_type":"text","name":"app_concept"},"core_functions":{"data_type":"text","name":"core_functions"},"value_proposition":{"data_type":"text","name":"value_proposition"},"target_user":{"data_type":"text","name":"target_user"},"monetization_model":{"data_type":"text","name":"monetization_model"},"opportunity_score":{"data_type":"double","name":"opportunity_score"},"final_score":{"data_type":"double","name":"final_score"},"status":{"data_type":"text","name":"status"},"ai_profile":{"data_type":"json","name":"ai_profile"},"app_name":{"data_type":"text","name":"app_name"},"app_category":{"data_type":"text","name":"app_category"},"profession":{"data_type":"text","name":"profession"},"core_problems":{"data_type":"json","name":"core_problems"},"dimension_scores":{"data_type":"json","name":"dimension_scores"},"priority":{"data_type":"text","name":"priority"},"confidence":{"data_type":"decimal","name":"confidence"},"evidence_based":{"data_type":"bool","name":"evidence_based"},"trust_score":{"data_type":"double","name":"trust_score"},"trust_badge":{"data_type":"text","name":"trust_badge"},"activity_score":{"data_type":"double","name":"activity_score"},"trust_level":{"data_type":"text","name":"trust_level"},"trust_badges":{"data_type":"json","name":"trust_badges"},"monetization_score":{"data_type":"decimal","name":"monetization_score"},"market_validation_score":{"data_type":"decimal","name":"market_validation_score"},"analyzed_at":{"data_type":"timestamp","name":"analyzed_at"},"enrichment_version":{"data_type":"text","name":"enrichment_version"},"pipeline_source":{"data_type":"text","name":"pipeline_source"},"title":{"data_type":"text","name":"title"},"subreddit":{"data_type":"text","name":"subreddit"},"reddit_score":{"data_type":"bigint","name":"reddit_score"},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"merge","name":"app_opportunities","resource":"app_opportunities","x-normalizer":{"max_nesting":1,"seen-data":true}},"_dlt_pipeline_state":{"columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"pipeline_name":{"name":"pipeline_name","data_type":"text","nullable":false},"state":{"name":"state","data_type":"text","nullable":false},"created_at":{"name":"created_at","data_type":"timestamp","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false,"precision":64},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"append","file_format":"preferred","name":"_dlt_pipeline_state","resource":"_dlt_pipeline_state","x-normalizer":{"seen-data":true}},"app_opportunities__core_functions":{"name":"app_opportunities__core_functions","columns":{"value":{"name":"value","data_type":"text","nullable":true},"_dlt_root_id":{"name":"_dlt_root_id","data_type":"text","nullable":false,"root_key":true},"_dlt_parent_id":{"name":"_dlt_parent_id","data_type":"text","nullable":false,"parent_key":true},"_dlt_list_idx":{"name":"_dlt_list_idx","data_type":"bigint","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"parent":"app_opportunities","x-normalizer":{"seen-data":true}}},"settings":{"detections":["iso_timestamp"],"default_hints":{"not_null":["_dlt_id","_dlt_root_id","_dlt_parent_id","_dlt_list_idx","_dlt_load_id"],"parent_key":["_dlt_parent_id"],"root_key":["_dlt_root_id"],"unique":["_dlt_id"],"row_key":["_dlt_id"]}},"normalizers":{"names":"snake_case","json":{"module":"dlt.common.normalizers.json.relational","config":{"propagation":{"tables":{"app_opportunities":{"_dlt_id":"_dlt_root_id"}}}}}},"previous_hashes":["nDLAp9QJLg67NRsvauHf5quET9LmaZ8YSmKcypr5Wds=","gbvcKYpG8BKSlO557kmGKeT9heSVkTsTEqxl8u4CjG4=","P1zh8nMT8IAl11VXtMGvpHoYLgpWM3DCZqRrTK3b4/A=","vLnuOt7zvQR+RNqUtD4/1PGBh7DzzjeKEnpJDdxvO18="]}
2	11	2025-11-24 00:47:24.129429+00	app_opportunities_loader	yuJ75xKwP3h5zR0FZqgtT9dyngWlP0ofPUwss+mV+Vg=	{"version":2,"version_hash":"yuJ75xKwP3h5zR0FZqgtT9dyngWlP0ofPUwss+mV+Vg=","engine_version":11,"name":"app_opportunities_loader","tables":{"_dlt_version":{"name":"_dlt_version","columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_name":{"name":"schema_name","data_type":"text","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":false},"schema":{"name":"schema","data_type":"text","nullable":false}},"write_disposition":"skip","resource":"_dlt_version","description":"Created by DLT. Tracks schema updates"},"_dlt_loads":{"name":"_dlt_loads","columns":{"load_id":{"name":"load_id","data_type":"text","nullable":false,"precision":64},"schema_name":{"name":"schema_name","data_type":"text","nullable":true},"status":{"name":"status","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_version_hash":{"name":"schema_version_hash","data_type":"text","nullable":true}},"write_disposition":"skip","resource":"_dlt_loads","description":"Created by DLT. Tracks completed loads"},"app_opportunities":{"columns":{"submission_id":{"data_type":"text","nullable":false,"name":"submission_id","primary_key":true},"problem_description":{"data_type":"text","name":"problem_description"},"app_concept":{"data_type":"text","name":"app_concept"},"core_functions":{"data_type":"text","name":"core_functions"},"value_proposition":{"data_type":"text","name":"value_proposition"},"target_user":{"data_type":"text","name":"target_user"},"monetization_model":{"data_type":"text","name":"monetization_model"},"opportunity_score":{"data_type":"double","name":"opportunity_score"},"final_score":{"data_type":"double","name":"final_score"},"status":{"data_type":"text","name":"status"},"ai_profile":{"data_type":"json","name":"ai_profile"},"app_name":{"data_type":"text","name":"app_name"},"app_category":{"data_type":"text","name":"app_category"},"profession":{"data_type":"text","name":"profession"},"core_problems":{"data_type":"json","name":"core_problems"},"dimension_scores":{"data_type":"json","name":"dimension_scores"},"priority":{"data_type":"text","name":"priority"},"confidence":{"data_type":"decimal","name":"confidence"},"evidence_based":{"data_type":"bool","name":"evidence_based"},"trust_level":{"data_type":"text","name":"trust_level"},"trust_badges":{"data_type":"json","name":"trust_badges"},"monetization_score":{"data_type":"decimal","name":"monetization_score"},"market_validation_score":{"data_type":"decimal","name":"market_validation_score"},"analyzed_at":{"data_type":"timestamp","name":"analyzed_at"},"enrichment_version":{"data_type":"text","name":"enrichment_version"},"pipeline_source":{"data_type":"text","name":"pipeline_source"},"title":{"data_type":"text","name":"title"},"subreddit":{"data_type":"text","name":"subreddit"},"reddit_score":{"data_type":"bigint","name":"reddit_score"},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"x-normalizer":{"max_nesting":1,"seen-data":true},"write_disposition":"merge","name":"app_opportunities","resource":"app_opportunities"},"_dlt_pipeline_state":{"columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"pipeline_name":{"name":"pipeline_name","data_type":"text","nullable":false},"state":{"name":"state","data_type":"text","nullable":false},"created_at":{"name":"created_at","data_type":"timestamp","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false,"precision":64},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"append","file_format":"preferred","name":"_dlt_pipeline_state","resource":"_dlt_pipeline_state","x-normalizer":{"seen-data":true}}},"settings":{"detections":["iso_timestamp"],"default_hints":{"not_null":["_dlt_id","_dlt_root_id","_dlt_parent_id","_dlt_list_idx","_dlt_load_id"],"parent_key":["_dlt_parent_id"],"root_key":["_dlt_root_id"],"unique":["_dlt_id"],"row_key":["_dlt_id"]}},"normalizers":{"names":"snake_case","json":{"module":"dlt.common.normalizers.json.relational","config":{"propagation":{"tables":{"app_opportunities":{"_dlt_id":"_dlt_root_id"}}}}}},"previous_hashes":["cBr73hZCGUCjl56SEqashWin+mcPJrpoWbC+T3cmyOQ=","U9+pGHMu2Lj/MM3bzVgoO0aCSH/BcGQ36tGnfUSoLgA="]}
15	11	2025-11-24 21:01:45.378624+00	reddit_harbor_problem_collection	NS4LPU4+tZlvO6LZkSMS3fknOeZhF6u9I8iK2Eth4yY=	{"version":15,"version_hash":"NS4LPU4+tZlvO6LZkSMS3fknOeZhF6u9I8iK2Eth4yY=","engine_version":11,"name":"reddit_harbor_problem_collection","tables":{"_dlt_version":{"name":"_dlt_version","columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_name":{"name":"schema_name","data_type":"text","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":false},"schema":{"name":"schema","data_type":"text","nullable":false}},"write_disposition":"skip","resource":"_dlt_version","description":"Created by DLT. Tracks schema updates"},"_dlt_loads":{"name":"_dlt_loads","columns":{"load_id":{"name":"load_id","data_type":"text","nullable":false,"precision":64},"schema_name":{"name":"schema_name","data_type":"text","nullable":true},"status":{"name":"status","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_version_hash":{"name":"schema_version_hash","data_type":"text","nullable":true}},"write_disposition":"skip","resource":"_dlt_loads","description":"Created by DLT. Tracks completed loads"},"workflow_results":{"columns":{"opportunity_id":{"data_type":"text","nullable":false,"unique":true,"name":"opportunity_id","primary_key":true},"app_name":{"data_type":"text","nullable":false,"name":"app_name"},"function_count":{"data_type":"bigint","nullable":false,"name":"function_count"},"function_list":{"data_type":"json","nullable":true,"name":"function_list"},"original_score":{"data_type":"double","nullable":false,"name":"original_score"},"final_score":{"data_type":"double","nullable":false,"name":"final_score"},"status":{"data_type":"text","nullable":false,"name":"status"},"constraint_applied":{"data_type":"bool","nullable":true,"name":"constraint_applied"},"ai_insight":{"data_type":"text","nullable":true,"name":"ai_insight"},"processed_at":{"data_type":"timestamp","nullable":true,"name":"processed_at"},"market_demand":{"data_type":"decimal","precision":5,"scale":2,"nullable":true,"name":"market_demand"},"pain_intensity":{"data_type":"decimal","precision":5,"scale":2,"nullable":true,"name":"pain_intensity"},"monetization_potential":{"data_type":"decimal","precision":5,"scale":2,"nullable":true,"name":"monetization_potential"},"market_gap":{"data_type":"decimal","precision":5,"scale":2,"nullable":true,"name":"market_gap"},"technical_feasibility":{"data_type":"decimal","precision":5,"scale":2,"nullable":true,"name":"technical_feasibility"},"core_functions":{"data_type":"bigint","nullable":true,"name":"core_functions"},"simplicity_score":{"data_type":"double","nullable":true,"name":"simplicity_score"},"is_disqualified":{"data_type":"bool","nullable":true,"name":"is_disqualified"},"constraint_version":{"data_type":"bigint","nullable":true,"name":"constraint_version"},"validation_timestamp":{"data_type":"timestamp","nullable":true,"name":"validation_timestamp"},"violation_reason":{"data_type":"text","nullable":true,"name":"violation_reason"},"validation_status":{"data_type":"text","nullable":true,"name":"validation_status"},"submission_id":{"name":"submission_id","data_type":"text","nullable":true},"problem_description":{"name":"problem_description","data_type":"text","nullable":true},"app_concept":{"name":"app_concept","data_type":"text","nullable":true},"value_proposition":{"name":"value_proposition","data_type":"text","nullable":true},"target_user":{"name":"target_user","data_type":"text","nullable":true},"monetization_model":{"name":"monetization_model","data_type":"text","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true},"trust_score":{"name":"trust_score","data_type":"double","nullable":true},"trust_badge":{"name":"trust_badge","data_type":"text","nullable":true},"activity_score":{"name":"activity_score","data_type":"double","nullable":true},"subreddit":{"name":"subreddit","data_type":"text","nullable":true},"llm_provider":{"name":"llm_provider","data_type":"text","nullable":true},"llm_prompt_tokens":{"name":"llm_prompt_tokens","data_type":"bigint","nullable":true},"llm_completion_tokens":{"name":"llm_completion_tokens","data_type":"bigint","nullable":true},"llm_total_tokens":{"name":"llm_total_tokens","data_type":"bigint","nullable":true},"llm_input_cost_usd":{"name":"llm_input_cost_usd","data_type":"double","nullable":true},"llm_output_cost_usd":{"name":"llm_output_cost_usd","data_type":"double","nullable":true},"llm_total_cost_usd":{"name":"llm_total_cost_usd","data_type":"double","nullable":true},"llm_latency_seconds":{"name":"llm_latency_seconds","data_type":"double","nullable":true},"cost_tracking_enabled":{"name":"cost_tracking_enabled","data_type":"bool","nullable":true},"llm_model_used":{"name":"llm_model_used","nullable":true,"data_type":"text"},"llm_timestamp":{"name":"llm_timestamp","nullable":true,"data_type":"timestamp"},"llm_pricing_info__input":{"name":"llm_pricing_info__input","data_type":"double","nullable":true},"llm_pricing_info__output":{"name":"llm_pricing_info__output","data_type":"double","nullable":true}},"write_disposition":"merge","name":"workflow_results","resource":"app_opportunities_with_constraint","x-normalizer":{"seen-data":true}},"_dlt_pipeline_state":{"columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"pipeline_name":{"name":"pipeline_name","data_type":"text","nullable":false},"state":{"name":"state","data_type":"text","nullable":false},"created_at":{"name":"created_at","data_type":"timestamp","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false,"precision":64},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"append","file_format":"preferred","name":"_dlt_pipeline_state","resource":"_dlt_pipeline_state","x-normalizer":{"seen-data":true}},"app_opportunities_trust":{"columns":{"submission_id":{"name":"submission_id","nullable":false,"primary_key":true,"data_type":"text"},"problem_description":{"name":"problem_description","data_type":"text","nullable":true},"app_concept":{"name":"app_concept","data_type":"text","nullable":true},"core_functions":{"name":"core_functions","data_type":"text","nullable":true},"value_proposition":{"name":"value_proposition","data_type":"text","nullable":true},"target_user":{"name":"target_user","data_type":"text","nullable":true},"monetization_model":{"name":"monetization_model","data_type":"text","nullable":true},"opportunity_score":{"name":"opportunity_score","data_type":"double","nullable":true},"title":{"name":"title","data_type":"text","nullable":true},"status":{"name":"status","data_type":"text","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true},"trust_score":{"name":"trust_score","data_type":"double","nullable":true},"trust_badge":{"name":"trust_badge","data_type":"text","nullable":true},"activity_score":{"name":"activity_score","data_type":"double","nullable":true},"engagement_level":{"name":"engagement_level","data_type":"text","nullable":true},"trust_level":{"name":"trust_level","data_type":"text","nullable":true},"trend_velocity":{"name":"trend_velocity","data_type":"bigint","nullable":true},"problem_validity":{"name":"problem_validity","data_type":"text","nullable":true},"discussion_quality":{"name":"discussion_quality","data_type":"text","nullable":true},"ai_confidence_level":{"name":"ai_confidence_level","data_type":"text","nullable":true},"trust_validation_timestamp":{"name":"trust_validation_timestamp","data_type":"double","nullable":true},"trust_validation_method":{"name":"trust_validation_method","data_type":"text","nullable":true},"subreddit":{"name":"subreddit","data_type":"text","nullable":true},"reddit_score":{"name":"reddit_score","data_type":"bigint","nullable":true},"num_comments":{"name":"num_comments","data_type":"bigint","nullable":true}},"write_disposition":"merge","name":"app_opportunities_trust","resource":"app_opportunities_trust","x-normalizer":{"seen-data":true}},"opportunity_analysis":{"columns":{"submission_id":{"name":"submission_id","nullable":false,"primary_key":true,"data_type":"text"},"opportunity_id":{"name":"opportunity_id","data_type":"text","nullable":true},"title":{"name":"title","data_type":"text","nullable":true},"subreddit":{"name":"subreddit","data_type":"text","nullable":true},"sector":{"name":"sector","data_type":"text","nullable":true},"market_demand":{"name":"market_demand","data_type":"bigint","nullable":true},"pain_intensity":{"name":"pain_intensity","data_type":"bigint","nullable":true},"monetization_potential":{"name":"monetization_potential","data_type":"bigint","nullable":true},"market_gap":{"name":"market_gap","data_type":"bigint","nullable":true},"technical_feasibility":{"name":"technical_feasibility","data_type":"bigint","nullable":true},"simplicity_score":{"name":"simplicity_score","data_type":"double","nullable":true},"final_score":{"name":"final_score","data_type":"bigint","nullable":true},"priority":{"name":"priority","data_type":"text","nullable":true},"app_concept":{"name":"app_concept","data_type":"text","nullable":true},"core_functions":{"name":"core_functions","data_type":"text","nullable":true},"growth_justification":{"name":"growth_justification","data_type":"text","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"merge","name":"opportunity_analysis","resource":"opportunity_analysis","x-normalizer":{"seen-data":true}},"app_opportunities":{"columns":{"submission_id":{"name":"submission_id","nullable":false,"primary_key":true,"data_type":"text"},"problem_description":{"name":"problem_description","data_type":"text","nullable":true},"app_concept":{"name":"app_concept","data_type":"text","nullable":true},"core_functions":{"name":"core_functions","data_type":"text","nullable":true},"value_proposition":{"name":"value_proposition","data_type":"text","nullable":true},"target_user":{"name":"target_user","data_type":"text","nullable":true},"monetization_model":{"name":"monetization_model","data_type":"text","nullable":true},"opportunity_score":{"name":"opportunity_score","data_type":"double","nullable":true},"title":{"name":"title","data_type":"text","nullable":true},"status":{"name":"status","data_type":"text","nullable":true},"trust_score":{"name":"trust_score","data_type":"double","nullable":true},"trust_badge":{"name":"trust_badge","data_type":"text","nullable":true},"activity_score":{"name":"activity_score","data_type":"bigint","nullable":true},"engagement_level":{"name":"engagement_level","data_type":"text","nullable":true},"trust_level":{"name":"trust_level","data_type":"text","nullable":true},"trend_velocity":{"name":"trend_velocity","data_type":"bigint","nullable":true},"problem_validity":{"name":"problem_validity","data_type":"text","nullable":true},"discussion_quality":{"name":"discussion_quality","data_type":"text","nullable":true},"ai_confidence_level":{"name":"ai_confidence_level","data_type":"text","nullable":true},"trust_validation_timestamp":{"name":"trust_validation_timestamp","data_type":"double","nullable":true},"trust_validation_method":{"name":"trust_validation_method","data_type":"text","nullable":true},"subreddit":{"name":"subreddit","data_type":"text","nullable":true},"reddit_score":{"name":"reddit_score","data_type":"bigint","nullable":true},"num_comments":{"name":"num_comments","data_type":"bigint","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"merge","name":"app_opportunities","resource":"app_opportunities","x-normalizer":{"seen-data":true}},"submissions":{"columns":{"submission_id":{"data_type":"text","nullable":true,"unique":true,"name":"submission_id","primary_key":true},"reddit_id":{"data_type":"text","nullable":true,"name":"reddit_id"},"title":{"data_type":"text","nullable":true,"name":"title"},"text":{"data_type":"text","nullable":true,"name":"text"},"content":{"data_type":"text","nullable":true,"name":"content"},"subreddit":{"data_type":"text","nullable":true,"name":"subreddit"},"upvotes":{"data_type":"bigint","nullable":true,"name":"upvotes"},"comments_count":{"data_type":"bigint","nullable":true,"name":"comments_count"},"url":{"data_type":"text","nullable":true,"name":"url"},"created_at":{"data_type":"timestamp","nullable":true,"name":"created_at"},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"merge","name":"submissions","resource":"submissions","x-normalizer":{"seen-data":true}}},"settings":{"detections":["iso_timestamp"],"default_hints":{"not_null":["_dlt_id","_dlt_root_id","_dlt_parent_id","_dlt_list_idx","_dlt_load_id"],"parent_key":["_dlt_parent_id"],"root_key":["_dlt_root_id"],"unique":["_dlt_id"],"row_key":["_dlt_id"]}},"normalizers":{"names":"snake_case","json":{"module":"dlt.common.normalizers.json.relational","config":{"propagation":{"tables":{"workflow_results":{"_dlt_id":"_dlt_root_id"},"app_opportunities_trust":{"_dlt_id":"_dlt_root_id"},"opportunity_analysis":{"_dlt_id":"_dlt_root_id"},"app_opportunities":{"_dlt_id":"_dlt_root_id"},"submissions":{"_dlt_id":"_dlt_root_id"}}}}}},"previous_hashes":["Ze6N3NbE1B7reRswjQaxqKsQCb0brwXgk/9nk6nyBkM=","uf0CuGV9MzBSfAoeUyyzMWNjFChzVTEPxt0YJ4yJExs=","4uTsDm0ZfWjpj4igxMXwwyDgyuNFwSRfcV7T6z6RVRw=","UvyLfXNOFpJw7lAY7kdOo0tvjN7mY2ctMTJKFkcKp6c=","ggA6NWSI+IJxDxR/TRFDL7ZUJeS8DaHBtw8yMah//t0=","IEeroXt9C83kuUSXk0UK9t0tYem+q595QqwSWa+/bfc=","e1ZGF//lZxGmI8hFvGQ19ekFPGy8ThnvASbEUP4hPk0=","Rrnd2OQofen4Ha5jPei/gWxYbR9HI6fwhT9WRNbVlB4=","7EIHexiIGLfsrqNB2X5TYTQJ8181N02y13Gbj8DO5uM=","Lwrd8V+0S1xbNeOyiq2auAW3Az6sWriZR3vlFUnLFQk="]}
16	11	2025-11-24 21:03:27.452774+00	reddit_harbor_problem_collection	oOqn9IwKatHf7VCRlELEy1nhpZL37tmsti+thh+OvtU=	{"version":16,"version_hash":"oOqn9IwKatHf7VCRlELEy1nhpZL37tmsti+thh+OvtU=","engine_version":11,"name":"reddit_harbor_problem_collection","tables":{"_dlt_version":{"name":"_dlt_version","columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_name":{"name":"schema_name","data_type":"text","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":false},"schema":{"name":"schema","data_type":"text","nullable":false}},"write_disposition":"skip","resource":"_dlt_version","description":"Created by DLT. Tracks schema updates"},"_dlt_loads":{"name":"_dlt_loads","columns":{"load_id":{"name":"load_id","data_type":"text","nullable":false,"precision":64},"schema_name":{"name":"schema_name","data_type":"text","nullable":true},"status":{"name":"status","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_version_hash":{"name":"schema_version_hash","data_type":"text","nullable":true}},"write_disposition":"skip","resource":"_dlt_loads","description":"Created by DLT. Tracks completed loads"},"workflow_results":{"columns":{"opportunity_id":{"data_type":"text","nullable":false,"unique":true,"name":"opportunity_id","primary_key":true},"app_name":{"data_type":"text","nullable":false,"name":"app_name"},"function_count":{"data_type":"bigint","nullable":false,"name":"function_count"},"function_list":{"data_type":"json","nullable":true,"name":"function_list"},"original_score":{"data_type":"double","nullable":false,"name":"original_score"},"final_score":{"data_type":"double","nullable":false,"name":"final_score"},"status":{"data_type":"text","nullable":false,"name":"status"},"constraint_applied":{"data_type":"bool","nullable":true,"name":"constraint_applied"},"ai_insight":{"data_type":"text","nullable":true,"name":"ai_insight"},"processed_at":{"data_type":"timestamp","nullable":true,"name":"processed_at"},"market_demand":{"data_type":"decimal","precision":5,"scale":2,"nullable":true,"name":"market_demand"},"pain_intensity":{"data_type":"decimal","precision":5,"scale":2,"nullable":true,"name":"pain_intensity"},"monetization_potential":{"data_type":"decimal","precision":5,"scale":2,"nullable":true,"name":"monetization_potential"},"market_gap":{"data_type":"decimal","precision":5,"scale":2,"nullable":true,"name":"market_gap"},"technical_feasibility":{"data_type":"decimal","precision":5,"scale":2,"nullable":true,"name":"technical_feasibility"},"core_functions":{"data_type":"bigint","nullable":true,"name":"core_functions"},"simplicity_score":{"data_type":"double","nullable":true,"name":"simplicity_score"},"is_disqualified":{"data_type":"bool","nullable":true,"name":"is_disqualified"},"constraint_version":{"data_type":"bigint","nullable":true,"name":"constraint_version"},"validation_timestamp":{"data_type":"timestamp","nullable":true,"name":"validation_timestamp"},"violation_reason":{"data_type":"text","nullable":true,"name":"violation_reason"},"validation_status":{"data_type":"text","nullable":true,"name":"validation_status"},"submission_id":{"name":"submission_id","data_type":"text","nullable":true},"problem_description":{"name":"problem_description","data_type":"text","nullable":true},"app_concept":{"name":"app_concept","data_type":"text","nullable":true},"value_proposition":{"name":"value_proposition","data_type":"text","nullable":true},"target_user":{"name":"target_user","data_type":"text","nullable":true},"monetization_model":{"name":"monetization_model","data_type":"text","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true},"trust_score":{"name":"trust_score","data_type":"double","nullable":true},"trust_badge":{"name":"trust_badge","data_type":"text","nullable":true},"activity_score":{"name":"activity_score","data_type":"double","nullable":true},"subreddit":{"name":"subreddit","data_type":"text","nullable":true},"llm_provider":{"name":"llm_provider","data_type":"text","nullable":true},"llm_prompt_tokens":{"name":"llm_prompt_tokens","data_type":"bigint","nullable":true},"llm_completion_tokens":{"name":"llm_completion_tokens","data_type":"bigint","nullable":true},"llm_total_tokens":{"name":"llm_total_tokens","data_type":"bigint","nullable":true},"llm_input_cost_usd":{"name":"llm_input_cost_usd","data_type":"double","nullable":true},"llm_output_cost_usd":{"name":"llm_output_cost_usd","data_type":"double","nullable":true},"llm_total_cost_usd":{"name":"llm_total_cost_usd","data_type":"double","nullable":true},"llm_latency_seconds":{"name":"llm_latency_seconds","data_type":"double","nullable":true},"cost_tracking_enabled":{"name":"cost_tracking_enabled","data_type":"bool","nullable":true},"llm_model_used":{"name":"llm_model_used","nullable":true,"data_type":"text"},"llm_timestamp":{"name":"llm_timestamp","nullable":true,"data_type":"timestamp"},"llm_pricing_info__input":{"name":"llm_pricing_info__input","data_type":"double","nullable":true},"llm_pricing_info__output":{"name":"llm_pricing_info__output","data_type":"double","nullable":true}},"write_disposition":"merge","name":"workflow_results","resource":"app_opportunities_with_constraint","x-normalizer":{"seen-data":true}},"_dlt_pipeline_state":{"columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"pipeline_name":{"name":"pipeline_name","data_type":"text","nullable":false},"state":{"name":"state","data_type":"text","nullable":false},"created_at":{"name":"created_at","data_type":"timestamp","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false,"precision":64},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"append","file_format":"preferred","name":"_dlt_pipeline_state","resource":"_dlt_pipeline_state","x-normalizer":{"seen-data":true}},"app_opportunities_trust":{"columns":{"submission_id":{"name":"submission_id","nullable":false,"primary_key":true,"data_type":"text"},"problem_description":{"name":"problem_description","data_type":"text","nullable":true},"app_concept":{"name":"app_concept","data_type":"text","nullable":true},"core_functions":{"name":"core_functions","data_type":"text","nullable":true},"value_proposition":{"name":"value_proposition","data_type":"text","nullable":true},"target_user":{"name":"target_user","data_type":"text","nullable":true},"monetization_model":{"name":"monetization_model","data_type":"text","nullable":true},"opportunity_score":{"name":"opportunity_score","data_type":"double","nullable":true},"title":{"name":"title","data_type":"text","nullable":true},"status":{"name":"status","data_type":"text","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true},"trust_score":{"name":"trust_score","data_type":"double","nullable":true},"trust_badge":{"name":"trust_badge","data_type":"text","nullable":true},"activity_score":{"name":"activity_score","data_type":"double","nullable":true},"engagement_level":{"name":"engagement_level","data_type":"text","nullable":true},"trust_level":{"name":"trust_level","data_type":"text","nullable":true},"trend_velocity":{"name":"trend_velocity","data_type":"bigint","nullable":true},"problem_validity":{"name":"problem_validity","data_type":"text","nullable":true},"discussion_quality":{"name":"discussion_quality","data_type":"text","nullable":true},"ai_confidence_level":{"name":"ai_confidence_level","data_type":"text","nullable":true},"trust_validation_timestamp":{"name":"trust_validation_timestamp","data_type":"double","nullable":true},"trust_validation_method":{"name":"trust_validation_method","data_type":"text","nullable":true},"subreddit":{"name":"subreddit","data_type":"text","nullable":true},"reddit_score":{"name":"reddit_score","data_type":"bigint","nullable":true},"num_comments":{"name":"num_comments","data_type":"bigint","nullable":true}},"write_disposition":"merge","name":"app_opportunities_trust","resource":"app_opportunities_trust","x-normalizer":{"seen-data":true}},"opportunity_analysis":{"columns":{"submission_id":{"name":"submission_id","nullable":false,"primary_key":true,"data_type":"text"},"opportunity_id":{"name":"opportunity_id","data_type":"text","nullable":true},"title":{"name":"title","data_type":"text","nullable":true},"subreddit":{"name":"subreddit","data_type":"text","nullable":true},"sector":{"name":"sector","data_type":"text","nullable":true},"market_demand":{"name":"market_demand","data_type":"bigint","nullable":true},"pain_intensity":{"name":"pain_intensity","data_type":"bigint","nullable":true},"monetization_potential":{"name":"monetization_potential","data_type":"bigint","nullable":true},"market_gap":{"name":"market_gap","data_type":"bigint","nullable":true},"technical_feasibility":{"name":"technical_feasibility","data_type":"bigint","nullable":true},"simplicity_score":{"name":"simplicity_score","data_type":"double","nullable":true},"final_score":{"name":"final_score","data_type":"bigint","nullable":true},"priority":{"name":"priority","data_type":"text","nullable":true},"app_concept":{"name":"app_concept","data_type":"text","nullable":true},"core_functions":{"name":"core_functions","data_type":"text","nullable":true},"growth_justification":{"name":"growth_justification","data_type":"text","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"merge","name":"opportunity_analysis","resource":"opportunity_analysis","x-normalizer":{"seen-data":true}},"app_opportunities":{"columns":{"submission_id":{"name":"submission_id","nullable":false,"primary_key":true,"data_type":"text"},"problem_description":{"name":"problem_description","data_type":"text","nullable":true},"app_concept":{"name":"app_concept","data_type":"text","nullable":true},"core_functions":{"name":"core_functions","data_type":"text","nullable":true},"value_proposition":{"name":"value_proposition","data_type":"text","nullable":true},"target_user":{"name":"target_user","data_type":"text","nullable":true},"monetization_model":{"name":"monetization_model","data_type":"text","nullable":true},"opportunity_score":{"name":"opportunity_score","data_type":"double","nullable":true},"title":{"name":"title","data_type":"text","nullable":true},"status":{"name":"status","data_type":"text","nullable":true},"trust_score":{"name":"trust_score","data_type":"double","nullable":true},"trust_badge":{"name":"trust_badge","data_type":"text","nullable":true},"activity_score":{"name":"activity_score","data_type":"bigint","nullable":true},"engagement_level":{"name":"engagement_level","data_type":"text","nullable":true},"trust_level":{"name":"trust_level","data_type":"text","nullable":true},"trend_velocity":{"name":"trend_velocity","data_type":"bigint","nullable":true},"problem_validity":{"name":"problem_validity","data_type":"text","nullable":true},"discussion_quality":{"name":"discussion_quality","data_type":"text","nullable":true},"ai_confidence_level":{"name":"ai_confidence_level","data_type":"text","nullable":true},"trust_validation_timestamp":{"name":"trust_validation_timestamp","data_type":"double","nullable":true},"trust_validation_method":{"name":"trust_validation_method","data_type":"text","nullable":true},"subreddit":{"name":"subreddit","data_type":"text","nullable":true},"reddit_score":{"name":"reddit_score","data_type":"bigint","nullable":true},"num_comments":{"name":"num_comments","data_type":"bigint","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"merge","name":"app_opportunities","resource":"app_opportunities","x-normalizer":{"seen-data":true}},"submissions":{"columns":{"submission_id":{"data_type":"text","nullable":true,"unique":true,"name":"submission_id","primary_key":true},"reddit_id":{"data_type":"text","nullable":false,"name":"reddit_id"},"title":{"data_type":"text","nullable":false,"name":"title"},"text":{"data_type":"text","nullable":true,"name":"text"},"content":{"data_type":"text","nullable":true,"name":"content"},"subreddit":{"data_type":"text","nullable":true,"name":"subreddit"},"upvotes":{"data_type":"bigint","nullable":true,"name":"upvotes"},"comments_count":{"data_type":"bigint","nullable":true,"name":"comments_count"},"url":{"data_type":"text","nullable":true,"name":"url"},"created_at":{"data_type":"timestamp","nullable":true,"name":"created_at"},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true},"id":{"data_type":"text","nullable":true,"unique":true,"name":"id","primary_key":true},"score":{"data_type":"bigint","nullable":true,"name":"score"},"num_comments":{"data_type":"bigint","nullable":true,"name":"num_comments"}},"write_disposition":"merge","name":"submissions","resource":"submissions","x-normalizer":{"seen-data":true}}},"settings":{"detections":["iso_timestamp"],"default_hints":{"not_null":["_dlt_id","_dlt_root_id","_dlt_parent_id","_dlt_list_idx","_dlt_load_id"],"parent_key":["_dlt_parent_id"],"root_key":["_dlt_root_id"],"unique":["_dlt_id"],"row_key":["_dlt_id"]}},"normalizers":{"names":"snake_case","json":{"module":"dlt.common.normalizers.json.relational","config":{"propagation":{"tables":{"workflow_results":{"_dlt_id":"_dlt_root_id"},"app_opportunities_trust":{"_dlt_id":"_dlt_root_id"},"opportunity_analysis":{"_dlt_id":"_dlt_root_id"},"app_opportunities":{"_dlt_id":"_dlt_root_id"},"submissions":{"_dlt_id":"_dlt_root_id"}}}}}},"previous_hashes":["NS4LPU4+tZlvO6LZkSMS3fknOeZhF6u9I8iK2Eth4yY=","Ze6N3NbE1B7reRswjQaxqKsQCb0brwXgk/9nk6nyBkM=","uf0CuGV9MzBSfAoeUyyzMWNjFChzVTEPxt0YJ4yJExs=","4uTsDm0ZfWjpj4igxMXwwyDgyuNFwSRfcV7T6z6RVRw=","UvyLfXNOFpJw7lAY7kdOo0tvjN7mY2ctMTJKFkcKp6c=","ggA6NWSI+IJxDxR/TRFDL7ZUJeS8DaHBtw8yMah//t0=","IEeroXt9C83kuUSXk0UK9t0tYem+q595QqwSWa+/bfc=","e1ZGF//lZxGmI8hFvGQ19ekFPGy8ThnvASbEUP4hPk0=","Rrnd2OQofen4Ha5jPei/gWxYbR9HI6fwhT9WRNbVlB4=","7EIHexiIGLfsrqNB2X5TYTQJ8181N02y13Gbj8DO5uM="]}
2	11	2025-11-24 21:17:49.671472+00	reddit_harbor_problem_collection	hDBzzYnadKBT/YMZePqnS7NbEcHd7SCPtG9ys2jMCDo=	{"version":2,"version_hash":"hDBzzYnadKBT/YMZePqnS7NbEcHd7SCPtG9ys2jMCDo=","engine_version":11,"name":"reddit_harbor_problem_collection","tables":{"_dlt_version":{"name":"_dlt_version","columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_name":{"name":"schema_name","data_type":"text","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":false},"schema":{"name":"schema","data_type":"text","nullable":false}},"write_disposition":"skip","resource":"_dlt_version","description":"Created by DLT. Tracks schema updates"},"_dlt_loads":{"name":"_dlt_loads","columns":{"load_id":{"name":"load_id","data_type":"text","nullable":false,"precision":64},"schema_name":{"name":"schema_name","data_type":"text","nullable":true},"status":{"name":"status","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_version_hash":{"name":"schema_version_hash","data_type":"text","nullable":true}},"write_disposition":"skip","resource":"_dlt_loads","description":"Created by DLT. Tracks completed loads"},"submissions":{"columns":{"id":{"data_type":"text","nullable":true,"unique":true,"name":"id","primary_key":true},"reddit_id":{"data_type":"text","nullable":false,"name":"reddit_id"},"title":{"data_type":"text","nullable":false,"name":"title"},"content":{"data_type":"text","nullable":true,"name":"content"},"url":{"data_type":"text","nullable":true,"name":"url"},"score":{"data_type":"bigint","nullable":true,"name":"score"},"num_comments":{"data_type":"bigint","nullable":true,"name":"num_comments"},"created_at":{"data_type":"timestamp","nullable":true,"name":"created_at"},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"merge","name":"submissions","resource":"submissions","x-normalizer":{"seen-data":true}},"_dlt_pipeline_state":{"columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"pipeline_name":{"name":"pipeline_name","data_type":"text","nullable":false},"state":{"name":"state","data_type":"text","nullable":false},"created_at":{"name":"created_at","data_type":"timestamp","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false,"precision":64},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"append","file_format":"preferred","name":"_dlt_pipeline_state","resource":"_dlt_pipeline_state","x-normalizer":{"seen-data":true}}},"settings":{"detections":["iso_timestamp"],"default_hints":{"not_null":["_dlt_id","_dlt_root_id","_dlt_parent_id","_dlt_list_idx","_dlt_load_id"],"parent_key":["_dlt_parent_id"],"root_key":["_dlt_root_id"],"unique":["_dlt_id"],"row_key":["_dlt_id"]}},"normalizers":{"names":"snake_case","json":{"module":"dlt.common.normalizers.json.relational","config":{"propagation":{"tables":{"submissions":{"_dlt_id":"_dlt_root_id"}}}}}},"previous_hashes":["lVlN6niPAJ26Yn5MRaeSW/KM+8034t2lkXlT6LDuwLY=","BRfhPSxTzoZLIYl2QVX+ToGT+l1nrZ8SMYwVo8StE3M="]}
2	11	2025-11-24 23:24:22.864071+00	app_opportunities_test_loader	wsCtuhTqV8A053UkyYqy+4m2mZvO6o/soZeiqiSOK6E=	{"version":2,"version_hash":"wsCtuhTqV8A053UkyYqy+4m2mZvO6o/soZeiqiSOK6E=","engine_version":11,"name":"app_opportunities_test_loader","tables":{"_dlt_version":{"name":"_dlt_version","columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_name":{"name":"schema_name","data_type":"text","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":false},"schema":{"name":"schema","data_type":"text","nullable":false}},"write_disposition":"skip","resource":"_dlt_version","description":"Created by DLT. Tracks schema updates"},"_dlt_loads":{"name":"_dlt_loads","columns":{"load_id":{"name":"load_id","data_type":"text","nullable":false,"precision":64},"schema_name":{"name":"schema_name","data_type":"text","nullable":true},"status":{"name":"status","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_version_hash":{"name":"schema_version_hash","data_type":"text","nullable":true}},"write_disposition":"skip","resource":"_dlt_loads","description":"Created by DLT. Tracks completed loads"},"app_opportunities_test":{"columns":{"id":{"data_type":"text","nullable":false,"name":"id","primary_key":true},"problem_description":{"data_type":"text","name":"problem_description"},"app_concept":{"data_type":"text","name":"app_concept"},"core_functions":{"data_type":"json","name":"core_functions"},"value_proposition":{"data_type":"text","name":"value_proposition"},"target_user":{"data_type":"text","name":"target_user"},"monetization_model":{"data_type":"text","name":"monetization_model"},"opportunity_score":{"data_type":"double","name":"opportunity_score"},"final_score":{"data_type":"double","name":"final_score"},"status":{"data_type":"text","name":"status"},"title":{"data_type":"text","name":"title"},"subreddit":{"data_type":"text","name":"subreddit"},"reddit_score":{"data_type":"bigint","name":"reddit_score"},"analyzed_at":{"data_type":"timestamp","name":"analyzed_at"},"enrichment_version":{"data_type":"text","name":"enrichment_version"},"pipeline_source":{"data_type":"text","name":"pipeline_source"},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"replace","name":"app_opportunities_test","resource":"app_opportunities_test","x-normalizer":{"seen-data":true}},"_dlt_pipeline_state":{"columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"pipeline_name":{"name":"pipeline_name","data_type":"text","nullable":false},"state":{"name":"state","data_type":"text","nullable":false},"created_at":{"name":"created_at","data_type":"timestamp","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false,"precision":64},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"append","file_format":"preferred","name":"_dlt_pipeline_state","resource":"_dlt_pipeline_state","x-normalizer":{"seen-data":true}}},"settings":{"detections":["iso_timestamp"],"default_hints":{"not_null":["_dlt_id","_dlt_root_id","_dlt_parent_id","_dlt_list_idx","_dlt_load_id"],"parent_key":["_dlt_parent_id"],"root_key":["_dlt_root_id"],"unique":["_dlt_id"],"row_key":["_dlt_id"]}},"normalizers":{"names":"snake_case","json":{"module":"dlt.common.normalizers.json.relational"}},"previous_hashes":["ExX04I7dX8wO2pn3IETV8/tS8c3PcZh+tf9PHxqo2TE=","HBC99cx3DhmHH44vmcMEcsdxngZcIUIj7mNw44wyjgs="]}
2	11	2025-11-24 23:26:40.739187+00	app_opportunities_test_20251124_202640_loader	k3trREG7jTIGBhx2Wu9qRSsahChfj39gnnicgNrat5g=	{"version":2,"version_hash":"k3trREG7jTIGBhx2Wu9qRSsahChfj39gnnicgNrat5g=","engine_version":11,"name":"app_opportunities_test_20251124_202640_loader","tables":{"_dlt_version":{"name":"_dlt_version","columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_name":{"name":"schema_name","data_type":"text","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":false},"schema":{"name":"schema","data_type":"text","nullable":false}},"write_disposition":"skip","resource":"_dlt_version","description":"Created by DLT. Tracks schema updates"},"_dlt_loads":{"name":"_dlt_loads","columns":{"load_id":{"name":"load_id","data_type":"text","nullable":false,"precision":64},"schema_name":{"name":"schema_name","data_type":"text","nullable":true},"status":{"name":"status","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_version_hash":{"name":"schema_version_hash","data_type":"text","nullable":true}},"write_disposition":"skip","resource":"_dlt_loads","description":"Created by DLT. Tracks completed loads"},"app_opportunities_test_20251124_202640":{"columns":{"id":{"data_type":"text","nullable":false,"name":"id","primary_key":true},"problem_description":{"data_type":"text","name":"problem_description"},"app_concept":{"data_type":"text","name":"app_concept"},"core_functions":{"data_type":"json","name":"core_functions"},"value_proposition":{"data_type":"text","name":"value_proposition"},"target_user":{"data_type":"text","name":"target_user"},"monetization_model":{"data_type":"text","name":"monetization_model"},"opportunity_score":{"data_type":"double","name":"opportunity_score"},"final_score":{"data_type":"double","name":"final_score"},"status":{"data_type":"text","name":"status"},"title":{"data_type":"text","name":"title"},"subreddit":{"data_type":"text","name":"subreddit"},"reddit_score":{"data_type":"bigint","name":"reddit_score"},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"merge","name":"app_opportunities_test_20251124_202640","resource":"app_opportunities_test_20251124_202640","x-normalizer":{"seen-data":true}},"_dlt_pipeline_state":{"columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"pipeline_name":{"name":"pipeline_name","data_type":"text","nullable":false},"state":{"name":"state","data_type":"text","nullable":false},"created_at":{"name":"created_at","data_type":"timestamp","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false,"precision":64},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"append","file_format":"preferred","name":"_dlt_pipeline_state","resource":"_dlt_pipeline_state","x-normalizer":{"seen-data":true}}},"settings":{"detections":["iso_timestamp"],"default_hints":{"not_null":["_dlt_id","_dlt_root_id","_dlt_parent_id","_dlt_list_idx","_dlt_load_id"],"parent_key":["_dlt_parent_id"],"root_key":["_dlt_root_id"],"unique":["_dlt_id"],"row_key":["_dlt_id"]}},"normalizers":{"names":"snake_case","json":{"module":"dlt.common.normalizers.json.relational","config":{"propagation":{"tables":{"app_opportunities_test_20251124_202640":{"_dlt_id":"_dlt_root_id"}}}}}},"previous_hashes":["armngwyS8Ef0gZLNqqEelVwbQ/pb8gfC1nu1AYmfl4k=","B4mXWDktv2nBKSWmatKCXv7i9o2p+KDeEAqmDSPExYw="]}
2	11	2025-11-24 23:36:10.275708+00	app_opportunities_test_20251124_203609_loader	BQ95pMDguFCyoBTC4UeGoYttu3g/xBMjxFuXBrcEj1c=	{"version":2,"version_hash":"BQ95pMDguFCyoBTC4UeGoYttu3g/xBMjxFuXBrcEj1c=","engine_version":11,"name":"app_opportunities_test_20251124_203609_loader","tables":{"_dlt_version":{"name":"_dlt_version","columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_name":{"name":"schema_name","data_type":"text","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":false},"schema":{"name":"schema","data_type":"text","nullable":false}},"write_disposition":"skip","resource":"_dlt_version","description":"Created by DLT. Tracks schema updates"},"_dlt_loads":{"name":"_dlt_loads","columns":{"load_id":{"name":"load_id","data_type":"text","nullable":false,"precision":64},"schema_name":{"name":"schema_name","data_type":"text","nullable":true},"status":{"name":"status","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_version_hash":{"name":"schema_version_hash","data_type":"text","nullable":true}},"write_disposition":"skip","resource":"_dlt_loads","description":"Created by DLT. Tracks completed loads"},"app_opportunities_test_20251124_203609":{"columns":{"id":{"data_type":"text","nullable":false,"name":"id","primary_key":true},"problem_description":{"data_type":"text","name":"problem_description"},"app_concept":{"data_type":"text","name":"app_concept"},"core_functions":{"data_type":"json","name":"core_functions"},"value_proposition":{"data_type":"text","name":"value_proposition"},"target_user":{"data_type":"text","name":"target_user"},"monetization_model":{"data_type":"text","name":"monetization_model"},"opportunity_score":{"data_type":"double","name":"opportunity_score"},"final_score":{"data_type":"double","name":"final_score"},"status":{"data_type":"text","name":"status"},"title":{"data_type":"text","name":"title"},"subreddit":{"data_type":"text","name":"subreddit"},"reddit_score":{"data_type":"bigint","name":"reddit_score"},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"merge","name":"app_opportunities_test_20251124_203609","resource":"app_opportunities_test_20251124_203609","x-normalizer":{"seen-data":true}},"_dlt_pipeline_state":{"columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"pipeline_name":{"name":"pipeline_name","data_type":"text","nullable":false},"state":{"name":"state","data_type":"text","nullable":false},"created_at":{"name":"created_at","data_type":"timestamp","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false,"precision":64},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"append","file_format":"preferred","name":"_dlt_pipeline_state","resource":"_dlt_pipeline_state","x-normalizer":{"seen-data":true}}},"settings":{"detections":["iso_timestamp"],"default_hints":{"not_null":["_dlt_id","_dlt_root_id","_dlt_parent_id","_dlt_list_idx","_dlt_load_id"],"parent_key":["_dlt_parent_id"],"root_key":["_dlt_root_id"],"unique":["_dlt_id"],"row_key":["_dlt_id"]}},"normalizers":{"names":"snake_case","json":{"module":"dlt.common.normalizers.json.relational","config":{"propagation":{"tables":{"app_opportunities_test_20251124_203609":{"_dlt_id":"_dlt_root_id"}}}}}},"previous_hashes":["8hRzASr7WCP1v7byCD/ABIZ+eEV8fKF280a+19W9uW0=","D18J2nEX9XP46n+ilM0H21diDMg+djlunruBWpPLZuI="]}
2	11	2025-11-24 23:57:59.169005+00	opportunities_loader	EAGvk3giyJEmhmpx3CaLjlV41JtuHf08JSpYGFfodGg=	{"version":2,"version_hash":"EAGvk3giyJEmhmpx3CaLjlV41JtuHf08JSpYGFfodGg=","engine_version":11,"name":"opportunities_loader","tables":{"_dlt_version":{"name":"_dlt_version","columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_name":{"name":"schema_name","data_type":"text","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":false},"schema":{"name":"schema","data_type":"text","nullable":false}},"write_disposition":"skip","resource":"_dlt_version","description":"Created by DLT. Tracks schema updates"},"_dlt_loads":{"name":"_dlt_loads","columns":{"load_id":{"name":"load_id","data_type":"text","nullable":false,"precision":64},"schema_name":{"name":"schema_name","data_type":"text","nullable":true},"status":{"name":"status","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_version_hash":{"name":"schema_version_hash","data_type":"text","nullable":true}},"write_disposition":"skip","resource":"_dlt_loads","description":"Created by DLT. Tracks completed loads"},"opportunities":{"columns":{"id":{"name":"id","data_type":"text","nullable":true},"title":{"name":"title","data_type":"text","nullable":true},"description":{"name":"description","data_type":"text","nullable":true},"problem_statement":{"name":"problem_statement","data_type":"text","nullable":true},"target_audience":{"name":"target_audience","data_type":"text","nullable":true},"submission_id":{"name":"submission_id","data_type":"text","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"append","name":"opportunities","resource":"opportunities","x-normalizer":{"seen-data":true}},"_dlt_pipeline_state":{"columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"pipeline_name":{"name":"pipeline_name","data_type":"text","nullable":false},"state":{"name":"state","data_type":"text","nullable":false},"created_at":{"name":"created_at","data_type":"timestamp","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false,"precision":64},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"append","file_format":"preferred","name":"_dlt_pipeline_state","resource":"_dlt_pipeline_state","x-normalizer":{"seen-data":true}}},"settings":{"detections":["iso_timestamp"],"default_hints":{"not_null":["_dlt_id","_dlt_root_id","_dlt_parent_id","_dlt_list_idx","_dlt_load_id"],"parent_key":["_dlt_parent_id"],"root_key":["_dlt_root_id"],"unique":["_dlt_id"],"row_key":["_dlt_id"]}},"normalizers":{"names":"snake_case","json":{"module":"dlt.common.normalizers.json.relational"}},"previous_hashes":["iA8JYKtKA8FXizm0mZkI2l3svvnliN/mBTLwi0BVztc=","wM89AARmfr3jI6M5iNB+sdy/jTDq3LSre+I561VOyy4="]}
4	11	2025-11-25 00:13:49.390198+00	opportunities_loader	p45PMIDkaCQ1NUiYjqTf2bnZ3mY1+apIEqJUHc7d1+A=	{"version":4,"version_hash":"p45PMIDkaCQ1NUiYjqTf2bnZ3mY1+apIEqJUHc7d1+A=","engine_version":11,"name":"opportunities_loader","tables":{"_dlt_version":{"name":"_dlt_version","columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_name":{"name":"schema_name","data_type":"text","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":false},"schema":{"name":"schema","data_type":"text","nullable":false}},"write_disposition":"skip","resource":"_dlt_version","description":"Created by DLT. Tracks schema updates"},"_dlt_loads":{"name":"_dlt_loads","columns":{"load_id":{"name":"load_id","data_type":"text","nullable":false,"precision":64},"schema_name":{"name":"schema_name","data_type":"text","nullable":true},"status":{"name":"status","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_version_hash":{"name":"schema_version_hash","data_type":"text","nullable":true}},"write_disposition":"skip","resource":"_dlt_loads","description":"Created by DLT. Tracks completed loads"},"opportunities":{"columns":{"id":{"name":"id","data_type":"text","nullable":true},"title":{"name":"title","data_type":"text","nullable":true},"description":{"name":"description","data_type":"text","nullable":true},"problem_statement":{"name":"problem_statement","data_type":"text","nullable":true},"target_audience":{"name":"target_audience","data_type":"text","nullable":true},"submission_id":{"name":"submission_id","data_type":"text","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"append","name":"opportunities","resource":"opportunities","x-normalizer":{"seen-data":true}},"_dlt_pipeline_state":{"columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"pipeline_name":{"name":"pipeline_name","data_type":"text","nullable":false},"state":{"name":"state","data_type":"text","nullable":false},"created_at":{"name":"created_at","data_type":"timestamp","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false,"precision":64},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"append","file_format":"preferred","name":"_dlt_pipeline_state","resource":"_dlt_pipeline_state","x-normalizer":{"seen-data":true}},"opportunities_test_02_scaled":{"columns":{"id":{"name":"id","data_type":"text","nullable":true},"title":{"name":"title","data_type":"text","nullable":true},"description":{"name":"description","data_type":"text","nullable":true},"problem_statement":{"name":"problem_statement","data_type":"text","nullable":true},"target_audience":{"name":"target_audience","data_type":"text","nullable":true},"submission_id":{"name":"submission_id","nullable":true,"x-normalizer":{"seen-null-first":true}},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"append","name":"opportunities_test_02_scaled","resource":"opportunities_test_02_scaled","x-normalizer":{"seen-data":true}}},"settings":{"detections":["iso_timestamp"],"default_hints":{"not_null":["_dlt_id","_dlt_root_id","_dlt_parent_id","_dlt_list_idx","_dlt_load_id"],"parent_key":["_dlt_parent_id"],"root_key":["_dlt_root_id"],"unique":["_dlt_id"],"row_key":["_dlt_id"]}},"normalizers":{"names":"snake_case","json":{"module":"dlt.common.normalizers.json.relational"}},"previous_hashes":["kHTm2AJw+IOxjz5bXgtJWc2gXOxfSANTAe1134vbII0=","EAGvk3giyJEmhmpx3CaLjlV41JtuHf08JSpYGFfodGg=","iA8JYKtKA8FXizm0mZkI2l3svvnliN/mBTLwi0BVztc=","wM89AARmfr3jI6M5iNB+sdy/jTDq3LSre+I561VOyy4="]}
2	11	2025-11-25 01:56:05.656355+00	reddit_harbor_problem_collection	iy5xTWOr3IvfT1it6NQxtcnkN9m3itA3IL+CMl6O47k=	{"version":2,"version_hash":"iy5xTWOr3IvfT1it6NQxtcnkN9m3itA3IL+CMl6O47k=","engine_version":11,"name":"reddit_harbor_problem_collection","tables":{"_dlt_version":{"name":"_dlt_version","columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_name":{"name":"schema_name","data_type":"text","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":false},"schema":{"name":"schema","data_type":"text","nullable":false}},"write_disposition":"skip","resource":"_dlt_version","description":"Created by DLT. Tracks schema updates"},"_dlt_loads":{"name":"_dlt_loads","columns":{"load_id":{"name":"load_id","data_type":"text","nullable":false,"precision":64},"schema_name":{"name":"schema_name","data_type":"text","nullable":true},"status":{"name":"status","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_version_hash":{"name":"schema_version_hash","data_type":"text","nullable":true}},"write_disposition":"skip","resource":"_dlt_loads","description":"Created by DLT. Tracks completed loads"},"submissions":{"columns":{"id":{"name":"id","nullable":false,"primary_key":true,"data_type":"text"},"reddit_id":{"name":"reddit_id","data_type":"text","nullable":true},"title":{"name":"title","data_type":"text","nullable":true},"content":{"name":"content","data_type":"text","nullable":true},"url":{"name":"url","data_type":"text","nullable":true},"score":{"name":"score","data_type":"bigint","nullable":true},"num_comments":{"name":"num_comments","data_type":"bigint","nullable":true},"created_at":{"name":"created_at","data_type":"timestamp","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"merge","name":"submissions","resource":"submissions","x-normalizer":{"seen-data":true}},"_dlt_pipeline_state":{"columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"pipeline_name":{"name":"pipeline_name","data_type":"text","nullable":false},"state":{"name":"state","data_type":"text","nullable":false},"created_at":{"name":"created_at","data_type":"timestamp","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false,"precision":64},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"append","file_format":"preferred","name":"_dlt_pipeline_state","resource":"_dlt_pipeline_state","x-normalizer":{"seen-data":true}}},"settings":{"detections":["iso_timestamp"],"default_hints":{"not_null":["_dlt_id","_dlt_root_id","_dlt_parent_id","_dlt_list_idx","_dlt_load_id"],"parent_key":["_dlt_parent_id"],"root_key":["_dlt_root_id"],"unique":["_dlt_id"],"row_key":["_dlt_id"]}},"normalizers":{"names":"snake_case","json":{"module":"dlt.common.normalizers.json.relational","config":{"propagation":{"tables":{"submissions":{"_dlt_id":"_dlt_root_id"}}}}}},"previous_hashes":["0yPRmG+YH6nqe24+F3bC+Nq9dJsj93bgHTmhDEHegIE=","ofb+bmHW4D62+SmF78gXDTs/P+87JqbWPGTmz5oVXCA="]}
2	11	2025-11-25 21:58:00.236356+00	submissions_loader	B4/GpSpGzR9FoHBhQ2tZuMnya+lHvK7dJJt1IaCBb40=	{"version":2,"version_hash":"B4/GpSpGzR9FoHBhQ2tZuMnya+lHvK7dJJt1IaCBb40=","engine_version":11,"name":"submissions_loader","tables":{"_dlt_version":{"name":"_dlt_version","columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_name":{"name":"schema_name","data_type":"text","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":false},"schema":{"name":"schema","data_type":"text","nullable":false}},"write_disposition":"skip","resource":"_dlt_version","description":"Created by DLT. Tracks schema updates"},"_dlt_loads":{"name":"_dlt_loads","columns":{"load_id":{"name":"load_id","data_type":"text","nullable":false,"precision":64},"schema_name":{"name":"schema_name","data_type":"text","nullable":true},"status":{"name":"status","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_version_hash":{"name":"schema_version_hash","data_type":"text","nullable":true}},"write_disposition":"skip","resource":"_dlt_loads","description":"Created by DLT. Tracks completed loads"},"submissions":{"columns":{"submission_id":{"name":"submission_id","nullable":false,"primary_key":true,"data_type":"text"},"reddit_id":{"name":"reddit_id","data_type":"text","nullable":true},"title":{"name":"title","data_type":"text","nullable":true},"selftext":{"name":"selftext","nullable":true,"x-normalizer":{"seen-null-first":true}},"author":{"name":"author","nullable":true,"x-normalizer":{"seen-null-first":true}},"subreddit":{"name":"subreddit","data_type":"text","nullable":true},"trust_score":{"name":"trust_score","nullable":true,"x-normalizer":{"seen-null-first":true}},"trust_level":{"name":"trust_level","nullable":true,"x-normalizer":{"seen-null-first":true}},"market_validation_score":{"name":"market_validation_score","nullable":true,"x-normalizer":{"seen-null-first":true}},"opportunity_score":{"name":"opportunity_score","nullable":true,"x-normalizer":{"seen-null-first":true}},"created_utc":{"name":"created_utc","data_type":"timestamp","nullable":true},"reddit_score":{"name":"reddit_score","nullable":true,"x-normalizer":{"seen-null-first":true}},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"merge","name":"submissions","resource":"submissions","x-normalizer":{"seen-data":true}},"_dlt_pipeline_state":{"columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"pipeline_name":{"name":"pipeline_name","data_type":"text","nullable":false},"state":{"name":"state","data_type":"text","nullable":false},"created_at":{"name":"created_at","data_type":"timestamp","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false,"precision":64},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"append","file_format":"preferred","name":"_dlt_pipeline_state","resource":"_dlt_pipeline_state","x-normalizer":{"seen-data":true}}},"settings":{"detections":["iso_timestamp"],"default_hints":{"not_null":["_dlt_id","_dlt_root_id","_dlt_parent_id","_dlt_list_idx","_dlt_load_id"],"parent_key":["_dlt_parent_id"],"root_key":["_dlt_root_id"],"unique":["_dlt_id"],"row_key":["_dlt_id"]}},"normalizers":{"names":"snake_case","json":{"module":"dlt.common.normalizers.json.relational","config":{"propagation":{"tables":{"submissions":{"_dlt_id":"_dlt_root_id"}}}}}},"previous_hashes":["q7WyAM1Y6iTT+/mssTH//AV8mVQK214ii+QjV05t2c4=","lU73DOREC2HYbaTZqFYKuBPvNzkEBK8uOu53qIxaMiQ="]}
\.


--
-- Data for Name: app_opportunities; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.app_opportunities (submission_id, problem_description, app_concept, core_functions, value_proposition, target_user, monetization_model, opportunity_score, final_score, status, ai_profile, app_name, app_category, profession, core_problems, dimension_scores, priority, confidence, evidence_based, trust_score, trust_badge, activity_score, trust_level, trust_badges, monetization_score, market_validation_score, analyzed_at, enrichment_version, pipeline_source, title, subreddit, reddit_score, _dlt_load_id, _dlt_id) FROM stdin;
af60cd42-6350-583a-ac79-7992422fe5dc	Medium batch performance test record 0		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	60		0		[]	0.000000000	0.000000000	2025-11-27 16:53:19.43387+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Medium Batch Test 0	performance_test	0	sqlalchemy_load_20251127_165320_146048	sqlalchemy_a90fb9abdfae496a8a24bd72db744b5a_1764262400146045
0b3fe4b5-6f5c-5ab7-82df-564fcdafef70	Medium batch performance test record 1		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	61		0		[]	0.000000000	0.000000000	2025-11-27 16:53:19.433887+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Medium Batch Test 1	performance_test	5	sqlalchemy_load_20251127_165320_146127	sqlalchemy_95a221fa7a7c4d5b8cc09086f4bc341c_1764262400146126
35d7e6cb-626a-5d79-afda-f0c7d4125f67	Medium batch performance test record 2		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	62		0		[]	0.000000000	0.000000000	2025-11-27 16:53:19.433891+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Medium Batch Test 2	performance_test	10	sqlalchemy_load_20251127_165320_146183	sqlalchemy_8c2f80a96b5748e0aa01dfa614b0e454_1764262400146182
b7200ffc-9117-50a9-ba23-46f9dc083169	Medium batch performance test record 3		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	63		0		[]	0.000000000	0.000000000	2025-11-27 16:53:19.433894+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Medium Batch Test 3	performance_test	15	sqlalchemy_load_20251127_165320_146233	sqlalchemy_f8894133ced94084b57157203bd21110_1764262400146232
0d09e9ce-5e6b-57f1-b22a-33973d2d3a47	Medium batch performance test record 4		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	64		0		[]	0.000000000	0.000000000	2025-11-27 16:53:19.433897+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Medium Batch Test 4	performance_test	20	sqlalchemy_load_20251127_165320_146282	sqlalchemy_044ed3f005464091884404808d19d4ce_1764262400146282
7c711584-2aed-5039-a1dc-c043e96ff542	Medium batch performance test record 5		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	65		0		[]	0.000000000	0.000000000	2025-11-27 16:53:19.433901+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Medium Batch Test 5	performance_test	25	sqlalchemy_load_20251127_165320_146331	sqlalchemy_e64cff6d7519466a9a9074cb00ad4906_1764262400146330
b21e5d1c-c5d4-5f16-bf5e-35e22aae8a40	Medium batch performance test record 6		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	66		0		[]	0.000000000	0.000000000	2025-11-27 16:53:19.433905+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Medium Batch Test 6	performance_test	30	sqlalchemy_load_20251127_165320_146380	sqlalchemy_45a21acaae9a4363b06e68969f2a6cc9_1764262400146379
475f53f4-1d94-562d-bba8-20ec92ba0c4d	Medium batch performance test record 7		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	67		0		[]	0.000000000	0.000000000	2025-11-27 16:53:19.433908+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Medium Batch Test 7	performance_test	35	sqlalchemy_load_20251127_165320_146427	sqlalchemy_cf4ead46f484486f8d037398da6b6bca_1764262400146426
87be4c0a-d12e-5e00-afa5-a7a658f2316e	Medium batch performance test record 8		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	68		0		[]	0.000000000	0.000000000	2025-11-27 16:53:19.433912+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Medium Batch Test 8	performance_test	40	sqlalchemy_load_20251127_165320_146473	sqlalchemy_64ea8cdc977f46f68be7f5b21015e160_1764262400146472
841f6d7c-e0b8-5d75-9bee-28903132341d	Medium batch performance test record 9		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	69		0		[]	0.000000000	0.000000000	2025-11-27 16:53:19.433915+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Medium Batch Test 9	performance_test	45	sqlalchemy_load_20251127_165320_146519	sqlalchemy_874e09383bec422a8fbe9f305c345008_1764262400146518
3feaa905-1a7d-57c2-a77a-afd49e5b54b5	Medium batch performance test record 10		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	70		0		[]	0.000000000	0.000000000	2025-11-27 16:53:19.433918+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Medium Batch Test 10	performance_test	50	sqlalchemy_load_20251127_165320_146564	sqlalchemy_296acfaf4f854d309a12c78fa1cefcfc_1764262400146564
990c8515-898e-5ff9-b0a4-4f1402ea0ef6	Medium batch performance test record 11		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	71		0		[]	0.000000000	0.000000000	2025-11-27 16:53:19.433922+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Medium Batch Test 11	performance_test	55	sqlalchemy_load_20251127_165320_146610	sqlalchemy_1d36b13edb2a4fd1b5535b6baa33f086_1764262400146610
2221a5c1-41a7-5741-bc65-d455e99cc65a	Medium batch performance test record 12		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	72		0		[]	0.000000000	0.000000000	2025-11-27 16:53:19.433925+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Medium Batch Test 12	performance_test	60	sqlalchemy_load_20251127_165320_146654	sqlalchemy_6c9ff54ccc8246e8a5807425ae79cfb7_1764262400146654
6d3e69e5-1487-5fcf-9195-6f644d278e0e	Medium batch performance test record 13		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	73		0		[]	0.000000000	0.000000000	2025-11-27 16:53:19.433928+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Medium Batch Test 13	performance_test	65	sqlalchemy_load_20251127_165320_146698	sqlalchemy_18c7492ce42a45ceb5fb963a215fb715_1764262400146698
76aa9659-dc96-5af5-9b23-bf395480f2f8	Medium batch performance test record 14		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	74		0		[]	0.000000000	0.000000000	2025-11-27 16:53:19.433931+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Medium Batch Test 14	performance_test	70	sqlalchemy_load_20251127_165320_146743	sqlalchemy_87bb2314576f427ab22f307cf96fa9dc_1764262400146742
392c8d9a-82a4-5a96-a6f2-8679d3f5e0db	Medium batch performance test record 15		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	75		0		[]	0.000000000	0.000000000	2025-11-27 16:53:19.433934+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Medium Batch Test 15	performance_test	75	sqlalchemy_load_20251127_165320_146787	sqlalchemy_a72fc019983a456c8a072c3889a0f3ef_1764262400146787
180d507f-f295-5db1-b074-0094b728c4f5	Medium batch performance test record 16		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	76		0		[]	0.000000000	0.000000000	2025-11-27 16:53:19.433937+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Medium Batch Test 16	performance_test	80	sqlalchemy_load_20251127_165320_146831	sqlalchemy_fbb3dcb80e3c46d88c1ef19ca36c8f63_1764262400146831
2cd026b8-b8ab-50da-91a7-73da2e56632b	Medium batch performance test record 17		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	77		0		[]	0.000000000	0.000000000	2025-11-27 16:53:19.43394+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Medium Batch Test 17	performance_test	85	sqlalchemy_load_20251127_165320_146875	sqlalchemy_1daf77e4c59f44cd811c8c57ebf54285_1764262400146875
4c85e4db-889d-58b3-9544-2987341c044f	Medium batch performance test record 18		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	78		0		[]	0.000000000	0.000000000	2025-11-27 16:53:19.433944+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Medium Batch Test 18	performance_test	90	sqlalchemy_load_20251127_165320_146920	sqlalchemy_ba321fc640664f5592df9b0aa4a93904_1764262400146920
60097439-1d12-5e8b-b9e7-1929a9e62890	Medium batch performance test record 19		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	79		0		[]	0.000000000	0.000000000	2025-11-27 16:53:19.433947+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Medium Batch Test 19	performance_test	95	sqlalchemy_load_20251127_165320_146964	sqlalchemy_fef856a5b1b54e8790f054fadfccc1b4_1764262400146964
60591ef6-d7b2-5ee8-a89a-a07cd1c74e04	Medium batch performance test record 20		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	80		0		[]	0.000000000	0.000000000	2025-11-27 16:53:19.433951+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Medium Batch Test 20	performance_test	100	sqlalchemy_load_20251127_165320_147008	sqlalchemy_e6bacf01ebfb467387aef4702a2ac9cc_1764262400147008
09a5931b-0f52-5e05-b4e4-97d7caabc333	Medium batch performance test record 21		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	81		0		[]	0.000000000	0.000000000	2025-11-27 16:53:19.433955+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Medium Batch Test 21	performance_test	105	sqlalchemy_load_20251127_165320_147053	sqlalchemy_e64bdf144b3d46c3b2945a96b262613c_1764262400147052
96a9da91-283f-5e25-a2d2-1564718c9dc2	Medium batch performance test record 22		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	82		0		[]	0.000000000	0.000000000	2025-11-27 16:53:19.433958+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Medium Batch Test 22	performance_test	110	sqlalchemy_load_20251127_165320_147096	sqlalchemy_95de4e94a39b4f81839f46543da4c3a7_1764262400147096
55fa6f5a-ba6c-54b6-afba-dcea343f8e91	Medium batch performance test record 23		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	83		0		[]	0.000000000	0.000000000	2025-11-27 16:53:19.433961+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Medium Batch Test 23	performance_test	115	sqlalchemy_load_20251127_165320_147191	sqlalchemy_06d2d303ff644d249e77c3691b4e4e79_1764262400147190
4d1097a1-a700-587b-92c2-062b957ce94e	Medium batch performance test record 24		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	84		0		[]	0.000000000	0.000000000	2025-11-27 16:53:19.433965+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Medium Batch Test 24	performance_test	120	sqlalchemy_load_20251127_165320_147239	sqlalchemy_20d73aeddd8045c8a2a0537c50fd3056_1764262400147239
d91ee9a6-8665-5933-8e2b-42a53459ec9d	Medium batch performance test record 25		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	85		0		[]	0.000000000	0.000000000	2025-11-27 16:53:19.433968+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Medium Batch Test 25	performance_test	125	sqlalchemy_load_20251127_165320_147288	sqlalchemy_3631702f39184b419359f458df0e072b_1764262400147287
e3351901-1535-5c26-9526-cb4404c1529f	Medium batch performance test record 26		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	86		0		[]	0.000000000	0.000000000	2025-11-27 16:53:19.433971+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Medium Batch Test 26	performance_test	130	sqlalchemy_load_20251127_165320_147333	sqlalchemy_073f20cc63634761830007f17bb6ca78_1764262400147333
dec96262-cf78-5284-9003-e85781109b0b	Medium batch performance test record 27		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	87		0		[]	0.000000000	0.000000000	2025-11-27 16:53:19.433974+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Medium Batch Test 27	performance_test	135	sqlalchemy_load_20251127_165320_147385	sqlalchemy_3c01b3516948446fb042ce76a5b2c2ee_1764262400147384
157e7e6f-6a8c-538b-8f87-59e57a3dabaf	Medium batch performance test record 28		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	88		0		[]	0.000000000	0.000000000	2025-11-27 16:53:19.433978+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Medium Batch Test 28	performance_test	140	sqlalchemy_load_20251127_165320_147445	sqlalchemy_cd373b3ce875428e939e9a35924e2e04_1764262400147444
53970b84-a488-5f33-ba0b-1977cab701ce	Medium batch performance test record 29		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	89		0		[]	0.000000000	0.000000000	2025-11-27 16:53:19.433981+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Medium Batch Test 29	performance_test	145	sqlalchemy_load_20251127_165320_147491	sqlalchemy_7ebebff39a97433dbbd9307b679d4a6a_1764262400147491
e072015c-001d-5bc0-8e24-ddc6defdf899	Medium batch performance test record 30		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	90		0		[]	0.000000000	0.000000000	2025-11-27 16:53:19.433984+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Medium Batch Test 30	performance_test	150	sqlalchemy_load_20251127_165320_147537	sqlalchemy_ac43ba9d05df4021b5f783de8d6defdd_1764262400147537
75fe8423-e580-58c0-a0bc-923904f96e8b	Medium batch performance test record 31		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	91		0		[]	0.000000000	0.000000000	2025-11-27 16:53:19.433988+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Medium Batch Test 31	performance_test	155	sqlalchemy_load_20251127_165320_147582	sqlalchemy_b56e25f7a61343e0abaccec580db56c5_1764262400147582
cccc2911-3c50-5308-84bb-0dccced970cc	Medium batch performance test record 32		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	92		0		[]	0.000000000	0.000000000	2025-11-27 16:53:19.433991+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Medium Batch Test 32	performance_test	160	sqlalchemy_load_20251127_165320_147627	sqlalchemy_9e49a71dad2d4e71999dd4df4b6f549e_1764262400147627
e1d5f4dc-6b7a-55e1-8bf1-a3240984e7e5	Medium batch performance test record 33		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	93		0		[]	0.000000000	0.000000000	2025-11-27 16:53:19.433995+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Medium Batch Test 33	performance_test	165	sqlalchemy_load_20251127_165320_147672	sqlalchemy_693bfe7d38a84fd2a3a71218db2f8616_1764262400147671
f52b1109-59ed-5c56-a36e-c1d3b98cd2da	Medium batch performance test record 34		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	94		0		[]	0.000000000	0.000000000	2025-11-27 16:53:19.433998+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Medium Batch Test 34	performance_test	170	sqlalchemy_load_20251127_165320_147717	sqlalchemy_d3e67522801a463fa3470831856e438e_1764262400147716
bc96daf8-59dc-5f4d-8da1-4c04fc541b0f	Medium batch performance test record 35		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	95		0		[]	0.000000000	0.000000000	2025-11-27 16:53:19.434002+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Medium Batch Test 35	performance_test	175	sqlalchemy_load_20251127_165320_147762	sqlalchemy_cd41a53a912b4b10a31c956b490f0984_1764262400147761
176e0895-8308-53e4-afaa-10871aa4f21a	Medium batch performance test record 36		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	96		0		[]	0.000000000	0.000000000	2025-11-27 16:53:19.434005+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Medium Batch Test 36	performance_test	180	sqlalchemy_load_20251127_165320_147807	sqlalchemy_ffeda6c7da384f5286493bae439e2d9e_1764262400147806
a45b5351-3495-541c-b637-97ba49e8ad72	Medium batch performance test record 37		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	97		0		[]	0.000000000	0.000000000	2025-11-27 16:53:19.434008+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Medium Batch Test 37	performance_test	185	sqlalchemy_load_20251127_165320_147852	sqlalchemy_7a9e195b462d4ae885a496b3d9dafa70_1764262400147851
4b1ffa28-1a26-51d1-9c2d-67dcc567dcf0	Medium batch performance test record 38		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	98		0		[]	0.000000000	0.000000000	2025-11-27 16:53:19.434011+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Medium Batch Test 38	performance_test	190	sqlalchemy_load_20251127_165320_147897	sqlalchemy_569c1c006ac146c3bcd463061b45758c_1764262400147896
f0a8a130-b78d-55fc-8647-e926ed310439	Medium batch performance test record 39		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	99		0		[]	0.000000000	0.000000000	2025-11-27 16:53:19.434014+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Medium Batch Test 39	performance_test	195	sqlalchemy_load_20251127_165320_147940	sqlalchemy_31dccba6832d4d009a59b2832ef5ecb1_1764262400147940
178980ce-c39c-5b2a-9cfd-5aa77953fd6c	Medium batch performance test record 40		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	60		0		[]	0.000000000	0.000000000	2025-11-27 16:53:19.434018+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Medium Batch Test 40	performance_test	200	sqlalchemy_load_20251127_165320_147984	sqlalchemy_b739c083d831475cb4c6a68103d118d3_1764262400147983
673ed519-6c3b-5764-a4ba-88114c9f879a	Medium batch performance test record 41		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	61		0		[]	0.000000000	0.000000000	2025-11-27 16:53:19.434021+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Medium Batch Test 41	performance_test	205	sqlalchemy_load_20251127_165320_148028	sqlalchemy_0476f441ebcd4dcd8f2965df276a425e_1764262400148028
a2332d04-e0cf-5563-ad62-7e500c8e16ea	Medium batch performance test record 42		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	62		0		[]	0.000000000	0.000000000	2025-11-27 16:53:19.434024+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Medium Batch Test 42	performance_test	210	sqlalchemy_load_20251127_165320_148072	sqlalchemy_99c37a6541094485ba9ebb5cdc5a6293_1764262400148071
91b00b5e-c8ed-5356-8678-83371bf35854	Medium batch performance test record 43		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	63		0		[]	0.000000000	0.000000000	2025-11-27 16:53:19.434028+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Medium Batch Test 43	performance_test	215	sqlalchemy_load_20251127_165320_148115	sqlalchemy_9e5895eb8ad54eeeac2404f8ae763627_1764262400148115
8dbf631e-d376-5e6d-844c-82cd1fa12b2f	Medium batch performance test record 44		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	64		0		[]	0.000000000	0.000000000	2025-11-27 16:53:19.434031+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Medium Batch Test 44	performance_test	220	sqlalchemy_load_20251127_165320_148158	sqlalchemy_a25a98402bdd4b688aa3e9fbc4f7349c_1764262400148158
4067915b-ce38-5267-87ea-0bd6f0254b13	Medium batch performance test record 45		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	65		0		[]	0.000000000	0.000000000	2025-11-27 16:53:19.434034+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Medium Batch Test 45	performance_test	225	sqlalchemy_load_20251127_165320_148202	sqlalchemy_5c4ee1f511b94c3a97fe6d040ed07776_1764262400148201
e0c2e236-239c-5c33-a139-55515ad6738b	Medium batch performance test record 46		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	66		0		[]	0.000000000	0.000000000	2025-11-27 16:53:19.434038+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Medium Batch Test 46	performance_test	230	sqlalchemy_load_20251127_165320_148245	sqlalchemy_09bd990a9312417ab67dce94823e110a_1764262400148244
72947f1a-a908-5167-913c-0ac4bb9202e9	Medium batch performance test record 47		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	67		0		[]	0.000000000	0.000000000	2025-11-27 16:53:19.434041+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Medium Batch Test 47	performance_test	235	sqlalchemy_load_20251127_165320_148288	sqlalchemy_f52ef0cc07814a87bd8e2a466b01c5be_1764262400148288
471e74da-3745-5eee-8dd0-e043ff8c64fe	Medium batch performance test record 48		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	68		0		[]	0.000000000	0.000000000	2025-11-27 16:53:19.434044+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Medium Batch Test 48	performance_test	240	sqlalchemy_load_20251127_165320_148332	sqlalchemy_0a0382887b804deca79898e6ac04e4d9_1764262400148332
0396d180-6474-5756-96dd-4fe1976e61be	Medium batch performance test record 49		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	69		0		[]	0.000000000	0.000000000	2025-11-27 16:53:19.434047+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Medium Batch Test 49	performance_test	245	sqlalchemy_load_20251127_165320_148375	sqlalchemy_80836cb329544b37917b6a33d6e93350_1764262400148375
f54177a6-ec23-5648-96db-581fab5885c7	Integrity test record 0		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	75		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.277781+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Integrity Test 0	integrity_test	0	sqlalchemy_load_20251127_165320_287538	sqlalchemy_0159b93bf73a4e08bb34184e2991ed03_1764262400287534
79590360-0dac-58c0-b671-7cf6e8746962	Integrity test record 1		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	76		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.277798+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Integrity Test 1	integrity_test	10	sqlalchemy_load_20251127_165320_287630	sqlalchemy_5dc0eedf89d849fd94a704f597005a34_1764262400287629
a6b97264-37fb-5d6d-9cd3-b54448206ef0	Integrity test record 2		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	77		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.277803+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Integrity Test 2	integrity_test	20	sqlalchemy_load_20251127_165320_287688	sqlalchemy_24afc87e7fbb4953bd07edb84f2c2cfe_1764262400287687
1bbabb00-ba6a-50e4-af0a-cb75472d1e32	Integrity test record 3		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	78		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.277806+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Integrity Test 3	integrity_test	30	sqlalchemy_load_20251127_165320_287743	sqlalchemy_b8920332569746c9ab0a0b7ef3dd19b0_1764262400287743
900fef70-955c-502d-a7da-c440fdff83ed	Integrity test record 4		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	79		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.27781+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Integrity Test 4	integrity_test	40	sqlalchemy_load_20251127_165320_287790	sqlalchemy_e55ecc714c1c48bdb8c32337a133b830_1764262400287789
a9b51d7c-83c5-5705-9e53-a4f7ec26821e	Integrity test record 5		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	80		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.277814+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Integrity Test 5	integrity_test	50	sqlalchemy_load_20251127_165320_287850	sqlalchemy_411dcca5678e44e1946d06893498f28f_1764262400287850
2e04f8ba-a643-5286-936c-fac6d711452b	Integrity test record 6		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	81		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.277818+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Integrity Test 6	integrity_test	60	sqlalchemy_load_20251127_165320_287896	sqlalchemy_b57b055930054d3e899264f41a1995ec_1764262400287896
6cf1a146-e7d1-5af2-b322-cf82d43c9097	Integrity test record 7		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	82		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.277821+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Integrity Test 7	integrity_test	70	sqlalchemy_load_20251127_165320_287958	sqlalchemy_698f44108018454bbfd894a1f4fa1452_1764262400287958
fdb226b3-3037-5022-8391-a455623ca364	Integrity test record 8		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	83		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.277824+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Integrity Test 8	integrity_test	80	sqlalchemy_load_20251127_165320_288008	sqlalchemy_184af51b5ed5466d86fd8acc082cf620_1764262400288007
2db9d0e4-013a-5bb2-81a4-a0f7fb9e2c23	Integrity test record 9		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	84		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.277828+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Integrity Test 9	integrity_test	90	sqlalchemy_load_20251127_165320_288102	sqlalchemy_a8fbd680354541e5844d0761677e04f3_1764262400288101
ce117e31-6a9b-533d-b266-57c78b677d2d	Integrity test record 10		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	85		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.277831+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Integrity Test 10	integrity_test	100	sqlalchemy_load_20251127_165320_288161	sqlalchemy_609fb3183cd24f0393608336a39c6de1_1764262400288160
dc4a6b7d-00bb-5db3-8ccf-13c60c4be556	Integrity test record 11		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	86		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.277835+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Integrity Test 11	integrity_test	110	sqlalchemy_load_20251127_165320_288210	sqlalchemy_16040a44a01b498ca2a45fee812ba9ee_1764262400288209
cf4a0417-6377-57f3-9fa2-133898e584e8	Integrity test record 12		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	87		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.277839+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Integrity Test 12	integrity_test	120	sqlalchemy_load_20251127_165320_288263	sqlalchemy_696ff7a014f24a3fbcf0434c572947d6_1764262400288263
2ee29a98-7a5e-5410-9403-1ec9976c3f6f	Integrity test record 13		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	88		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.277843+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Integrity Test 13	integrity_test	130	sqlalchemy_load_20251127_165320_288324	sqlalchemy_dbbd0e502b264b6290bdb4f02a912aef_1764262400288324
373889dc-7215-5eda-b7ae-226977e5e6bb	Integrity test record 14		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	89		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.277846+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Integrity Test 14	integrity_test	140	sqlalchemy_load_20251127_165320_288408	sqlalchemy_bc48dd5b9a04475bbcb871af874501ba_1764262400288407
ac283231-5371-5134-a81e-d205e368fd5f	Integrity test record 15		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	90		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.27785+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Integrity Test 15	integrity_test	150	sqlalchemy_load_20251127_165320_288461	sqlalchemy_86a0431f81f54699b8c365a6310edb9e_1764262400288460
ef668a47-3577-5296-8ba9-7d0f194e04c0	Integrity test record 16		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	91		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.277853+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Integrity Test 16	integrity_test	160	sqlalchemy_load_20251127_165320_288511	sqlalchemy_9aaa2ac81c1b41298497b04e6db0810f_1764262400288510
74184921-2e6b-53ef-b1fe-67feb5ac4fe1	Integrity test record 17		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	92		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.277857+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Integrity Test 17	integrity_test	170	sqlalchemy_load_20251127_165320_288566	sqlalchemy_cdbc18c4cac9481c9c10b1d0a6bff889_1764262400288566
a4334810-de78-57cc-b09d-0ccebf0ed818	Integrity test record 18		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	93		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.27786+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Integrity Test 18	integrity_test	180	sqlalchemy_load_20251127_165320_288648	sqlalchemy_70d7f8e1a626472e873e53a51769fc71_1764262400288647
67c2a494-826c-53fb-90c0-63ced6aa9abe	Integrity test record 19		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	94		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.277864+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Integrity Test 19	integrity_test	190	sqlalchemy_load_20251127_165320_288712	sqlalchemy_c7402952a6124724a1f0a4a0b064f20f_1764262400288711
2ef06ff1-f4ea-5f27-98d0-744af8e2e55b	Integrity test record 20		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	95		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.277867+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Integrity Test 20	integrity_test	200	sqlalchemy_load_20251127_165320_288774	sqlalchemy_2da4da7fa8ae467499d27dc94fd513a8_1764262400288773
66ee0cf0-0133-57c8-93f0-fb1a466fea6c	Integrity test record 21		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	96		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.27787+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Integrity Test 21	integrity_test	210	sqlalchemy_load_20251127_165320_288877	sqlalchemy_a0afcdc5682f4a3db22516049fa883a2_1764262400288876
3a22be30-04bd-539b-bbaa-adc7fca5b3e8	Integrity test record 22		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	97		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.277874+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Integrity Test 22	integrity_test	220	sqlalchemy_load_20251127_165320_288943	sqlalchemy_d910d761d1314ba2ad497e15a754a8c9_1764262400288942
b491040e-a122-56e3-b411-bf5dbd6428ae	Integrity test record 23		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	98		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.277877+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Integrity Test 23	integrity_test	230	sqlalchemy_load_20251127_165320_289039	sqlalchemy_c68e2965bc2d488ba1fd81ca52faf4c5_1764262400289036
991ca793-da32-5161-9d66-059f11dac4f6	Integrity test record 24		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	99		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.27788+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Integrity Test 24	integrity_test	240	sqlalchemy_load_20251127_165320_289121	sqlalchemy_3e56afa776af48f39f98c08da24027aa_1764262400289120
ed2c9378-ae7a-58b5-a73e-f0a4638c47fd	Integrity test record 25		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	100		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.277884+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Integrity Test 25	integrity_test	250	sqlalchemy_load_20251127_165320_289221	sqlalchemy_3dc3f20669d44b70909f5218683d2b9a_1764262400289219
6db63432-f42f-5bac-97b6-045d30b3f0da	Integrity test record 26		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	101		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.277888+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Integrity Test 26	integrity_test	260	sqlalchemy_load_20251127_165320_289311	sqlalchemy_0013a1fbf91245a7a3e75b8efd25f7fb_1764262400289310
0438037e-8464-5676-8079-9bdef5c34203	Integrity test record 27		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	102		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.277891+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Integrity Test 27	integrity_test	270	sqlalchemy_load_20251127_165320_289370	sqlalchemy_c8528095bb1043ee938a0fbc215a0dde_1764262400289369
8d64313e-17c8-5776-a512-394905357a93	Integrity test record 28		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	103		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.277895+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Integrity Test 28	integrity_test	280	sqlalchemy_load_20251127_165320_289453	sqlalchemy_6b4154dacb7c42b6bea599464d2c11ef_1764262400289452
6cd1aa79-cf75-5676-8414-8a4c4e7b1a7b	Integrity test record 29		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	104		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.277898+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Integrity Test 29	integrity_test	290	sqlalchemy_load_20251127_165320_289510	sqlalchemy_7eddaaa919d045389c77315a443dab2f_1764262400289510
ffcdef27-ea30-59f7-818b-110563e03fb0	Integrity test record 30		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	105		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.277902+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Integrity Test 30	integrity_test	300	sqlalchemy_load_20251127_165320_289557	sqlalchemy_dc86dd3bdca04746bac01937db769f12_1764262400289557
9db0012f-d68d-583b-80c0-1dc295254d73	Integrity test record 31		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	106		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.277906+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Integrity Test 31	integrity_test	310	sqlalchemy_load_20251127_165320_289603	sqlalchemy_746ae774a9f24ab1972377b23cfc96a2_1764262400289603
72fad47a-3cdf-5a97-ac21-6067a20b0694	Integrity test record 32		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	107		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.277909+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Integrity Test 32	integrity_test	320	sqlalchemy_load_20251127_165320_289649	sqlalchemy_6e7fa1484afc4bcba602fc4beb0de146_1764262400289649
c5516f23-3f99-5e98-bde2-ef42d430111a	Integrity test record 33		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	108		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.277912+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Integrity Test 33	integrity_test	330	sqlalchemy_load_20251127_165320_289695	sqlalchemy_6fd4bd68956e48c582353d602bea3917_1764262400289695
1e9e597c-978f-55e9-8814-a24c0525645c	Integrity test record 34		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	109		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.277916+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Integrity Test 34	integrity_test	340	sqlalchemy_load_20251127_165320_289740	sqlalchemy_3286fd53caee4a16bd8c47bd73268a67_1764262400289740
7fdd65e3-69c6-505c-aac6-206ddac5573b	Integrity test record 35		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	110		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.277919+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Integrity Test 35	integrity_test	350	sqlalchemy_load_20251127_165320_289785	sqlalchemy_5fcf0f32ee9c4451956e7f61915306ee_1764262400289784
66d2b3eb-88d3-557d-bac0-45ba5a05a72c	Integrity test record 36		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	111		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.277923+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Integrity Test 36	integrity_test	360	sqlalchemy_load_20251127_165320_289829	sqlalchemy_ca023bf707624eedbdcca3f4e20c38bc_1764262400289828
6e9947c2-a21c-554f-b859-00c34fd51f7d	Integrity test record 37		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	112		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.277926+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Integrity Test 37	integrity_test	370	sqlalchemy_load_20251127_165320_289874	sqlalchemy_d857901ed1e6413383c8d75ec1dcf284_1764262400289873
c366500e-7b04-51e0-9c0a-daaad784d3c2	Integrity test record 38		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	113		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.27793+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Integrity Test 38	integrity_test	380	sqlalchemy_load_20251127_165320_289919	sqlalchemy_ae68afa252c64af08d5951adf0a7fcfa_1764262400289918
c6efa4f5-3fb9-5de9-a636-90388fd27e0f	Integrity test record 39		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	114		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.277933+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Integrity Test 39	integrity_test	390	sqlalchemy_load_20251127_165320_289996	sqlalchemy_e98f8f84b12d408ea642c56be32143b2_1764262400289993
69a3bf75-710e-5ee1-ac61-9615a567b398	Integrity test record 40		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	115		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.277937+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Integrity Test 40	integrity_test	400	sqlalchemy_load_20251127_165320_290063	sqlalchemy_fda6624435234a9bb399b7af4fec4240_1764262400290062
7ba29770-377f-5ad2-afc2-0d09431b534d	Integrity test record 41		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	116		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.27794+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Integrity Test 41	integrity_test	410	sqlalchemy_load_20251127_165320_290112	sqlalchemy_358598edd79b4c5ebb0b7f6b7176d656_1764262400290111
ce44d714-4beb-5587-8490-afa089225fbf	Integrity test record 42		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	117		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.277944+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Integrity Test 42	integrity_test	420	sqlalchemy_load_20251127_165320_290166	sqlalchemy_d2001bac20a1482194468738b74393c4_1764262400290165
baa09889-eeae-56ab-a305-086895c9c6ec	Integrity test record 43		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	118		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.277947+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Integrity Test 43	integrity_test	430	sqlalchemy_load_20251127_165320_290213	sqlalchemy_c259ddd4fa904178aaf749328b962423_1764262400290212
1fa6412b-799e-50c3-8033-37f915e3c238	Integrity test record 44		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	119		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.277951+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Integrity Test 44	integrity_test	440	sqlalchemy_load_20251127_165320_290288	sqlalchemy_1dd9c264e0b44c81b94ab80a2ef19356_1764262400290287
0a163a4c-32ea-5b8e-80c2-a23cc7535674	Integrity test record 45		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	120		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.277954+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Integrity Test 45	integrity_test	450	sqlalchemy_load_20251127_165320_290342	sqlalchemy_5877ce22dc0e4bb59d7d60f0821477d9_1764262400290341
f28476a8-7427-572d-a3d3-fe4c5bae7e78	Integrity test record 46		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	121		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.277958+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Integrity Test 46	integrity_test	460	sqlalchemy_load_20251127_165320_290388	sqlalchemy_e1fcb23b99434a108ce1bfa34d8d9259_1764262400290387
e4e8273f-515b-52d9-883e-e82af5d5de00	Integrity test record 47		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	122		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.277961+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Integrity Test 47	integrity_test	470	sqlalchemy_load_20251127_165320_290434	sqlalchemy_cb19889a2b404c9db40c26a6060f3320_1764262400290434
816d6b64-8410-548e-ac1a-316ba7bc09e6	Integrity test record 48		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	123		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.277964+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Integrity Test 48	integrity_test	480	sqlalchemy_load_20251127_165320_290480	sqlalchemy_8f2268145f5d4f27a93f06541251d8aa_1764262400290479
6f7bcf6b-3cd6-5e34-b5bf-1637e36ce343	Integrity test record 49		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	124		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.277968+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Integrity Test 49	integrity_test	490	sqlalchemy_load_20251127_165320_290525	sqlalchemy_4ae8f1af307f4ba4915a7e99dc7f1413_1764262400290524
43af70d2-ca2d-5242-9165-d18566f2bbc3	Specific text for corruption detection: ABC123XYZ		{}				92.3	\N	discovered	\N				\N	\N		0.000000000	f	87.5		0	HIGH	["BADGE1", "BADGE2"]	0.000000000	0.000000000	2024-11-27 12:00:00+00	v3.0.0	corruption_test_v1.0	Corruption Test Title	corruption_test	42	sqlalchemy_load_20251127_165320_537085	sqlalchemy_bbcdf625a2dd4f6db56bef81503ab4c2_1764262400537080
7aca7d76-a13e-5339-ac20-b38fff0b5907			{}				0	\N	discovered	\N				\N	\N		0.000000000	f	0		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.610755+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Second Load	consistency_test	20	sqlalchemy_load_20251127_165320_611156	sqlalchemy_48387dbad7594d49ab7a62ad03b2c7eb_1764262400611151
292ff495-c15b-5ea6-a4dd-eff38e9d9c85	Updated text		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	90		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.676108+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Updated Title	duplicate_test	200	sqlalchemy_load_20251127_165320_676329	sqlalchemy_27cdbffce69b456598758ec4ab25e419_1764262400676327
dc3a8005-80d2-5080-807c-78c05c31b429	Testing verification step		{}				0	\N	discovered	\N				\N	\N		0.000000000	f	85		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.794694+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Verification Test	verification_test	50	sqlalchemy_load_20251127_165320_795132	sqlalchemy_474763498d8e4720a78482b225d67aeb_1764262400795130
87dbd813-b325-5b1a-9f60-fb53ebe75a17			{}				0	\N	discovered	\N				\N	\N		0.000000000	f	0		0		[]	0.000000000	0.000000000	2025-11-27 16:53:20.838069+00	v3.0.0	pipeline_v2_sqlalchemy_fixed	Test	test	0	sqlalchemy_load_20251127_165320_837959	sqlalchemy_23a241c391d3462080b899c37fb737e5_1764262400837957
\.


--
-- Data for Name: app_opportunities_test; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.app_opportunities_test (id, problem_description, app_concept, core_functions, value_proposition, target_user, monetization_model, opportunity_score, final_score, status, title, subreddit, reddit_score, analyzed_at, enrichment_version, pipeline_source, _dlt_load_id, _dlt_id) FROM stdin;
5a6ec608-4d29-5191-bfa1-8aa8d1030e5a	I struggle with managing my time effectively across multiple projects	AI-powered project management tool with automatic prioritization	["Task prioritization", "Time tracking", "Progress visualization"]	Save 10+ hours per week through intelligent automation	Freelancers and small team managers	Subscription-based pricing tiers	85.5	88.2	discovered	I struggle with managing my time effectively across multiple projects	productivity	156	2025-11-24 20:25:00+00	1.0.0	test_02_direct	1764027363.4295378	EbP9ezLN0qUl+A
63304062-2fc8-5dc7-8ad7-bee9f18cec31	This manual data entry is frustrating and time consuming	Automated data extraction and entry platform	["OCR scanning", "Data validation", "Auto-form filling"]	Reduce data entry time by 95% with AI accuracy	Small business administrators	Per-document processing fee	78.3	81.7	discovered	This manual data entry is frustrating and time consuming	productivity	89	2025-11-24 20:25:00+00	1.0.0	test_02_direct	1764027363.4295378	u7+hz1jXZSvw8Q
f7b46c32-b2e9-5467-9699-5ee9bb4fd194	Looking for better tools to organize our startup workflow	Startup workflow orchestration platform	["Workflow templates", "Team collaboration", "Progress tracking"]	Accelerate startup development by 40%	Early-stage startup founders	Freemium with team features	92.1	94.8	validated	Looking for better tools to organize our startup workflow	entrepreneurship	124	2025-11-24 20:25:00+00	1.0.0	test_02_direct	1764027363.4295378	XiRlq9Q9BB1NRA
8eab83e2-9f0e-5b63-a2e8-12746c0a986e	Wish there was an app to boost my daily productivity	Personal productivity coach with habit tracking	["Habit formation", "Productivity analytics", "Goal setting"]	Increase daily productivity by 30%	Students and professionals	Premium subscription	76.8	79.4	discovered	Wish there was an app to boost my daily productivity	productivity	67	2025-11-24 20:25:00+00	1.0.0	test_02_direct	1764027363.4295378	WXScs3ZaiLVJjw
43a32f4d-309c-5c1c-b019-5a11702ef66f	Need help organizing multiple side projects	Multi-project management dashboard	["Project overview", "Resource allocation", "Timeline management"]	Effortlessly manage unlimited side projects	Side project creators and solopreneurs	Tiered pricing based on project count	88.7	91.3	validated	Need help organizing multiple side projects	SideProject	203	2025-11-24 20:25:00+00	1.0.0	test_02_direct	1764027363.4295378	p3DhQXplRlnNvQ
\.


--
-- Data for Name: app_opportunities_test_20251124_202640; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.app_opportunities_test_20251124_202640 (id, problem_description, app_concept, core_functions, value_proposition, target_user, monetization_model, opportunity_score, final_score, status, title, subreddit, reddit_score, _dlt_load_id, _dlt_id) FROM stdin;
test-001	Teams waste time managing multiple project tools	Integrated project management platform	["Task tracking", "Team collaboration"]	Save 10 hours per week with unified workflow	Small to medium teams	Subscription: $29/month per team	85.5	88.2	discovered	I struggle with managing my time effectively	productivity	156	1764026800.5946286	Oa6Rt/v5ZgSl6A
test-002	Manual data entry is frustrating	Automated data extraction platform	["OCR scanning", "Data validation"]	Reduce data entry time by 95%	Small business administrators	Per-document processing fee	78.3	81.7	discovered	This manual data entry is time consuming	productivity	89	1764026800.5946286	cSHdvdLCag236w
test-003	Looking for better startup workflow tools	Startup workflow orchestration platform	["Workflow templates", "Team collaboration"]	Accelerate startup development by 40%	Early-stage startup founders	Freemium with team features	92.1	94.8	validated	Better tools for startup workflow	entrepreneurship	124	1764026800.5946286	YKHrJJEBY3GzRQ
test-004	Need app to boost daily productivity	Personal productivity coach with habit tracking	["Habit formation", "Productivity analytics"]	Increase daily productivity by 30%	Students and professionals	Premium subscription	76.8	79.4	discovered	App to boost daily productivity	productivity	67	1764026800.5946286	iAP1LYO8e/nUgw
test-005	Help organizing multiple side projects	Multi-project management dashboard	["Project overview", "Resource allocation"]	Effortlessly manage unlimited side projects	Side project creators and solopreneurs	Tiered pricing based on project count	88.7	91.3	validated	Need help organizing side projects	SideProject	203	1764026800.5946286	AiHLEKyV+eKKeA
\.


--
-- Data for Name: app_opportunities_test_20251124_203609; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.app_opportunities_test_20251124_203609 (id, problem_description, app_concept, core_functions, value_proposition, target_user, monetization_model, opportunity_score, final_score, status, title, subreddit, reddit_score, _dlt_load_id, _dlt_id) FROM stdin;
test-001	Teams waste time managing multiple project tools	Integrated project management platform	["Task tracking", "Team collaboration"]	Save 10 hours per week with unified workflow	Small to medium teams	Subscription: $29/month per team	85.5	88.2	discovered	I struggle with managing my time effectively	productivity	156	1764027370.1243253	FgWbjimY/Jkegw
test-002	Manual data entry is frustrating	Automated data extraction platform	["OCR scanning", "Data validation"]	Reduce data entry time by 95%	Small business administrators	Per-document processing fee	78.3	81.7	discovered	This manual data entry is time consuming	productivity	89	1764027370.1243253	RbWPwJzSFY2zPg
test-003	Looking for better startup workflow tools	Startup workflow orchestration platform	["Workflow templates", "Team collaboration"]	Accelerate startup development by 40%	Early-stage startup founders	Freemium with team features	92.1	94.8	validated	Better tools for startup workflow	entrepreneurship	124	1764027370.1243253	c71R3P0/P8B1fg
test-004	Need app to boost daily productivity	Personal productivity coach with habit tracking	["Habit formation", "Productivity analytics"]	Increase daily productivity by 30%	Students and professionals	Premium subscription	76.8	79.4	discovered	App to boost daily productivity	productivity	67	1764027370.1243253	9Oa1a+oEDGzZ1Q
test-005	Help organizing multiple side projects	Multi-project management dashboard	["Project overview", "Resource allocation"]	Effortlessly manage unlimited side projects	Side project creators and solopreneurs	Tiered pricing based on project count	88.7	91.3	validated	Need help organizing side projects	SideProject	203	1764027370.1243253	6C45wRKoCD9+bg
\.


--
-- Data for Name: competitive_landscape; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.competitive_landscape (opportunity_id, competitor_name, competitor_features, competitive_analysis, market_share, pricing_model, target_market, source_url, confidence, extracted_at, created_at, _dlt_load_id, _dlt_id) FROM stdin;
d59d07ea-685d-4d0a-ad70-b8a33f0ebea8	Calendly	["Scheduling", "Timezone support"]		\N	unknown	unknown		0.5	2025-11-22 21:07:39.836101+00	2025-11-22 21:07:39.836105+00	1763845661.1364803	GiVvwF0+trudIw
\.


--
-- Data for Name: market_validations; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.market_validations (opportunity_id, validation_type, validation_source, validation_date, validation_result, confidence_score, notes, status, evidence_url, market_validation_score, market_data_quality_score, market_validation_reasoning, market_competitors_found, market_size_tam, market_size_sam, market_size_growth, market_similar_launches, market_validation_cost_usd, search_queries_used, urls_fetched, extraction_stats, jina_api_calls_count, jina_cache_hit_rate, _dlt_load_id, _dlt_id) FROM stdin;
d59d07ea-685d-4d0a-ad70-b8a33f0ebea8	jina_reader_market_validation	ai_analysis	2025-11-22 21:07:39.836059+00	{"reasoning": "Several competing tools exist, validating market need", "competitor_count": 2, "validation_score": 85.0, "data_quality_score": 90.0, "market_size_estimate": 50000000.0, "validation_reasoning": "Market validation shows strong demand", "similar_launches_count": 15}	0.9	Several competing tools exist, validating market need	completed		85	90	Several competing tools exist, validating market need	[{"features": ["Scheduling", "Timezone support"], "company_name": "Calendly"}, {"features": ["Timezone conversion", "Meeting planning"], "company_name": "World Time Buddy"}]	50000000	\N	\N	15	0	[]	[]	{}	0	0	1763845660.7684696	BlqTRvYTPH698w
\.


--
-- Data for Name: monetization_patterns; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.monetization_patterns (opportunity_id, pattern_type, revenue_model, target_pricing, market_size, willingness_to_pay_score, customer_segment, price_sensitivity_score, revenue_potential_score, mentioned_price_points, existing_payment_behavior, urgency_level, sentiment_toward_payment, payment_friction_indicators, llm_monetization_score, confidence, reasoning, created_at, _dlt_load_id, _dlt_id) FROM stdin;
d59d07ea-685d-4d0a-ad70-b8a33f0ebea8	ai_analysis	unknown	\N	\N	75	B2B	60	80	["$10/month", "$100/year"]	Currently using free tools	medium	positive	[]	70	0.85	Teams actively need coordination tools	2025-11-22 21:07:39.836053+00	1763845660.3141646	XtOKrDQLsrj4/A
\.


--
-- Data for Name: opportunities; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.opportunities (id, title, description, problem_statement, target_audience, submission_id, _dlt_load_id, _dlt_id) FROM stdin;
9f9cef87-d970-481d-b31c-54b6d513bda4	FINAL TEST: AI Task Manager	Productivity tool that uses machine learning to prioritize tasks automatically	Users waste time managing tasks instead of completing them	Productivity enthusiasts and project managers	a0f305c3-fdff-4f11-ab29-84936fb7c8c1	1764028678.981518	YYoZtI1OVb1XUg
fee2cb84-6a8f-4ef4-a38d-cd38bc33968d	Opportunity: Need help organizing multiple side projects	High-engagement Reddit post with 203 upvotes and 45 comments indicates strong market interest in productivity solutions.	Reddit users actively discussing productivity challenges with 203 upvotes, indicating clear market need.	Productivity-focused individuals, freelancers, and startup teams	550e8400-e29b-41d4-a716-446655440001	1764029549.2952976	cneBb82IhtetTQ
3ad717ad-ab70-4293-9d57-520d92ce0620	Opportunity: I struggle with managing my time effectively across multiple	High-engagement Reddit post with 156 upvotes and 23 comments indicates strong market interest in productivity solutions.	Reddit users actively discussing productivity challenges with 156 upvotes, indicating clear market need.	Productivity-focused individuals, freelancers, and startup teams	550e8400-e29b-41d4-a716-446655440002	1764029549.2952976	g8CGI1WMpb8Fag
abec64bf-1a66-4ffb-bf74-9507ad0ed819	Opportunity: Looking for better tools to organize our startup workflow	High-engagement Reddit post with 124 upvotes and 67 comments indicates strong market interest in productivity solutions.	Reddit users actively discussing productivity challenges with 124 upvotes, indicating clear market need.	Productivity-focused individuals, freelancers, and startup teams	550e8400-e29b-41d4-a716-446655440003	1764029549.2952976	ABBwPrHqFSf2Mw
66c76396-8773-4220-bae1-395c53652fb6	Opportunity: Best productivity apps for freelance developers	High-engagement Reddit post with 98 upvotes and 31 comments indicates strong market interest in productivity solutions.	Reddit users actively discussing productivity challenges with 98 upvotes, indicating clear market need.	Productivity-focused individuals, freelancers, and startup teams	550e8400-e29b-41d4-a716-446655440004	1764029549.2952976	KDKpOxpIvuvpfg
a4769634-1374-4387-8eda-963642e2cc9f	Opportunity: How do you prioritize tasks when everything seems urgent	High-engagement Reddit post with 87 upvotes and 19 comments indicates strong market interest in productivity solutions.	Reddit users actively discussing productivity challenges with 87 upvotes, indicating clear market need.	Productivity-focused individuals, freelancers, and startup teams	550e8400-e29b-41d4-a716-446655440005	1764029549.2952976	afunjwi1Sf4qtg
ea726d83-c37e-4257-b924-8cd051c65f1f	SCALED TEST 02 SUCCESS - REDDIT DATA PROCESSING	This record confirms that Test 02 scaling works perfectly. DLT pipeline processed Reddit submissions at production scale without errors.	Validation complete - DLT pipeline can scale Reddit data collection operations without schema blocking issues.	Production systems and large-scale data processing	9b92ff47-1e3d-44e6-808a-d5ee15b9f413	1764029669.703498	4HFSPIFMmRuT/A
fa589613-e55f-4f9c-a0fb-c8650fd9b46a	DEBUG TEST	Debug test	Debug test	Debug test	455be4be-f540-4021-9dc5-776367acf00e	1764029987.5142696	TusL4pGzF/0uLA
feb5755c-a286-4c63-83ce-a13cfa850502	UUID Type Fix Test	Testing that UUID data types work correctly	Verify DLT handles UUID data types properly	Database developers and DevOps engineers	f50155a9-ab0f-4418-8179-df6c48c3ab0c	1764031135.058126	Sn4wJ2Ds/rMwew
9408c5f2-1795-46ad-b95d-7143b46a3940	UUID Normalizer Fix Test	Testing with disabled normalizer for UUID fields	UUID fields should now be treated as proper UUID type	Database developers and DLT engineers	038a11a2-f160-49d1-ac98-67222c7923b3	1764031305.5583394	SVs6IIPlHbpNwA
\.


--
-- Data for Name: opportunities_test_02_scaled; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.opportunities_test_02_scaled (id, title, description, problem_statement, target_audience, _dlt_load_id, _dlt_id) FROM stdin;
78fbcc67-ca1b-4774-8c8d-176ab718252d	SCALED TEST 02 RECORD 2c20ac55	Verification record for scaled Test 02 execution - SUCCESS CONFIRMED	Test validation to ensure DLT pipeline scales correctly	Test validation and quality assurance	1764029629.26987	XE8QHCYQUdk2Ng
\.


--
-- Data for Name: opportunity_scores; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.opportunity_scores (opportunity_id, market_demand, pain_intensity, competition_level, technical_feasibility, monetization_potential, simplicity_score, total_score, created_at, updated_at, _dlt_load_id, _dlt_id) FROM stdin;
d59d07ea-685d-4d0a-ad70-b8a33f0ebea8	0.8	0.9	0.6	0.8	0.7	0.5	85.5	2025-11-22 21:07:39.836024+00	2025-11-22 21:07:39.836041+00	1763845659.9238393	rTzxAuyV7yW8RA
\.


--
-- Data for Name: submissions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.submissions (submission_id, title, selftext, author, subreddit, trust_score, trust_level, market_validation_score, opportunity_score, created_utc, reddit_score, _dlt_load_id, _dlt_id, reddit_id, text, content, upvotes, comments_count, url, created_at, id, score, num_comments) FROM stdin;
test_enhanced_123	Test submission for enhanced storage	\N	\N	test	\N	medium	70	\N	\N	\N	1763845189.6130137	8B5m2qMiaOxfIg	test_enhanced_123	\N	\N	\N	\N	\N	\N	\N	\N	\N
hybrid_1	Need feedback on timezone scheduling tool	\N	remote_manager	remotework	45.67	low	68.1	\N	1699423456	\N	1763849114.8465176	XMtHVjt7Di6+Xw	hybrid_1	\N	\N	\N	\N	\N	\N	\N	\N	\N
f71da084-b019-591d-b582-b6c8034ead3f	Test Submission for EnhancedHybridStore Fix Validation	\N	\N	test_subreddit	\N	\N	70	75	\N	\N	1763852562.9658973	d9CE9T0uFr4nsg	f71da084-b019-591d-b582-b6c8034ead3f	\N	\N	\N	\N	\N	\N	\N	\N	\N
2918b13e-cb82-53f1-ad4b-667854633a40	Test submission for enhanced storage	\N	\N	test	\N	medium	70	\N	\N	\N	1763856885.4599204	3rDVHYbpdceCIg	2918b13e-cb82-53f1-ad4b-667854633a40	\N	\N	\N	\N	\N	\N	\N	\N	\N
e7763e41-d7bf-4bf1-a004-decff9f0f0c5	Need feedback on timezone scheduling tool	\N	remote_manager	remotework	44.06	low	10	\N	1699423456	\N	1763939881.686538	TPth7mkVpCO+Wg	e7763e41-d7bf-4bf1-a004-decff9f0f0c5	\N	\N	\N	\N	\N	\N	\N	\N	\N
010b3ed9-6785-5b18-a4ab-83bb902dd945	Looking for a tool to help with productivity	\N	\N	SideProject	\N	\N	\N	\N	\N	\N	1764018105.1331246	CI9hbEe3g8BqyA	test_1_8	This is frustrating and time consuming. I wish there was a better tool.	This is frustrating and time consuming. I wish there was a better tool.	23	13	https://reddit.com/r/SideProject/comments/test_1_8	2023-12-31 21:16:48+00	\N	\N	\N
1a68c8bf-8e3f-530a-8188-471af03029f7	This is frustrating and time consuming. I wish there was better automation	\N	\N	SideProject	\N	\N	\N	\N	\N	\N	1764018105.1331246	BZiPtVbcSQ4s9A	test_1_1	This is frustrating and time consuming. I wish there was a better tool.	This is frustrating and time consuming. I wish there was a better tool.	16	6	https://reddit.com/r/SideProject/comments/test_1_1	2023-12-31 21:16:41+00	\N	\N	\N
1bd88742-4008-5614-b9a9-75b2bfc9979a	I struggle with managing my time effectively	\N	\N	opensource	\N	\N	\N	\N	\N	\N	1764018105.1331246	g2UsMGs4RKwx8w	test_0_5	This is frustrating and time consuming. I wish there was a better tool.	This is frustrating and time consuming. I wish there was a better tool.	20	10	https://reddit.com/r/opensource/comments/test_0_5	2023-12-31 21:00:05+00	\N	\N	\N
d914bf4e-9591-53c6-9163-10385af87a3c	Need feedback on timezone scheduling tool	\N	\N	remotework	\N	\N	85	\N	\N	\N	1763866305.324112	SGEredqslLb23g	d914bf4e-9591-53c6-9163-10385af87a3c	\N	\N	\N	\N	\N	\N	\N	\N	\N
910282e7-7340-5b70-bdaf-4a5c715c6084	Need feedback on project management tool	\N	\N	remotework	\N	\N	\N	\N	\N	\N	1763866496.3663373	/ITRgJqe3Htv8w	910282e7-7340-5b70-bdaf-4a5c715c6084	\N	\N	\N	\N	\N	\N	\N	\N	\N
1894f752-f7df-5197-b3ca-a32424562c91	Test	Long text content here that meets minimum length requirements	\N	test	\N	\N	\N	\N	\N	\N	1763901277.8762057	5Ek4BJBCuAJm8Q	1894f752-f7df-5197-b3ca-a32424562c91	\N	\N	\N	\N	\N	\N	\N	\N	\N
2264a997-0e80-587d-b1d5-c0a4396ab4f9	Test 2	\N	\N	test	\N	\N	\N	\N	\N	\N	1763901282.490578	7MvcVOVKfaWsAQ	2264a997-0e80-587d-b1d5-c0a4396ab4f9	\N	\N	\N	\N	\N	\N	\N	\N	\N
35d2921b-9f6c-5988-bbe2-89481281f0ce	Test 3	\N	\N	test	\N	\N	\N	\N	\N	\N	1763901282.490578	/QkzHFJUdOah8Q	35d2921b-9f6c-5988-bbe2-89481281f0ce	\N	\N	\N	\N	\N	\N	\N	\N	\N
87686b53-6b91-5ad7-988e-f661ace0df24	Test 1	\N	\N	test	\N	\N	\N	\N	\N	\N	1763901282.490578	oxneXLhtaCCZUQ	87686b53-6b91-5ad7-988e-f661ace0df24	\N	\N	\N	\N	\N	\N	\N	\N	\N
b13b254e-568e-556a-b3f8-9b3a12baabe0	Test	\N	\N	test	\N	\N	\N	\N	\N	\N	1763901284.1283803	Wy33fdwVHYIpbQ	b13b254e-568e-556a-b3f8-9b3a12baabe0	\N	\N	\N	\N	\N	\N	\N	\N	\N
1f6fa0a9-0add-570e-a15a-f4202bfa9c63	Can't figure out how to organize my work	\N	\N	opensource	\N	\N	\N	\N	\N	\N	1764018105.1331246	1idhsRQ5W2bsRA	test_0_2	This is frustrating and time consuming. I wish there was a better tool.	This is frustrating and time consuming. I wish there was a better tool.	17	7	https://reddit.com/r/opensource/comments/test_0_2	2023-12-31 21:00:02+00	\N	\N	\N
2c6ce72d-27dd-5a55-b178-4bbffea11fad	Can't figure out how to organize my work	\N	\N	opensource	\N	\N	\N	\N	\N	\N	1764018105.1331246	7LRcbmcme8xjyA	test_0_17	This is frustrating and time consuming. I wish there was a better tool.	This is frustrating and time consuming. I wish there was a better tool.	32	22	https://reddit.com/r/opensource/comments/test_0_17	2023-12-31 21:00:17+00	\N	\N	\N
30fe06e9-6e14-56db-99ee-ec7d44afbfa4	This is frustrating and time consuming. I wish there was better automation	\N	\N	opensource	\N	\N	\N	\N	\N	\N	1764018105.1331246	0R8UcZDbrTs91Q	test_0_16	This is frustrating and time consuming. I wish there was a better tool.	This is frustrating and time consuming. I wish there was a better tool.	31	21	https://reddit.com/r/opensource/comments/test_0_16	2023-12-31 21:00:16+00	\N	\N	\N
3934bbd1-5293-572c-8229-5ceab34c3fe3	I struggle with managing my time effectively	\N	\N	opensource	\N	\N	\N	\N	\N	\N	1764018105.1331246	WgDsWe7LlH2kgg	test_0_10	This is frustrating and time consuming. I wish there was a better tool.	This is frustrating and time consuming. I wish there was a better tool.	25	15	https://reddit.com/r/opensource/comments/test_0_10	2023-12-31 21:00:10+00	\N	\N	\N
4bf21458-4ea2-5ef8-80d4-67b4018ca6fc	Manual processes are so tedious and annoying	\N	\N	opensource	\N	\N	\N	\N	\N	\N	1764018105.1331246	KZPYLa1jNYXlmw	test_0_14	This is frustrating and time consuming. I wish there was a better tool.	This is frustrating and time consuming. I wish there was a better tool.	29	19	https://reddit.com/r/opensource/comments/test_0_14	2023-12-31 21:00:14+00	\N	\N	\N
5b28d009-1bf9-5dde-a79c-da2dbd10efa8	Looking for a tool to help with productivity	\N	\N	opensource	\N	\N	\N	\N	\N	\N	1764018105.1331246	uqYngFJrtaIdHQ	test_0_8	This is frustrating and time consuming. I wish there was a better tool.	This is frustrating and time consuming. I wish there was a better tool.	23	13	https://reddit.com/r/opensource/comments/test_0_8	2023-12-31 21:00:08+00	\N	\N	\N
5dff122b-5964-5e48-8d6e-c9a32eba7b57	I struggle with managing my time effectively	\N	\N	opensource	\N	\N	\N	\N	\N	\N	1764018105.1331246	T6L/GOnDumfJ0Q	test_0_15	This is frustrating and time consuming. I wish there was a better tool.	This is frustrating and time consuming. I wish there was a better tool.	30	20	https://reddit.com/r/opensource/comments/test_0_15	2023-12-31 21:00:15+00	\N	\N	\N
6cd78e60-95ce-5fe1-928f-c2e240f7b858	This is frustrating and time consuming. I wish there was better automation	\N	\N	SideProject	\N	\N	\N	\N	\N	\N	1764018105.1331246	SWzaiU2jUvA8Zg	test_1_11	This is frustrating and time consuming. I wish there was a better tool.	This is frustrating and time consuming. I wish there was a better tool.	26	16	https://reddit.com/r/SideProject/comments/test_1_11	2023-12-31 21:16:51+00	\N	\N	\N
6f13cb8e-5796-598e-a238-7656138b5134	This is frustrating and time consuming. I wish there was better automation	\N	\N	opensource	\N	\N	\N	\N	\N	\N	1764018105.1331246	JENGXoC/g0Nj0Q	test_0_6	This is frustrating and time consuming. I wish there was a better tool.	This is frustrating and time consuming. I wish there was a better tool.	21	11	https://reddit.com/r/opensource/comments/test_0_6	2023-12-31 21:00:06+00	\N	\N	\N
71000c52-4e37-5517-85b1-8a4ae24151b1	Looking for a tool to help with productivity	\N	\N	opensource	\N	\N	\N	\N	\N	\N	1764018105.1331246	pnVSqfZAYLUvpw	test_0_13	This is frustrating and time consuming. I wish there was a better tool.	This is frustrating and time consuming. I wish there was a better tool.	28	18	https://reddit.com/r/opensource/comments/test_0_13	2023-12-31 21:00:13+00	\N	\N	\N
854a919c-d901-5ea1-8df8-3942627c99b3	Manual processes are so tedious and annoying	\N	\N	SideProject	\N	\N	\N	\N	\N	\N	1764018105.1331246	hAgdJZinq1Pgpg	test_1_9	This is frustrating and time consuming. I wish there was a better tool.	This is frustrating and time consuming. I wish there was a better tool.	24	14	https://reddit.com/r/SideProject/comments/test_1_9	2023-12-31 21:16:49+00	\N	\N	\N
872b0820-8b6a-5933-97bf-fdb5d1122955	This is frustrating and time consuming. I wish there was better automation	\N	\N	SideProject	\N	\N	\N	\N	\N	\N	1764018105.1331246	ddtTJMqdX+Lk8Q	test_1_6	This is frustrating and time consuming. I wish there was a better tool.	This is frustrating and time consuming. I wish there was a better tool.	21	11	https://reddit.com/r/SideProject/comments/test_1_6	2023-12-31 21:16:46+00	\N	\N	\N
877fed77-7daa-5e07-9805-34aeaabbad12	Manual processes are so tedious and annoying	\N	\N	SideProject	\N	\N	\N	\N	\N	\N	1764018105.1331246	x/SXxt/95OPGcA	test_1_14	This is frustrating and time consuming. I wish there was a better tool.	This is frustrating and time consuming. I wish there was a better tool.	29	19	https://reddit.com/r/SideProject/comments/test_1_14	2023-12-31 21:16:54+00	\N	\N	\N
96e3851a-6988-5f1c-b9df-d55d4cecc1c7	Can't figure out how to organize my work	\N	\N	opensource	\N	\N	\N	\N	\N	\N	1764018105.1331246	8R4XU8NETDGa2Q	test_0_7	This is frustrating and time consuming. I wish there was a better tool.	This is frustrating and time consuming. I wish there was a better tool.	22	12	https://reddit.com/r/opensource/comments/test_0_7	2023-12-31 21:00:07+00	\N	\N	\N
97508434-f284-5366-9ce7-0ea2a5dc914b	Looking for a tool to help with productivity	\N	\N	opensource	\N	\N	\N	\N	\N	\N	1764018105.1331246	M2CgTnu/XT1NSQ	test_0_3	This is frustrating and time consuming. I wish there was a better tool.	This is frustrating and time consuming. I wish there was a better tool.	18	8	https://reddit.com/r/opensource/comments/test_0_3	2023-12-31 21:00:03+00	\N	\N	\N
9997fde8-fd9c-59e7-87a3-483025b738a1	Looking for a tool to help with productivity	\N	\N	SideProject	\N	\N	\N	\N	\N	\N	1764018105.1331246	CCh7feDoMJps4g	test_1_13	This is frustrating and time consuming. I wish there was a better tool.	This is frustrating and time consuming. I wish there was a better tool.	28	18	https://reddit.com/r/SideProject/comments/test_1_13	2023-12-31 21:16:53+00	\N	\N	\N
99edd31b-6b01-58c4-a26b-2f516e8f5d79	This is frustrating and time consuming. I wish there was better automation	\N	\N	SideProject	\N	\N	\N	\N	\N	\N	1764018105.1331246	HN9zOqYR0eWSTw	test_1_16	This is frustrating and time consuming. I wish there was a better tool.	This is frustrating and time consuming. I wish there was a better tool.	31	21	https://reddit.com/r/SideProject/comments/test_1_16	2023-12-31 21:16:56+00	\N	\N	\N
a05c400a-8620-5018-ac5d-ff88d996e81a	Manual processes are so tedious and annoying	\N	\N	opensource	\N	\N	\N	\N	\N	\N	1764018105.1331246	Bhqe/rGksRPhqQ	test_0_19	This is frustrating and time consuming. I wish there was a better tool.	This is frustrating and time consuming. I wish there was a better tool.	34	24	https://reddit.com/r/opensource/comments/test_0_19	2023-12-31 21:00:19+00	\N	\N	\N
a26c3b83-297f-5433-97fd-812c8a85b071	I struggle with managing my time effectively	\N	\N	SideProject	\N	\N	\N	\N	\N	\N	1764018105.1331246	vGg7Cz3RoXVsMg	test_1_10	This is frustrating and time consuming. I wish there was a better tool.	This is frustrating and time consuming. I wish there was a better tool.	25	15	https://reddit.com/r/SideProject/comments/test_1_10	2023-12-31 21:16:50+00	\N	\N	\N
adea8706-14e3-51e5-bc02-c46e7a8a3394	Can't figure out how to organize my work	\N	\N	SideProject	\N	\N	\N	\N	\N	\N	1764018105.1331246	eNeqe2rtF5MTkA	test_1_2	This is frustrating and time consuming. I wish there was a better tool.	This is frustrating and time consuming. I wish there was a better tool.	17	7	https://reddit.com/r/SideProject/comments/test_1_2	2023-12-31 21:16:42+00	\N	\N	\N
b19b6124-efc6-5628-9b06-c6ea13c44377	Can't figure out how to organize my work	\N	\N	SideProject	\N	\N	\N	\N	\N	\N	1764018105.1331246	XFiE3lbE8+chiw	test_1_17	This is frustrating and time consuming. I wish there was a better tool.	This is frustrating and time consuming. I wish there was a better tool.	32	22	https://reddit.com/r/SideProject/comments/test_1_17	2023-12-31 21:16:57+00	\N	\N	\N
b3f56232-9c7d-5d50-a548-64dcfa0047e7	Manual processes are so tedious and annoying	\N	\N	opensource	\N	\N	\N	\N	\N	\N	1764018105.1331246	YmLxIFSgNB+yow	test_0_4	This is frustrating and time consuming. I wish there was a better tool.	This is frustrating and time consuming. I wish there was a better tool.	19	9	https://reddit.com/r/opensource/comments/test_0_4	2023-12-31 21:00:04+00	\N	\N	\N
b588fc1b-f5ad-5cd2-92b9-8b598d3bd383	Can't figure out how to organize my work	\N	\N	SideProject	\N	\N	\N	\N	\N	\N	1764018105.1331246	cjVHPsx9DS4xJQ	test_1_7	This is frustrating and time consuming. I wish there was a better tool.	This is frustrating and time consuming. I wish there was a better tool.	22	12	https://reddit.com/r/SideProject/comments/test_1_7	2023-12-31 21:16:47+00	\N	\N	\N
b71f234a-7b2b-5672-bc97-7f64ed6c2b27	This is frustrating and time consuming. I wish there was better automation	\N	\N	opensource	\N	\N	\N	\N	\N	\N	1764018105.1331246	HfDxJ3pUhDcOhw	test_0_11	This is frustrating and time consuming. I wish there was a better tool.	This is frustrating and time consuming. I wish there was a better tool.	26	16	https://reddit.com/r/opensource/comments/test_0_11	2023-12-31 21:00:11+00	\N	\N	\N
c3f187d8-61fe-5e73-8c1d-4aa763a1a429	Can't figure out how to organize my work	\N	\N	SideProject	\N	\N	\N	\N	\N	\N	1764018105.1331246	uwVW5WlGDknBSQ	test_1_12	This is frustrating and time consuming. I wish there was a better tool.	This is frustrating and time consuming. I wish there was a better tool.	27	17	https://reddit.com/r/SideProject/comments/test_1_12	2023-12-31 21:16:52+00	\N	\N	\N
ce233564-98f6-54d2-92ef-f15225f0b042	Looking for a tool to help with productivity	\N	\N	SideProject	\N	\N	\N	\N	\N	\N	1764018105.1331246	TRYTA/RqgEYRJQ	test_1_3	This is frustrating and time consuming. I wish there was a better tool.	This is frustrating and time consuming. I wish there was a better tool.	18	8	https://reddit.com/r/SideProject/comments/test_1_3	2023-12-31 21:16:43+00	\N	\N	\N
dc88f14c-5fc3-50c6-be08-44b74ba1894e	I struggle with managing my time effectively	\N	\N	SideProject	\N	\N	\N	\N	\N	\N	1764018105.1331246	yAREXTgrvUvh6g	test_1_15	This is frustrating and time consuming. I wish there was a better tool.	This is frustrating and time consuming. I wish there was a better tool.	30	20	https://reddit.com/r/SideProject/comments/test_1_15	2023-12-31 21:16:55+00	\N	\N	\N
dedec24c-942f-53cd-b4d5-20ffade1def1	Looking for a tool to help with productivity	\N	\N	opensource	\N	\N	\N	\N	\N	\N	1764018105.1331246	DlE7f7/eOi5fdQ	test_0_18	This is frustrating and time consuming. I wish there was a better tool.	This is frustrating and time consuming. I wish there was a better tool.	33	23	https://reddit.com/r/opensource/comments/test_0_18	2023-12-31 21:00:18+00	\N	\N	\N
e0b77355-2158-587b-8436-9587b2828f9f	Looking for a tool to help with productivity	\N	\N	SideProject	\N	\N	\N	\N	\N	\N	1764018105.1331246	VFsimwkjR8svjg	test_1_18	This is frustrating and time consuming. I wish there was a better tool.	This is frustrating and time consuming. I wish there was a better tool.	33	23	https://reddit.com/r/SideProject/comments/test_1_18	2023-12-31 21:16:58+00	\N	\N	\N
e0f980ac-ca4b-55e5-b7e9-1ab57185f1fe	Manual processes are so tedious and annoying	\N	\N	SideProject	\N	\N	\N	\N	\N	\N	1764018105.1331246	sffQn2cYHXE4cw	test_1_4	This is frustrating and time consuming. I wish there was a better tool.	This is frustrating and time consuming. I wish there was a better tool.	19	9	https://reddit.com/r/SideProject/comments/test_1_4	2023-12-31 21:16:44+00	\N	\N	\N
e21beeed-592b-5d1f-9416-cb31364ca662	Can't figure out how to organize my work	\N	\N	opensource	\N	\N	\N	\N	\N	\N	1764018105.1331246	rP2tewePRwI+vA	test_0_12	This is frustrating and time consuming. I wish there was a better tool.	This is frustrating and time consuming. I wish there was a better tool.	27	17	https://reddit.com/r/opensource/comments/test_0_12	2023-12-31 21:00:12+00	\N	\N	\N
e56c4db4-1578-5a96-a586-f6b9d5f926ad	I struggle with managing my time effectively	\N	\N	opensource	\N	\N	\N	\N	\N	\N	1764018105.1331246	PwfHKB0hkWJ/LQ	test_0_0	This is frustrating and time consuming. I wish there was a better tool.	This is frustrating and time consuming. I wish there was a better tool.	15	5	https://reddit.com/r/opensource/comments/test_0_0	2023-12-31 21:00:00+00	\N	\N	\N
e68307ef-f2af-593c-8903-017abfb18d59	Manual processes are so tedious and annoying	\N	\N	opensource	\N	\N	\N	\N	\N	\N	1764018105.1331246	K6o3s9/FBYqglw	test_0_9	This is frustrating and time consuming. I wish there was a better tool.	This is frustrating and time consuming. I wish there was a better tool.	24	14	https://reddit.com/r/opensource/comments/test_0_9	2023-12-31 21:00:09+00	\N	\N	\N
e8fc7bd4-9e48-5c2a-98c0-d5369c47d4f2	Manual processes are so tedious and annoying	\N	\N	SideProject	\N	\N	\N	\N	\N	\N	1764018105.1331246	qosRndMC9gV/WA	test_1_19	This is frustrating and time consuming. I wish there was a better tool.	This is frustrating and time consuming. I wish there was a better tool.	34	24	https://reddit.com/r/SideProject/comments/test_1_19	2023-12-31 21:16:59+00	\N	\N	\N
ecbfbf72-4d6b-5076-a53d-a26e59052c07	This is frustrating and time consuming. I wish there was better automation	\N	\N	opensource	\N	\N	\N	\N	\N	\N	1764018105.1331246	CXc+VsqGjlMdYA	test_0_1	This is frustrating and time consuming. I wish there was a better tool.	This is frustrating and time consuming. I wish there was a better tool.	16	6	https://reddit.com/r/opensource/comments/test_0_1	2023-12-31 21:00:01+00	\N	\N	\N
fabca474-5d9a-577d-ae64-de1d39115ba4	I struggle with managing my time effectively	\N	\N	SideProject	\N	\N	\N	\N	\N	\N	1764018105.1331246	y5pb/y8UZYmtqQ	test_1_5	This is frustrating and time consuming. I wish there was a better tool.	This is frustrating and time consuming. I wish there was a better tool.	20	10	https://reddit.com/r/SideProject/comments/test_1_5	2023-12-31 21:16:45+00	\N	\N	\N
fcedcd61-8399-5ebf-81aa-ea6d630ee31f	I struggle with managing my time effectively	\N	\N	SideProject	\N	\N	\N	\N	\N	\N	1764018105.1331246	AU62HFpAqZJpDA	test_1_0	This is frustrating and time consuming. I wish there was a better tool.	This is frustrating and time consuming. I wish there was a better tool.	15	5	https://reddit.com/r/SideProject/comments/test_1_0	2023-12-31 21:16:40+00	\N	\N	\N
test-submission-id-123	Test Submission	Test content here	test_user	test	\N	\N	\N	\N	1672531200	100	1234567890.123456	test_dlt_id_123	t3_test123	\N	\N	0	0	\N	\N	\N	0	25
test-submission-1764074287782	Test Submission	Test content here	test_user	test	\N	\N	\N	\N	1672531200	100	1764074287.7823088	test_dlt_1764074287	t3_test_1764074287	\N	\N	0	0	\N	\N	\N	0	25
test-submission-1764074741152	Test Submission	Test content here	test_user	test	\N	\N	\N	\N	1672531200	100	1764074741.1529868	test_dlt_1764074741	t3_test_1764074741	\N	\N	0	0	\N	\N	\N	0	25
test-submission-1764074815984	Test Submission	Test content here	test_user	test	\N	\N	\N	\N	1672531200	100	1764074815.984104	test_dlt_1764074815	t3_test_1764074815	\N	\N	0	0	\N	\N	\N	0	25
\.


--
-- Data for Name: _dlt_version; Type: TABLE DATA; Schema: public_staging; Owner: postgres
--

COPY public_staging._dlt_version (version, engine_version, inserted_at, schema_name, version_hash, schema) FROM stdin;
10	11	2025-11-22 20:40:50.669683+00	app_opportunities_loader	9/Fe7suggUVlen8Kubxf7rm9EoSWiu56sPN9qZPfb1s=	{"version":10,"version_hash":"9/Fe7suggUVlen8Kubxf7rm9EoSWiu56sPN9qZPfb1s=","engine_version":11,"name":"app_opportunities_loader","tables":{"_dlt_version":{"name":"_dlt_version","columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_name":{"name":"schema_name","data_type":"text","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":false},"schema":{"name":"schema","data_type":"text","nullable":false}},"write_disposition":"skip","resource":"_dlt_version","description":"Created by DLT. Tracks schema updates"},"_dlt_loads":{"name":"_dlt_loads","columns":{"load_id":{"name":"load_id","data_type":"text","nullable":false,"precision":64},"schema_name":{"name":"schema_name","data_type":"text","nullable":true},"status":{"name":"status","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_version_hash":{"name":"schema_version_hash","data_type":"text","nullable":true}},"write_disposition":"skip","resource":"_dlt_loads","description":"Created by DLT. Tracks completed loads"},"app_opportunities":{"columns":{"submission_id":{"name":"submission_id","nullable":false,"primary_key":true,"data_type":"text"},"problem_description":{"name":"problem_description","data_type":"text","nullable":true},"app_concept":{"name":"app_concept","data_type":"text","nullable":true},"value_proposition":{"name":"value_proposition","data_type":"text","nullable":true},"target_user":{"name":"target_user","data_type":"text","nullable":true},"monetization_model":{"name":"monetization_model","data_type":"text","nullable":true},"opportunity_score":{"name":"opportunity_score","data_type":"double","nullable":true},"title":{"name":"title","data_type":"text","nullable":true},"subreddit":{"name":"subreddit","data_type":"text","nullable":true},"reddit_score":{"name":"reddit_score","data_type":"bigint","nullable":true},"status":{"name":"status","data_type":"text","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true},"final_score":{"name":"final_score","nullable":true,"data_type":"double"},"app_name":{"name":"app_name","data_type":"text","nullable":true},"dimension_scores__market_demand":{"name":"dimension_scores__market_demand","data_type":"double","nullable":true},"dimension_scores__pain_intensity":{"name":"dimension_scores__pain_intensity","data_type":"bigint","nullable":true},"dimension_scores__monetization_potential":{"name":"dimension_scores__monetization_potential","data_type":"bigint","nullable":true},"dimension_scores__market_gap":{"name":"dimension_scores__market_gap","data_type":"bigint","nullable":true},"dimension_scores__technical_feasibility":{"name":"dimension_scores__technical_feasibility","data_type":"bigint","nullable":true},"dimension_scores__simplicity_score":{"name":"dimension_scores__simplicity_score","data_type":"double","nullable":true},"priority":{"name":"priority","data_type":"text","nullable":true},"confidence":{"name":"confidence","data_type":"double","nullable":true},"evidence_based":{"name":"evidence_based","data_type":"bool","nullable":true},"trust_level":{"name":"trust_level","data_type":"text","nullable":true},"enrichment_version":{"name":"enrichment_version","data_type":"text","nullable":true},"pipeline_source":{"name":"pipeline_source","data_type":"text","nullable":true},"market_validation_score":{"name":"market_validation_score","nullable":true,"data_type":"double"},"ai_profile__analysis_summary__app_name":{"name":"ai_profile__analysis_summary__app_name","data_type":"text","nullable":true},"ai_profile__analysis_summary__app_category":{"name":"ai_profile__analysis_summary__app_category","data_type":"text","nullable":true},"ai_profile__analysis_summary__target_profession":{"name":"ai_profile__analysis_summary__target_profession","data_type":"text","nullable":true},"ai_profile__analysis_summary__core_problem_solved":{"name":"ai_profile__analysis_summary__core_problem_solved","data_type":"text","nullable":true},"ai_profile__analysis_summary__unique_value_prop":{"name":"ai_profile__analysis_summary__unique_value_prop","data_type":"text","nullable":true},"ai_profile__analysis_summary__primary_target_user":{"name":"ai_profile__analysis_summary__primary_target_user","data_type":"text","nullable":true},"ai_profile__analysis_summary__monetization_approach":{"name":"ai_profile__analysis_summary__monetization_approach","data_type":"text","nullable":true},"ai_profile__technical_feasibility__estimated_complexity":{"name":"ai_profile__technical_feasibility__estimated_complexity","data_type":"text","nullable":true},"ai_profile__technical_feasibility__core_function_count":{"name":"ai_profile__technical_feasibility__core_function_count","data_type":"bigint","nullable":true},"ai_profile__market_analysis__target_market_segment":{"name":"ai_profile__market_analysis__target_market_segment","data_type":"text","nullable":true},"ai_profile__market_analysis__app_category":{"name":"ai_profile__market_analysis__app_category","data_type":"text","nullable":true},"ai_profile__market_analysis__evidence_based":{"name":"ai_profile__market_analysis__evidence_based","data_type":"bool","nullable":true},"ai_profile__market_analysis__opportunity_score":{"name":"ai_profile__market_analysis__opportunity_score","data_type":"bigint","nullable":true},"ai_profile__generation_metadata__model_used":{"name":"ai_profile__generation_metadata__model_used","data_type":"text","nullable":true},"ai_profile__generation_metadata__analysis_timestamp":{"name":"ai_profile__generation_metadata__analysis_timestamp","data_type":"timestamp","nullable":true},"ai_profile__generation_metadata__evidence_available":{"name":"ai_profile__generation_metadata__evidence_available","data_type":"bool","nullable":true},"ai_profile__generation_metadata__cost_tracking__model_used":{"name":"ai_profile__generation_metadata__cost_tracking__model_used","data_type":"text","nullable":true},"ai_profile__generation_metadata__cost_tracking__provider":{"name":"ai_profile__generation_metadata__cost_tracking__provider","data_type":"text","nullable":true},"ai_profile__generation_metadata__cost_tracking__prompt_tokens":{"name":"ai_profile__generation_metadata__cost_tracking__prompt_tokens","data_type":"bigint","nullable":true},"ai_profile__generation_metadagfa09q_tracking__completion_tokens":{"name":"ai_profile__generation_metadagfa09q_tracking__completion_tokens","data_type":"bigint","nullable":true},"ai_profile__generation_metadata__cost_tracking__total_tokens":{"name":"ai_profile__generation_metadata__cost_tracking__total_tokens","data_type":"bigint","nullable":true},"ai_profile__generation_metadata__cost_tracking__input_cost_usd":{"name":"ai_profile__generation_metadata__cost_tracking__input_cost_usd","data_type":"double","nullable":true},"ai_profile__generation_metadata__cost_tracking__output_cost_usd":{"name":"ai_profile__generation_metadata__cost_tracking__output_cost_usd","data_type":"double","nullable":true},"ai_profile__generation_metadata__cost_tracking__total_cost_usd":{"name":"ai_profile__generation_metadata__cost_tracking__total_cost_usd","data_type":"double","nullable":true},"ai_profile__generation_metadata__cost_tracking__latency_seconds":{"name":"ai_profile__generation_metadata__cost_tracking__latency_seconds","data_type":"double","nullable":true},"ai_profile__generation_metadapa0rsgracking__prompt_length_chars":{"name":"ai_profile__generation_metadapa0rsgracking__prompt_length_chars","data_type":"bigint","nullable":true},"ai_profile__generation_metadata__cost_tracking__timestamp":{"name":"ai_profile__generation_metadata__cost_tracking__timestamp","data_type":"timestamp","nullable":true},"ai_profile__generation_metadaovvxfg_pricing_per_m_tokens__input":{"name":"ai_profile__generation_metadaovvxfg_pricing_per_m_tokens__input","data_type":"double","nullable":true},"ai_profile__generation_metadai9kwcgpricing_per_m_tokens__output":{"name":"ai_profile__generation_metadai9kwcgpricing_per_m_tokens__output","data_type":"double","nullable":true},"app_category":{"name":"app_category","nullable":true,"data_type":"text"},"profession":{"name":"profession","nullable":true,"data_type":"text"},"monetization_score":{"name":"monetization_score","nullable":true,"data_type":"double"},"core_functions":{"data_type":"text","name":"core_functions"},"ai_profile":{"name":"ai_profile","nullable":true,"data_type":"json"},"core_problems":{"name":"core_problems","nullable":true,"data_type":"json"},"dimension_scores":{"data_type":"json","name":"dimension_scores"},"trust_badges":{"data_type":"json","name":"trust_badges"},"analyzed_at":{"name":"analyzed_at","nullable":true,"data_type":"timestamp"},"trust_score":{"data_type":"double","name":"trust_score"},"trust_badge":{"data_type":"text","name":"trust_badge"},"activity_score":{"data_type":"double","name":"activity_score"}},"write_disposition":"merge","name":"app_opportunities","resource":"app_opportunities","x-normalizer":{"seen-data":true}},"_dlt_pipeline_state":{"columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"pipeline_name":{"name":"pipeline_name","data_type":"text","nullable":false},"state":{"name":"state","data_type":"text","nullable":false},"created_at":{"name":"created_at","data_type":"timestamp","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false,"precision":64},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"append","file_format":"preferred","name":"_dlt_pipeline_state","resource":"_dlt_pipeline_state","x-normalizer":{"seen-data":true}},"app_opportunities__core_functions":{"name":"app_opportunities__core_functions","columns":{"value":{"name":"value","data_type":"text","nullable":true},"_dlt_root_id":{"name":"_dlt_root_id","data_type":"text","nullable":false,"root_key":true},"_dlt_parent_id":{"name":"_dlt_parent_id","data_type":"text","nullable":false,"parent_key":true},"_dlt_list_idx":{"name":"_dlt_list_idx","data_type":"bigint","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"parent":"app_opportunities","x-normalizer":{"seen-data":true}},"app_opportunities__trust_badges":{"name":"app_opportunities__trust_badges","columns":{"value":{"name":"value","data_type":"text","nullable":true},"_dlt_root_id":{"name":"_dlt_root_id","data_type":"text","nullable":false,"root_key":true},"_dlt_parent_id":{"name":"_dlt_parent_id","data_type":"text","nullable":false,"parent_key":true},"_dlt_list_idx":{"name":"_dlt_list_idx","data_type":"bigint","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"parent":"app_opportunities","x-normalizer":{"seen-data":true}},"app_opportunities__ai_profile__technical_feasibility__functions":{"name":"app_opportunities__ai_profile__technical_feasibility__functions","columns":{"value":{"name":"value","data_type":"text","nullable":true},"_dlt_root_id":{"name":"_dlt_root_id","data_type":"text","nullable":false,"root_key":true},"_dlt_parent_id":{"name":"_dlt_parent_id","data_type":"text","nullable":false,"parent_key":true},"_dlt_list_idx":{"name":"_dlt_list_idx","data_type":"bigint","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"parent":"app_opportunities","x-normalizer":{"seen-data":true}},"app_opportunities__ai_profile6devwwfeasibility__target_problems":{"name":"app_opportunities__ai_profile6devwwfeasibility__target_problems","columns":{"value":{"name":"value","data_type":"text","nullable":true},"_dlt_root_id":{"name":"_dlt_root_id","data_type":"text","nullable":false,"root_key":true},"_dlt_parent_id":{"name":"_dlt_parent_id","data_type":"text","nullable":false,"parent_key":true},"_dlt_list_idx":{"name":"_dlt_list_idx","data_type":"bigint","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"parent":"app_opportunities","x-normalizer":{"seen-data":true}},"app_opportunities__core_problems":{"name":"app_opportunities__core_problems","columns":{"value":{"name":"value","data_type":"text","nullable":true},"_dlt_root_id":{"name":"_dlt_root_id","data_type":"text","nullable":false,"root_key":true},"_dlt_parent_id":{"name":"_dlt_parent_id","data_type":"text","nullable":false,"parent_key":true},"_dlt_list_idx":{"name":"_dlt_list_idx","data_type":"bigint","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"parent":"app_opportunities","x-normalizer":{"seen-data":true}}},"settings":{"detections":["iso_timestamp"],"default_hints":{"not_null":["_dlt_id","_dlt_root_id","_dlt_parent_id","_dlt_list_idx","_dlt_load_id"],"parent_key":["_dlt_parent_id"],"root_key":["_dlt_root_id"],"unique":["_dlt_id"],"row_key":["_dlt_id"]}},"normalizers":{"names":"snake_case","json":{"module":"dlt.common.normalizers.json.relational","config":{"propagation":{"tables":{"app_opportunities":{"_dlt_id":"_dlt_root_id"}}}}}},"previous_hashes":["9dL6BrkRTYxuoNyjDnEMqJNiOSPgJUC1+zFmKzQrqYk=","24qoKqTa2ujixvGMbiYKxjUiMzgk8Ema2/yYws8nVso=","5b5rQHxdhEh9d5phn/dcU9fO/Px34pvdEHYpKacSGa4=","ZnSqPdePDFEyemAwmaiwZ4T6iEp08g6X6H29vcQDVwY=","xosN3zI9NHbp3MjtwOr7bIQRNc0bYps+FWTtEtrta3I=","4cO4gUVRApntGAdhSIe7nehZvj9VKxbQVI1v2rZ/I/E=","sB804Z1S+uvK3Aymzx2hDAMvyZCrI6Rhkc8xIQ1lmA4=","/Xquk7NUqym5XAEKJjt6fJBqSMaLU5XNsK0n3NA1u50=","uqPvUxKHtmRTRCe5l65mYYeo3sUDPwPYNFXHpv996NY=","7GAft10sahvE91rJCLmjkHhpY+t+mHibe9Sz+3vnATw="]}
3	11	2025-11-22 20:40:51.159507+00	submissions_loader	ZfUAmhTRncyjoC/K4ceeHR/8LwFGY26N2A7D+kOFdRI=	{"version":3,"version_hash":"ZfUAmhTRncyjoC/K4ceeHR/8LwFGY26N2A7D+kOFdRI=","engine_version":11,"name":"submissions_loader","tables":{"_dlt_version":{"name":"_dlt_version","columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_name":{"name":"schema_name","data_type":"text","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":false},"schema":{"name":"schema","data_type":"text","nullable":false}},"write_disposition":"skip","resource":"_dlt_version","description":"Created by DLT. Tracks schema updates"},"_dlt_loads":{"name":"_dlt_loads","columns":{"load_id":{"name":"load_id","data_type":"text","nullable":false,"precision":64},"schema_name":{"name":"schema_name","data_type":"text","nullable":true},"status":{"name":"status","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_version_hash":{"name":"schema_version_hash","data_type":"text","nullable":true}},"write_disposition":"skip","resource":"_dlt_loads","description":"Created by DLT. Tracks completed loads"},"submissions":{"columns":{"submission_id":{"name":"submission_id","nullable":false,"primary_key":true,"data_type":"text"},"title":{"name":"title","data_type":"text","nullable":true},"selftext":{"name":"selftext","data_type":"text","nullable":true},"author":{"name":"author","data_type":"text","nullable":true},"subreddit":{"name":"subreddit","data_type":"text","nullable":true},"trust_score":{"name":"trust_score","data_type":"double","nullable":true},"trust_level":{"name":"trust_level","data_type":"text","nullable":true},"market_validation_score":{"name":"market_validation_score","data_type":"double","nullable":true},"opportunity_score":{"name":"opportunity_score","data_type":"double","nullable":true},"created_utc":{"name":"created_utc","data_type":"double","nullable":true},"reddit_score":{"name":"reddit_score","data_type":"bigint","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true},"reddit_id":{"name":"reddit_id","data_type":"text","nullable":true}},"write_disposition":"merge","name":"submissions","resource":"submissions","x-normalizer":{"seen-data":true}},"_dlt_pipeline_state":{"columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"pipeline_name":{"name":"pipeline_name","data_type":"text","nullable":false},"state":{"name":"state","data_type":"text","nullable":false},"created_at":{"name":"created_at","data_type":"timestamp","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false,"precision":64},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"append","file_format":"preferred","name":"_dlt_pipeline_state","resource":"_dlt_pipeline_state","x-normalizer":{"seen-data":true}}},"settings":{"detections":["iso_timestamp"],"default_hints":{"not_null":["_dlt_id","_dlt_root_id","_dlt_parent_id","_dlt_list_idx","_dlt_load_id"],"parent_key":["_dlt_parent_id"],"root_key":["_dlt_root_id"],"unique":["_dlt_id"],"row_key":["_dlt_id"]}},"normalizers":{"names":"snake_case","json":{"module":"dlt.common.normalizers.json.relational","config":{"propagation":{"tables":{"submissions":{"_dlt_id":"_dlt_root_id"}}}}}},"previous_hashes":["twO6NVACyN/rIUfxAKk4B38ztLkvbgXGKFGvrVKFuQo=","q7WyAM1Y6iTT+/mssTH//AV8mVQK214ii+QjV05t2c4=","lU73DOREC2HYbaTZqFYKuBPvNzkEBK8uOu53qIxaMiQ="]}
2	11	2025-11-22 21:07:40.156768+00	opportunity_scores_loader	JINoVltXBM6DmOym0mQWjTFvpTQWUg2Jw+DiyA6BWh0=	{"version":2,"version_hash":"JINoVltXBM6DmOym0mQWjTFvpTQWUg2Jw+DiyA6BWh0=","engine_version":11,"name":"opportunity_scores_loader","tables":{"_dlt_version":{"name":"_dlt_version","columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_name":{"name":"schema_name","data_type":"text","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":false},"schema":{"name":"schema","data_type":"text","nullable":false}},"write_disposition":"skip","resource":"_dlt_version","description":"Created by DLT. Tracks schema updates"},"_dlt_loads":{"name":"_dlt_loads","columns":{"load_id":{"name":"load_id","data_type":"text","nullable":false,"precision":64},"schema_name":{"name":"schema_name","data_type":"text","nullable":true},"status":{"name":"status","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_version_hash":{"name":"schema_version_hash","data_type":"text","nullable":true}},"write_disposition":"skip","resource":"_dlt_loads","description":"Created by DLT. Tracks completed loads"},"opportunity_scores":{"columns":{"opportunity_id":{"data_type":"text","nullable":false,"name":"opportunity_id","primary_key":true},"market_demand":{"data_type":"double","nullable":false,"name":"market_demand"},"pain_intensity":{"data_type":"double","nullable":false,"name":"pain_intensity"},"competition_level":{"data_type":"double","nullable":false,"name":"competition_level"},"technical_feasibility":{"data_type":"double","nullable":false,"name":"technical_feasibility"},"monetization_potential":{"data_type":"double","nullable":false,"name":"monetization_potential"},"simplicity_score":{"data_type":"double","nullable":false,"name":"simplicity_score"},"total_score":{"data_type":"double","name":"total_score"},"created_at":{"data_type":"timestamp","name":"created_at"},"updated_at":{"data_type":"timestamp","name":"updated_at"},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"merge","name":"opportunity_scores","resource":"opportunity_scores","x-normalizer":{"seen-data":true}},"_dlt_pipeline_state":{"columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"pipeline_name":{"name":"pipeline_name","data_type":"text","nullable":false},"state":{"name":"state","data_type":"text","nullable":false},"created_at":{"name":"created_at","data_type":"timestamp","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false,"precision":64},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"append","file_format":"preferred","name":"_dlt_pipeline_state","resource":"_dlt_pipeline_state","x-normalizer":{"seen-data":true}}},"settings":{"detections":["iso_timestamp"],"default_hints":{"not_null":["_dlt_id","_dlt_root_id","_dlt_parent_id","_dlt_list_idx","_dlt_load_id"],"parent_key":["_dlt_parent_id"],"root_key":["_dlt_root_id"],"unique":["_dlt_id"],"row_key":["_dlt_id"]}},"normalizers":{"names":"snake_case","json":{"module":"dlt.common.normalizers.json.relational","config":{"propagation":{"tables":{"opportunity_scores":{"_dlt_id":"_dlt_root_id"}}}}}},"previous_hashes":["BuRHxgJ2ex9ARP5xAzQmS/7pn3E0pDn8gq11DiY/+Ok=","eb3Y8PFH8rVzmwq49QnA98jMTLU7UrrpaIY8A1v2hBY="]}
2	11	2025-11-22 21:07:40.605394+00	monetization_patterns_loader	lwOMSUlEs+iiYrWlxx826rsuGiDJBQnGopfbV72BR3I=	{"version":2,"version_hash":"lwOMSUlEs+iiYrWlxx826rsuGiDJBQnGopfbV72BR3I=","engine_version":11,"name":"monetization_patterns_loader","tables":{"_dlt_version":{"name":"_dlt_version","columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_name":{"name":"schema_name","data_type":"text","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":false},"schema":{"name":"schema","data_type":"text","nullable":false}},"write_disposition":"skip","resource":"_dlt_version","description":"Created by DLT. Tracks schema updates"},"_dlt_loads":{"name":"_dlt_loads","columns":{"load_id":{"name":"load_id","data_type":"text","nullable":false,"precision":64},"schema_name":{"name":"schema_name","data_type":"text","nullable":true},"status":{"name":"status","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_version_hash":{"name":"schema_version_hash","data_type":"text","nullable":true}},"write_disposition":"skip","resource":"_dlt_loads","description":"Created by DLT. Tracks completed loads"},"monetization_patterns":{"columns":{"opportunity_id":{"data_type":"text","nullable":false,"name":"opportunity_id","primary_key":true},"pattern_type":{"data_type":"text","nullable":false,"name":"pattern_type"},"revenue_model":{"data_type":"text","name":"revenue_model"},"target_pricing":{"data_type":"double","name":"target_pricing"},"market_size":{"data_type":"double","name":"market_size"},"willingness_to_pay_score":{"data_type":"double","name":"willingness_to_pay_score"},"customer_segment":{"data_type":"text","name":"customer_segment"},"price_sensitivity_score":{"data_type":"double","name":"price_sensitivity_score"},"revenue_potential_score":{"data_type":"double","name":"revenue_potential_score"},"mentioned_price_points":{"data_type":"json","name":"mentioned_price_points"},"existing_payment_behavior":{"data_type":"text","name":"existing_payment_behavior"},"urgency_level":{"data_type":"text","name":"urgency_level"},"sentiment_toward_payment":{"data_type":"text","name":"sentiment_toward_payment"},"payment_friction_indicators":{"data_type":"json","name":"payment_friction_indicators"},"llm_monetization_score":{"data_type":"double","name":"llm_monetization_score"},"confidence":{"data_type":"double","name":"confidence"},"reasoning":{"data_type":"text","name":"reasoning"},"created_at":{"data_type":"timestamp","name":"created_at"},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"merge","name":"monetization_patterns","resource":"monetization_patterns","x-normalizer":{"seen-data":true}},"_dlt_pipeline_state":{"columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"pipeline_name":{"name":"pipeline_name","data_type":"text","nullable":false},"state":{"name":"state","data_type":"text","nullable":false},"created_at":{"name":"created_at","data_type":"timestamp","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false,"precision":64},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"append","file_format":"preferred","name":"_dlt_pipeline_state","resource":"_dlt_pipeline_state","x-normalizer":{"seen-data":true}}},"settings":{"detections":["iso_timestamp"],"default_hints":{"not_null":["_dlt_id","_dlt_root_id","_dlt_parent_id","_dlt_list_idx","_dlt_load_id"],"parent_key":["_dlt_parent_id"],"root_key":["_dlt_root_id"],"unique":["_dlt_id"],"row_key":["_dlt_id"]}},"normalizers":{"names":"snake_case","json":{"module":"dlt.common.normalizers.json.relational","config":{"propagation":{"tables":{"monetization_patterns":{"_dlt_id":"_dlt_root_id"}}}}}},"previous_hashes":["6nCK50PWItVtZMgzHkmQ8sqCpjMTcqSqctQUV99O4+w=","e47VzjyfrypGIME3B0/iE9yxECjGtA1qOzzH2jJwyqM="]}
2	11	2025-11-22 21:07:40.943485+00	market_validations_loader	5Ptrjc16vfqGalFhp7XygADFreOdltpHqO1ThvfHdpI=	{"version":2,"version_hash":"5Ptrjc16vfqGalFhp7XygADFreOdltpHqO1ThvfHdpI=","engine_version":11,"name":"market_validations_loader","tables":{"_dlt_version":{"name":"_dlt_version","columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_name":{"name":"schema_name","data_type":"text","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":false},"schema":{"name":"schema","data_type":"text","nullable":false}},"write_disposition":"skip","resource":"_dlt_version","description":"Created by DLT. Tracks schema updates"},"_dlt_loads":{"name":"_dlt_loads","columns":{"load_id":{"name":"load_id","data_type":"text","nullable":false,"precision":64},"schema_name":{"name":"schema_name","data_type":"text","nullable":true},"status":{"name":"status","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_version_hash":{"name":"schema_version_hash","data_type":"text","nullable":true}},"write_disposition":"skip","resource":"_dlt_loads","description":"Created by DLT. Tracks completed loads"},"market_validations":{"columns":{"opportunity_id":{"data_type":"text","nullable":false,"name":"opportunity_id","primary_key":true},"validation_type":{"data_type":"text","nullable":false,"name":"validation_type"},"validation_source":{"data_type":"text","name":"validation_source"},"validation_date":{"data_type":"timestamp","name":"validation_date"},"validation_result":{"data_type":"json","name":"validation_result"},"confidence_score":{"data_type":"double","name":"confidence_score"},"notes":{"data_type":"text","name":"notes"},"status":{"data_type":"text","name":"status"},"evidence_url":{"data_type":"text","name":"evidence_url"},"market_validation_score":{"data_type":"double","name":"market_validation_score"},"market_data_quality_score":{"data_type":"double","name":"market_data_quality_score"},"market_validation_reasoning":{"data_type":"text","name":"market_validation_reasoning"},"market_competitors_found":{"data_type":"json","name":"market_competitors_found"},"market_size_tam":{"data_type":"double","name":"market_size_tam"},"market_size_sam":{"data_type":"double","name":"market_size_sam"},"market_size_growth":{"data_type":"double","name":"market_size_growth"},"market_similar_launches":{"data_type":"bigint","name":"market_similar_launches"},"market_validation_cost_usd":{"data_type":"double","name":"market_validation_cost_usd"},"search_queries_used":{"data_type":"json","name":"search_queries_used"},"urls_fetched":{"data_type":"json","name":"urls_fetched"},"extraction_stats":{"data_type":"json","name":"extraction_stats"},"jina_api_calls_count":{"data_type":"bigint","name":"jina_api_calls_count"},"jina_cache_hit_rate":{"data_type":"double","name":"jina_cache_hit_rate"},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"merge","name":"market_validations","resource":"market_validations","x-normalizer":{"seen-data":true}},"_dlt_pipeline_state":{"columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"pipeline_name":{"name":"pipeline_name","data_type":"text","nullable":false},"state":{"name":"state","data_type":"text","nullable":false},"created_at":{"name":"created_at","data_type":"timestamp","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false,"precision":64},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"append","file_format":"preferred","name":"_dlt_pipeline_state","resource":"_dlt_pipeline_state","x-normalizer":{"seen-data":true}}},"settings":{"detections":["iso_timestamp"],"default_hints":{"not_null":["_dlt_id","_dlt_root_id","_dlt_parent_id","_dlt_list_idx","_dlt_load_id"],"parent_key":["_dlt_parent_id"],"root_key":["_dlt_root_id"],"unique":["_dlt_id"],"row_key":["_dlt_id"]}},"normalizers":{"names":"snake_case","json":{"module":"dlt.common.normalizers.json.relational","config":{"propagation":{"tables":{"market_validations":{"_dlt_id":"_dlt_root_id"}}}}}},"previous_hashes":["vqE8uBvSVOuUbByq3ir84M6yuRSjnlE6Kc6c3juMeu4=","6dYw9ZiXhDmLmQn6ca745o8rNXmdl2EChQEVB0aij1I="]}
2	11	2025-11-22 21:07:41.3122+00	competitive_landscape_loader	3ZTwlQ0XrRR5iKKiTKgAk9b+QdxYnCWJqx8FM0a3Lqk=	{"version":2,"version_hash":"3ZTwlQ0XrRR5iKKiTKgAk9b+QdxYnCWJqx8FM0a3Lqk=","engine_version":11,"name":"competitive_landscape_loader","tables":{"_dlt_version":{"name":"_dlt_version","columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_name":{"name":"schema_name","data_type":"text","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":false},"schema":{"name":"schema","data_type":"text","nullable":false}},"write_disposition":"skip","resource":"_dlt_version","description":"Created by DLT. Tracks schema updates"},"_dlt_loads":{"name":"_dlt_loads","columns":{"load_id":{"name":"load_id","data_type":"text","nullable":false,"precision":64},"schema_name":{"name":"schema_name","data_type":"text","nullable":true},"status":{"name":"status","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_version_hash":{"name":"schema_version_hash","data_type":"text","nullable":true}},"write_disposition":"skip","resource":"_dlt_loads","description":"Created by DLT. Tracks completed loads"},"competitive_landscape":{"columns":{"opportunity_id":{"data_type":"text","nullable":false,"name":"opportunity_id","primary_key":true},"competitor_name":{"data_type":"text","nullable":false,"name":"competitor_name"},"competitor_features":{"data_type":"json","name":"competitor_features"},"competitive_analysis":{"data_type":"text","name":"competitive_analysis"},"market_share":{"data_type":"double","name":"market_share"},"pricing_model":{"data_type":"text","name":"pricing_model"},"target_market":{"data_type":"text","name":"target_market"},"source_url":{"data_type":"text","name":"source_url"},"confidence":{"data_type":"double","name":"confidence"},"extracted_at":{"data_type":"timestamp","name":"extracted_at"},"created_at":{"data_type":"timestamp","name":"created_at"},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"merge","name":"competitive_landscape","resource":"competitive_landscape","x-normalizer":{"seen-data":true}},"_dlt_pipeline_state":{"columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"pipeline_name":{"name":"pipeline_name","data_type":"text","nullable":false},"state":{"name":"state","data_type":"text","nullable":false},"created_at":{"name":"created_at","data_type":"timestamp","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false,"precision":64},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"append","file_format":"preferred","name":"_dlt_pipeline_state","resource":"_dlt_pipeline_state","x-normalizer":{"seen-data":true}}},"settings":{"detections":["iso_timestamp"],"default_hints":{"not_null":["_dlt_id","_dlt_root_id","_dlt_parent_id","_dlt_list_idx","_dlt_load_id"],"parent_key":["_dlt_parent_id"],"root_key":["_dlt_root_id"],"unique":["_dlt_id"],"row_key":["_dlt_id"]}},"normalizers":{"names":"snake_case","json":{"module":"dlt.common.normalizers.json.relational","config":{"propagation":{"tables":{"competitive_landscape":{"_dlt_id":"_dlt_root_id"}}}}}},"previous_hashes":["mOdm3OMPTvHerqKrucC2kMUtTRPX8zOF93iDQUT8UL0=","xXETqUwrK32jW3C88/WKsb7rkqzmpyhgpyxx9JBOyAk="]}
2	11	2025-11-22 23:21:21.41535+00	app_opportunities_loader	gbvcKYpG8BKSlO557kmGKeT9heSVkTsTEqxl8u4CjG4=	{"version":2,"version_hash":"gbvcKYpG8BKSlO557kmGKeT9heSVkTsTEqxl8u4CjG4=","engine_version":11,"name":"app_opportunities_loader","tables":{"_dlt_version":{"name":"_dlt_version","columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_name":{"name":"schema_name","data_type":"text","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":false},"schema":{"name":"schema","data_type":"text","nullable":false}},"write_disposition":"skip","resource":"_dlt_version","description":"Created by DLT. Tracks schema updates"},"_dlt_loads":{"name":"_dlt_loads","columns":{"load_id":{"name":"load_id","data_type":"text","nullable":false,"precision":64},"schema_name":{"name":"schema_name","data_type":"text","nullable":true},"status":{"name":"status","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_version_hash":{"name":"schema_version_hash","data_type":"text","nullable":true}},"write_disposition":"skip","resource":"_dlt_loads","description":"Created by DLT. Tracks completed loads"},"app_opportunities":{"columns":{"submission_id":{"data_type":"text","nullable":false,"name":"submission_id","primary_key":true},"problem_description":{"data_type":"text","name":"problem_description"},"app_concept":{"data_type":"text","name":"app_concept"},"core_functions":{"data_type":"text","name":"core_functions"},"value_proposition":{"data_type":"text","name":"value_proposition"},"target_user":{"data_type":"text","name":"target_user"},"monetization_model":{"data_type":"text","name":"monetization_model"},"opportunity_score":{"data_type":"double","name":"opportunity_score"},"final_score":{"data_type":"double","name":"final_score"},"status":{"data_type":"text","name":"status"},"ai_profile":{"data_type":"json","name":"ai_profile"},"app_name":{"data_type":"text","name":"app_name"},"app_category":{"data_type":"text","name":"app_category"},"profession":{"data_type":"text","name":"profession"},"core_problems":{"data_type":"json","name":"core_problems"},"dimension_scores":{"data_type":"json","name":"dimension_scores"},"priority":{"data_type":"text","name":"priority"},"confidence":{"data_type":"double","name":"confidence"},"evidence_based":{"data_type":"bool","name":"evidence_based"},"trust_score":{"data_type":"double","name":"trust_score"},"trust_badge":{"data_type":"text","name":"trust_badge"},"activity_score":{"data_type":"double","name":"activity_score"},"trust_level":{"data_type":"text","name":"trust_level"},"trust_badges":{"data_type":"json","name":"trust_badges"},"monetization_score":{"data_type":"double","name":"monetization_score"},"market_validation_score":{"data_type":"double","name":"market_validation_score"},"analyzed_at":{"data_type":"timestamp","name":"analyzed_at"},"enrichment_version":{"data_type":"text","name":"enrichment_version"},"pipeline_source":{"data_type":"text","name":"pipeline_source"},"title":{"data_type":"text","name":"title"},"subreddit":{"data_type":"text","name":"subreddit"},"reddit_score":{"data_type":"bigint","name":"reddit_score"},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"merge","name":"app_opportunities","resource":"app_opportunities","x-normalizer":{"seen-data":true}},"_dlt_pipeline_state":{"columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"pipeline_name":{"name":"pipeline_name","data_type":"text","nullable":false},"state":{"name":"state","data_type":"text","nullable":false},"created_at":{"name":"created_at","data_type":"timestamp","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false,"precision":64},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"append","file_format":"preferred","name":"_dlt_pipeline_state","resource":"_dlt_pipeline_state","x-normalizer":{"seen-data":true}},"app_opportunities__core_functions":{"name":"app_opportunities__core_functions","columns":{"value":{"name":"value","data_type":"text","nullable":true},"_dlt_root_id":{"name":"_dlt_root_id","data_type":"text","nullable":false,"root_key":true},"_dlt_parent_id":{"name":"_dlt_parent_id","data_type":"text","nullable":false,"parent_key":true},"_dlt_list_idx":{"name":"_dlt_list_idx","data_type":"bigint","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"parent":"app_opportunities","x-normalizer":{"seen-data":true}}},"settings":{"detections":["iso_timestamp"],"default_hints":{"not_null":["_dlt_id","_dlt_root_id","_dlt_parent_id","_dlt_list_idx","_dlt_load_id"],"parent_key":["_dlt_parent_id"],"root_key":["_dlt_root_id"],"unique":["_dlt_id"],"row_key":["_dlt_id"]}},"normalizers":{"names":"snake_case","json":{"module":"dlt.common.normalizers.json.relational","config":{"propagation":{"tables":{"app_opportunities":{"_dlt_id":"_dlt_root_id"}}}}}},"previous_hashes":["P1zh8nMT8IAl11VXtMGvpHoYLgpWM3DCZqRrTK3b4/A=","vLnuOt7zvQR+RNqUtD4/1PGBh7DzzjeKEnpJDdxvO18="]}
4	11	2025-11-24 00:46:57.38303+00	app_opportunities_loader	arbeBJe3bDZdsPHsb4+PfhEh5R/dFCCbFDjZjur5Sh0=	{"version":4,"version_hash":"arbeBJe3bDZdsPHsb4+PfhEh5R/dFCCbFDjZjur5Sh0=","engine_version":11,"name":"app_opportunities_loader","tables":{"_dlt_version":{"name":"_dlt_version","columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_name":{"name":"schema_name","data_type":"text","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":false},"schema":{"name":"schema","data_type":"text","nullable":false}},"write_disposition":"skip","resource":"_dlt_version","description":"Created by DLT. Tracks schema updates"},"_dlt_loads":{"name":"_dlt_loads","columns":{"load_id":{"name":"load_id","data_type":"text","nullable":false,"precision":64},"schema_name":{"name":"schema_name","data_type":"text","nullable":true},"status":{"name":"status","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_version_hash":{"name":"schema_version_hash","data_type":"text","nullable":true}},"write_disposition":"skip","resource":"_dlt_loads","description":"Created by DLT. Tracks completed loads"},"app_opportunities":{"columns":{"submission_id":{"data_type":"text","nullable":false,"name":"submission_id","primary_key":true},"problem_description":{"data_type":"text","name":"problem_description"},"app_concept":{"data_type":"text","name":"app_concept"},"core_functions":{"data_type":"text","name":"core_functions"},"value_proposition":{"data_type":"text","name":"value_proposition"},"target_user":{"data_type":"text","name":"target_user"},"monetization_model":{"data_type":"text","name":"monetization_model"},"opportunity_score":{"data_type":"double","name":"opportunity_score"},"final_score":{"data_type":"double","name":"final_score"},"status":{"data_type":"text","name":"status"},"ai_profile":{"data_type":"json","name":"ai_profile"},"app_name":{"data_type":"text","name":"app_name"},"app_category":{"data_type":"text","name":"app_category"},"profession":{"data_type":"text","name":"profession"},"core_problems":{"data_type":"json","name":"core_problems"},"dimension_scores":{"data_type":"json","name":"dimension_scores"},"priority":{"data_type":"text","name":"priority"},"confidence":{"data_type":"decimal","name":"confidence"},"evidence_based":{"data_type":"bool","name":"evidence_based"},"trust_score":{"data_type":"double","name":"trust_score"},"trust_badge":{"data_type":"text","name":"trust_badge"},"activity_score":{"data_type":"double","name":"activity_score"},"trust_level":{"data_type":"text","name":"trust_level"},"trust_badges":{"data_type":"json","name":"trust_badges"},"monetization_score":{"data_type":"decimal","name":"monetization_score"},"market_validation_score":{"data_type":"decimal","name":"market_validation_score"},"analyzed_at":{"data_type":"timestamp","name":"analyzed_at"},"enrichment_version":{"data_type":"text","name":"enrichment_version"},"pipeline_source":{"data_type":"text","name":"pipeline_source"},"title":{"data_type":"text","name":"title"},"subreddit":{"data_type":"text","name":"subreddit"},"reddit_score":{"data_type":"bigint","name":"reddit_score"},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"merge","name":"app_opportunities","resource":"app_opportunities","x-normalizer":{"max_nesting":1,"seen-data":true}},"_dlt_pipeline_state":{"columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"pipeline_name":{"name":"pipeline_name","data_type":"text","nullable":false},"state":{"name":"state","data_type":"text","nullable":false},"created_at":{"name":"created_at","data_type":"timestamp","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false,"precision":64},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"append","file_format":"preferred","name":"_dlt_pipeline_state","resource":"_dlt_pipeline_state","x-normalizer":{"seen-data":true}},"app_opportunities__core_functions":{"name":"app_opportunities__core_functions","columns":{"value":{"name":"value","data_type":"text","nullable":true},"_dlt_root_id":{"name":"_dlt_root_id","data_type":"text","nullable":false,"root_key":true},"_dlt_parent_id":{"name":"_dlt_parent_id","data_type":"text","nullable":false,"parent_key":true},"_dlt_list_idx":{"name":"_dlt_list_idx","data_type":"bigint","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"parent":"app_opportunities","x-normalizer":{"seen-data":true}}},"settings":{"detections":["iso_timestamp"],"default_hints":{"not_null":["_dlt_id","_dlt_root_id","_dlt_parent_id","_dlt_list_idx","_dlt_load_id"],"parent_key":["_dlt_parent_id"],"root_key":["_dlt_root_id"],"unique":["_dlt_id"],"row_key":["_dlt_id"]}},"normalizers":{"names":"snake_case","json":{"module":"dlt.common.normalizers.json.relational","config":{"propagation":{"tables":{"app_opportunities":{"_dlt_id":"_dlt_root_id"}}}}}},"previous_hashes":["nDLAp9QJLg67NRsvauHf5quET9LmaZ8YSmKcypr5Wds=","gbvcKYpG8BKSlO557kmGKeT9heSVkTsTEqxl8u4CjG4=","P1zh8nMT8IAl11VXtMGvpHoYLgpWM3DCZqRrTK3b4/A=","vLnuOt7zvQR+RNqUtD4/1PGBh7DzzjeKEnpJDdxvO18="]}
2	11	2025-11-24 00:47:24.192734+00	app_opportunities_loader	yuJ75xKwP3h5zR0FZqgtT9dyngWlP0ofPUwss+mV+Vg=	{"version":2,"version_hash":"yuJ75xKwP3h5zR0FZqgtT9dyngWlP0ofPUwss+mV+Vg=","engine_version":11,"name":"app_opportunities_loader","tables":{"_dlt_version":{"name":"_dlt_version","columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_name":{"name":"schema_name","data_type":"text","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":false},"schema":{"name":"schema","data_type":"text","nullable":false}},"write_disposition":"skip","resource":"_dlt_version","description":"Created by DLT. Tracks schema updates"},"_dlt_loads":{"name":"_dlt_loads","columns":{"load_id":{"name":"load_id","data_type":"text","nullable":false,"precision":64},"schema_name":{"name":"schema_name","data_type":"text","nullable":true},"status":{"name":"status","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_version_hash":{"name":"schema_version_hash","data_type":"text","nullable":true}},"write_disposition":"skip","resource":"_dlt_loads","description":"Created by DLT. Tracks completed loads"},"app_opportunities":{"columns":{"submission_id":{"data_type":"text","nullable":false,"name":"submission_id","primary_key":true},"problem_description":{"data_type":"text","name":"problem_description"},"app_concept":{"data_type":"text","name":"app_concept"},"core_functions":{"data_type":"text","name":"core_functions"},"value_proposition":{"data_type":"text","name":"value_proposition"},"target_user":{"data_type":"text","name":"target_user"},"monetization_model":{"data_type":"text","name":"monetization_model"},"opportunity_score":{"data_type":"double","name":"opportunity_score"},"final_score":{"data_type":"double","name":"final_score"},"status":{"data_type":"text","name":"status"},"ai_profile":{"data_type":"json","name":"ai_profile"},"app_name":{"data_type":"text","name":"app_name"},"app_category":{"data_type":"text","name":"app_category"},"profession":{"data_type":"text","name":"profession"},"core_problems":{"data_type":"json","name":"core_problems"},"dimension_scores":{"data_type":"json","name":"dimension_scores"},"priority":{"data_type":"text","name":"priority"},"confidence":{"data_type":"decimal","name":"confidence"},"evidence_based":{"data_type":"bool","name":"evidence_based"},"trust_level":{"data_type":"text","name":"trust_level"},"trust_badges":{"data_type":"json","name":"trust_badges"},"monetization_score":{"data_type":"decimal","name":"monetization_score"},"market_validation_score":{"data_type":"decimal","name":"market_validation_score"},"analyzed_at":{"data_type":"timestamp","name":"analyzed_at"},"enrichment_version":{"data_type":"text","name":"enrichment_version"},"pipeline_source":{"data_type":"text","name":"pipeline_source"},"title":{"data_type":"text","name":"title"},"subreddit":{"data_type":"text","name":"subreddit"},"reddit_score":{"data_type":"bigint","name":"reddit_score"},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"x-normalizer":{"max_nesting":1,"seen-data":true},"write_disposition":"merge","name":"app_opportunities","resource":"app_opportunities"},"_dlt_pipeline_state":{"columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"pipeline_name":{"name":"pipeline_name","data_type":"text","nullable":false},"state":{"name":"state","data_type":"text","nullable":false},"created_at":{"name":"created_at","data_type":"timestamp","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false,"precision":64},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"append","file_format":"preferred","name":"_dlt_pipeline_state","resource":"_dlt_pipeline_state","x-normalizer":{"seen-data":true}}},"settings":{"detections":["iso_timestamp"],"default_hints":{"not_null":["_dlt_id","_dlt_root_id","_dlt_parent_id","_dlt_list_idx","_dlt_load_id"],"parent_key":["_dlt_parent_id"],"root_key":["_dlt_root_id"],"unique":["_dlt_id"],"row_key":["_dlt_id"]}},"normalizers":{"names":"snake_case","json":{"module":"dlt.common.normalizers.json.relational","config":{"propagation":{"tables":{"app_opportunities":{"_dlt_id":"_dlt_root_id"}}}}}},"previous_hashes":["cBr73hZCGUCjl56SEqashWin+mcPJrpoWbC+T3cmyOQ=","U9+pGHMu2Lj/MM3bzVgoO0aCSH/BcGQ36tGnfUSoLgA="]}
15	11	2025-11-24 21:01:45.409948+00	reddit_harbor_problem_collection	NS4LPU4+tZlvO6LZkSMS3fknOeZhF6u9I8iK2Eth4yY=	{"version":15,"version_hash":"NS4LPU4+tZlvO6LZkSMS3fknOeZhF6u9I8iK2Eth4yY=","engine_version":11,"name":"reddit_harbor_problem_collection","tables":{"_dlt_version":{"name":"_dlt_version","columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_name":{"name":"schema_name","data_type":"text","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":false},"schema":{"name":"schema","data_type":"text","nullable":false}},"write_disposition":"skip","resource":"_dlt_version","description":"Created by DLT. Tracks schema updates"},"_dlt_loads":{"name":"_dlt_loads","columns":{"load_id":{"name":"load_id","data_type":"text","nullable":false,"precision":64},"schema_name":{"name":"schema_name","data_type":"text","nullable":true},"status":{"name":"status","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_version_hash":{"name":"schema_version_hash","data_type":"text","nullable":true}},"write_disposition":"skip","resource":"_dlt_loads","description":"Created by DLT. Tracks completed loads"},"workflow_results":{"columns":{"opportunity_id":{"data_type":"text","nullable":false,"unique":true,"name":"opportunity_id","primary_key":true},"app_name":{"data_type":"text","nullable":false,"name":"app_name"},"function_count":{"data_type":"bigint","nullable":false,"name":"function_count"},"function_list":{"data_type":"json","nullable":true,"name":"function_list"},"original_score":{"data_type":"double","nullable":false,"name":"original_score"},"final_score":{"data_type":"double","nullable":false,"name":"final_score"},"status":{"data_type":"text","nullable":false,"name":"status"},"constraint_applied":{"data_type":"bool","nullable":true,"name":"constraint_applied"},"ai_insight":{"data_type":"text","nullable":true,"name":"ai_insight"},"processed_at":{"data_type":"timestamp","nullable":true,"name":"processed_at"},"market_demand":{"data_type":"decimal","precision":5,"scale":2,"nullable":true,"name":"market_demand"},"pain_intensity":{"data_type":"decimal","precision":5,"scale":2,"nullable":true,"name":"pain_intensity"},"monetization_potential":{"data_type":"decimal","precision":5,"scale":2,"nullable":true,"name":"monetization_potential"},"market_gap":{"data_type":"decimal","precision":5,"scale":2,"nullable":true,"name":"market_gap"},"technical_feasibility":{"data_type":"decimal","precision":5,"scale":2,"nullable":true,"name":"technical_feasibility"},"core_functions":{"data_type":"bigint","nullable":true,"name":"core_functions"},"simplicity_score":{"data_type":"double","nullable":true,"name":"simplicity_score"},"is_disqualified":{"data_type":"bool","nullable":true,"name":"is_disqualified"},"constraint_version":{"data_type":"bigint","nullable":true,"name":"constraint_version"},"validation_timestamp":{"data_type":"timestamp","nullable":true,"name":"validation_timestamp"},"violation_reason":{"data_type":"text","nullable":true,"name":"violation_reason"},"validation_status":{"data_type":"text","nullable":true,"name":"validation_status"},"submission_id":{"name":"submission_id","data_type":"text","nullable":true},"problem_description":{"name":"problem_description","data_type":"text","nullable":true},"app_concept":{"name":"app_concept","data_type":"text","nullable":true},"value_proposition":{"name":"value_proposition","data_type":"text","nullable":true},"target_user":{"name":"target_user","data_type":"text","nullable":true},"monetization_model":{"name":"monetization_model","data_type":"text","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true},"trust_score":{"name":"trust_score","data_type":"double","nullable":true},"trust_badge":{"name":"trust_badge","data_type":"text","nullable":true},"activity_score":{"name":"activity_score","data_type":"double","nullable":true},"subreddit":{"name":"subreddit","data_type":"text","nullable":true},"llm_provider":{"name":"llm_provider","data_type":"text","nullable":true},"llm_prompt_tokens":{"name":"llm_prompt_tokens","data_type":"bigint","nullable":true},"llm_completion_tokens":{"name":"llm_completion_tokens","data_type":"bigint","nullable":true},"llm_total_tokens":{"name":"llm_total_tokens","data_type":"bigint","nullable":true},"llm_input_cost_usd":{"name":"llm_input_cost_usd","data_type":"double","nullable":true},"llm_output_cost_usd":{"name":"llm_output_cost_usd","data_type":"double","nullable":true},"llm_total_cost_usd":{"name":"llm_total_cost_usd","data_type":"double","nullable":true},"llm_latency_seconds":{"name":"llm_latency_seconds","data_type":"double","nullable":true},"cost_tracking_enabled":{"name":"cost_tracking_enabled","data_type":"bool","nullable":true},"llm_model_used":{"name":"llm_model_used","nullable":true,"data_type":"text"},"llm_timestamp":{"name":"llm_timestamp","nullable":true,"data_type":"timestamp"},"llm_pricing_info__input":{"name":"llm_pricing_info__input","data_type":"double","nullable":true},"llm_pricing_info__output":{"name":"llm_pricing_info__output","data_type":"double","nullable":true}},"write_disposition":"merge","name":"workflow_results","resource":"app_opportunities_with_constraint","x-normalizer":{"seen-data":true}},"_dlt_pipeline_state":{"columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"pipeline_name":{"name":"pipeline_name","data_type":"text","nullable":false},"state":{"name":"state","data_type":"text","nullable":false},"created_at":{"name":"created_at","data_type":"timestamp","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false,"precision":64},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"append","file_format":"preferred","name":"_dlt_pipeline_state","resource":"_dlt_pipeline_state","x-normalizer":{"seen-data":true}},"app_opportunities_trust":{"columns":{"submission_id":{"name":"submission_id","nullable":false,"primary_key":true,"data_type":"text"},"problem_description":{"name":"problem_description","data_type":"text","nullable":true},"app_concept":{"name":"app_concept","data_type":"text","nullable":true},"core_functions":{"name":"core_functions","data_type":"text","nullable":true},"value_proposition":{"name":"value_proposition","data_type":"text","nullable":true},"target_user":{"name":"target_user","data_type":"text","nullable":true},"monetization_model":{"name":"monetization_model","data_type":"text","nullable":true},"opportunity_score":{"name":"opportunity_score","data_type":"double","nullable":true},"title":{"name":"title","data_type":"text","nullable":true},"status":{"name":"status","data_type":"text","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true},"trust_score":{"name":"trust_score","data_type":"double","nullable":true},"trust_badge":{"name":"trust_badge","data_type":"text","nullable":true},"activity_score":{"name":"activity_score","data_type":"double","nullable":true},"engagement_level":{"name":"engagement_level","data_type":"text","nullable":true},"trust_level":{"name":"trust_level","data_type":"text","nullable":true},"trend_velocity":{"name":"trend_velocity","data_type":"bigint","nullable":true},"problem_validity":{"name":"problem_validity","data_type":"text","nullable":true},"discussion_quality":{"name":"discussion_quality","data_type":"text","nullable":true},"ai_confidence_level":{"name":"ai_confidence_level","data_type":"text","nullable":true},"trust_validation_timestamp":{"name":"trust_validation_timestamp","data_type":"double","nullable":true},"trust_validation_method":{"name":"trust_validation_method","data_type":"text","nullable":true},"subreddit":{"name":"subreddit","data_type":"text","nullable":true},"reddit_score":{"name":"reddit_score","data_type":"bigint","nullable":true},"num_comments":{"name":"num_comments","data_type":"bigint","nullable":true}},"write_disposition":"merge","name":"app_opportunities_trust","resource":"app_opportunities_trust","x-normalizer":{"seen-data":true}},"opportunity_analysis":{"columns":{"submission_id":{"name":"submission_id","nullable":false,"primary_key":true,"data_type":"text"},"opportunity_id":{"name":"opportunity_id","data_type":"text","nullable":true},"title":{"name":"title","data_type":"text","nullable":true},"subreddit":{"name":"subreddit","data_type":"text","nullable":true},"sector":{"name":"sector","data_type":"text","nullable":true},"market_demand":{"name":"market_demand","data_type":"bigint","nullable":true},"pain_intensity":{"name":"pain_intensity","data_type":"bigint","nullable":true},"monetization_potential":{"name":"monetization_potential","data_type":"bigint","nullable":true},"market_gap":{"name":"market_gap","data_type":"bigint","nullable":true},"technical_feasibility":{"name":"technical_feasibility","data_type":"bigint","nullable":true},"simplicity_score":{"name":"simplicity_score","data_type":"double","nullable":true},"final_score":{"name":"final_score","data_type":"bigint","nullable":true},"priority":{"name":"priority","data_type":"text","nullable":true},"app_concept":{"name":"app_concept","data_type":"text","nullable":true},"core_functions":{"name":"core_functions","data_type":"text","nullable":true},"growth_justification":{"name":"growth_justification","data_type":"text","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"merge","name":"opportunity_analysis","resource":"opportunity_analysis","x-normalizer":{"seen-data":true}},"app_opportunities":{"columns":{"submission_id":{"name":"submission_id","nullable":false,"primary_key":true,"data_type":"text"},"problem_description":{"name":"problem_description","data_type":"text","nullable":true},"app_concept":{"name":"app_concept","data_type":"text","nullable":true},"core_functions":{"name":"core_functions","data_type":"text","nullable":true},"value_proposition":{"name":"value_proposition","data_type":"text","nullable":true},"target_user":{"name":"target_user","data_type":"text","nullable":true},"monetization_model":{"name":"monetization_model","data_type":"text","nullable":true},"opportunity_score":{"name":"opportunity_score","data_type":"double","nullable":true},"title":{"name":"title","data_type":"text","nullable":true},"status":{"name":"status","data_type":"text","nullable":true},"trust_score":{"name":"trust_score","data_type":"double","nullable":true},"trust_badge":{"name":"trust_badge","data_type":"text","nullable":true},"activity_score":{"name":"activity_score","data_type":"bigint","nullable":true},"engagement_level":{"name":"engagement_level","data_type":"text","nullable":true},"trust_level":{"name":"trust_level","data_type":"text","nullable":true},"trend_velocity":{"name":"trend_velocity","data_type":"bigint","nullable":true},"problem_validity":{"name":"problem_validity","data_type":"text","nullable":true},"discussion_quality":{"name":"discussion_quality","data_type":"text","nullable":true},"ai_confidence_level":{"name":"ai_confidence_level","data_type":"text","nullable":true},"trust_validation_timestamp":{"name":"trust_validation_timestamp","data_type":"double","nullable":true},"trust_validation_method":{"name":"trust_validation_method","data_type":"text","nullable":true},"subreddit":{"name":"subreddit","data_type":"text","nullable":true},"reddit_score":{"name":"reddit_score","data_type":"bigint","nullable":true},"num_comments":{"name":"num_comments","data_type":"bigint","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"merge","name":"app_opportunities","resource":"app_opportunities","x-normalizer":{"seen-data":true}},"submissions":{"columns":{"submission_id":{"data_type":"text","nullable":true,"unique":true,"name":"submission_id","primary_key":true},"reddit_id":{"data_type":"text","nullable":true,"name":"reddit_id"},"title":{"data_type":"text","nullable":true,"name":"title"},"text":{"data_type":"text","nullable":true,"name":"text"},"content":{"data_type":"text","nullable":true,"name":"content"},"subreddit":{"data_type":"text","nullable":true,"name":"subreddit"},"upvotes":{"data_type":"bigint","nullable":true,"name":"upvotes"},"comments_count":{"data_type":"bigint","nullable":true,"name":"comments_count"},"url":{"data_type":"text","nullable":true,"name":"url"},"created_at":{"data_type":"timestamp","nullable":true,"name":"created_at"},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"merge","name":"submissions","resource":"submissions","x-normalizer":{"seen-data":true}}},"settings":{"detections":["iso_timestamp"],"default_hints":{"not_null":["_dlt_id","_dlt_root_id","_dlt_parent_id","_dlt_list_idx","_dlt_load_id"],"parent_key":["_dlt_parent_id"],"root_key":["_dlt_root_id"],"unique":["_dlt_id"],"row_key":["_dlt_id"]}},"normalizers":{"names":"snake_case","json":{"module":"dlt.common.normalizers.json.relational","config":{"propagation":{"tables":{"workflow_results":{"_dlt_id":"_dlt_root_id"},"app_opportunities_trust":{"_dlt_id":"_dlt_root_id"},"opportunity_analysis":{"_dlt_id":"_dlt_root_id"},"app_opportunities":{"_dlt_id":"_dlt_root_id"},"submissions":{"_dlt_id":"_dlt_root_id"}}}}}},"previous_hashes":["Ze6N3NbE1B7reRswjQaxqKsQCb0brwXgk/9nk6nyBkM=","uf0CuGV9MzBSfAoeUyyzMWNjFChzVTEPxt0YJ4yJExs=","4uTsDm0ZfWjpj4igxMXwwyDgyuNFwSRfcV7T6z6RVRw=","UvyLfXNOFpJw7lAY7kdOo0tvjN7mY2ctMTJKFkcKp6c=","ggA6NWSI+IJxDxR/TRFDL7ZUJeS8DaHBtw8yMah//t0=","IEeroXt9C83kuUSXk0UK9t0tYem+q595QqwSWa+/bfc=","e1ZGF//lZxGmI8hFvGQ19ekFPGy8ThnvASbEUP4hPk0=","Rrnd2OQofen4Ha5jPei/gWxYbR9HI6fwhT9WRNbVlB4=","7EIHexiIGLfsrqNB2X5TYTQJ8181N02y13Gbj8DO5uM=","Lwrd8V+0S1xbNeOyiq2auAW3Az6sWriZR3vlFUnLFQk="]}
16	11	2025-11-24 21:03:27.477886+00	reddit_harbor_problem_collection	oOqn9IwKatHf7VCRlELEy1nhpZL37tmsti+thh+OvtU=	{"version":16,"version_hash":"oOqn9IwKatHf7VCRlELEy1nhpZL37tmsti+thh+OvtU=","engine_version":11,"name":"reddit_harbor_problem_collection","tables":{"_dlt_version":{"name":"_dlt_version","columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_name":{"name":"schema_name","data_type":"text","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":false},"schema":{"name":"schema","data_type":"text","nullable":false}},"write_disposition":"skip","resource":"_dlt_version","description":"Created by DLT. Tracks schema updates"},"_dlt_loads":{"name":"_dlt_loads","columns":{"load_id":{"name":"load_id","data_type":"text","nullable":false,"precision":64},"schema_name":{"name":"schema_name","data_type":"text","nullable":true},"status":{"name":"status","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_version_hash":{"name":"schema_version_hash","data_type":"text","nullable":true}},"write_disposition":"skip","resource":"_dlt_loads","description":"Created by DLT. Tracks completed loads"},"workflow_results":{"columns":{"opportunity_id":{"data_type":"text","nullable":false,"unique":true,"name":"opportunity_id","primary_key":true},"app_name":{"data_type":"text","nullable":false,"name":"app_name"},"function_count":{"data_type":"bigint","nullable":false,"name":"function_count"},"function_list":{"data_type":"json","nullable":true,"name":"function_list"},"original_score":{"data_type":"double","nullable":false,"name":"original_score"},"final_score":{"data_type":"double","nullable":false,"name":"final_score"},"status":{"data_type":"text","nullable":false,"name":"status"},"constraint_applied":{"data_type":"bool","nullable":true,"name":"constraint_applied"},"ai_insight":{"data_type":"text","nullable":true,"name":"ai_insight"},"processed_at":{"data_type":"timestamp","nullable":true,"name":"processed_at"},"market_demand":{"data_type":"decimal","precision":5,"scale":2,"nullable":true,"name":"market_demand"},"pain_intensity":{"data_type":"decimal","precision":5,"scale":2,"nullable":true,"name":"pain_intensity"},"monetization_potential":{"data_type":"decimal","precision":5,"scale":2,"nullable":true,"name":"monetization_potential"},"market_gap":{"data_type":"decimal","precision":5,"scale":2,"nullable":true,"name":"market_gap"},"technical_feasibility":{"data_type":"decimal","precision":5,"scale":2,"nullable":true,"name":"technical_feasibility"},"core_functions":{"data_type":"bigint","nullable":true,"name":"core_functions"},"simplicity_score":{"data_type":"double","nullable":true,"name":"simplicity_score"},"is_disqualified":{"data_type":"bool","nullable":true,"name":"is_disqualified"},"constraint_version":{"data_type":"bigint","nullable":true,"name":"constraint_version"},"validation_timestamp":{"data_type":"timestamp","nullable":true,"name":"validation_timestamp"},"violation_reason":{"data_type":"text","nullable":true,"name":"violation_reason"},"validation_status":{"data_type":"text","nullable":true,"name":"validation_status"},"submission_id":{"name":"submission_id","data_type":"text","nullable":true},"problem_description":{"name":"problem_description","data_type":"text","nullable":true},"app_concept":{"name":"app_concept","data_type":"text","nullable":true},"value_proposition":{"name":"value_proposition","data_type":"text","nullable":true},"target_user":{"name":"target_user","data_type":"text","nullable":true},"monetization_model":{"name":"monetization_model","data_type":"text","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true},"trust_score":{"name":"trust_score","data_type":"double","nullable":true},"trust_badge":{"name":"trust_badge","data_type":"text","nullable":true},"activity_score":{"name":"activity_score","data_type":"double","nullable":true},"subreddit":{"name":"subreddit","data_type":"text","nullable":true},"llm_provider":{"name":"llm_provider","data_type":"text","nullable":true},"llm_prompt_tokens":{"name":"llm_prompt_tokens","data_type":"bigint","nullable":true},"llm_completion_tokens":{"name":"llm_completion_tokens","data_type":"bigint","nullable":true},"llm_total_tokens":{"name":"llm_total_tokens","data_type":"bigint","nullable":true},"llm_input_cost_usd":{"name":"llm_input_cost_usd","data_type":"double","nullable":true},"llm_output_cost_usd":{"name":"llm_output_cost_usd","data_type":"double","nullable":true},"llm_total_cost_usd":{"name":"llm_total_cost_usd","data_type":"double","nullable":true},"llm_latency_seconds":{"name":"llm_latency_seconds","data_type":"double","nullable":true},"cost_tracking_enabled":{"name":"cost_tracking_enabled","data_type":"bool","nullable":true},"llm_model_used":{"name":"llm_model_used","nullable":true,"data_type":"text"},"llm_timestamp":{"name":"llm_timestamp","nullable":true,"data_type":"timestamp"},"llm_pricing_info__input":{"name":"llm_pricing_info__input","data_type":"double","nullable":true},"llm_pricing_info__output":{"name":"llm_pricing_info__output","data_type":"double","nullable":true}},"write_disposition":"merge","name":"workflow_results","resource":"app_opportunities_with_constraint","x-normalizer":{"seen-data":true}},"_dlt_pipeline_state":{"columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"pipeline_name":{"name":"pipeline_name","data_type":"text","nullable":false},"state":{"name":"state","data_type":"text","nullable":false},"created_at":{"name":"created_at","data_type":"timestamp","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false,"precision":64},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"append","file_format":"preferred","name":"_dlt_pipeline_state","resource":"_dlt_pipeline_state","x-normalizer":{"seen-data":true}},"app_opportunities_trust":{"columns":{"submission_id":{"name":"submission_id","nullable":false,"primary_key":true,"data_type":"text"},"problem_description":{"name":"problem_description","data_type":"text","nullable":true},"app_concept":{"name":"app_concept","data_type":"text","nullable":true},"core_functions":{"name":"core_functions","data_type":"text","nullable":true},"value_proposition":{"name":"value_proposition","data_type":"text","nullable":true},"target_user":{"name":"target_user","data_type":"text","nullable":true},"monetization_model":{"name":"monetization_model","data_type":"text","nullable":true},"opportunity_score":{"name":"opportunity_score","data_type":"double","nullable":true},"title":{"name":"title","data_type":"text","nullable":true},"status":{"name":"status","data_type":"text","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true},"trust_score":{"name":"trust_score","data_type":"double","nullable":true},"trust_badge":{"name":"trust_badge","data_type":"text","nullable":true},"activity_score":{"name":"activity_score","data_type":"double","nullable":true},"engagement_level":{"name":"engagement_level","data_type":"text","nullable":true},"trust_level":{"name":"trust_level","data_type":"text","nullable":true},"trend_velocity":{"name":"trend_velocity","data_type":"bigint","nullable":true},"problem_validity":{"name":"problem_validity","data_type":"text","nullable":true},"discussion_quality":{"name":"discussion_quality","data_type":"text","nullable":true},"ai_confidence_level":{"name":"ai_confidence_level","data_type":"text","nullable":true},"trust_validation_timestamp":{"name":"trust_validation_timestamp","data_type":"double","nullable":true},"trust_validation_method":{"name":"trust_validation_method","data_type":"text","nullable":true},"subreddit":{"name":"subreddit","data_type":"text","nullable":true},"reddit_score":{"name":"reddit_score","data_type":"bigint","nullable":true},"num_comments":{"name":"num_comments","data_type":"bigint","nullable":true}},"write_disposition":"merge","name":"app_opportunities_trust","resource":"app_opportunities_trust","x-normalizer":{"seen-data":true}},"opportunity_analysis":{"columns":{"submission_id":{"name":"submission_id","nullable":false,"primary_key":true,"data_type":"text"},"opportunity_id":{"name":"opportunity_id","data_type":"text","nullable":true},"title":{"name":"title","data_type":"text","nullable":true},"subreddit":{"name":"subreddit","data_type":"text","nullable":true},"sector":{"name":"sector","data_type":"text","nullable":true},"market_demand":{"name":"market_demand","data_type":"bigint","nullable":true},"pain_intensity":{"name":"pain_intensity","data_type":"bigint","nullable":true},"monetization_potential":{"name":"monetization_potential","data_type":"bigint","nullable":true},"market_gap":{"name":"market_gap","data_type":"bigint","nullable":true},"technical_feasibility":{"name":"technical_feasibility","data_type":"bigint","nullable":true},"simplicity_score":{"name":"simplicity_score","data_type":"double","nullable":true},"final_score":{"name":"final_score","data_type":"bigint","nullable":true},"priority":{"name":"priority","data_type":"text","nullable":true},"app_concept":{"name":"app_concept","data_type":"text","nullable":true},"core_functions":{"name":"core_functions","data_type":"text","nullable":true},"growth_justification":{"name":"growth_justification","data_type":"text","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"merge","name":"opportunity_analysis","resource":"opportunity_analysis","x-normalizer":{"seen-data":true}},"app_opportunities":{"columns":{"submission_id":{"name":"submission_id","nullable":false,"primary_key":true,"data_type":"text"},"problem_description":{"name":"problem_description","data_type":"text","nullable":true},"app_concept":{"name":"app_concept","data_type":"text","nullable":true},"core_functions":{"name":"core_functions","data_type":"text","nullable":true},"value_proposition":{"name":"value_proposition","data_type":"text","nullable":true},"target_user":{"name":"target_user","data_type":"text","nullable":true},"monetization_model":{"name":"monetization_model","data_type":"text","nullable":true},"opportunity_score":{"name":"opportunity_score","data_type":"double","nullable":true},"title":{"name":"title","data_type":"text","nullable":true},"status":{"name":"status","data_type":"text","nullable":true},"trust_score":{"name":"trust_score","data_type":"double","nullable":true},"trust_badge":{"name":"trust_badge","data_type":"text","nullable":true},"activity_score":{"name":"activity_score","data_type":"bigint","nullable":true},"engagement_level":{"name":"engagement_level","data_type":"text","nullable":true},"trust_level":{"name":"trust_level","data_type":"text","nullable":true},"trend_velocity":{"name":"trend_velocity","data_type":"bigint","nullable":true},"problem_validity":{"name":"problem_validity","data_type":"text","nullable":true},"discussion_quality":{"name":"discussion_quality","data_type":"text","nullable":true},"ai_confidence_level":{"name":"ai_confidence_level","data_type":"text","nullable":true},"trust_validation_timestamp":{"name":"trust_validation_timestamp","data_type":"double","nullable":true},"trust_validation_method":{"name":"trust_validation_method","data_type":"text","nullable":true},"subreddit":{"name":"subreddit","data_type":"text","nullable":true},"reddit_score":{"name":"reddit_score","data_type":"bigint","nullable":true},"num_comments":{"name":"num_comments","data_type":"bigint","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"merge","name":"app_opportunities","resource":"app_opportunities","x-normalizer":{"seen-data":true}},"submissions":{"columns":{"submission_id":{"data_type":"text","nullable":true,"unique":true,"name":"submission_id","primary_key":true},"reddit_id":{"data_type":"text","nullable":false,"name":"reddit_id"},"title":{"data_type":"text","nullable":false,"name":"title"},"text":{"data_type":"text","nullable":true,"name":"text"},"content":{"data_type":"text","nullable":true,"name":"content"},"subreddit":{"data_type":"text","nullable":true,"name":"subreddit"},"upvotes":{"data_type":"bigint","nullable":true,"name":"upvotes"},"comments_count":{"data_type":"bigint","nullable":true,"name":"comments_count"},"url":{"data_type":"text","nullable":true,"name":"url"},"created_at":{"data_type":"timestamp","nullable":true,"name":"created_at"},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true},"id":{"data_type":"text","nullable":true,"unique":true,"name":"id","primary_key":true},"score":{"data_type":"bigint","nullable":true,"name":"score"},"num_comments":{"data_type":"bigint","nullable":true,"name":"num_comments"}},"write_disposition":"merge","name":"submissions","resource":"submissions","x-normalizer":{"seen-data":true}}},"settings":{"detections":["iso_timestamp"],"default_hints":{"not_null":["_dlt_id","_dlt_root_id","_dlt_parent_id","_dlt_list_idx","_dlt_load_id"],"parent_key":["_dlt_parent_id"],"root_key":["_dlt_root_id"],"unique":["_dlt_id"],"row_key":["_dlt_id"]}},"normalizers":{"names":"snake_case","json":{"module":"dlt.common.normalizers.json.relational","config":{"propagation":{"tables":{"workflow_results":{"_dlt_id":"_dlt_root_id"},"app_opportunities_trust":{"_dlt_id":"_dlt_root_id"},"opportunity_analysis":{"_dlt_id":"_dlt_root_id"},"app_opportunities":{"_dlt_id":"_dlt_root_id"},"submissions":{"_dlt_id":"_dlt_root_id"}}}}}},"previous_hashes":["NS4LPU4+tZlvO6LZkSMS3fknOeZhF6u9I8iK2Eth4yY=","Ze6N3NbE1B7reRswjQaxqKsQCb0brwXgk/9nk6nyBkM=","uf0CuGV9MzBSfAoeUyyzMWNjFChzVTEPxt0YJ4yJExs=","4uTsDm0ZfWjpj4igxMXwwyDgyuNFwSRfcV7T6z6RVRw=","UvyLfXNOFpJw7lAY7kdOo0tvjN7mY2ctMTJKFkcKp6c=","ggA6NWSI+IJxDxR/TRFDL7ZUJeS8DaHBtw8yMah//t0=","IEeroXt9C83kuUSXk0UK9t0tYem+q595QqwSWa+/bfc=","e1ZGF//lZxGmI8hFvGQ19ekFPGy8ThnvASbEUP4hPk0=","Rrnd2OQofen4Ha5jPei/gWxYbR9HI6fwhT9WRNbVlB4=","7EIHexiIGLfsrqNB2X5TYTQJ8181N02y13Gbj8DO5uM="]}
2	11	2025-11-24 21:17:49.682914+00	reddit_harbor_problem_collection	hDBzzYnadKBT/YMZePqnS7NbEcHd7SCPtG9ys2jMCDo=	{"version":2,"version_hash":"hDBzzYnadKBT/YMZePqnS7NbEcHd7SCPtG9ys2jMCDo=","engine_version":11,"name":"reddit_harbor_problem_collection","tables":{"_dlt_version":{"name":"_dlt_version","columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_name":{"name":"schema_name","data_type":"text","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":false},"schema":{"name":"schema","data_type":"text","nullable":false}},"write_disposition":"skip","resource":"_dlt_version","description":"Created by DLT. Tracks schema updates"},"_dlt_loads":{"name":"_dlt_loads","columns":{"load_id":{"name":"load_id","data_type":"text","nullable":false,"precision":64},"schema_name":{"name":"schema_name","data_type":"text","nullable":true},"status":{"name":"status","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_version_hash":{"name":"schema_version_hash","data_type":"text","nullable":true}},"write_disposition":"skip","resource":"_dlt_loads","description":"Created by DLT. Tracks completed loads"},"submissions":{"columns":{"id":{"data_type":"text","nullable":true,"unique":true,"name":"id","primary_key":true},"reddit_id":{"data_type":"text","nullable":false,"name":"reddit_id"},"title":{"data_type":"text","nullable":false,"name":"title"},"content":{"data_type":"text","nullable":true,"name":"content"},"url":{"data_type":"text","nullable":true,"name":"url"},"score":{"data_type":"bigint","nullable":true,"name":"score"},"num_comments":{"data_type":"bigint","nullable":true,"name":"num_comments"},"created_at":{"data_type":"timestamp","nullable":true,"name":"created_at"},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"merge","name":"submissions","resource":"submissions","x-normalizer":{"seen-data":true}},"_dlt_pipeline_state":{"columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"pipeline_name":{"name":"pipeline_name","data_type":"text","nullable":false},"state":{"name":"state","data_type":"text","nullable":false},"created_at":{"name":"created_at","data_type":"timestamp","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false,"precision":64},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"append","file_format":"preferred","name":"_dlt_pipeline_state","resource":"_dlt_pipeline_state","x-normalizer":{"seen-data":true}}},"settings":{"detections":["iso_timestamp"],"default_hints":{"not_null":["_dlt_id","_dlt_root_id","_dlt_parent_id","_dlt_list_idx","_dlt_load_id"],"parent_key":["_dlt_parent_id"],"root_key":["_dlt_root_id"],"unique":["_dlt_id"],"row_key":["_dlt_id"]}},"normalizers":{"names":"snake_case","json":{"module":"dlt.common.normalizers.json.relational","config":{"propagation":{"tables":{"submissions":{"_dlt_id":"_dlt_root_id"}}}}}},"previous_hashes":["lVlN6niPAJ26Yn5MRaeSW/KM+8034t2lkXlT6LDuwLY=","BRfhPSxTzoZLIYl2QVX+ToGT+l1nrZ8SMYwVo8StE3M="]}
2	11	2025-11-24 23:26:40.767262+00	app_opportunities_test_20251124_202640_loader	k3trREG7jTIGBhx2Wu9qRSsahChfj39gnnicgNrat5g=	{"version":2,"version_hash":"k3trREG7jTIGBhx2Wu9qRSsahChfj39gnnicgNrat5g=","engine_version":11,"name":"app_opportunities_test_20251124_202640_loader","tables":{"_dlt_version":{"name":"_dlt_version","columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_name":{"name":"schema_name","data_type":"text","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":false},"schema":{"name":"schema","data_type":"text","nullable":false}},"write_disposition":"skip","resource":"_dlt_version","description":"Created by DLT. Tracks schema updates"},"_dlt_loads":{"name":"_dlt_loads","columns":{"load_id":{"name":"load_id","data_type":"text","nullable":false,"precision":64},"schema_name":{"name":"schema_name","data_type":"text","nullable":true},"status":{"name":"status","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_version_hash":{"name":"schema_version_hash","data_type":"text","nullable":true}},"write_disposition":"skip","resource":"_dlt_loads","description":"Created by DLT. Tracks completed loads"},"app_opportunities_test_20251124_202640":{"columns":{"id":{"data_type":"text","nullable":false,"name":"id","primary_key":true},"problem_description":{"data_type":"text","name":"problem_description"},"app_concept":{"data_type":"text","name":"app_concept"},"core_functions":{"data_type":"json","name":"core_functions"},"value_proposition":{"data_type":"text","name":"value_proposition"},"target_user":{"data_type":"text","name":"target_user"},"monetization_model":{"data_type":"text","name":"monetization_model"},"opportunity_score":{"data_type":"double","name":"opportunity_score"},"final_score":{"data_type":"double","name":"final_score"},"status":{"data_type":"text","name":"status"},"title":{"data_type":"text","name":"title"},"subreddit":{"data_type":"text","name":"subreddit"},"reddit_score":{"data_type":"bigint","name":"reddit_score"},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"merge","name":"app_opportunities_test_20251124_202640","resource":"app_opportunities_test_20251124_202640","x-normalizer":{"seen-data":true}},"_dlt_pipeline_state":{"columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"pipeline_name":{"name":"pipeline_name","data_type":"text","nullable":false},"state":{"name":"state","data_type":"text","nullable":false},"created_at":{"name":"created_at","data_type":"timestamp","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false,"precision":64},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"append","file_format":"preferred","name":"_dlt_pipeline_state","resource":"_dlt_pipeline_state","x-normalizer":{"seen-data":true}}},"settings":{"detections":["iso_timestamp"],"default_hints":{"not_null":["_dlt_id","_dlt_root_id","_dlt_parent_id","_dlt_list_idx","_dlt_load_id"],"parent_key":["_dlt_parent_id"],"root_key":["_dlt_root_id"],"unique":["_dlt_id"],"row_key":["_dlt_id"]}},"normalizers":{"names":"snake_case","json":{"module":"dlt.common.normalizers.json.relational","config":{"propagation":{"tables":{"app_opportunities_test_20251124_202640":{"_dlt_id":"_dlt_root_id"}}}}}},"previous_hashes":["armngwyS8Ef0gZLNqqEelVwbQ/pb8gfC1nu1AYmfl4k=","B4mXWDktv2nBKSWmatKCXv7i9o2p+KDeEAqmDSPExYw="]}
2	11	2025-11-24 23:36:10.301626+00	app_opportunities_test_20251124_203609_loader	BQ95pMDguFCyoBTC4UeGoYttu3g/xBMjxFuXBrcEj1c=	{"version":2,"version_hash":"BQ95pMDguFCyoBTC4UeGoYttu3g/xBMjxFuXBrcEj1c=","engine_version":11,"name":"app_opportunities_test_20251124_203609_loader","tables":{"_dlt_version":{"name":"_dlt_version","columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_name":{"name":"schema_name","data_type":"text","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":false},"schema":{"name":"schema","data_type":"text","nullable":false}},"write_disposition":"skip","resource":"_dlt_version","description":"Created by DLT. Tracks schema updates"},"_dlt_loads":{"name":"_dlt_loads","columns":{"load_id":{"name":"load_id","data_type":"text","nullable":false,"precision":64},"schema_name":{"name":"schema_name","data_type":"text","nullable":true},"status":{"name":"status","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_version_hash":{"name":"schema_version_hash","data_type":"text","nullable":true}},"write_disposition":"skip","resource":"_dlt_loads","description":"Created by DLT. Tracks completed loads"},"app_opportunities_test_20251124_203609":{"columns":{"id":{"data_type":"text","nullable":false,"name":"id","primary_key":true},"problem_description":{"data_type":"text","name":"problem_description"},"app_concept":{"data_type":"text","name":"app_concept"},"core_functions":{"data_type":"json","name":"core_functions"},"value_proposition":{"data_type":"text","name":"value_proposition"},"target_user":{"data_type":"text","name":"target_user"},"monetization_model":{"data_type":"text","name":"monetization_model"},"opportunity_score":{"data_type":"double","name":"opportunity_score"},"final_score":{"data_type":"double","name":"final_score"},"status":{"data_type":"text","name":"status"},"title":{"data_type":"text","name":"title"},"subreddit":{"data_type":"text","name":"subreddit"},"reddit_score":{"data_type":"bigint","name":"reddit_score"},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"merge","name":"app_opportunities_test_20251124_203609","resource":"app_opportunities_test_20251124_203609","x-normalizer":{"seen-data":true}},"_dlt_pipeline_state":{"columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"pipeline_name":{"name":"pipeline_name","data_type":"text","nullable":false},"state":{"name":"state","data_type":"text","nullable":false},"created_at":{"name":"created_at","data_type":"timestamp","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false,"precision":64},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"append","file_format":"preferred","name":"_dlt_pipeline_state","resource":"_dlt_pipeline_state","x-normalizer":{"seen-data":true}}},"settings":{"detections":["iso_timestamp"],"default_hints":{"not_null":["_dlt_id","_dlt_root_id","_dlt_parent_id","_dlt_list_idx","_dlt_load_id"],"parent_key":["_dlt_parent_id"],"root_key":["_dlt_root_id"],"unique":["_dlt_id"],"row_key":["_dlt_id"]}},"normalizers":{"names":"snake_case","json":{"module":"dlt.common.normalizers.json.relational","config":{"propagation":{"tables":{"app_opportunities_test_20251124_203609":{"_dlt_id":"_dlt_root_id"}}}}}},"previous_hashes":["8hRzASr7WCP1v7byCD/ABIZ+eEV8fKF280a+19W9uW0=","D18J2nEX9XP46n+ilM0H21diDMg+djlunruBWpPLZuI="]}
2	11	2025-11-25 01:56:05.704968+00	reddit_harbor_problem_collection	iy5xTWOr3IvfT1it6NQxtcnkN9m3itA3IL+CMl6O47k=	{"version":2,"version_hash":"iy5xTWOr3IvfT1it6NQxtcnkN9m3itA3IL+CMl6O47k=","engine_version":11,"name":"reddit_harbor_problem_collection","tables":{"_dlt_version":{"name":"_dlt_version","columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_name":{"name":"schema_name","data_type":"text","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":false},"schema":{"name":"schema","data_type":"text","nullable":false}},"write_disposition":"skip","resource":"_dlt_version","description":"Created by DLT. Tracks schema updates"},"_dlt_loads":{"name":"_dlt_loads","columns":{"load_id":{"name":"load_id","data_type":"text","nullable":false,"precision":64},"schema_name":{"name":"schema_name","data_type":"text","nullable":true},"status":{"name":"status","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_version_hash":{"name":"schema_version_hash","data_type":"text","nullable":true}},"write_disposition":"skip","resource":"_dlt_loads","description":"Created by DLT. Tracks completed loads"},"submissions":{"columns":{"id":{"name":"id","nullable":false,"primary_key":true,"data_type":"text"},"reddit_id":{"name":"reddit_id","data_type":"text","nullable":true},"title":{"name":"title","data_type":"text","nullable":true},"content":{"name":"content","data_type":"text","nullable":true},"url":{"name":"url","data_type":"text","nullable":true},"score":{"name":"score","data_type":"bigint","nullable":true},"num_comments":{"name":"num_comments","data_type":"bigint","nullable":true},"created_at":{"name":"created_at","data_type":"timestamp","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"merge","name":"submissions","resource":"submissions","x-normalizer":{"seen-data":true}},"_dlt_pipeline_state":{"columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"pipeline_name":{"name":"pipeline_name","data_type":"text","nullable":false},"state":{"name":"state","data_type":"text","nullable":false},"created_at":{"name":"created_at","data_type":"timestamp","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false,"precision":64},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"append","file_format":"preferred","name":"_dlt_pipeline_state","resource":"_dlt_pipeline_state","x-normalizer":{"seen-data":true}}},"settings":{"detections":["iso_timestamp"],"default_hints":{"not_null":["_dlt_id","_dlt_root_id","_dlt_parent_id","_dlt_list_idx","_dlt_load_id"],"parent_key":["_dlt_parent_id"],"root_key":["_dlt_root_id"],"unique":["_dlt_id"],"row_key":["_dlt_id"]}},"normalizers":{"names":"snake_case","json":{"module":"dlt.common.normalizers.json.relational","config":{"propagation":{"tables":{"submissions":{"_dlt_id":"_dlt_root_id"}}}}}},"previous_hashes":["0yPRmG+YH6nqe24+F3bC+Nq9dJsj93bgHTmhDEHegIE=","ofb+bmHW4D62+SmF78gXDTs/P+87JqbWPGTmz5oVXCA="]}
2	11	2025-11-25 21:58:00.261872+00	submissions_loader	B4/GpSpGzR9FoHBhQ2tZuMnya+lHvK7dJJt1IaCBb40=	{"version":2,"version_hash":"B4/GpSpGzR9FoHBhQ2tZuMnya+lHvK7dJJt1IaCBb40=","engine_version":11,"name":"submissions_loader","tables":{"_dlt_version":{"name":"_dlt_version","columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_name":{"name":"schema_name","data_type":"text","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":false},"schema":{"name":"schema","data_type":"text","nullable":false}},"write_disposition":"skip","resource":"_dlt_version","description":"Created by DLT. Tracks schema updates"},"_dlt_loads":{"name":"_dlt_loads","columns":{"load_id":{"name":"load_id","data_type":"text","nullable":false,"precision":64},"schema_name":{"name":"schema_name","data_type":"text","nullable":true},"status":{"name":"status","data_type":"bigint","nullable":false},"inserted_at":{"name":"inserted_at","data_type":"timestamp","nullable":false},"schema_version_hash":{"name":"schema_version_hash","data_type":"text","nullable":true}},"write_disposition":"skip","resource":"_dlt_loads","description":"Created by DLT. Tracks completed loads"},"submissions":{"columns":{"submission_id":{"name":"submission_id","nullable":false,"primary_key":true,"data_type":"text"},"reddit_id":{"name":"reddit_id","data_type":"text","nullable":true},"title":{"name":"title","data_type":"text","nullable":true},"selftext":{"name":"selftext","nullable":true,"x-normalizer":{"seen-null-first":true}},"author":{"name":"author","nullable":true,"x-normalizer":{"seen-null-first":true}},"subreddit":{"name":"subreddit","data_type":"text","nullable":true},"trust_score":{"name":"trust_score","nullable":true,"x-normalizer":{"seen-null-first":true}},"trust_level":{"name":"trust_level","nullable":true,"x-normalizer":{"seen-null-first":true}},"market_validation_score":{"name":"market_validation_score","nullable":true,"x-normalizer":{"seen-null-first":true}},"opportunity_score":{"name":"opportunity_score","nullable":true,"x-normalizer":{"seen-null-first":true}},"created_utc":{"name":"created_utc","data_type":"timestamp","nullable":true},"reddit_score":{"name":"reddit_score","nullable":true,"x-normalizer":{"seen-null-first":true}},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"merge","name":"submissions","resource":"submissions","x-normalizer":{"seen-data":true}},"_dlt_pipeline_state":{"columns":{"version":{"name":"version","data_type":"bigint","nullable":false},"engine_version":{"name":"engine_version","data_type":"bigint","nullable":false},"pipeline_name":{"name":"pipeline_name","data_type":"text","nullable":false},"state":{"name":"state","data_type":"text","nullable":false},"created_at":{"name":"created_at","data_type":"timestamp","nullable":false},"version_hash":{"name":"version_hash","data_type":"text","nullable":true},"_dlt_load_id":{"name":"_dlt_load_id","data_type":"text","nullable":false,"precision":64},"_dlt_id":{"name":"_dlt_id","data_type":"text","nullable":false,"unique":true,"row_key":true}},"write_disposition":"append","file_format":"preferred","name":"_dlt_pipeline_state","resource":"_dlt_pipeline_state","x-normalizer":{"seen-data":true}}},"settings":{"detections":["iso_timestamp"],"default_hints":{"not_null":["_dlt_id","_dlt_root_id","_dlt_parent_id","_dlt_list_idx","_dlt_load_id"],"parent_key":["_dlt_parent_id"],"root_key":["_dlt_root_id"],"unique":["_dlt_id"],"row_key":["_dlt_id"]}},"normalizers":{"names":"snake_case","json":{"module":"dlt.common.normalizers.json.relational","config":{"propagation":{"tables":{"submissions":{"_dlt_id":"_dlt_root_id"}}}}}},"previous_hashes":["q7WyAM1Y6iTT+/mssTH//AV8mVQK214ii+QjV05t2c4=","lU73DOREC2HYbaTZqFYKuBPvNzkEBK8uOu53qIxaMiQ="]}
\.


--
-- Data for Name: app_opportunities; Type: TABLE DATA; Schema: public_staging; Owner: postgres
--

COPY public_staging.app_opportunities (submission_id, problem_description, app_concept, value_proposition, target_user, monetization_model, opportunity_score, title, subreddit, reddit_score, status, _dlt_load_id, _dlt_id, final_score, app_name, dimension_scores__market_demand, dimension_scores__pain_intensity, dimension_scores__monetization_potential, dimension_scores__market_gap, dimension_scores__technical_feasibility, dimension_scores__simplicity_score, priority, confidence, evidence_based, trust_level, enrichment_version, pipeline_source, market_validation_score, ai_profile__analysis_summary__app_name, ai_profile__analysis_summary__app_category, ai_profile__analysis_summary__target_profession, ai_profile__analysis_summary__core_problem_solved, ai_profile__analysis_summary__unique_value_prop, ai_profile__analysis_summary__primary_target_user, ai_profile__analysis_summary__monetization_approach, ai_profile__technical_feasibility__estimated_complexity, ai_profile__technical_feasibility__core_function_count, ai_profile__market_analysis__target_market_segment, ai_profile__market_analysis__app_category, ai_profile__market_analysis__evidence_based, ai_profile__market_analysis__opportunity_score, ai_profile__generation_metadata__model_used, ai_profile__generation_metadata__analysis_timestamp, ai_profile__generation_metadata__evidence_available, ai_profile__generation_metadata__cost_tracking__model_used, ai_profile__generation_metadata__cost_tracking__provider, ai_profile__generation_metadata__cost_tracking__prompt_tokens, ai_profile__generation_metadagfa09q_tracking__completion_tokens, ai_profile__generation_metadata__cost_tracking__total_tokens, ai_profile__generation_metadata__cost_tracking__input_cost_usd, ai_profile__generation_metadata__cost_tracking__output_cost_usd, ai_profile__generation_metadata__cost_tracking__total_cost_usd, ai_profile__generation_metadata__cost_tracking__latency_seconds, ai_profile__generation_metadapa0rsgracking__prompt_length_chars, ai_profile__generation_metadata__cost_tracking__timestamp, ai_profile__generation_metadaovvxfg_pricing_per_m_tokens__input, ai_profile__generation_metadai9kwcgpricing_per_m_tokens__output, app_category, profession, monetization_score, core_functions, ai_profile, core_problems, dimension_scores, trust_badges, analyzed_at, trust_score, trust_badge, activity_score) FROM stdin;
b6acaeb8-f79c-4b23-bb70-49788d9b3bc9	Testing if nested objects stay nested	Validation tool	Testing DLT schema is clean	Developers	Free	0.75	Test Post Title	test_subreddit	\N	test	1763946993.1489778	U8qE6EX7awb/Zg	0.8	Test App Schema Validation	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	["test", "function", "list"]	{"array_field": [1, 2, 3], "nested_field_1": "value1", "nested_field_2": {"deeply_nested": "value2"}}	\N	\N	\N	2025-11-24 01:16:32.67978+00	\N	\N	\N
\.


--
-- Data for Name: app_opportunities__ai_profile6devwwfeasibility__target_problems; Type: TABLE DATA; Schema: public_staging; Owner: postgres
--

COPY public_staging.app_opportunities__ai_profile6devwwfeasibility__target_problems (value, _dlt_root_id, _dlt_parent_id, _dlt_list_idx, _dlt_id) FROM stdin;
\.


--
-- Data for Name: app_opportunities__ai_profile__technical_feasibility__functions; Type: TABLE DATA; Schema: public_staging; Owner: postgres
--

COPY public_staging.app_opportunities__ai_profile__technical_feasibility__functions (value, _dlt_root_id, _dlt_parent_id, _dlt_list_idx, _dlt_id) FROM stdin;
\.


--
-- Data for Name: app_opportunities__core_functions; Type: TABLE DATA; Schema: public_staging; Owner: postgres
--

COPY public_staging.app_opportunities__core_functions (value, _dlt_root_id, _dlt_parent_id, _dlt_list_idx, _dlt_id) FROM stdin;
\.


--
-- Data for Name: app_opportunities__core_problems; Type: TABLE DATA; Schema: public_staging; Owner: postgres
--

COPY public_staging.app_opportunities__core_problems (value, _dlt_root_id, _dlt_parent_id, _dlt_list_idx, _dlt_id) FROM stdin;
\.


--
-- Data for Name: app_opportunities__trust_badges; Type: TABLE DATA; Schema: public_staging; Owner: postgres
--

COPY public_staging.app_opportunities__trust_badges (value, _dlt_root_id, _dlt_parent_id, _dlt_list_idx, _dlt_id) FROM stdin;
\.


--
-- Data for Name: app_opportunities_test_20251124_202640; Type: TABLE DATA; Schema: public_staging; Owner: postgres
--

COPY public_staging.app_opportunities_test_20251124_202640 (id, problem_description, app_concept, core_functions, value_proposition, target_user, monetization_model, opportunity_score, final_score, status, title, subreddit, reddit_score, _dlt_load_id, _dlt_id) FROM stdin;
test-001	Teams waste time managing multiple project tools	Integrated project management platform	["Task tracking", "Team collaboration"]	Save 10 hours per week with unified workflow	Small to medium teams	Subscription: $29/month per team	85.5	88.2	discovered	I struggle with managing my time effectively	productivity	156	1764026800.5946286	Oa6Rt/v5ZgSl6A
test-002	Manual data entry is frustrating	Automated data extraction platform	["OCR scanning", "Data validation"]	Reduce data entry time by 95%	Small business administrators	Per-document processing fee	78.3	81.7	discovered	This manual data entry is time consuming	productivity	89	1764026800.5946286	cSHdvdLCag236w
test-003	Looking for better startup workflow tools	Startup workflow orchestration platform	["Workflow templates", "Team collaboration"]	Accelerate startup development by 40%	Early-stage startup founders	Freemium with team features	92.1	94.8	validated	Better tools for startup workflow	entrepreneurship	124	1764026800.5946286	YKHrJJEBY3GzRQ
test-004	Need app to boost daily productivity	Personal productivity coach with habit tracking	["Habit formation", "Productivity analytics"]	Increase daily productivity by 30%	Students and professionals	Premium subscription	76.8	79.4	discovered	App to boost daily productivity	productivity	67	1764026800.5946286	iAP1LYO8e/nUgw
test-005	Help organizing multiple side projects	Multi-project management dashboard	["Project overview", "Resource allocation"]	Effortlessly manage unlimited side projects	Side project creators and solopreneurs	Tiered pricing based on project count	88.7	91.3	validated	Need help organizing side projects	SideProject	203	1764026800.5946286	AiHLEKyV+eKKeA
\.


--
-- Data for Name: app_opportunities_test_20251124_203609; Type: TABLE DATA; Schema: public_staging; Owner: postgres
--

COPY public_staging.app_opportunities_test_20251124_203609 (id, problem_description, app_concept, core_functions, value_proposition, target_user, monetization_model, opportunity_score, final_score, status, title, subreddit, reddit_score, _dlt_load_id, _dlt_id) FROM stdin;
test-001	Teams waste time managing multiple project tools	Integrated project management platform	["Task tracking", "Team collaboration"]	Save 10 hours per week with unified workflow	Small to medium teams	Subscription: $29/month per team	85.5	88.2	discovered	I struggle with managing my time effectively	productivity	156	1764027370.1243253	FgWbjimY/Jkegw
test-002	Manual data entry is frustrating	Automated data extraction platform	["OCR scanning", "Data validation"]	Reduce data entry time by 95%	Small business administrators	Per-document processing fee	78.3	81.7	discovered	This manual data entry is time consuming	productivity	89	1764027370.1243253	RbWPwJzSFY2zPg
test-003	Looking for better startup workflow tools	Startup workflow orchestration platform	["Workflow templates", "Team collaboration"]	Accelerate startup development by 40%	Early-stage startup founders	Freemium with team features	92.1	94.8	validated	Better tools for startup workflow	entrepreneurship	124	1764027370.1243253	c71R3P0/P8B1fg
test-004	Need app to boost daily productivity	Personal productivity coach with habit tracking	["Habit formation", "Productivity analytics"]	Increase daily productivity by 30%	Students and professionals	Premium subscription	76.8	79.4	discovered	App to boost daily productivity	productivity	67	1764027370.1243253	9Oa1a+oEDGzZ1Q
test-005	Help organizing multiple side projects	Multi-project management dashboard	["Project overview", "Resource allocation"]	Effortlessly manage unlimited side projects	Side project creators and solopreneurs	Tiered pricing based on project count	88.7	91.3	validated	Need help organizing side projects	SideProject	203	1764027370.1243253	6C45wRKoCD9+bg
\.


--
-- Data for Name: competitive_landscape; Type: TABLE DATA; Schema: public_staging; Owner: postgres
--

COPY public_staging.competitive_landscape (opportunity_id, competitor_name, competitor_features, competitive_analysis, market_share, pricing_model, target_market, source_url, confidence, extracted_at, created_at, _dlt_load_id, _dlt_id) FROM stdin;
d59d07ea-685d-4d0a-ad70-b8a33f0ebea8	Calendly	["Scheduling", "Timezone support"]		\N	unknown	unknown		0.5	2025-11-22 21:07:39.836101+00	2025-11-22 21:07:39.836105+00	1763845661.1364803	GiVvwF0+trudIw
d59d07ea-685d-4d0a-ad70-b8a33f0ebea8	World Time Buddy	["Timezone conversion", "Meeting planning"]		\N	unknown	unknown		0.5	2025-11-22 21:07:39.836112+00	2025-11-22 21:07:39.836116+00	1763845661.1364803	36ctwcgr/nOfrg
\.


--
-- Data for Name: market_validations; Type: TABLE DATA; Schema: public_staging; Owner: postgres
--

COPY public_staging.market_validations (opportunity_id, validation_type, validation_source, validation_date, validation_result, confidence_score, notes, status, evidence_url, market_validation_score, market_data_quality_score, market_validation_reasoning, market_competitors_found, market_size_tam, market_size_sam, market_size_growth, market_similar_launches, market_validation_cost_usd, search_queries_used, urls_fetched, extraction_stats, jina_api_calls_count, jina_cache_hit_rate, _dlt_load_id, _dlt_id) FROM stdin;
d59d07ea-685d-4d0a-ad70-b8a33f0ebea8	jina_reader_market_validation	ai_analysis	2025-11-22 21:07:39.836059+00	{"reasoning": "Several competing tools exist, validating market need", "competitor_count": 2, "validation_score": 85.0, "data_quality_score": 90.0, "market_size_estimate": 50000000.0, "validation_reasoning": "Market validation shows strong demand", "similar_launches_count": 15}	0.9	Several competing tools exist, validating market need	completed		85	90	Several competing tools exist, validating market need	[{"features": ["Scheduling", "Timezone support"], "company_name": "Calendly"}, {"features": ["Timezone conversion", "Meeting planning"], "company_name": "World Time Buddy"}]	50000000	\N	\N	15	0	[]	[]	{}	0	0	1763845660.7684696	BlqTRvYTPH698w
\.


--
-- Data for Name: monetization_patterns; Type: TABLE DATA; Schema: public_staging; Owner: postgres
--

COPY public_staging.monetization_patterns (opportunity_id, pattern_type, revenue_model, target_pricing, market_size, willingness_to_pay_score, customer_segment, price_sensitivity_score, revenue_potential_score, mentioned_price_points, existing_payment_behavior, urgency_level, sentiment_toward_payment, payment_friction_indicators, llm_monetization_score, confidence, reasoning, created_at, _dlt_load_id, _dlt_id) FROM stdin;
d59d07ea-685d-4d0a-ad70-b8a33f0ebea8	ai_analysis	unknown	\N	\N	75	B2B	60	80	["$10/month", "$100/year"]	Currently using free tools	medium	positive	[]	70	0.85	Teams actively need coordination tools	2025-11-22 21:07:39.836053+00	1763845660.3141646	XtOKrDQLsrj4/A
\.


--
-- Data for Name: opportunity_scores; Type: TABLE DATA; Schema: public_staging; Owner: postgres
--

COPY public_staging.opportunity_scores (opportunity_id, market_demand, pain_intensity, competition_level, technical_feasibility, monetization_potential, simplicity_score, total_score, created_at, updated_at, _dlt_load_id, _dlt_id) FROM stdin;
d59d07ea-685d-4d0a-ad70-b8a33f0ebea8	0.8	0.9	0.6	0.8	0.7	0.5	85.5	2025-11-22 21:07:39.836024+00	2025-11-22 21:07:39.836041+00	1763845659.9238393	rTzxAuyV7yW8RA
\.


--
-- Data for Name: submissions; Type: TABLE DATA; Schema: public_staging; Owner: postgres
--

COPY public_staging.submissions (submission_id, title, selftext, author, subreddit, trust_score, trust_level, market_validation_score, opportunity_score, created_utc, reddit_score, _dlt_load_id, _dlt_id, reddit_id, text, content, upvotes, comments_count, url, created_at, id, score, num_comments) FROM stdin;
\.


--
-- Data for Name: buckets; Type: TABLE DATA; Schema: storage; Owner: supabase_storage_admin
--

COPY storage.buckets (id, name, owner, created_at, updated_at, public, avif_autodetection, file_size_limit, allowed_mime_types, owner_id, type) FROM stdin;
company-logos	company-logos	\N	2025-08-31 16:16:40.3776+00	2025-08-31 16:16:40.3776+00	t	f	2097152	{image/png,image/jpeg,image/webp}	\N	STANDARD
\.


--
-- Data for Name: buckets_analytics; Type: TABLE DATA; Schema: storage; Owner: supabase_storage_admin
--

COPY storage.buckets_analytics (id, type, format, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: iceberg_namespaces; Type: TABLE DATA; Schema: storage; Owner: supabase_storage_admin
--

COPY storage.iceberg_namespaces (id, bucket_id, name, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: iceberg_tables; Type: TABLE DATA; Schema: storage; Owner: supabase_storage_admin
--

COPY storage.iceberg_tables (id, namespace_id, bucket_id, name, location, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: migrations; Type: TABLE DATA; Schema: storage; Owner: supabase_storage_admin
--

COPY storage.migrations (id, name, hash, executed_at) FROM stdin;
0	create-migrations-table	e18db593bcde2aca2a408c4d1100f6abba2195df	2025-08-31 16:12:42.805118
1	initialmigration	6ab16121fbaa08bbd11b712d05f358f9b555d777	2025-08-31 16:12:42.813967
2	storage-schema	5c7968fd083fcea04050c1b7f6253c9771b99011	2025-08-31 16:12:42.817904
3	pathtoken-column	2cb1b0004b817b29d5b0a971af16bafeede4b70d	2025-08-31 16:12:42.830221
4	add-migrations-rls	427c5b63fe1c5937495d9c635c263ee7a5905058	2025-08-31 16:12:42.854009
5	add-size-functions	79e081a1455b63666c1294a440f8ad4b1e6a7f84	2025-08-31 16:12:42.85812
6	change-column-name-in-get-size	f93f62afdf6613ee5e7e815b30d02dc990201044	2025-08-31 16:12:42.862611
7	add-rls-to-buckets	e7e7f86adbc51049f341dfe8d30256c1abca17aa	2025-08-31 16:12:42.866523
8	add-public-to-buckets	fd670db39ed65f9d08b01db09d6202503ca2bab3	2025-08-31 16:12:42.870242
9	fix-search-function	3a0af29f42e35a4d101c259ed955b67e1bee6825	2025-08-31 16:12:42.87457
10	search-files-search-function	68dc14822daad0ffac3746a502234f486182ef6e	2025-08-31 16:12:42.878794
11	add-trigger-to-auto-update-updated_at-column	7425bdb14366d1739fa8a18c83100636d74dcaa2	2025-08-31 16:12:42.883463
12	add-automatic-avif-detection-flag	8e92e1266eb29518b6a4c5313ab8f29dd0d08df9	2025-08-31 16:12:42.890354
13	add-bucket-custom-limits	cce962054138135cd9a8c4bcd531598684b25e7d	2025-08-31 16:12:42.894936
14	use-bytes-for-max-size	941c41b346f9802b411f06f30e972ad4744dad27	2025-08-31 16:12:42.899092
15	add-can-insert-object-function	934146bc38ead475f4ef4b555c524ee5d66799e5	2025-08-31 16:12:42.926872
16	add-version	76debf38d3fd07dcfc747ca49096457d95b1221b	2025-08-31 16:12:42.930932
17	drop-owner-foreign-key	f1cbb288f1b7a4c1eb8c38504b80ae2a0153d101	2025-08-31 16:12:42.935985
18	add_owner_id_column_deprecate_owner	e7a511b379110b08e2f214be852c35414749fe66	2025-08-31 16:12:42.940555
19	alter-default-value-objects-id	02e5e22a78626187e00d173dc45f58fa66a4f043	2025-08-31 16:12:42.945067
20	list-objects-with-delimiter	cd694ae708e51ba82bf012bba00caf4f3b6393b7	2025-08-31 16:12:42.949478
21	s3-multipart-uploads	8c804d4a566c40cd1e4cc5b3725a664a9303657f	2025-08-31 16:12:42.958644
22	s3-multipart-uploads-big-ints	9737dc258d2397953c9953d9b86920b8be0cdb73	2025-08-31 16:12:42.991507
23	optimize-search-function	9d7e604cddc4b56a5422dc68c9313f4a1b6f132c	2025-08-31 16:12:43.022653
24	operation-function	8312e37c2bf9e76bbe841aa5fda889206d2bf8aa	2025-08-31 16:12:43.02729
25	custom-metadata	d974c6057c3db1c1f847afa0e291e6165693b990	2025-08-31 16:12:43.032237
26	objects-prefixes	ef3f7871121cdc47a65308e6702519e853422ae2	2025-08-31 16:12:43.036169
27	search-v2	33b8f2a7ae53105f028e13e9fcda9dc4f356b4a2	2025-08-31 16:12:43.061311
28	object-bucket-name-sorting	ba85ec41b62c6a30a3f136788227ee47f311c436	2025-08-31 16:12:43.076929
29	create-prefixes	a7b1a22c0dc3ab630e3055bfec7ce7d2045c5b7b	2025-08-31 16:12:43.081803
30	update-object-levels	6c6f6cc9430d570f26284a24cf7b210599032db7	2025-08-31 16:12:43.08748
31	objects-level-index	33f1fef7ec7fea08bb892222f4f0f5d79bab5eb8	2025-08-31 16:12:43.102752
32	backward-compatible-index-on-objects	2d51eeb437a96868b36fcdfb1ddefdf13bef1647	2025-08-31 16:12:43.116063
33	backward-compatible-index-on-prefixes	fe473390e1b8c407434c0e470655945b110507bf	2025-08-31 16:12:43.130606
34	optimize-search-function-v1	82b0e469a00e8ebce495e29bfa70a0797f7ebd2c	2025-08-31 16:12:43.133277
35	add-insert-trigger-prefixes	63bb9fd05deb3dc5e9fa66c83e82b152f0caf589	2025-08-31 16:12:43.140616
36	optimise-existing-functions	81cf92eb0c36612865a18016a38496c530443899	2025-08-31 16:12:43.145144
37	add-bucket-name-length-trigger	3944135b4e3e8b22d6d4cbb568fe3b0b51df15c1	2025-08-31 16:12:43.152937
38	iceberg-catalog-flag-on-buckets	19a8bd89d5dfa69af7f222a46c726b7c41e462c5	2025-08-31 16:12:43.158219
\.


--
-- Data for Name: objects; Type: TABLE DATA; Schema: storage; Owner: supabase_storage_admin
--

COPY storage.objects (id, bucket_id, name, owner, created_at, updated_at, last_accessed_at, metadata, version, owner_id, user_metadata, level) FROM stdin;
\.


--
-- Data for Name: prefixes; Type: TABLE DATA; Schema: storage; Owner: supabase_storage_admin
--

COPY storage.prefixes (bucket_id, name, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: s3_multipart_uploads; Type: TABLE DATA; Schema: storage; Owner: supabase_storage_admin
--

COPY storage.s3_multipart_uploads (id, in_progress_size, upload_signature, bucket_id, key, version, owner_id, created_at, user_metadata) FROM stdin;
\.


--
-- Data for Name: s3_multipart_uploads_parts; Type: TABLE DATA; Schema: storage; Owner: supabase_storage_admin
--

COPY storage.s3_multipart_uploads_parts (id, upload_id, size, part_number, bucket_id, key, etag, owner_id, version, created_at) FROM stdin;
\.


--
-- Data for Name: hooks; Type: TABLE DATA; Schema: supabase_functions; Owner: supabase_functions_admin
--

COPY supabase_functions.hooks (id, hook_table_id, hook_name, created_at, request_id) FROM stdin;
\.


--
-- Data for Name: migrations; Type: TABLE DATA; Schema: supabase_functions; Owner: supabase_functions_admin
--

COPY supabase_functions.migrations (version, inserted_at) FROM stdin;
initial	2025-08-31 16:10:55.739729+00
20210809183423_update_grants	2025-08-31 16:10:55.739729+00
\.


--
-- Data for Name: secrets; Type: TABLE DATA; Schema: vault; Owner: supabase_admin
--

COPY vault.secrets (id, name, description, secret, key_id, nonce, created_at, updated_at) FROM stdin;
\.


--
-- Name: refresh_tokens_id_seq; Type: SEQUENCE SET; Schema: auth; Owner: supabase_auth_admin
--

SELECT pg_catalog.setval('auth.refresh_tokens_id_seq', 1, false);


--
-- Name: hooks_id_seq; Type: SEQUENCE SET; Schema: supabase_functions; Owner: supabase_functions_admin
--

SELECT pg_catalog.setval('supabase_functions.hooks_id_seq', 1, false);


--
-- Name: _dlt_pipeline_state _dlt_pipeline_state__dlt_id_key; Type: CONSTRAINT; Schema: app_opportunities; Owner: postgres
--

ALTER TABLE ONLY app_opportunities._dlt_pipeline_state
    ADD CONSTRAINT _dlt_pipeline_state__dlt_id_key UNIQUE (_dlt_id);


--
-- Name: app_opportunities app_opportunities__dlt_id_key; Type: CONSTRAINT; Schema: app_opportunities; Owner: postgres
--

ALTER TABLE ONLY app_opportunities.app_opportunities
    ADD CONSTRAINT app_opportunities__dlt_id_key UNIQUE (_dlt_id);


--
-- Name: app_opportunities app_opportunities__dlt_id_key; Type: CONSTRAINT; Schema: app_opportunities_staging; Owner: postgres
--

ALTER TABLE ONLY app_opportunities_staging.app_opportunities
    ADD CONSTRAINT app_opportunities__dlt_id_key UNIQUE (_dlt_id);


--
-- Name: mfa_amr_claims amr_id_pk; Type: CONSTRAINT; Schema: auth; Owner: supabase_auth_admin
--

ALTER TABLE ONLY auth.mfa_amr_claims
    ADD CONSTRAINT amr_id_pk PRIMARY KEY (id);


--
-- Name: audit_log_entries audit_log_entries_pkey; Type: CONSTRAINT; Schema: auth; Owner: supabase_auth_admin
--

ALTER TABLE ONLY auth.audit_log_entries
    ADD CONSTRAINT audit_log_entries_pkey PRIMARY KEY (id);


--
-- Name: flow_state flow_state_pkey; Type: CONSTRAINT; Schema: auth; Owner: supabase_auth_admin
--

ALTER TABLE ONLY auth.flow_state
    ADD CONSTRAINT flow_state_pkey PRIMARY KEY (id);


--
-- Name: identities identities_pkey; Type: CONSTRAINT; Schema: auth; Owner: supabase_auth_admin
--

ALTER TABLE ONLY auth.identities
    ADD CONSTRAINT identities_pkey PRIMARY KEY (id);


--
-- Name: identities identities_provider_id_provider_unique; Type: CONSTRAINT; Schema: auth; Owner: supabase_auth_admin
--

ALTER TABLE ONLY auth.identities
    ADD CONSTRAINT identities_provider_id_provider_unique UNIQUE (provider_id, provider);


--
-- Name: instances instances_pkey; Type: CONSTRAINT; Schema: auth; Owner: supabase_auth_admin
--

ALTER TABLE ONLY auth.instances
    ADD CONSTRAINT instances_pkey PRIMARY KEY (id);


--
-- Name: mfa_amr_claims mfa_amr_claims_session_id_authentication_method_pkey; Type: CONSTRAINT; Schema: auth; Owner: supabase_auth_admin
--

ALTER TABLE ONLY auth.mfa_amr_claims
    ADD CONSTRAINT mfa_amr_claims_session_id_authentication_method_pkey UNIQUE (session_id, authentication_method);


--
-- Name: mfa_challenges mfa_challenges_pkey; Type: CONSTRAINT; Schema: auth; Owner: supabase_auth_admin
--

ALTER TABLE ONLY auth.mfa_challenges
    ADD CONSTRAINT mfa_challenges_pkey PRIMARY KEY (id);


--
-- Name: mfa_factors mfa_factors_last_challenged_at_key; Type: CONSTRAINT; Schema: auth; Owner: supabase_auth_admin
--

ALTER TABLE ONLY auth.mfa_factors
    ADD CONSTRAINT mfa_factors_last_challenged_at_key UNIQUE (last_challenged_at);


--
-- Name: mfa_factors mfa_factors_pkey; Type: CONSTRAINT; Schema: auth; Owner: supabase_auth_admin
--

ALTER TABLE ONLY auth.mfa_factors
    ADD CONSTRAINT mfa_factors_pkey PRIMARY KEY (id);


--
-- Name: one_time_tokens one_time_tokens_pkey; Type: CONSTRAINT; Schema: auth; Owner: supabase_auth_admin
--

ALTER TABLE ONLY auth.one_time_tokens
    ADD CONSTRAINT one_time_tokens_pkey PRIMARY KEY (id);


--
-- Name: refresh_tokens refresh_tokens_pkey; Type: CONSTRAINT; Schema: auth; Owner: supabase_auth_admin
--

ALTER TABLE ONLY auth.refresh_tokens
    ADD CONSTRAINT refresh_tokens_pkey PRIMARY KEY (id);


--
-- Name: refresh_tokens refresh_tokens_token_unique; Type: CONSTRAINT; Schema: auth; Owner: supabase_auth_admin
--

ALTER TABLE ONLY auth.refresh_tokens
    ADD CONSTRAINT refresh_tokens_token_unique UNIQUE (token);


--
-- Name: saml_providers saml_providers_entity_id_key; Type: CONSTRAINT; Schema: auth; Owner: supabase_auth_admin
--

ALTER TABLE ONLY auth.saml_providers
    ADD CONSTRAINT saml_providers_entity_id_key UNIQUE (entity_id);


--
-- Name: saml_providers saml_providers_pkey; Type: CONSTRAINT; Schema: auth; Owner: supabase_auth_admin
--

ALTER TABLE ONLY auth.saml_providers
    ADD CONSTRAINT saml_providers_pkey PRIMARY KEY (id);


--
-- Name: saml_relay_states saml_relay_states_pkey; Type: CONSTRAINT; Schema: auth; Owner: supabase_auth_admin
--

ALTER TABLE ONLY auth.saml_relay_states
    ADD CONSTRAINT saml_relay_states_pkey PRIMARY KEY (id);


--
-- Name: schema_migrations schema_migrations_pkey; Type: CONSTRAINT; Schema: auth; Owner: supabase_auth_admin
--

ALTER TABLE ONLY auth.schema_migrations
    ADD CONSTRAINT schema_migrations_pkey PRIMARY KEY (version);


--
-- Name: sessions sessions_pkey; Type: CONSTRAINT; Schema: auth; Owner: supabase_auth_admin
--

ALTER TABLE ONLY auth.sessions
    ADD CONSTRAINT sessions_pkey PRIMARY KEY (id);


--
-- Name: sso_domains sso_domains_pkey; Type: CONSTRAINT; Schema: auth; Owner: supabase_auth_admin
--

ALTER TABLE ONLY auth.sso_domains
    ADD CONSTRAINT sso_domains_pkey PRIMARY KEY (id);


--
-- Name: sso_providers sso_providers_pkey; Type: CONSTRAINT; Schema: auth; Owner: supabase_auth_admin
--

ALTER TABLE ONLY auth.sso_providers
    ADD CONSTRAINT sso_providers_pkey PRIMARY KEY (id);


--
-- Name: users users_phone_key; Type: CONSTRAINT; Schema: auth; Owner: supabase_auth_admin
--

ALTER TABLE ONLY auth.users
    ADD CONSTRAINT users_phone_key UNIQUE (phone);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: auth; Owner: supabase_auth_admin
--

ALTER TABLE ONLY auth.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: _dlt_pipeline_state _dlt_pipeline_state__dlt_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public._dlt_pipeline_state
    ADD CONSTRAINT _dlt_pipeline_state__dlt_id_key UNIQUE (_dlt_id);


--
-- Name: app_opportunities app_opportunities__dlt_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.app_opportunities
    ADD CONSTRAINT app_opportunities__dlt_id_key UNIQUE (_dlt_id);


--
-- Name: app_opportunities_test_20251124_202640 app_opportunities_test_20251124_202640__dlt_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.app_opportunities_test_20251124_202640
    ADD CONSTRAINT app_opportunities_test_20251124_202640__dlt_id_key UNIQUE (_dlt_id);


--
-- Name: app_opportunities_test_20251124_203609 app_opportunities_test_20251124_203609__dlt_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.app_opportunities_test_20251124_203609
    ADD CONSTRAINT app_opportunities_test_20251124_203609__dlt_id_key UNIQUE (_dlt_id);


--
-- Name: app_opportunities_test app_opportunities_test__dlt_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.app_opportunities_test
    ADD CONSTRAINT app_opportunities_test__dlt_id_key UNIQUE (_dlt_id);


--
-- Name: competitive_landscape competitive_landscape__dlt_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.competitive_landscape
    ADD CONSTRAINT competitive_landscape__dlt_id_key UNIQUE (_dlt_id);


--
-- Name: market_validations market_validations__dlt_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.market_validations
    ADD CONSTRAINT market_validations__dlt_id_key UNIQUE (_dlt_id);


--
-- Name: monetization_patterns monetization_patterns__dlt_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.monetization_patterns
    ADD CONSTRAINT monetization_patterns__dlt_id_key UNIQUE (_dlt_id);


--
-- Name: opportunities opportunities__dlt_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.opportunities
    ADD CONSTRAINT opportunities__dlt_id_key UNIQUE (_dlt_id);


--
-- Name: opportunities_test_02_scaled opportunities_test_02_scaled__dlt_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.opportunities_test_02_scaled
    ADD CONSTRAINT opportunities_test_02_scaled__dlt_id_key UNIQUE (_dlt_id);


--
-- Name: opportunity_scores opportunity_scores__dlt_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.opportunity_scores
    ADD CONSTRAINT opportunity_scores__dlt_id_key UNIQUE (_dlt_id);


--
-- Name: submissions submissions__dlt_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.submissions
    ADD CONSTRAINT submissions__dlt_id_key UNIQUE (_dlt_id);


--
-- Name: submissions submissions_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.submissions
    ADD CONSTRAINT submissions_id_key UNIQUE (id);


--
-- Name: app_opportunities__ai_profile6devwwfeasibility__target_problems app_opportunities__ai_profile6devwwfeasibility__tar__dlt_id_key; Type: CONSTRAINT; Schema: public_staging; Owner: postgres
--

ALTER TABLE ONLY public_staging.app_opportunities__ai_profile6devwwfeasibility__target_problems
    ADD CONSTRAINT app_opportunities__ai_profile6devwwfeasibility__tar__dlt_id_key UNIQUE (_dlt_id);


--
-- Name: app_opportunities__ai_profile__technical_feasibility__functions app_opportunities__ai_profile__technical_feasibilit__dlt_id_key; Type: CONSTRAINT; Schema: public_staging; Owner: postgres
--

ALTER TABLE ONLY public_staging.app_opportunities__ai_profile__technical_feasibility__functions
    ADD CONSTRAINT app_opportunities__ai_profile__technical_feasibilit__dlt_id_key UNIQUE (_dlt_id);


--
-- Name: app_opportunities__core_functions app_opportunities__core_functions__dlt_id_key; Type: CONSTRAINT; Schema: public_staging; Owner: postgres
--

ALTER TABLE ONLY public_staging.app_opportunities__core_functions
    ADD CONSTRAINT app_opportunities__core_functions__dlt_id_key UNIQUE (_dlt_id);


--
-- Name: app_opportunities__core_problems app_opportunities__core_problems__dlt_id_key; Type: CONSTRAINT; Schema: public_staging; Owner: postgres
--

ALTER TABLE ONLY public_staging.app_opportunities__core_problems
    ADD CONSTRAINT app_opportunities__core_problems__dlt_id_key UNIQUE (_dlt_id);


--
-- Name: app_opportunities app_opportunities__dlt_id_key; Type: CONSTRAINT; Schema: public_staging; Owner: postgres
--

ALTER TABLE ONLY public_staging.app_opportunities
    ADD CONSTRAINT app_opportunities__dlt_id_key UNIQUE (_dlt_id);


--
-- Name: app_opportunities__trust_badges app_opportunities__trust_badges__dlt_id_key; Type: CONSTRAINT; Schema: public_staging; Owner: postgres
--

ALTER TABLE ONLY public_staging.app_opportunities__trust_badges
    ADD CONSTRAINT app_opportunities__trust_badges__dlt_id_key UNIQUE (_dlt_id);


--
-- Name: app_opportunities_test_20251124_202640 app_opportunities_test_20251124_202640__dlt_id_key; Type: CONSTRAINT; Schema: public_staging; Owner: postgres
--

ALTER TABLE ONLY public_staging.app_opportunities_test_20251124_202640
    ADD CONSTRAINT app_opportunities_test_20251124_202640__dlt_id_key UNIQUE (_dlt_id);


--
-- Name: app_opportunities_test_20251124_203609 app_opportunities_test_20251124_203609__dlt_id_key; Type: CONSTRAINT; Schema: public_staging; Owner: postgres
--

ALTER TABLE ONLY public_staging.app_opportunities_test_20251124_203609
    ADD CONSTRAINT app_opportunities_test_20251124_203609__dlt_id_key UNIQUE (_dlt_id);


--
-- Name: competitive_landscape competitive_landscape__dlt_id_key; Type: CONSTRAINT; Schema: public_staging; Owner: postgres
--

ALTER TABLE ONLY public_staging.competitive_landscape
    ADD CONSTRAINT competitive_landscape__dlt_id_key UNIQUE (_dlt_id);


--
-- Name: market_validations market_validations__dlt_id_key; Type: CONSTRAINT; Schema: public_staging; Owner: postgres
--

ALTER TABLE ONLY public_staging.market_validations
    ADD CONSTRAINT market_validations__dlt_id_key UNIQUE (_dlt_id);


--
-- Name: monetization_patterns monetization_patterns__dlt_id_key; Type: CONSTRAINT; Schema: public_staging; Owner: postgres
--

ALTER TABLE ONLY public_staging.monetization_patterns
    ADD CONSTRAINT monetization_patterns__dlt_id_key UNIQUE (_dlt_id);


--
-- Name: opportunity_scores opportunity_scores__dlt_id_key; Type: CONSTRAINT; Schema: public_staging; Owner: postgres
--

ALTER TABLE ONLY public_staging.opportunity_scores
    ADD CONSTRAINT opportunity_scores__dlt_id_key UNIQUE (_dlt_id);


--
-- Name: submissions submissions__dlt_id_key; Type: CONSTRAINT; Schema: public_staging; Owner: postgres
--

ALTER TABLE ONLY public_staging.submissions
    ADD CONSTRAINT submissions__dlt_id_key UNIQUE (_dlt_id);


--
-- Name: submissions submissions_id_key; Type: CONSTRAINT; Schema: public_staging; Owner: postgres
--

ALTER TABLE ONLY public_staging.submissions
    ADD CONSTRAINT submissions_id_key UNIQUE (id);


--
-- Name: buckets_analytics buckets_analytics_pkey; Type: CONSTRAINT; Schema: storage; Owner: supabase_storage_admin
--

ALTER TABLE ONLY storage.buckets_analytics
    ADD CONSTRAINT buckets_analytics_pkey PRIMARY KEY (id);


--
-- Name: buckets buckets_pkey; Type: CONSTRAINT; Schema: storage; Owner: supabase_storage_admin
--

ALTER TABLE ONLY storage.buckets
    ADD CONSTRAINT buckets_pkey PRIMARY KEY (id);


--
-- Name: iceberg_namespaces iceberg_namespaces_pkey; Type: CONSTRAINT; Schema: storage; Owner: supabase_storage_admin
--

ALTER TABLE ONLY storage.iceberg_namespaces
    ADD CONSTRAINT iceberg_namespaces_pkey PRIMARY KEY (id);


--
-- Name: iceberg_tables iceberg_tables_pkey; Type: CONSTRAINT; Schema: storage; Owner: supabase_storage_admin
--

ALTER TABLE ONLY storage.iceberg_tables
    ADD CONSTRAINT iceberg_tables_pkey PRIMARY KEY (id);


--
-- Name: migrations migrations_name_key; Type: CONSTRAINT; Schema: storage; Owner: supabase_storage_admin
--

ALTER TABLE ONLY storage.migrations
    ADD CONSTRAINT migrations_name_key UNIQUE (name);


--
-- Name: migrations migrations_pkey; Type: CONSTRAINT; Schema: storage; Owner: supabase_storage_admin
--

ALTER TABLE ONLY storage.migrations
    ADD CONSTRAINT migrations_pkey PRIMARY KEY (id);


--
-- Name: objects objects_pkey; Type: CONSTRAINT; Schema: storage; Owner: supabase_storage_admin
--

ALTER TABLE ONLY storage.objects
    ADD CONSTRAINT objects_pkey PRIMARY KEY (id);


--
-- Name: prefixes prefixes_pkey; Type: CONSTRAINT; Schema: storage; Owner: supabase_storage_admin
--

ALTER TABLE ONLY storage.prefixes
    ADD CONSTRAINT prefixes_pkey PRIMARY KEY (bucket_id, level, name);


--
-- Name: s3_multipart_uploads_parts s3_multipart_uploads_parts_pkey; Type: CONSTRAINT; Schema: storage; Owner: supabase_storage_admin
--

ALTER TABLE ONLY storage.s3_multipart_uploads_parts
    ADD CONSTRAINT s3_multipart_uploads_parts_pkey PRIMARY KEY (id);


--
-- Name: s3_multipart_uploads s3_multipart_uploads_pkey; Type: CONSTRAINT; Schema: storage; Owner: supabase_storage_admin
--

ALTER TABLE ONLY storage.s3_multipart_uploads
    ADD CONSTRAINT s3_multipart_uploads_pkey PRIMARY KEY (id);


--
-- Name: hooks hooks_pkey; Type: CONSTRAINT; Schema: supabase_functions; Owner: supabase_functions_admin
--

ALTER TABLE ONLY supabase_functions.hooks
    ADD CONSTRAINT hooks_pkey PRIMARY KEY (id);


--
-- Name: migrations migrations_pkey; Type: CONSTRAINT; Schema: supabase_functions; Owner: supabase_functions_admin
--

ALTER TABLE ONLY supabase_functions.migrations
    ADD CONSTRAINT migrations_pkey PRIMARY KEY (version);


--
-- Name: audit_logs_instance_id_idx; Type: INDEX; Schema: auth; Owner: supabase_auth_admin
--

CREATE INDEX audit_logs_instance_id_idx ON auth.audit_log_entries USING btree (instance_id);


--
-- Name: confirmation_token_idx; Type: INDEX; Schema: auth; Owner: supabase_auth_admin
--

CREATE UNIQUE INDEX confirmation_token_idx ON auth.users USING btree (confirmation_token) WHERE ((confirmation_token)::text !~ '^[0-9 ]*$'::text);


--
-- Name: email_change_token_current_idx; Type: INDEX; Schema: auth; Owner: supabase_auth_admin
--

CREATE UNIQUE INDEX email_change_token_current_idx ON auth.users USING btree (email_change_token_current) WHERE ((email_change_token_current)::text !~ '^[0-9 ]*$'::text);


--
-- Name: email_change_token_new_idx; Type: INDEX; Schema: auth; Owner: supabase_auth_admin
--

CREATE UNIQUE INDEX email_change_token_new_idx ON auth.users USING btree (email_change_token_new) WHERE ((email_change_token_new)::text !~ '^[0-9 ]*$'::text);


--
-- Name: factor_id_created_at_idx; Type: INDEX; Schema: auth; Owner: supabase_auth_admin
--

CREATE INDEX factor_id_created_at_idx ON auth.mfa_factors USING btree (user_id, created_at);


--
-- Name: flow_state_created_at_idx; Type: INDEX; Schema: auth; Owner: supabase_auth_admin
--

CREATE INDEX flow_state_created_at_idx ON auth.flow_state USING btree (created_at DESC);


--
-- Name: identities_email_idx; Type: INDEX; Schema: auth; Owner: supabase_auth_admin
--

CREATE INDEX identities_email_idx ON auth.identities USING btree (email text_pattern_ops);


--
-- Name: INDEX identities_email_idx; Type: COMMENT; Schema: auth; Owner: supabase_auth_admin
--

COMMENT ON INDEX auth.identities_email_idx IS 'Auth: Ensures indexed queries on the email column';


--
-- Name: identities_user_id_idx; Type: INDEX; Schema: auth; Owner: supabase_auth_admin
--

CREATE INDEX identities_user_id_idx ON auth.identities USING btree (user_id);


--
-- Name: idx_auth_code; Type: INDEX; Schema: auth; Owner: supabase_auth_admin
--

CREATE INDEX idx_auth_code ON auth.flow_state USING btree (auth_code);


--
-- Name: idx_user_id_auth_method; Type: INDEX; Schema: auth; Owner: supabase_auth_admin
--

CREATE INDEX idx_user_id_auth_method ON auth.flow_state USING btree (user_id, authentication_method);


--
-- Name: mfa_challenge_created_at_idx; Type: INDEX; Schema: auth; Owner: supabase_auth_admin
--

CREATE INDEX mfa_challenge_created_at_idx ON auth.mfa_challenges USING btree (created_at DESC);


--
-- Name: mfa_factors_user_friendly_name_unique; Type: INDEX; Schema: auth; Owner: supabase_auth_admin
--

CREATE UNIQUE INDEX mfa_factors_user_friendly_name_unique ON auth.mfa_factors USING btree (friendly_name, user_id) WHERE (TRIM(BOTH FROM friendly_name) <> ''::text);


--
-- Name: mfa_factors_user_id_idx; Type: INDEX; Schema: auth; Owner: supabase_auth_admin
--

CREATE INDEX mfa_factors_user_id_idx ON auth.mfa_factors USING btree (user_id);


--
-- Name: one_time_tokens_relates_to_hash_idx; Type: INDEX; Schema: auth; Owner: supabase_auth_admin
--

CREATE INDEX one_time_tokens_relates_to_hash_idx ON auth.one_time_tokens USING hash (relates_to);


--
-- Name: one_time_tokens_token_hash_hash_idx; Type: INDEX; Schema: auth; Owner: supabase_auth_admin
--

CREATE INDEX one_time_tokens_token_hash_hash_idx ON auth.one_time_tokens USING hash (token_hash);


--
-- Name: one_time_tokens_user_id_token_type_key; Type: INDEX; Schema: auth; Owner: supabase_auth_admin
--

CREATE UNIQUE INDEX one_time_tokens_user_id_token_type_key ON auth.one_time_tokens USING btree (user_id, token_type);


--
-- Name: reauthentication_token_idx; Type: INDEX; Schema: auth; Owner: supabase_auth_admin
--

CREATE UNIQUE INDEX reauthentication_token_idx ON auth.users USING btree (reauthentication_token) WHERE ((reauthentication_token)::text !~ '^[0-9 ]*$'::text);


--
-- Name: recovery_token_idx; Type: INDEX; Schema: auth; Owner: supabase_auth_admin
--

CREATE UNIQUE INDEX recovery_token_idx ON auth.users USING btree (recovery_token) WHERE ((recovery_token)::text !~ '^[0-9 ]*$'::text);


--
-- Name: refresh_tokens_instance_id_idx; Type: INDEX; Schema: auth; Owner: supabase_auth_admin
--

CREATE INDEX refresh_tokens_instance_id_idx ON auth.refresh_tokens USING btree (instance_id);


--
-- Name: refresh_tokens_instance_id_user_id_idx; Type: INDEX; Schema: auth; Owner: supabase_auth_admin
--

CREATE INDEX refresh_tokens_instance_id_user_id_idx ON auth.refresh_tokens USING btree (instance_id, user_id);


--
-- Name: refresh_tokens_parent_idx; Type: INDEX; Schema: auth; Owner: supabase_auth_admin
--

CREATE INDEX refresh_tokens_parent_idx ON auth.refresh_tokens USING btree (parent);


--
-- Name: refresh_tokens_session_id_revoked_idx; Type: INDEX; Schema: auth; Owner: supabase_auth_admin
--

CREATE INDEX refresh_tokens_session_id_revoked_idx ON auth.refresh_tokens USING btree (session_id, revoked);


--
-- Name: refresh_tokens_updated_at_idx; Type: INDEX; Schema: auth; Owner: supabase_auth_admin
--

CREATE INDEX refresh_tokens_updated_at_idx ON auth.refresh_tokens USING btree (updated_at DESC);


--
-- Name: saml_providers_sso_provider_id_idx; Type: INDEX; Schema: auth; Owner: supabase_auth_admin
--

CREATE INDEX saml_providers_sso_provider_id_idx ON auth.saml_providers USING btree (sso_provider_id);


--
-- Name: saml_relay_states_created_at_idx; Type: INDEX; Schema: auth; Owner: supabase_auth_admin
--

CREATE INDEX saml_relay_states_created_at_idx ON auth.saml_relay_states USING btree (created_at DESC);


--
-- Name: saml_relay_states_for_email_idx; Type: INDEX; Schema: auth; Owner: supabase_auth_admin
--

CREATE INDEX saml_relay_states_for_email_idx ON auth.saml_relay_states USING btree (for_email);


--
-- Name: saml_relay_states_sso_provider_id_idx; Type: INDEX; Schema: auth; Owner: supabase_auth_admin
--

CREATE INDEX saml_relay_states_sso_provider_id_idx ON auth.saml_relay_states USING btree (sso_provider_id);


--
-- Name: sessions_not_after_idx; Type: INDEX; Schema: auth; Owner: supabase_auth_admin
--

CREATE INDEX sessions_not_after_idx ON auth.sessions USING btree (not_after DESC);


--
-- Name: sessions_user_id_idx; Type: INDEX; Schema: auth; Owner: supabase_auth_admin
--

CREATE INDEX sessions_user_id_idx ON auth.sessions USING btree (user_id);


--
-- Name: sso_domains_domain_idx; Type: INDEX; Schema: auth; Owner: supabase_auth_admin
--

CREATE UNIQUE INDEX sso_domains_domain_idx ON auth.sso_domains USING btree (lower(domain));


--
-- Name: sso_domains_sso_provider_id_idx; Type: INDEX; Schema: auth; Owner: supabase_auth_admin
--

CREATE INDEX sso_domains_sso_provider_id_idx ON auth.sso_domains USING btree (sso_provider_id);


--
-- Name: sso_providers_resource_id_idx; Type: INDEX; Schema: auth; Owner: supabase_auth_admin
--

CREATE UNIQUE INDEX sso_providers_resource_id_idx ON auth.sso_providers USING btree (lower(resource_id));


--
-- Name: sso_providers_resource_id_pattern_idx; Type: INDEX; Schema: auth; Owner: supabase_auth_admin
--

CREATE INDEX sso_providers_resource_id_pattern_idx ON auth.sso_providers USING btree (resource_id text_pattern_ops);


--
-- Name: unique_phone_factor_per_user; Type: INDEX; Schema: auth; Owner: supabase_auth_admin
--

CREATE UNIQUE INDEX unique_phone_factor_per_user ON auth.mfa_factors USING btree (user_id, phone);


--
-- Name: user_id_created_at_idx; Type: INDEX; Schema: auth; Owner: supabase_auth_admin
--

CREATE INDEX user_id_created_at_idx ON auth.sessions USING btree (user_id, created_at);


--
-- Name: users_email_partial_key; Type: INDEX; Schema: auth; Owner: supabase_auth_admin
--

CREATE UNIQUE INDEX users_email_partial_key ON auth.users USING btree (email) WHERE (is_sso_user = false);


--
-- Name: INDEX users_email_partial_key; Type: COMMENT; Schema: auth; Owner: supabase_auth_admin
--

COMMENT ON INDEX auth.users_email_partial_key IS 'Auth: A partial unique index that applies only when is_sso_user is false';


--
-- Name: users_instance_id_email_idx; Type: INDEX; Schema: auth; Owner: supabase_auth_admin
--

CREATE INDEX users_instance_id_email_idx ON auth.users USING btree (instance_id, lower((email)::text));


--
-- Name: users_instance_id_idx; Type: INDEX; Schema: auth; Owner: supabase_auth_admin
--

CREATE INDEX users_instance_id_idx ON auth.users USING btree (instance_id);


--
-- Name: users_is_anonymous_idx; Type: INDEX; Schema: auth; Owner: supabase_auth_admin
--

CREATE INDEX users_is_anonymous_idx ON auth.users USING btree (is_anonymous);


--
-- Name: bname; Type: INDEX; Schema: storage; Owner: supabase_storage_admin
--

CREATE UNIQUE INDEX bname ON storage.buckets USING btree (name);


--
-- Name: bucketid_objname; Type: INDEX; Schema: storage; Owner: supabase_storage_admin
--

CREATE UNIQUE INDEX bucketid_objname ON storage.objects USING btree (bucket_id, name);


--
-- Name: idx_iceberg_namespaces_bucket_id; Type: INDEX; Schema: storage; Owner: supabase_storage_admin
--

CREATE UNIQUE INDEX idx_iceberg_namespaces_bucket_id ON storage.iceberg_namespaces USING btree (bucket_id, name);


--
-- Name: idx_iceberg_tables_namespace_id; Type: INDEX; Schema: storage; Owner: supabase_storage_admin
--

CREATE UNIQUE INDEX idx_iceberg_tables_namespace_id ON storage.iceberg_tables USING btree (namespace_id, name);


--
-- Name: idx_multipart_uploads_list; Type: INDEX; Schema: storage; Owner: supabase_storage_admin
--

CREATE INDEX idx_multipart_uploads_list ON storage.s3_multipart_uploads USING btree (bucket_id, key, created_at);


--
-- Name: idx_name_bucket_level_unique; Type: INDEX; Schema: storage; Owner: supabase_storage_admin
--

CREATE UNIQUE INDEX idx_name_bucket_level_unique ON storage.objects USING btree (name COLLATE "C", bucket_id, level);


--
-- Name: idx_objects_bucket_id_name; Type: INDEX; Schema: storage; Owner: supabase_storage_admin
--

CREATE INDEX idx_objects_bucket_id_name ON storage.objects USING btree (bucket_id, name COLLATE "C");


--
-- Name: idx_objects_lower_name; Type: INDEX; Schema: storage; Owner: supabase_storage_admin
--

CREATE INDEX idx_objects_lower_name ON storage.objects USING btree ((path_tokens[level]), lower(name) text_pattern_ops, bucket_id, level);


--
-- Name: idx_prefixes_lower_name; Type: INDEX; Schema: storage; Owner: supabase_storage_admin
--

CREATE INDEX idx_prefixes_lower_name ON storage.prefixes USING btree (bucket_id, level, ((string_to_array(name, '/'::text))[level]), lower(name) text_pattern_ops);


--
-- Name: name_prefix_search; Type: INDEX; Schema: storage; Owner: supabase_storage_admin
--

CREATE INDEX name_prefix_search ON storage.objects USING btree (name text_pattern_ops);


--
-- Name: objects_bucket_id_level_idx; Type: INDEX; Schema: storage; Owner: supabase_storage_admin
--

CREATE UNIQUE INDEX objects_bucket_id_level_idx ON storage.objects USING btree (bucket_id, level, name COLLATE "C");


--
-- Name: supabase_functions_hooks_h_table_id_h_name_idx; Type: INDEX; Schema: supabase_functions; Owner: supabase_functions_admin
--

CREATE INDEX supabase_functions_hooks_h_table_id_h_name_idx ON supabase_functions.hooks USING btree (hook_table_id, hook_name);


--
-- Name: supabase_functions_hooks_request_id_idx; Type: INDEX; Schema: supabase_functions; Owner: supabase_functions_admin
--

CREATE INDEX supabase_functions_hooks_request_id_idx ON supabase_functions.hooks USING btree (request_id);


--
-- Name: buckets enforce_bucket_name_length_trigger; Type: TRIGGER; Schema: storage; Owner: supabase_storage_admin
--

CREATE TRIGGER enforce_bucket_name_length_trigger BEFORE INSERT OR UPDATE OF name ON storage.buckets FOR EACH ROW EXECUTE FUNCTION storage.enforce_bucket_name_length();


--
-- Name: objects objects_delete_delete_prefix; Type: TRIGGER; Schema: storage; Owner: supabase_storage_admin
--

CREATE TRIGGER objects_delete_delete_prefix AFTER DELETE ON storage.objects FOR EACH ROW EXECUTE FUNCTION storage.delete_prefix_hierarchy_trigger();


--
-- Name: objects objects_insert_create_prefix; Type: TRIGGER; Schema: storage; Owner: supabase_storage_admin
--

CREATE TRIGGER objects_insert_create_prefix BEFORE INSERT ON storage.objects FOR EACH ROW EXECUTE FUNCTION storage.objects_insert_prefix_trigger();


--
-- Name: objects objects_update_create_prefix; Type: TRIGGER; Schema: storage; Owner: supabase_storage_admin
--

CREATE TRIGGER objects_update_create_prefix BEFORE UPDATE ON storage.objects FOR EACH ROW WHEN (((new.name <> old.name) OR (new.bucket_id <> old.bucket_id))) EXECUTE FUNCTION storage.objects_update_prefix_trigger();


--
-- Name: prefixes prefixes_create_hierarchy; Type: TRIGGER; Schema: storage; Owner: supabase_storage_admin
--

CREATE TRIGGER prefixes_create_hierarchy BEFORE INSERT ON storage.prefixes FOR EACH ROW WHEN ((pg_trigger_depth() < 1)) EXECUTE FUNCTION storage.prefixes_insert_trigger();


--
-- Name: prefixes prefixes_delete_hierarchy; Type: TRIGGER; Schema: storage; Owner: supabase_storage_admin
--

CREATE TRIGGER prefixes_delete_hierarchy AFTER DELETE ON storage.prefixes FOR EACH ROW EXECUTE FUNCTION storage.delete_prefix_hierarchy_trigger();


--
-- Name: objects update_objects_updated_at; Type: TRIGGER; Schema: storage; Owner: supabase_storage_admin
--

CREATE TRIGGER update_objects_updated_at BEFORE UPDATE ON storage.objects FOR EACH ROW EXECUTE FUNCTION storage.update_updated_at_column();


--
-- Name: identities identities_user_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: supabase_auth_admin
--

ALTER TABLE ONLY auth.identities
    ADD CONSTRAINT identities_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: mfa_amr_claims mfa_amr_claims_session_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: supabase_auth_admin
--

ALTER TABLE ONLY auth.mfa_amr_claims
    ADD CONSTRAINT mfa_amr_claims_session_id_fkey FOREIGN KEY (session_id) REFERENCES auth.sessions(id) ON DELETE CASCADE;


--
-- Name: mfa_challenges mfa_challenges_auth_factor_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: supabase_auth_admin
--

ALTER TABLE ONLY auth.mfa_challenges
    ADD CONSTRAINT mfa_challenges_auth_factor_id_fkey FOREIGN KEY (factor_id) REFERENCES auth.mfa_factors(id) ON DELETE CASCADE;


--
-- Name: mfa_factors mfa_factors_user_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: supabase_auth_admin
--

ALTER TABLE ONLY auth.mfa_factors
    ADD CONSTRAINT mfa_factors_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: one_time_tokens one_time_tokens_user_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: supabase_auth_admin
--

ALTER TABLE ONLY auth.one_time_tokens
    ADD CONSTRAINT one_time_tokens_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: refresh_tokens refresh_tokens_session_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: supabase_auth_admin
--

ALTER TABLE ONLY auth.refresh_tokens
    ADD CONSTRAINT refresh_tokens_session_id_fkey FOREIGN KEY (session_id) REFERENCES auth.sessions(id) ON DELETE CASCADE;


--
-- Name: saml_providers saml_providers_sso_provider_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: supabase_auth_admin
--

ALTER TABLE ONLY auth.saml_providers
    ADD CONSTRAINT saml_providers_sso_provider_id_fkey FOREIGN KEY (sso_provider_id) REFERENCES auth.sso_providers(id) ON DELETE CASCADE;


--
-- Name: saml_relay_states saml_relay_states_flow_state_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: supabase_auth_admin
--

ALTER TABLE ONLY auth.saml_relay_states
    ADD CONSTRAINT saml_relay_states_flow_state_id_fkey FOREIGN KEY (flow_state_id) REFERENCES auth.flow_state(id) ON DELETE CASCADE;


--
-- Name: saml_relay_states saml_relay_states_sso_provider_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: supabase_auth_admin
--

ALTER TABLE ONLY auth.saml_relay_states
    ADD CONSTRAINT saml_relay_states_sso_provider_id_fkey FOREIGN KEY (sso_provider_id) REFERENCES auth.sso_providers(id) ON DELETE CASCADE;


--
-- Name: sessions sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: supabase_auth_admin
--

ALTER TABLE ONLY auth.sessions
    ADD CONSTRAINT sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: sso_domains sso_domains_sso_provider_id_fkey; Type: FK CONSTRAINT; Schema: auth; Owner: supabase_auth_admin
--

ALTER TABLE ONLY auth.sso_domains
    ADD CONSTRAINT sso_domains_sso_provider_id_fkey FOREIGN KEY (sso_provider_id) REFERENCES auth.sso_providers(id) ON DELETE CASCADE;


--
-- Name: iceberg_namespaces iceberg_namespaces_bucket_id_fkey; Type: FK CONSTRAINT; Schema: storage; Owner: supabase_storage_admin
--

ALTER TABLE ONLY storage.iceberg_namespaces
    ADD CONSTRAINT iceberg_namespaces_bucket_id_fkey FOREIGN KEY (bucket_id) REFERENCES storage.buckets_analytics(id) ON DELETE CASCADE;


--
-- Name: iceberg_tables iceberg_tables_bucket_id_fkey; Type: FK CONSTRAINT; Schema: storage; Owner: supabase_storage_admin
--

ALTER TABLE ONLY storage.iceberg_tables
    ADD CONSTRAINT iceberg_tables_bucket_id_fkey FOREIGN KEY (bucket_id) REFERENCES storage.buckets_analytics(id) ON DELETE CASCADE;


--
-- Name: iceberg_tables iceberg_tables_namespace_id_fkey; Type: FK CONSTRAINT; Schema: storage; Owner: supabase_storage_admin
--

ALTER TABLE ONLY storage.iceberg_tables
    ADD CONSTRAINT iceberg_tables_namespace_id_fkey FOREIGN KEY (namespace_id) REFERENCES storage.iceberg_namespaces(id) ON DELETE CASCADE;


--
-- Name: objects objects_bucketId_fkey; Type: FK CONSTRAINT; Schema: storage; Owner: supabase_storage_admin
--

ALTER TABLE ONLY storage.objects
    ADD CONSTRAINT "objects_bucketId_fkey" FOREIGN KEY (bucket_id) REFERENCES storage.buckets(id);


--
-- Name: prefixes prefixes_bucketId_fkey; Type: FK CONSTRAINT; Schema: storage; Owner: supabase_storage_admin
--

ALTER TABLE ONLY storage.prefixes
    ADD CONSTRAINT "prefixes_bucketId_fkey" FOREIGN KEY (bucket_id) REFERENCES storage.buckets(id);


--
-- Name: s3_multipart_uploads s3_multipart_uploads_bucket_id_fkey; Type: FK CONSTRAINT; Schema: storage; Owner: supabase_storage_admin
--

ALTER TABLE ONLY storage.s3_multipart_uploads
    ADD CONSTRAINT s3_multipart_uploads_bucket_id_fkey FOREIGN KEY (bucket_id) REFERENCES storage.buckets(id);


--
-- Name: s3_multipart_uploads_parts s3_multipart_uploads_parts_bucket_id_fkey; Type: FK CONSTRAINT; Schema: storage; Owner: supabase_storage_admin
--

ALTER TABLE ONLY storage.s3_multipart_uploads_parts
    ADD CONSTRAINT s3_multipart_uploads_parts_bucket_id_fkey FOREIGN KEY (bucket_id) REFERENCES storage.buckets(id);


--
-- Name: s3_multipart_uploads_parts s3_multipart_uploads_parts_upload_id_fkey; Type: FK CONSTRAINT; Schema: storage; Owner: supabase_storage_admin
--

ALTER TABLE ONLY storage.s3_multipart_uploads_parts
    ADD CONSTRAINT s3_multipart_uploads_parts_upload_id_fkey FOREIGN KEY (upload_id) REFERENCES storage.s3_multipart_uploads(id) ON DELETE CASCADE;


--
-- Name: audit_log_entries; Type: ROW SECURITY; Schema: auth; Owner: supabase_auth_admin
--

ALTER TABLE auth.audit_log_entries ENABLE ROW LEVEL SECURITY;

--
-- Name: flow_state; Type: ROW SECURITY; Schema: auth; Owner: supabase_auth_admin
--

ALTER TABLE auth.flow_state ENABLE ROW LEVEL SECURITY;

--
-- Name: identities; Type: ROW SECURITY; Schema: auth; Owner: supabase_auth_admin
--

ALTER TABLE auth.identities ENABLE ROW LEVEL SECURITY;

--
-- Name: instances; Type: ROW SECURITY; Schema: auth; Owner: supabase_auth_admin
--

ALTER TABLE auth.instances ENABLE ROW LEVEL SECURITY;

--
-- Name: mfa_amr_claims; Type: ROW SECURITY; Schema: auth; Owner: supabase_auth_admin
--

ALTER TABLE auth.mfa_amr_claims ENABLE ROW LEVEL SECURITY;

--
-- Name: mfa_challenges; Type: ROW SECURITY; Schema: auth; Owner: supabase_auth_admin
--

ALTER TABLE auth.mfa_challenges ENABLE ROW LEVEL SECURITY;

--
-- Name: mfa_factors; Type: ROW SECURITY; Schema: auth; Owner: supabase_auth_admin
--

ALTER TABLE auth.mfa_factors ENABLE ROW LEVEL SECURITY;

--
-- Name: one_time_tokens; Type: ROW SECURITY; Schema: auth; Owner: supabase_auth_admin
--

ALTER TABLE auth.one_time_tokens ENABLE ROW LEVEL SECURITY;

--
-- Name: refresh_tokens; Type: ROW SECURITY; Schema: auth; Owner: supabase_auth_admin
--

ALTER TABLE auth.refresh_tokens ENABLE ROW LEVEL SECURITY;

--
-- Name: saml_providers; Type: ROW SECURITY; Schema: auth; Owner: supabase_auth_admin
--

ALTER TABLE auth.saml_providers ENABLE ROW LEVEL SECURITY;

--
-- Name: saml_relay_states; Type: ROW SECURITY; Schema: auth; Owner: supabase_auth_admin
--

ALTER TABLE auth.saml_relay_states ENABLE ROW LEVEL SECURITY;

--
-- Name: schema_migrations; Type: ROW SECURITY; Schema: auth; Owner: supabase_auth_admin
--

ALTER TABLE auth.schema_migrations ENABLE ROW LEVEL SECURITY;

--
-- Name: sessions; Type: ROW SECURITY; Schema: auth; Owner: supabase_auth_admin
--

ALTER TABLE auth.sessions ENABLE ROW LEVEL SECURITY;

--
-- Name: sso_domains; Type: ROW SECURITY; Schema: auth; Owner: supabase_auth_admin
--

ALTER TABLE auth.sso_domains ENABLE ROW LEVEL SECURITY;

--
-- Name: sso_providers; Type: ROW SECURITY; Schema: auth; Owner: supabase_auth_admin
--

ALTER TABLE auth.sso_providers ENABLE ROW LEVEL SECURITY;

--
-- Name: users; Type: ROW SECURITY; Schema: auth; Owner: supabase_auth_admin
--

ALTER TABLE auth.users ENABLE ROW LEVEL SECURITY;

--
-- Name: buckets; Type: ROW SECURITY; Schema: storage; Owner: supabase_storage_admin
--

ALTER TABLE storage.buckets ENABLE ROW LEVEL SECURITY;

--
-- Name: buckets_analytics; Type: ROW SECURITY; Schema: storage; Owner: supabase_storage_admin
--

ALTER TABLE storage.buckets_analytics ENABLE ROW LEVEL SECURITY;

--
-- Name: iceberg_namespaces; Type: ROW SECURITY; Schema: storage; Owner: supabase_storage_admin
--

ALTER TABLE storage.iceberg_namespaces ENABLE ROW LEVEL SECURITY;

--
-- Name: iceberg_tables; Type: ROW SECURITY; Schema: storage; Owner: supabase_storage_admin
--

ALTER TABLE storage.iceberg_tables ENABLE ROW LEVEL SECURITY;

--
-- Name: migrations; Type: ROW SECURITY; Schema: storage; Owner: supabase_storage_admin
--

ALTER TABLE storage.migrations ENABLE ROW LEVEL SECURITY;

--
-- Name: objects; Type: ROW SECURITY; Schema: storage; Owner: supabase_storage_admin
--

ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;

--
-- Name: prefixes; Type: ROW SECURITY; Schema: storage; Owner: supabase_storage_admin
--

ALTER TABLE storage.prefixes ENABLE ROW LEVEL SECURITY;

--
-- Name: s3_multipart_uploads; Type: ROW SECURITY; Schema: storage; Owner: supabase_storage_admin
--

ALTER TABLE storage.s3_multipart_uploads ENABLE ROW LEVEL SECURITY;

--
-- Name: s3_multipart_uploads_parts; Type: ROW SECURITY; Schema: storage; Owner: supabase_storage_admin
--

ALTER TABLE storage.s3_multipart_uploads_parts ENABLE ROW LEVEL SECURITY;

--
-- Name: supabase_realtime; Type: PUBLICATION; Schema: -; Owner: postgres
--

CREATE PUBLICATION supabase_realtime WITH (publish = 'insert, update, delete, truncate');


ALTER PUBLICATION supabase_realtime OWNER TO postgres;

--
-- Name: SCHEMA auth; Type: ACL; Schema: -; Owner: supabase_admin
--

GRANT USAGE ON SCHEMA auth TO anon;
GRANT USAGE ON SCHEMA auth TO authenticated;
GRANT USAGE ON SCHEMA auth TO service_role;
GRANT ALL ON SCHEMA auth TO supabase_auth_admin;
GRANT ALL ON SCHEMA auth TO dashboard_user;
GRANT USAGE ON SCHEMA auth TO postgres;


--
-- Name: SCHEMA extensions; Type: ACL; Schema: -; Owner: postgres
--

GRANT USAGE ON SCHEMA extensions TO anon;
GRANT USAGE ON SCHEMA extensions TO authenticated;
GRANT USAGE ON SCHEMA extensions TO service_role;
GRANT ALL ON SCHEMA extensions TO dashboard_user;


--
-- Name: SCHEMA net; Type: ACL; Schema: -; Owner: supabase_admin
--

GRANT USAGE ON SCHEMA net TO supabase_functions_admin;
GRANT USAGE ON SCHEMA net TO postgres;
GRANT USAGE ON SCHEMA net TO anon;
GRANT USAGE ON SCHEMA net TO authenticated;
GRANT USAGE ON SCHEMA net TO service_role;


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: pg_database_owner
--

GRANT USAGE ON SCHEMA public TO postgres;
GRANT USAGE ON SCHEMA public TO anon;
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT USAGE ON SCHEMA public TO service_role;


--
-- Name: SCHEMA realtime; Type: ACL; Schema: -; Owner: supabase_admin
--

GRANT USAGE ON SCHEMA realtime TO postgres;


--
-- Name: SCHEMA storage; Type: ACL; Schema: -; Owner: supabase_admin
--

GRANT USAGE ON SCHEMA storage TO postgres;
GRANT USAGE ON SCHEMA storage TO anon;
GRANT USAGE ON SCHEMA storage TO authenticated;
GRANT USAGE ON SCHEMA storage TO service_role;
GRANT ALL ON SCHEMA storage TO supabase_storage_admin;
GRANT ALL ON SCHEMA storage TO dashboard_user;


--
-- Name: SCHEMA supabase_functions; Type: ACL; Schema: -; Owner: supabase_admin
--

GRANT USAGE ON SCHEMA supabase_functions TO postgres;
GRANT USAGE ON SCHEMA supabase_functions TO anon;
GRANT USAGE ON SCHEMA supabase_functions TO authenticated;
GRANT USAGE ON SCHEMA supabase_functions TO service_role;
GRANT ALL ON SCHEMA supabase_functions TO supabase_functions_admin;


--
-- Name: SCHEMA vault; Type: ACL; Schema: -; Owner: supabase_admin
--

GRANT USAGE ON SCHEMA vault TO postgres WITH GRANT OPTION;
GRANT USAGE ON SCHEMA vault TO service_role;


--
-- Name: FUNCTION email(); Type: ACL; Schema: auth; Owner: supabase_auth_admin
--

GRANT ALL ON FUNCTION auth.email() TO dashboard_user;


--
-- Name: FUNCTION jwt(); Type: ACL; Schema: auth; Owner: supabase_auth_admin
--

GRANT ALL ON FUNCTION auth.jwt() TO postgres;
GRANT ALL ON FUNCTION auth.jwt() TO dashboard_user;


--
-- Name: FUNCTION role(); Type: ACL; Schema: auth; Owner: supabase_auth_admin
--

GRANT ALL ON FUNCTION auth.role() TO dashboard_user;


--
-- Name: FUNCTION uid(); Type: ACL; Schema: auth; Owner: supabase_auth_admin
--

GRANT ALL ON FUNCTION auth.uid() TO dashboard_user;


--
-- Name: FUNCTION algorithm_sign(signables text, secret text, algorithm text); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.algorithm_sign(signables text, secret text, algorithm text) TO dashboard_user;
GRANT ALL ON FUNCTION extensions.algorithm_sign(signables text, secret text, algorithm text) TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION armor(bytea); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.armor(bytea) TO dashboard_user;
GRANT ALL ON FUNCTION extensions.armor(bytea) TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION armor(bytea, text[], text[]); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.armor(bytea, text[], text[]) TO dashboard_user;
GRANT ALL ON FUNCTION extensions.armor(bytea, text[], text[]) TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION crypt(text, text); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.crypt(text, text) TO dashboard_user;
GRANT ALL ON FUNCTION extensions.crypt(text, text) TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION dearmor(text); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.dearmor(text) TO dashboard_user;
GRANT ALL ON FUNCTION extensions.dearmor(text) TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION decrypt(bytea, bytea, text); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.decrypt(bytea, bytea, text) TO dashboard_user;
GRANT ALL ON FUNCTION extensions.decrypt(bytea, bytea, text) TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION decrypt_iv(bytea, bytea, bytea, text); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.decrypt_iv(bytea, bytea, bytea, text) TO dashboard_user;
GRANT ALL ON FUNCTION extensions.decrypt_iv(bytea, bytea, bytea, text) TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION digest(bytea, text); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.digest(bytea, text) TO dashboard_user;
GRANT ALL ON FUNCTION extensions.digest(bytea, text) TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION digest(text, text); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.digest(text, text) TO dashboard_user;
GRANT ALL ON FUNCTION extensions.digest(text, text) TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION encrypt(bytea, bytea, text); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.encrypt(bytea, bytea, text) TO dashboard_user;
GRANT ALL ON FUNCTION extensions.encrypt(bytea, bytea, text) TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION encrypt_iv(bytea, bytea, bytea, text); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.encrypt_iv(bytea, bytea, bytea, text) TO dashboard_user;
GRANT ALL ON FUNCTION extensions.encrypt_iv(bytea, bytea, bytea, text) TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION gen_random_bytes(integer); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.gen_random_bytes(integer) TO dashboard_user;
GRANT ALL ON FUNCTION extensions.gen_random_bytes(integer) TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION gen_random_uuid(); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.gen_random_uuid() TO dashboard_user;
GRANT ALL ON FUNCTION extensions.gen_random_uuid() TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION gen_salt(text); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.gen_salt(text) TO dashboard_user;
GRANT ALL ON FUNCTION extensions.gen_salt(text) TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION gen_salt(text, integer); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.gen_salt(text, integer) TO dashboard_user;
GRANT ALL ON FUNCTION extensions.gen_salt(text, integer) TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION grant_pg_cron_access(); Type: ACL; Schema: extensions; Owner: supabase_admin
--

REVOKE ALL ON FUNCTION extensions.grant_pg_cron_access() FROM supabase_admin;
GRANT ALL ON FUNCTION extensions.grant_pg_cron_access() TO supabase_admin WITH GRANT OPTION;
GRANT ALL ON FUNCTION extensions.grant_pg_cron_access() TO dashboard_user;


--
-- Name: FUNCTION grant_pg_graphql_access(); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.grant_pg_graphql_access() TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION grant_pg_net_access(); Type: ACL; Schema: extensions; Owner: supabase_admin
--

REVOKE ALL ON FUNCTION extensions.grant_pg_net_access() FROM supabase_admin;
GRANT ALL ON FUNCTION extensions.grant_pg_net_access() TO supabase_admin WITH GRANT OPTION;
GRANT ALL ON FUNCTION extensions.grant_pg_net_access() TO dashboard_user;


--
-- Name: FUNCTION hmac(bytea, bytea, text); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.hmac(bytea, bytea, text) TO dashboard_user;
GRANT ALL ON FUNCTION extensions.hmac(bytea, bytea, text) TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION hmac(text, text, text); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.hmac(text, text, text) TO dashboard_user;
GRANT ALL ON FUNCTION extensions.hmac(text, text, text) TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION pg_stat_statements(showtext boolean, OUT userid oid, OUT dbid oid, OUT toplevel boolean, OUT queryid bigint, OUT query text, OUT plans bigint, OUT total_plan_time double precision, OUT min_plan_time double precision, OUT max_plan_time double precision, OUT mean_plan_time double precision, OUT stddev_plan_time double precision, OUT calls bigint, OUT total_exec_time double precision, OUT min_exec_time double precision, OUT max_exec_time double precision, OUT mean_exec_time double precision, OUT stddev_exec_time double precision, OUT rows bigint, OUT shared_blks_hit bigint, OUT shared_blks_read bigint, OUT shared_blks_dirtied bigint, OUT shared_blks_written bigint, OUT local_blks_hit bigint, OUT local_blks_read bigint, OUT local_blks_dirtied bigint, OUT local_blks_written bigint, OUT temp_blks_read bigint, OUT temp_blks_written bigint, OUT blk_read_time double precision, OUT blk_write_time double precision, OUT temp_blk_read_time double precision, OUT temp_blk_write_time double precision, OUT wal_records bigint, OUT wal_fpi bigint, OUT wal_bytes numeric, OUT jit_functions bigint, OUT jit_generation_time double precision, OUT jit_inlining_count bigint, OUT jit_inlining_time double precision, OUT jit_optimization_count bigint, OUT jit_optimization_time double precision, OUT jit_emission_count bigint, OUT jit_emission_time double precision); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.pg_stat_statements(showtext boolean, OUT userid oid, OUT dbid oid, OUT toplevel boolean, OUT queryid bigint, OUT query text, OUT plans bigint, OUT total_plan_time double precision, OUT min_plan_time double precision, OUT max_plan_time double precision, OUT mean_plan_time double precision, OUT stddev_plan_time double precision, OUT calls bigint, OUT total_exec_time double precision, OUT min_exec_time double precision, OUT max_exec_time double precision, OUT mean_exec_time double precision, OUT stddev_exec_time double precision, OUT rows bigint, OUT shared_blks_hit bigint, OUT shared_blks_read bigint, OUT shared_blks_dirtied bigint, OUT shared_blks_written bigint, OUT local_blks_hit bigint, OUT local_blks_read bigint, OUT local_blks_dirtied bigint, OUT local_blks_written bigint, OUT temp_blks_read bigint, OUT temp_blks_written bigint, OUT blk_read_time double precision, OUT blk_write_time double precision, OUT temp_blk_read_time double precision, OUT temp_blk_write_time double precision, OUT wal_records bigint, OUT wal_fpi bigint, OUT wal_bytes numeric, OUT jit_functions bigint, OUT jit_generation_time double precision, OUT jit_inlining_count bigint, OUT jit_inlining_time double precision, OUT jit_optimization_count bigint, OUT jit_optimization_time double precision, OUT jit_emission_count bigint, OUT jit_emission_time double precision) TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION pg_stat_statements_info(OUT dealloc bigint, OUT stats_reset timestamp with time zone); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.pg_stat_statements_info(OUT dealloc bigint, OUT stats_reset timestamp with time zone) TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION pg_stat_statements_reset(userid oid, dbid oid, queryid bigint); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.pg_stat_statements_reset(userid oid, dbid oid, queryid bigint) TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION pgp_armor_headers(text, OUT key text, OUT value text); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.pgp_armor_headers(text, OUT key text, OUT value text) TO dashboard_user;
GRANT ALL ON FUNCTION extensions.pgp_armor_headers(text, OUT key text, OUT value text) TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION pgp_key_id(bytea); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.pgp_key_id(bytea) TO dashboard_user;
GRANT ALL ON FUNCTION extensions.pgp_key_id(bytea) TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION pgp_pub_decrypt(bytea, bytea); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.pgp_pub_decrypt(bytea, bytea) TO dashboard_user;
GRANT ALL ON FUNCTION extensions.pgp_pub_decrypt(bytea, bytea) TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION pgp_pub_decrypt(bytea, bytea, text); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.pgp_pub_decrypt(bytea, bytea, text) TO dashboard_user;
GRANT ALL ON FUNCTION extensions.pgp_pub_decrypt(bytea, bytea, text) TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION pgp_pub_decrypt(bytea, bytea, text, text); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.pgp_pub_decrypt(bytea, bytea, text, text) TO dashboard_user;
GRANT ALL ON FUNCTION extensions.pgp_pub_decrypt(bytea, bytea, text, text) TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION pgp_pub_decrypt_bytea(bytea, bytea); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.pgp_pub_decrypt_bytea(bytea, bytea) TO dashboard_user;
GRANT ALL ON FUNCTION extensions.pgp_pub_decrypt_bytea(bytea, bytea) TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION pgp_pub_decrypt_bytea(bytea, bytea, text); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.pgp_pub_decrypt_bytea(bytea, bytea, text) TO dashboard_user;
GRANT ALL ON FUNCTION extensions.pgp_pub_decrypt_bytea(bytea, bytea, text) TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION pgp_pub_decrypt_bytea(bytea, bytea, text, text); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.pgp_pub_decrypt_bytea(bytea, bytea, text, text) TO dashboard_user;
GRANT ALL ON FUNCTION extensions.pgp_pub_decrypt_bytea(bytea, bytea, text, text) TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION pgp_pub_encrypt(text, bytea); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.pgp_pub_encrypt(text, bytea) TO dashboard_user;
GRANT ALL ON FUNCTION extensions.pgp_pub_encrypt(text, bytea) TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION pgp_pub_encrypt(text, bytea, text); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.pgp_pub_encrypt(text, bytea, text) TO dashboard_user;
GRANT ALL ON FUNCTION extensions.pgp_pub_encrypt(text, bytea, text) TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION pgp_pub_encrypt_bytea(bytea, bytea); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.pgp_pub_encrypt_bytea(bytea, bytea) TO dashboard_user;
GRANT ALL ON FUNCTION extensions.pgp_pub_encrypt_bytea(bytea, bytea) TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION pgp_pub_encrypt_bytea(bytea, bytea, text); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.pgp_pub_encrypt_bytea(bytea, bytea, text) TO dashboard_user;
GRANT ALL ON FUNCTION extensions.pgp_pub_encrypt_bytea(bytea, bytea, text) TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION pgp_sym_decrypt(bytea, text); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.pgp_sym_decrypt(bytea, text) TO dashboard_user;
GRANT ALL ON FUNCTION extensions.pgp_sym_decrypt(bytea, text) TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION pgp_sym_decrypt(bytea, text, text); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.pgp_sym_decrypt(bytea, text, text) TO dashboard_user;
GRANT ALL ON FUNCTION extensions.pgp_sym_decrypt(bytea, text, text) TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION pgp_sym_decrypt_bytea(bytea, text); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.pgp_sym_decrypt_bytea(bytea, text) TO dashboard_user;
GRANT ALL ON FUNCTION extensions.pgp_sym_decrypt_bytea(bytea, text) TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION pgp_sym_decrypt_bytea(bytea, text, text); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.pgp_sym_decrypt_bytea(bytea, text, text) TO dashboard_user;
GRANT ALL ON FUNCTION extensions.pgp_sym_decrypt_bytea(bytea, text, text) TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION pgp_sym_encrypt(text, text); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.pgp_sym_encrypt(text, text) TO dashboard_user;
GRANT ALL ON FUNCTION extensions.pgp_sym_encrypt(text, text) TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION pgp_sym_encrypt(text, text, text); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.pgp_sym_encrypt(text, text, text) TO dashboard_user;
GRANT ALL ON FUNCTION extensions.pgp_sym_encrypt(text, text, text) TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION pgp_sym_encrypt_bytea(bytea, text); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.pgp_sym_encrypt_bytea(bytea, text) TO dashboard_user;
GRANT ALL ON FUNCTION extensions.pgp_sym_encrypt_bytea(bytea, text) TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION pgp_sym_encrypt_bytea(bytea, text, text); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.pgp_sym_encrypt_bytea(bytea, text, text) TO dashboard_user;
GRANT ALL ON FUNCTION extensions.pgp_sym_encrypt_bytea(bytea, text, text) TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION pgrst_ddl_watch(); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.pgrst_ddl_watch() TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION pgrst_drop_watch(); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.pgrst_drop_watch() TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION set_graphql_placeholder(); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.set_graphql_placeholder() TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION sign(payload json, secret text, algorithm text); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.sign(payload json, secret text, algorithm text) TO dashboard_user;
GRANT ALL ON FUNCTION extensions.sign(payload json, secret text, algorithm text) TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION try_cast_double(inp text); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.try_cast_double(inp text) TO dashboard_user;
GRANT ALL ON FUNCTION extensions.try_cast_double(inp text) TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION url_decode(data text); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.url_decode(data text) TO dashboard_user;
GRANT ALL ON FUNCTION extensions.url_decode(data text) TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION url_encode(data bytea); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.url_encode(data bytea) TO dashboard_user;
GRANT ALL ON FUNCTION extensions.url_encode(data bytea) TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION uuid_generate_v1(); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.uuid_generate_v1() TO dashboard_user;
GRANT ALL ON FUNCTION extensions.uuid_generate_v1() TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION uuid_generate_v1mc(); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.uuid_generate_v1mc() TO dashboard_user;
GRANT ALL ON FUNCTION extensions.uuid_generate_v1mc() TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION uuid_generate_v3(namespace uuid, name text); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.uuid_generate_v3(namespace uuid, name text) TO dashboard_user;
GRANT ALL ON FUNCTION extensions.uuid_generate_v3(namespace uuid, name text) TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION uuid_generate_v4(); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.uuid_generate_v4() TO dashboard_user;
GRANT ALL ON FUNCTION extensions.uuid_generate_v4() TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION uuid_generate_v5(namespace uuid, name text); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.uuid_generate_v5(namespace uuid, name text) TO dashboard_user;
GRANT ALL ON FUNCTION extensions.uuid_generate_v5(namespace uuid, name text) TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION uuid_nil(); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.uuid_nil() TO dashboard_user;
GRANT ALL ON FUNCTION extensions.uuid_nil() TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION uuid_ns_dns(); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.uuid_ns_dns() TO dashboard_user;
GRANT ALL ON FUNCTION extensions.uuid_ns_dns() TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION uuid_ns_oid(); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.uuid_ns_oid() TO dashboard_user;
GRANT ALL ON FUNCTION extensions.uuid_ns_oid() TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION uuid_ns_url(); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.uuid_ns_url() TO dashboard_user;
GRANT ALL ON FUNCTION extensions.uuid_ns_url() TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION uuid_ns_x500(); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.uuid_ns_x500() TO dashboard_user;
GRANT ALL ON FUNCTION extensions.uuid_ns_x500() TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION verify(token text, secret text, algorithm text); Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON FUNCTION extensions.verify(token text, secret text, algorithm text) TO dashboard_user;
GRANT ALL ON FUNCTION extensions.verify(token text, secret text, algorithm text) TO postgres WITH GRANT OPTION;


--
-- Name: FUNCTION graphql("operationName" text, query text, variables jsonb, extensions jsonb); Type: ACL; Schema: graphql_public; Owner: supabase_admin
--

GRANT ALL ON FUNCTION graphql_public.graphql("operationName" text, query text, variables jsonb, extensions jsonb) TO postgres;
GRANT ALL ON FUNCTION graphql_public.graphql("operationName" text, query text, variables jsonb, extensions jsonb) TO anon;
GRANT ALL ON FUNCTION graphql_public.graphql("operationName" text, query text, variables jsonb, extensions jsonb) TO authenticated;
GRANT ALL ON FUNCTION graphql_public.graphql("operationName" text, query text, variables jsonb, extensions jsonb) TO service_role;


--
-- Name: FUNCTION http_get(url text, params jsonb, headers jsonb, timeout_milliseconds integer); Type: ACL; Schema: net; Owner: supabase_admin
--

REVOKE ALL ON FUNCTION net.http_get(url text, params jsonb, headers jsonb, timeout_milliseconds integer) FROM PUBLIC;
GRANT ALL ON FUNCTION net.http_get(url text, params jsonb, headers jsonb, timeout_milliseconds integer) TO supabase_functions_admin;
GRANT ALL ON FUNCTION net.http_get(url text, params jsonb, headers jsonb, timeout_milliseconds integer) TO postgres;
GRANT ALL ON FUNCTION net.http_get(url text, params jsonb, headers jsonb, timeout_milliseconds integer) TO anon;
GRANT ALL ON FUNCTION net.http_get(url text, params jsonb, headers jsonb, timeout_milliseconds integer) TO authenticated;
GRANT ALL ON FUNCTION net.http_get(url text, params jsonb, headers jsonb, timeout_milliseconds integer) TO service_role;


--
-- Name: FUNCTION http_post(url text, body jsonb, params jsonb, headers jsonb, timeout_milliseconds integer); Type: ACL; Schema: net; Owner: supabase_admin
--

REVOKE ALL ON FUNCTION net.http_post(url text, body jsonb, params jsonb, headers jsonb, timeout_milliseconds integer) FROM PUBLIC;
GRANT ALL ON FUNCTION net.http_post(url text, body jsonb, params jsonb, headers jsonb, timeout_milliseconds integer) TO supabase_functions_admin;
GRANT ALL ON FUNCTION net.http_post(url text, body jsonb, params jsonb, headers jsonb, timeout_milliseconds integer) TO postgres;
GRANT ALL ON FUNCTION net.http_post(url text, body jsonb, params jsonb, headers jsonb, timeout_milliseconds integer) TO anon;
GRANT ALL ON FUNCTION net.http_post(url text, body jsonb, params jsonb, headers jsonb, timeout_milliseconds integer) TO authenticated;
GRANT ALL ON FUNCTION net.http_post(url text, body jsonb, params jsonb, headers jsonb, timeout_milliseconds integer) TO service_role;


--
-- Name: FUNCTION get_auth(p_usename text); Type: ACL; Schema: pgbouncer; Owner: supabase_admin
--

REVOKE ALL ON FUNCTION pgbouncer.get_auth(p_usename text) FROM PUBLIC;
GRANT ALL ON FUNCTION pgbouncer.get_auth(p_usename text) TO pgbouncer;
GRANT ALL ON FUNCTION pgbouncer.get_auth(p_usename text) TO postgres;


--
-- Name: FUNCTION normalize_app_opportunities_submission_id(); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.normalize_app_opportunities_submission_id() TO anon;
GRANT ALL ON FUNCTION public.normalize_app_opportunities_submission_id() TO authenticated;
GRANT ALL ON FUNCTION public.normalize_app_opportunities_submission_id() TO service_role;


--
-- Name: FUNCTION normalize_submission_id(input_id text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.normalize_submission_id(input_id text) TO anon;
GRANT ALL ON FUNCTION public.normalize_submission_id(input_id text) TO authenticated;
GRANT ALL ON FUNCTION public.normalize_submission_id(input_id text) TO service_role;


--
-- Name: FUNCTION redditharbor_namespace(); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.redditharbor_namespace() TO anon;
GRANT ALL ON FUNCTION public.redditharbor_namespace() TO authenticated;
GRANT ALL ON FUNCTION public.redditharbor_namespace() TO service_role;


--
-- Name: FUNCTION uuid5_generate(namespace_uuid uuid, name_string text); Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON FUNCTION public.uuid5_generate(namespace_uuid uuid, name_string text) TO anon;
GRANT ALL ON FUNCTION public.uuid5_generate(namespace_uuid uuid, name_string text) TO authenticated;
GRANT ALL ON FUNCTION public.uuid5_generate(namespace_uuid uuid, name_string text) TO service_role;


--
-- Name: FUNCTION http_request(); Type: ACL; Schema: supabase_functions; Owner: supabase_functions_admin
--

REVOKE ALL ON FUNCTION supabase_functions.http_request() FROM PUBLIC;
GRANT ALL ON FUNCTION supabase_functions.http_request() TO postgres;
GRANT ALL ON FUNCTION supabase_functions.http_request() TO anon;
GRANT ALL ON FUNCTION supabase_functions.http_request() TO authenticated;
GRANT ALL ON FUNCTION supabase_functions.http_request() TO service_role;


--
-- Name: FUNCTION _crypto_aead_det_decrypt(message bytea, additional bytea, key_id bigint, context bytea, nonce bytea); Type: ACL; Schema: vault; Owner: supabase_admin
--

GRANT ALL ON FUNCTION vault._crypto_aead_det_decrypt(message bytea, additional bytea, key_id bigint, context bytea, nonce bytea) TO postgres WITH GRANT OPTION;
GRANT ALL ON FUNCTION vault._crypto_aead_det_decrypt(message bytea, additional bytea, key_id bigint, context bytea, nonce bytea) TO service_role;


--
-- Name: FUNCTION create_secret(new_secret text, new_name text, new_description text, new_key_id uuid); Type: ACL; Schema: vault; Owner: supabase_admin
--

GRANT ALL ON FUNCTION vault.create_secret(new_secret text, new_name text, new_description text, new_key_id uuid) TO postgres WITH GRANT OPTION;
GRANT ALL ON FUNCTION vault.create_secret(new_secret text, new_name text, new_description text, new_key_id uuid) TO service_role;


--
-- Name: FUNCTION update_secret(secret_id uuid, new_secret text, new_name text, new_description text, new_key_id uuid); Type: ACL; Schema: vault; Owner: supabase_admin
--

GRANT ALL ON FUNCTION vault.update_secret(secret_id uuid, new_secret text, new_name text, new_description text, new_key_id uuid) TO postgres WITH GRANT OPTION;
GRANT ALL ON FUNCTION vault.update_secret(secret_id uuid, new_secret text, new_name text, new_description text, new_key_id uuid) TO service_role;


--
-- Name: TABLE audit_log_entries; Type: ACL; Schema: auth; Owner: supabase_auth_admin
--

GRANT ALL ON TABLE auth.audit_log_entries TO dashboard_user;
GRANT INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE auth.audit_log_entries TO postgres;
GRANT SELECT ON TABLE auth.audit_log_entries TO postgres WITH GRANT OPTION;


--
-- Name: TABLE flow_state; Type: ACL; Schema: auth; Owner: supabase_auth_admin
--

GRANT INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE auth.flow_state TO postgres;
GRANT SELECT ON TABLE auth.flow_state TO postgres WITH GRANT OPTION;
GRANT ALL ON TABLE auth.flow_state TO dashboard_user;


--
-- Name: TABLE identities; Type: ACL; Schema: auth; Owner: supabase_auth_admin
--

GRANT INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE auth.identities TO postgres;
GRANT SELECT ON TABLE auth.identities TO postgres WITH GRANT OPTION;
GRANT ALL ON TABLE auth.identities TO dashboard_user;


--
-- Name: TABLE instances; Type: ACL; Schema: auth; Owner: supabase_auth_admin
--

GRANT ALL ON TABLE auth.instances TO dashboard_user;
GRANT INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE auth.instances TO postgres;
GRANT SELECT ON TABLE auth.instances TO postgres WITH GRANT OPTION;


--
-- Name: TABLE mfa_amr_claims; Type: ACL; Schema: auth; Owner: supabase_auth_admin
--

GRANT INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE auth.mfa_amr_claims TO postgres;
GRANT SELECT ON TABLE auth.mfa_amr_claims TO postgres WITH GRANT OPTION;
GRANT ALL ON TABLE auth.mfa_amr_claims TO dashboard_user;


--
-- Name: TABLE mfa_challenges; Type: ACL; Schema: auth; Owner: supabase_auth_admin
--

GRANT INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE auth.mfa_challenges TO postgres;
GRANT SELECT ON TABLE auth.mfa_challenges TO postgres WITH GRANT OPTION;
GRANT ALL ON TABLE auth.mfa_challenges TO dashboard_user;


--
-- Name: TABLE mfa_factors; Type: ACL; Schema: auth; Owner: supabase_auth_admin
--

GRANT INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE auth.mfa_factors TO postgres;
GRANT SELECT ON TABLE auth.mfa_factors TO postgres WITH GRANT OPTION;
GRANT ALL ON TABLE auth.mfa_factors TO dashboard_user;


--
-- Name: TABLE one_time_tokens; Type: ACL; Schema: auth; Owner: supabase_auth_admin
--

GRANT INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE auth.one_time_tokens TO postgres;
GRANT SELECT ON TABLE auth.one_time_tokens TO postgres WITH GRANT OPTION;
GRANT ALL ON TABLE auth.one_time_tokens TO dashboard_user;


--
-- Name: TABLE refresh_tokens; Type: ACL; Schema: auth; Owner: supabase_auth_admin
--

GRANT ALL ON TABLE auth.refresh_tokens TO dashboard_user;
GRANT INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE auth.refresh_tokens TO postgres;
GRANT SELECT ON TABLE auth.refresh_tokens TO postgres WITH GRANT OPTION;


--
-- Name: SEQUENCE refresh_tokens_id_seq; Type: ACL; Schema: auth; Owner: supabase_auth_admin
--

GRANT ALL ON SEQUENCE auth.refresh_tokens_id_seq TO dashboard_user;
GRANT ALL ON SEQUENCE auth.refresh_tokens_id_seq TO postgres;


--
-- Name: TABLE saml_providers; Type: ACL; Schema: auth; Owner: supabase_auth_admin
--

GRANT INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE auth.saml_providers TO postgres;
GRANT SELECT ON TABLE auth.saml_providers TO postgres WITH GRANT OPTION;
GRANT ALL ON TABLE auth.saml_providers TO dashboard_user;


--
-- Name: TABLE saml_relay_states; Type: ACL; Schema: auth; Owner: supabase_auth_admin
--

GRANT INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE auth.saml_relay_states TO postgres;
GRANT SELECT ON TABLE auth.saml_relay_states TO postgres WITH GRANT OPTION;
GRANT ALL ON TABLE auth.saml_relay_states TO dashboard_user;


--
-- Name: TABLE schema_migrations; Type: ACL; Schema: auth; Owner: supabase_auth_admin
--

GRANT SELECT ON TABLE auth.schema_migrations TO postgres WITH GRANT OPTION;


--
-- Name: TABLE sessions; Type: ACL; Schema: auth; Owner: supabase_auth_admin
--

GRANT INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE auth.sessions TO postgres;
GRANT SELECT ON TABLE auth.sessions TO postgres WITH GRANT OPTION;
GRANT ALL ON TABLE auth.sessions TO dashboard_user;


--
-- Name: TABLE sso_domains; Type: ACL; Schema: auth; Owner: supabase_auth_admin
--

GRANT INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE auth.sso_domains TO postgres;
GRANT SELECT ON TABLE auth.sso_domains TO postgres WITH GRANT OPTION;
GRANT ALL ON TABLE auth.sso_domains TO dashboard_user;


--
-- Name: TABLE sso_providers; Type: ACL; Schema: auth; Owner: supabase_auth_admin
--

GRANT INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE auth.sso_providers TO postgres;
GRANT SELECT ON TABLE auth.sso_providers TO postgres WITH GRANT OPTION;
GRANT ALL ON TABLE auth.sso_providers TO dashboard_user;


--
-- Name: TABLE users; Type: ACL; Schema: auth; Owner: supabase_auth_admin
--

GRANT ALL ON TABLE auth.users TO dashboard_user;
GRANT INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLE auth.users TO postgres;
GRANT SELECT ON TABLE auth.users TO postgres WITH GRANT OPTION;


--
-- Name: TABLE pg_stat_statements; Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON TABLE extensions.pg_stat_statements TO postgres WITH GRANT OPTION;


--
-- Name: TABLE pg_stat_statements_info; Type: ACL; Schema: extensions; Owner: supabase_admin
--

GRANT ALL ON TABLE extensions.pg_stat_statements_info TO postgres WITH GRANT OPTION;


--
-- Name: TABLE _dlt_loads; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public._dlt_loads TO anon;
GRANT ALL ON TABLE public._dlt_loads TO authenticated;
GRANT ALL ON TABLE public._dlt_loads TO service_role;


--
-- Name: TABLE _dlt_pipeline_state; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public._dlt_pipeline_state TO anon;
GRANT ALL ON TABLE public._dlt_pipeline_state TO authenticated;
GRANT ALL ON TABLE public._dlt_pipeline_state TO service_role;


--
-- Name: TABLE _dlt_version; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public._dlt_version TO anon;
GRANT ALL ON TABLE public._dlt_version TO authenticated;
GRANT ALL ON TABLE public._dlt_version TO service_role;


--
-- Name: TABLE app_opportunities; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.app_opportunities TO anon;
GRANT ALL ON TABLE public.app_opportunities TO authenticated;
GRANT ALL ON TABLE public.app_opportunities TO service_role;


--
-- Name: TABLE app_opportunities_test; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.app_opportunities_test TO anon;
GRANT ALL ON TABLE public.app_opportunities_test TO authenticated;
GRANT ALL ON TABLE public.app_opportunities_test TO service_role;


--
-- Name: TABLE app_opportunities_test_20251124_202640; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.app_opportunities_test_20251124_202640 TO anon;
GRANT ALL ON TABLE public.app_opportunities_test_20251124_202640 TO authenticated;
GRANT ALL ON TABLE public.app_opportunities_test_20251124_202640 TO service_role;


--
-- Name: TABLE app_opportunities_test_20251124_203609; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.app_opportunities_test_20251124_203609 TO anon;
GRANT ALL ON TABLE public.app_opportunities_test_20251124_203609 TO authenticated;
GRANT ALL ON TABLE public.app_opportunities_test_20251124_203609 TO service_role;


--
-- Name: TABLE competitive_landscape; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.competitive_landscape TO anon;
GRANT ALL ON TABLE public.competitive_landscape TO authenticated;
GRANT ALL ON TABLE public.competitive_landscape TO service_role;


--
-- Name: TABLE market_validations; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.market_validations TO anon;
GRANT ALL ON TABLE public.market_validations TO authenticated;
GRANT ALL ON TABLE public.market_validations TO service_role;


--
-- Name: TABLE monetization_patterns; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.monetization_patterns TO anon;
GRANT ALL ON TABLE public.monetization_patterns TO authenticated;
GRANT ALL ON TABLE public.monetization_patterns TO service_role;


--
-- Name: TABLE opportunities; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.opportunities TO anon;
GRANT ALL ON TABLE public.opportunities TO authenticated;
GRANT ALL ON TABLE public.opportunities TO service_role;


--
-- Name: TABLE opportunities_test_02_scaled; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.opportunities_test_02_scaled TO anon;
GRANT ALL ON TABLE public.opportunities_test_02_scaled TO authenticated;
GRANT ALL ON TABLE public.opportunities_test_02_scaled TO service_role;


--
-- Name: TABLE opportunity_scores; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.opportunity_scores TO anon;
GRANT ALL ON TABLE public.opportunity_scores TO authenticated;
GRANT ALL ON TABLE public.opportunity_scores TO service_role;


--
-- Name: TABLE submissions; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.submissions TO anon;
GRANT ALL ON TABLE public.submissions TO authenticated;
GRANT ALL ON TABLE public.submissions TO service_role;


--
-- Name: TABLE buckets; Type: ACL; Schema: storage; Owner: supabase_storage_admin
--

GRANT ALL ON TABLE storage.buckets TO anon;
GRANT ALL ON TABLE storage.buckets TO authenticated;
GRANT ALL ON TABLE storage.buckets TO service_role;
GRANT ALL ON TABLE storage.buckets TO postgres;


--
-- Name: TABLE buckets_analytics; Type: ACL; Schema: storage; Owner: supabase_storage_admin
--

GRANT ALL ON TABLE storage.buckets_analytics TO service_role;
GRANT ALL ON TABLE storage.buckets_analytics TO authenticated;
GRANT ALL ON TABLE storage.buckets_analytics TO anon;


--
-- Name: TABLE iceberg_namespaces; Type: ACL; Schema: storage; Owner: supabase_storage_admin
--

GRANT ALL ON TABLE storage.iceberg_namespaces TO service_role;
GRANT SELECT ON TABLE storage.iceberg_namespaces TO authenticated;
GRANT SELECT ON TABLE storage.iceberg_namespaces TO anon;


--
-- Name: TABLE iceberg_tables; Type: ACL; Schema: storage; Owner: supabase_storage_admin
--

GRANT ALL ON TABLE storage.iceberg_tables TO service_role;
GRANT SELECT ON TABLE storage.iceberg_tables TO authenticated;
GRANT SELECT ON TABLE storage.iceberg_tables TO anon;


--
-- Name: TABLE objects; Type: ACL; Schema: storage; Owner: supabase_storage_admin
--

GRANT ALL ON TABLE storage.objects TO anon;
GRANT ALL ON TABLE storage.objects TO authenticated;
GRANT ALL ON TABLE storage.objects TO service_role;
GRANT ALL ON TABLE storage.objects TO postgres;


--
-- Name: TABLE prefixes; Type: ACL; Schema: storage; Owner: supabase_storage_admin
--

GRANT ALL ON TABLE storage.prefixes TO service_role;
GRANT ALL ON TABLE storage.prefixes TO authenticated;
GRANT ALL ON TABLE storage.prefixes TO anon;


--
-- Name: TABLE s3_multipart_uploads; Type: ACL; Schema: storage; Owner: supabase_storage_admin
--

GRANT ALL ON TABLE storage.s3_multipart_uploads TO service_role;
GRANT SELECT ON TABLE storage.s3_multipart_uploads TO authenticated;
GRANT SELECT ON TABLE storage.s3_multipart_uploads TO anon;


--
-- Name: TABLE s3_multipart_uploads_parts; Type: ACL; Schema: storage; Owner: supabase_storage_admin
--

GRANT ALL ON TABLE storage.s3_multipart_uploads_parts TO service_role;
GRANT SELECT ON TABLE storage.s3_multipart_uploads_parts TO authenticated;
GRANT SELECT ON TABLE storage.s3_multipart_uploads_parts TO anon;


--
-- Name: TABLE hooks; Type: ACL; Schema: supabase_functions; Owner: supabase_functions_admin
--

GRANT ALL ON TABLE supabase_functions.hooks TO postgres;
GRANT ALL ON TABLE supabase_functions.hooks TO anon;
GRANT ALL ON TABLE supabase_functions.hooks TO authenticated;
GRANT ALL ON TABLE supabase_functions.hooks TO service_role;


--
-- Name: SEQUENCE hooks_id_seq; Type: ACL; Schema: supabase_functions; Owner: supabase_functions_admin
--

GRANT ALL ON SEQUENCE supabase_functions.hooks_id_seq TO postgres;
GRANT ALL ON SEQUENCE supabase_functions.hooks_id_seq TO anon;
GRANT ALL ON SEQUENCE supabase_functions.hooks_id_seq TO authenticated;
GRANT ALL ON SEQUENCE supabase_functions.hooks_id_seq TO service_role;


--
-- Name: TABLE migrations; Type: ACL; Schema: supabase_functions; Owner: supabase_functions_admin
--

GRANT ALL ON TABLE supabase_functions.migrations TO postgres;
GRANT ALL ON TABLE supabase_functions.migrations TO anon;
GRANT ALL ON TABLE supabase_functions.migrations TO authenticated;
GRANT ALL ON TABLE supabase_functions.migrations TO service_role;


--
-- Name: TABLE secrets; Type: ACL; Schema: vault; Owner: supabase_admin
--

GRANT SELECT,REFERENCES,DELETE,TRUNCATE ON TABLE vault.secrets TO postgres WITH GRANT OPTION;
GRANT SELECT,DELETE ON TABLE vault.secrets TO service_role;


--
-- Name: TABLE decrypted_secrets; Type: ACL; Schema: vault; Owner: supabase_admin
--

GRANT SELECT,REFERENCES,DELETE,TRUNCATE ON TABLE vault.decrypted_secrets TO postgres WITH GRANT OPTION;
GRANT SELECT,DELETE ON TABLE vault.decrypted_secrets TO service_role;


--
-- Name: DEFAULT PRIVILEGES FOR SEQUENCES; Type: DEFAULT ACL; Schema: auth; Owner: supabase_auth_admin
--

ALTER DEFAULT PRIVILEGES FOR ROLE supabase_auth_admin IN SCHEMA auth GRANT ALL ON SEQUENCES TO postgres;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_auth_admin IN SCHEMA auth GRANT ALL ON SEQUENCES TO dashboard_user;


--
-- Name: DEFAULT PRIVILEGES FOR FUNCTIONS; Type: DEFAULT ACL; Schema: auth; Owner: supabase_auth_admin
--

ALTER DEFAULT PRIVILEGES FOR ROLE supabase_auth_admin IN SCHEMA auth GRANT ALL ON FUNCTIONS TO postgres;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_auth_admin IN SCHEMA auth GRANT ALL ON FUNCTIONS TO dashboard_user;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: auth; Owner: supabase_auth_admin
--

ALTER DEFAULT PRIVILEGES FOR ROLE supabase_auth_admin IN SCHEMA auth GRANT ALL ON TABLES TO postgres;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_auth_admin IN SCHEMA auth GRANT ALL ON TABLES TO dashboard_user;


--
-- Name: DEFAULT PRIVILEGES FOR SEQUENCES; Type: DEFAULT ACL; Schema: extensions; Owner: supabase_admin
--

ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA extensions GRANT ALL ON SEQUENCES TO postgres WITH GRANT OPTION;


--
-- Name: DEFAULT PRIVILEGES FOR FUNCTIONS; Type: DEFAULT ACL; Schema: extensions; Owner: supabase_admin
--

ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA extensions GRANT ALL ON FUNCTIONS TO postgres WITH GRANT OPTION;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: extensions; Owner: supabase_admin
--

ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA extensions GRANT ALL ON TABLES TO postgres WITH GRANT OPTION;


--
-- Name: DEFAULT PRIVILEGES FOR SEQUENCES; Type: DEFAULT ACL; Schema: graphql; Owner: supabase_admin
--

ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA graphql GRANT ALL ON SEQUENCES TO postgres;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA graphql GRANT ALL ON SEQUENCES TO anon;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA graphql GRANT ALL ON SEQUENCES TO authenticated;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA graphql GRANT ALL ON SEQUENCES TO service_role;


--
-- Name: DEFAULT PRIVILEGES FOR FUNCTIONS; Type: DEFAULT ACL; Schema: graphql; Owner: supabase_admin
--

ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA graphql GRANT ALL ON FUNCTIONS TO postgres;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA graphql GRANT ALL ON FUNCTIONS TO anon;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA graphql GRANT ALL ON FUNCTIONS TO authenticated;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA graphql GRANT ALL ON FUNCTIONS TO service_role;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: graphql; Owner: supabase_admin
--

ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA graphql GRANT ALL ON TABLES TO postgres;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA graphql GRANT ALL ON TABLES TO anon;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA graphql GRANT ALL ON TABLES TO authenticated;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA graphql GRANT ALL ON TABLES TO service_role;


--
-- Name: DEFAULT PRIVILEGES FOR SEQUENCES; Type: DEFAULT ACL; Schema: graphql_public; Owner: supabase_admin
--

ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA graphql_public GRANT ALL ON SEQUENCES TO postgres;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA graphql_public GRANT ALL ON SEQUENCES TO anon;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA graphql_public GRANT ALL ON SEQUENCES TO authenticated;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA graphql_public GRANT ALL ON SEQUENCES TO service_role;


--
-- Name: DEFAULT PRIVILEGES FOR FUNCTIONS; Type: DEFAULT ACL; Schema: graphql_public; Owner: supabase_admin
--

ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA graphql_public GRANT ALL ON FUNCTIONS TO postgres;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA graphql_public GRANT ALL ON FUNCTIONS TO anon;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA graphql_public GRANT ALL ON FUNCTIONS TO authenticated;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA graphql_public GRANT ALL ON FUNCTIONS TO service_role;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: graphql_public; Owner: supabase_admin
--

ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA graphql_public GRANT ALL ON TABLES TO postgres;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA graphql_public GRANT ALL ON TABLES TO anon;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA graphql_public GRANT ALL ON TABLES TO authenticated;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA graphql_public GRANT ALL ON TABLES TO service_role;


--
-- Name: DEFAULT PRIVILEGES FOR SEQUENCES; Type: DEFAULT ACL; Schema: public; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON SEQUENCES TO postgres;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON SEQUENCES TO anon;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON SEQUENCES TO authenticated;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON SEQUENCES TO service_role;


--
-- Name: DEFAULT PRIVILEGES FOR SEQUENCES; Type: DEFAULT ACL; Schema: public; Owner: supabase_admin
--

ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA public GRANT ALL ON SEQUENCES TO postgres;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA public GRANT ALL ON SEQUENCES TO anon;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA public GRANT ALL ON SEQUENCES TO authenticated;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA public GRANT ALL ON SEQUENCES TO service_role;


--
-- Name: DEFAULT PRIVILEGES FOR FUNCTIONS; Type: DEFAULT ACL; Schema: public; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON FUNCTIONS TO postgres;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON FUNCTIONS TO anon;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON FUNCTIONS TO authenticated;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON FUNCTIONS TO service_role;


--
-- Name: DEFAULT PRIVILEGES FOR FUNCTIONS; Type: DEFAULT ACL; Schema: public; Owner: supabase_admin
--

ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA public GRANT ALL ON FUNCTIONS TO postgres;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA public GRANT ALL ON FUNCTIONS TO anon;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA public GRANT ALL ON FUNCTIONS TO authenticated;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA public GRANT ALL ON FUNCTIONS TO service_role;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: public; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON TABLES TO postgres;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON TABLES TO anon;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON TABLES TO authenticated;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON TABLES TO service_role;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: public; Owner: supabase_admin
--

ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA public GRANT ALL ON TABLES TO postgres;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA public GRANT ALL ON TABLES TO anon;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA public GRANT ALL ON TABLES TO authenticated;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA public GRANT ALL ON TABLES TO service_role;


--
-- Name: DEFAULT PRIVILEGES FOR SEQUENCES; Type: DEFAULT ACL; Schema: realtime; Owner: supabase_admin
--

ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA realtime GRANT ALL ON SEQUENCES TO postgres;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA realtime GRANT ALL ON SEQUENCES TO dashboard_user;


--
-- Name: DEFAULT PRIVILEGES FOR FUNCTIONS; Type: DEFAULT ACL; Schema: realtime; Owner: supabase_admin
--

ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA realtime GRANT ALL ON FUNCTIONS TO postgres;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA realtime GRANT ALL ON FUNCTIONS TO dashboard_user;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: realtime; Owner: supabase_admin
--

ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA realtime GRANT ALL ON TABLES TO postgres;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA realtime GRANT ALL ON TABLES TO dashboard_user;


--
-- Name: DEFAULT PRIVILEGES FOR SEQUENCES; Type: DEFAULT ACL; Schema: storage; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA storage GRANT ALL ON SEQUENCES TO postgres;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA storage GRANT ALL ON SEQUENCES TO anon;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA storage GRANT ALL ON SEQUENCES TO authenticated;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA storage GRANT ALL ON SEQUENCES TO service_role;


--
-- Name: DEFAULT PRIVILEGES FOR FUNCTIONS; Type: DEFAULT ACL; Schema: storage; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA storage GRANT ALL ON FUNCTIONS TO postgres;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA storage GRANT ALL ON FUNCTIONS TO anon;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA storage GRANT ALL ON FUNCTIONS TO authenticated;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA storage GRANT ALL ON FUNCTIONS TO service_role;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: storage; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA storage GRANT ALL ON TABLES TO postgres;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA storage GRANT ALL ON TABLES TO anon;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA storage GRANT ALL ON TABLES TO authenticated;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA storage GRANT ALL ON TABLES TO service_role;


--
-- Name: DEFAULT PRIVILEGES FOR SEQUENCES; Type: DEFAULT ACL; Schema: supabase_functions; Owner: supabase_admin
--

ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA supabase_functions GRANT ALL ON SEQUENCES TO postgres;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA supabase_functions GRANT ALL ON SEQUENCES TO anon;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA supabase_functions GRANT ALL ON SEQUENCES TO authenticated;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA supabase_functions GRANT ALL ON SEQUENCES TO service_role;


--
-- Name: DEFAULT PRIVILEGES FOR FUNCTIONS; Type: DEFAULT ACL; Schema: supabase_functions; Owner: supabase_admin
--

ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA supabase_functions GRANT ALL ON FUNCTIONS TO postgres;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA supabase_functions GRANT ALL ON FUNCTIONS TO anon;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA supabase_functions GRANT ALL ON FUNCTIONS TO authenticated;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA supabase_functions GRANT ALL ON FUNCTIONS TO service_role;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: supabase_functions; Owner: supabase_admin
--

ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA supabase_functions GRANT ALL ON TABLES TO postgres;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA supabase_functions GRANT ALL ON TABLES TO anon;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA supabase_functions GRANT ALL ON TABLES TO authenticated;
ALTER DEFAULT PRIVILEGES FOR ROLE supabase_admin IN SCHEMA supabase_functions GRANT ALL ON TABLES TO service_role;


--
-- Name: issue_graphql_placeholder; Type: EVENT TRIGGER; Schema: -; Owner: supabase_admin
--

CREATE EVENT TRIGGER issue_graphql_placeholder ON sql_drop
         WHEN TAG IN ('DROP EXTENSION')
   EXECUTE FUNCTION extensions.set_graphql_placeholder();


ALTER EVENT TRIGGER issue_graphql_placeholder OWNER TO supabase_admin;

--
-- Name: issue_pg_cron_access; Type: EVENT TRIGGER; Schema: -; Owner: supabase_admin
--

CREATE EVENT TRIGGER issue_pg_cron_access ON ddl_command_end
         WHEN TAG IN ('CREATE EXTENSION')
   EXECUTE FUNCTION extensions.grant_pg_cron_access();


ALTER EVENT TRIGGER issue_pg_cron_access OWNER TO supabase_admin;

--
-- Name: issue_pg_graphql_access; Type: EVENT TRIGGER; Schema: -; Owner: supabase_admin
--

CREATE EVENT TRIGGER issue_pg_graphql_access ON ddl_command_end
         WHEN TAG IN ('CREATE FUNCTION')
   EXECUTE FUNCTION extensions.grant_pg_graphql_access();


ALTER EVENT TRIGGER issue_pg_graphql_access OWNER TO supabase_admin;

--
-- Name: issue_pg_net_access; Type: EVENT TRIGGER; Schema: -; Owner: supabase_admin
--

CREATE EVENT TRIGGER issue_pg_net_access ON ddl_command_end
         WHEN TAG IN ('CREATE EXTENSION')
   EXECUTE FUNCTION extensions.grant_pg_net_access();


ALTER EVENT TRIGGER issue_pg_net_access OWNER TO supabase_admin;

--
-- Name: pgrst_ddl_watch; Type: EVENT TRIGGER; Schema: -; Owner: supabase_admin
--

CREATE EVENT TRIGGER pgrst_ddl_watch ON ddl_command_end
   EXECUTE FUNCTION extensions.pgrst_ddl_watch();


ALTER EVENT TRIGGER pgrst_ddl_watch OWNER TO supabase_admin;

--
-- Name: pgrst_drop_watch; Type: EVENT TRIGGER; Schema: -; Owner: supabase_admin
--

CREATE EVENT TRIGGER pgrst_drop_watch ON sql_drop
   EXECUTE FUNCTION extensions.pgrst_drop_watch();


ALTER EVENT TRIGGER pgrst_drop_watch OWNER TO supabase_admin;

--
-- PostgreSQL database dump complete
--

\unrestrict DbRlBskkgDqhWaSufMi9OJFSv4edAh3SxjPpyzrbh9N2thhjWEFDvrBawtqrbZT

