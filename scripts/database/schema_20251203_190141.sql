-- RedditHarbor Database Schema Dump
-- Generated: 2025-12-03 19:01:41
-- Database: reddit_harbor (localhost:54322)
-- Purpose: Complete schema structure backup
-- Note: This file contains table structures only, no data

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- AUTH SCHEMA TABLES
-- ================================================================================

CREATE TABLE auth.audit_log_entries (
    instance_id uuid NULL,
    id uuid NOT NULL,
    payload json NULL,
    created_at timestamp with time zone NULL,
    ip_address character varying(64) NOT NULL DEFAULT ''::character varying
);

CREATE TABLE auth.flow_state (
    id uuid NOT NULL,
    user_id uuid NULL,
    auth_code text NOT NULL,
    code_challenge_method USER-DEFINED NOT NULL,
    code_challenge text NOT NULL,
    provider_type text NOT NULL,
    provider_access_token text NULL,
    provider_refresh_token text NULL,
    created_at timestamp with time zone NULL,
    updated_at timestamp with time zone NULL,
    authentication_method text NOT NULL,
    auth_code_issued_at timestamp with time zone NULL
);

CREATE TABLE auth.identities (
    provider_id text NOT NULL,
    user_id uuid NOT NULL,
    identity_data jsonb NOT NULL,
    provider text NOT NULL,
    last_sign_in_at timestamp with time zone NULL,
    created_at timestamp with time zone NULL,
    updated_at timestamp with time zone NULL,
    email text NULL,
    id uuid NOT NULL DEFAULT gen_random_uuid()
);

CREATE TABLE auth.instances (
    id uuid NOT NULL,
    uuid uuid NULL,
    raw_base_config text NULL,
    created_at timestamp with time zone NULL,
    updated_at timestamp with time zone NULL
);

CREATE TABLE auth.mfa_amr_claims (
    session_id uuid NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    authentication_method text NOT NULL,
    id uuid NOT NULL
);

CREATE TABLE auth.mfa_challenges (
    id uuid NOT NULL,
    factor_id uuid NOT NULL,
    created_at timestamp with time zone NOT NULL,
    verified_at timestamp with time zone NULL,
    ip_address inet NOT NULL,
    otp_code text NULL,
    web_authn_session_data jsonb NULL
);

CREATE TABLE auth.mfa_factors (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    friendly_name text NULL,
    factor_type USER-DEFINED NOT NULL,
    status USER-DEFINED NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    secret text NULL,
    phone text NULL,
    last_challenged_at timestamp with time zone NULL,
    web_authn_credential jsonb NULL,
    web_authn_aaguid uuid NULL
);

CREATE TABLE auth.one_time_tokens (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    token_type USER-DEFINED NOT NULL,
    token_hash text NOT NULL,
    relates_to text NOT NULL,
    created_at timestamp without time zone NOT NULL DEFAULT now(),
    updated_at timestamp without time zone NOT NULL DEFAULT now()
);

CREATE TABLE auth.refresh_tokens (
    instance_id uuid NULL,
    id bigint NOT NULL DEFAULT nextval('auth.refresh_tokens_id_seq'::regclass),
    token character varying(255) NULL,
    user_id character varying(255) NULL,
    revoked boolean NULL,
    created_at timestamp with time zone NULL,
    updated_at timestamp with time zone NULL,
    parent character varying(255) NULL,
    session_id uuid NULL
);

CREATE TABLE auth.saml_providers (
    id uuid NOT NULL,
    sso_provider_id uuid NOT NULL,
    entity_id text NOT NULL,
    metadata_xml text NOT NULL,
    metadata_url text NULL,
    attribute_mapping jsonb NULL,
    created_at timestamp with time zone NULL,
    updated_at timestamp with time zone NULL,
    name_id_format text NULL
);

CREATE TABLE auth.saml_relay_states (
    id uuid NOT NULL,
    sso_provider_id uuid NOT NULL,
    request_id text NOT NULL,
    for_email text NULL,
    redirect_to text NULL,
    created_at timestamp with time zone NULL,
    updated_at timestamp with time zone NULL,
    flow_state_id uuid NULL
);

CREATE TABLE auth.schema_migrations (
    version character varying(255) NOT NULL
);

CREATE TABLE auth.sessions (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    created_at timestamp with time zone NULL,
    updated_at timestamp with time zone NULL,
    factor_id uuid NULL,
    aal USER-DEFINED NULL,
    not_after timestamp with time zone NULL,
    refreshed_at timestamp without time zone NULL,
    user_agent text NULL,
    ip inet NULL,
    tag text NULL
);

CREATE TABLE auth.sso_domains (
    id uuid NOT NULL,
    sso_provider_id uuid NOT NULL,
    domain text NOT NULL,
    created_at timestamp with time zone NULL,
    updated_at timestamp with time zone NULL
);

CREATE TABLE auth.sso_providers (
    id uuid NOT NULL,
    resource_id text NULL,
    created_at timestamp with time zone NULL,
    updated_at timestamp with time zone NULL,
    disabled boolean NULL
);

CREATE TABLE auth.users (
    instance_id uuid NULL,
    id uuid NOT NULL,
    aud character varying(255) NULL,
    role character varying(255) NULL,
    email character varying(255) NULL,
    encrypted_password character varying(255) NULL,
    email_confirmed_at timestamp with time zone NULL,
    invited_at timestamp with time zone NULL,
    confirmation_token character varying(255) NULL,
    confirmation_sent_at timestamp with time zone NULL,
    recovery_token character varying(255) NULL,
    recovery_sent_at timestamp with time zone NULL,
    email_change_token_new character varying(255) NULL,
    email_change character varying(255) NULL,
    email_change_sent_at timestamp with time zone NULL,
    last_sign_in_at timestamp with time zone NULL,
    raw_app_meta_data jsonb NULL,
    raw_user_meta_data jsonb NULL,
    is_super_admin boolean NULL,
    created_at timestamp with time zone NULL,
    updated_at timestamp with time zone NULL,
    phone text NULL DEFAULT NULL::character varying,
    phone_confirmed_at timestamp with time zone NULL,
    phone_change text NULL DEFAULT ''::character varying,
    phone_change_token character varying(255) NULL DEFAULT ''::character varying,
    phone_change_sent_at timestamp with time zone NULL,
    confirmed_at timestamp with time zone NULL,
    email_change_token_current character varying(255) NULL DEFAULT ''::character varying,
    email_change_confirm_status smallint NULL DEFAULT 0,
    banned_until timestamp with time zone NULL,
    reauthentication_token character varying(255) NULL DEFAULT ''::character varying,
    reauthentication_sent_at timestamp with time zone NULL,
    is_sso_user boolean NOT NULL DEFAULT false,
    deleted_at timestamp with time zone NULL,
    is_anonymous boolean NOT NULL DEFAULT false
);

-- PUBLIC SCHEMA TABLES
-- ================================================================================

CREATE TABLE public._dlt_loads (
    load_id character varying(64) NOT NULL,
    schema_name character varying NULL,
    status bigint NOT NULL,
    inserted_at timestamp with time zone NOT NULL,
    schema_version_hash character varying NULL
);

CREATE TABLE public._dlt_pipeline_state (
    version bigint NOT NULL,
    engine_version bigint NOT NULL,
    pipeline_name character varying NOT NULL,
    state character varying NOT NULL,
    created_at timestamp with time zone NOT NULL,
    version_hash character varying NULL,
    _dlt_load_id character varying(64) NOT NULL,
    _dlt_id character varying NOT NULL
);

CREATE TABLE public._dlt_version (
    version bigint NOT NULL,
    engine_version bigint NOT NULL,
    inserted_at timestamp with time zone NOT NULL,
    schema_name character varying NOT NULL,
    version_hash character varying NOT NULL,
    schema character varying NOT NULL
);

CREATE TABLE public.app_opportunities_backup_20251127_154500 (
    submission_id character varying NULL,
    problem_description character varying NULL,
    app_concept character varying NULL,
    core_functions character varying NULL,
    value_proposition character varying NULL,
    target_user character varying NULL,
    monetization_model character varying NULL,
    opportunity_score double precision NULL,
    final_score double precision NULL,
    status character varying NULL,
    ai_profile jsonb NULL,
    app_name character varying NULL,
    app_category character varying NULL,
    profession character varying NULL,
    core_problems jsonb NULL,
    dimension_scores jsonb NULL,
    priority character varying NULL,
    confidence numeric(38,9) NULL,
    evidence_based boolean NULL,
    trust_score double precision NULL,
    trust_badge character varying NULL,
    activity_score double precision NULL,
    trust_level character varying NULL,
    trust_badges jsonb NULL,
    monetization_score numeric(38,9) NULL,
    market_validation_score numeric(38,9) NULL,
    analyzed_at timestamp with time zone NULL,
    enrichment_version character varying NULL,
    pipeline_source character varying NULL,
    title character varying NULL,
    subreddit character varying NULL,
    reddit_score bigint NULL,
    _dlt_load_id character varying NULL,
    _dlt_id character varying NULL
);

CREATE TABLE public.competitive_landscape (
    opportunity_id character varying NOT NULL,
    competitor_name character varying NOT NULL,
    competitor_features jsonb NULL,
    competitive_analysis character varying NULL,
    market_share double precision NULL,
    pricing_model character varying NULL,
    target_market character varying NULL,
    source_url character varying NULL,
    confidence double precision NULL,
    extracted_at timestamp with time zone NULL,
    created_at timestamp with time zone NULL,
    _dlt_load_id character varying NOT NULL,
    _dlt_id character varying NOT NULL
);

CREATE TABLE public.market_validations (
    opportunity_id character varying NOT NULL,
    validation_type character varying NOT NULL,
    validation_source character varying NULL,
    validation_date timestamp with time zone NULL,
    validation_result jsonb NULL,
    confidence_score double precision NULL,
    notes character varying NULL,
    status character varying NULL,
    evidence_url character varying NULL,
    market_validation_score double precision NULL,
    market_data_quality_score double precision NULL,
    market_validation_reasoning character varying NULL,
    market_competitors_found jsonb NULL,
    market_size_tam double precision NULL,
    market_size_sam double precision NULL,
    market_size_growth double precision NULL,
    market_similar_launches bigint NULL,
    market_validation_cost_usd double precision NULL,
    search_queries_used jsonb NULL,
    urls_fetched jsonb NULL,
    extraction_stats jsonb NULL,
    jina_api_calls_count bigint NULL,
    jina_cache_hit_rate double precision NULL,
    _dlt_load_id character varying NOT NULL,
    _dlt_id character varying NOT NULL
);

CREATE TABLE public.monetization_patterns (
    opportunity_id character varying NOT NULL,
    pattern_type character varying NOT NULL,
    revenue_model character varying NULL,
    target_pricing double precision NULL,
    market_size double precision NULL,
    willingness_to_pay_score double precision NULL,
    customer_segment character varying NULL,
    price_sensitivity_score double precision NULL,
    revenue_potential_score double precision NULL,
    mentioned_price_points jsonb NULL,
    existing_payment_behavior character varying NULL,
    urgency_level character varying NULL,
    sentiment_toward_payment character varying NULL,
    payment_friction_indicators jsonb NULL,
    llm_monetization_score double precision NULL,
    confidence double precision NULL,
    reasoning character varying NULL,
    created_at timestamp with time zone NULL,
    _dlt_load_id character varying NOT NULL,
    _dlt_id character varying NOT NULL
);

CREATE TABLE public.opportunities (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    submission_id character varying(10) NOT NULL,
    reddit_title character varying(300) NOT NULL,
    reddit_url character varying(500) NOT NULL,
    subreddit character varying(100) NOT NULL,
    reddit_author character varying(100) NULL,
    reddit_upvotes integer NOT NULL DEFAULT 0,
    reddit_comments_count integer NOT NULL DEFAULT 0,
    reddit_created_at timestamp without time zone NOT NULL,
    app_title character varying(200) NOT NULL,
    app_concept text NOT NULL,
    problem_statement text NOT NULL,
    target_audience text NOT NULL,
    core_functions jsonb NOT NULL,
    market_demand double precision NOT NULL,
    pain_intensity double precision NOT NULL,
    monetization_potential double precision NOT NULL,
    competition_level double precision NOT NULL,
    technical_feasibility double precision NOT NULL,
    final_score double precision NOT NULL,
    confidence_score double precision NOT NULL,
    trust_level character varying(10) NOT NULL,
    content_quality_score double precision NOT NULL DEFAULT 50.0,
    is_spam boolean NOT NULL DEFAULT false,
    spam_indicators jsonb NULL,
    embedding jsonb NULL,
    analyzed_at timestamp without time zone NOT NULL DEFAULT now(),
    created_at timestamp without time zone NOT NULL DEFAULT now(),
    updated_at timestamp without time zone NOT NULL DEFAULT now(),
    is_duplicate boolean NOT NULL DEFAULT false,
    duplicate_of_id uuid NULL,
    embedding_vector USER-DEFINED NULL
);

CREATE TABLE public.opportunity_scores (
    opportunity_id character varying NOT NULL,
    market_demand double precision NOT NULL,
    pain_intensity double precision NOT NULL,
    competition_level double precision NOT NULL,
    technical_feasibility double precision NOT NULL,
    monetization_potential double precision NOT NULL,
    simplicity_score double precision NOT NULL,
    total_score double precision NULL,
    created_at timestamp with time zone NULL,
    updated_at timestamp with time zone NULL,
    _dlt_load_id character varying NOT NULL,
    _dlt_id character varying NOT NULL
);

CREATE TABLE public.submissions (
    submission_id character varying NOT NULL,
    title character varying NULL,
    selftext character varying NULL,
    author character varying NULL,
    subreddit character varying NULL,
    trust_score double precision NULL,
    trust_level character varying NULL,
    market_validation_score double precision NULL,
    opportunity_score double precision NULL,
    created_utc double precision NULL,
    reddit_score bigint NULL,
    _dlt_load_id character varying NOT NULL,
    _dlt_id character varying NOT NULL,
    reddit_id character varying NULL,
    text character varying NULL,
    content character varying NULL,
    upvotes bigint NULL,
    comments_count bigint NULL,
    url character varying NULL,
    created_at timestamp with time zone NULL,
    id character varying NULL,
    score bigint NULL,
    num_comments bigint NULL
);

-- STORAGE SCHEMA TABLES
-- ================================================================================

CREATE TABLE storage.buckets (
    id text NOT NULL,
    name text NOT NULL,
    owner uuid NULL,
    created_at timestamp with time zone NULL DEFAULT now(),
    updated_at timestamp with time zone NULL DEFAULT now(),
    public boolean NULL DEFAULT false,
    avif_autodetection boolean NULL DEFAULT false,
    file_size_limit bigint NULL,
    allowed_mime_types ARRAY NULL,
    owner_id text NULL,
    type USER-DEFINED NOT NULL DEFAULT 'STANDARD'::storage.buckettype
);

CREATE TABLE storage.buckets_analytics (
    id text NOT NULL,
    type USER-DEFINED NOT NULL DEFAULT 'ANALYTICS'::storage.buckettype,
    format text NOT NULL DEFAULT 'ICEBERG'::text,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now()
);

CREATE TABLE storage.iceberg_namespaces (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    bucket_id text NOT NULL,
    name text NOT NULL,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now()
);

CREATE TABLE storage.iceberg_tables (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    namespace_id uuid NOT NULL,
    bucket_id text NOT NULL,
    name text NOT NULL,
    location text NOT NULL,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now()
);

CREATE TABLE storage.migrations (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    hash character varying(40) NOT NULL,
    executed_at timestamp without time zone NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE storage.objects (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    bucket_id text NULL,
    name text NULL,
    owner uuid NULL,
    created_at timestamp with time zone NULL DEFAULT now(),
    updated_at timestamp with time zone NULL DEFAULT now(),
    last_accessed_at timestamp with time zone NULL DEFAULT now(),
    metadata jsonb NULL,
    path_tokens ARRAY NULL,
    version text NULL,
    owner_id text NULL,
    user_metadata jsonb NULL,
    level integer NULL
);

CREATE TABLE storage.prefixes (
    bucket_id text NOT NULL,
    name text NOT NULL,
    level integer NOT NULL,
    created_at timestamp with time zone NULL DEFAULT now(),
    updated_at timestamp with time zone NULL DEFAULT now()
);

CREATE TABLE storage.s3_multipart_uploads (
    id text NOT NULL,
    in_progress_size bigint NOT NULL DEFAULT 0,
    upload_signature text NOT NULL,
    bucket_id text NOT NULL,
    key text NOT NULL,
    version text NOT NULL,
    owner_id text NULL,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    user_metadata jsonb NULL
);

CREATE TABLE storage.s3_multipart_uploads_parts (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    upload_id text NOT NULL,
    size bigint NOT NULL DEFAULT 0,
    part_number integer NOT NULL,
    bucket_id text NOT NULL,
    key text NOT NULL,
    etag text NOT NULL,
    owner_id text NULL,
    version text NOT NULL,
    created_at timestamp with time zone NOT NULL DEFAULT now()
);

-- SCHEMA DUMP COMPLETED
-- ================================================================================
-- Total tables: 27
-- Generated by: RedditHarbor MCP Integration
-- Use this schema to recreate the database structure
-- For data restoration, use the corresponding data backup files