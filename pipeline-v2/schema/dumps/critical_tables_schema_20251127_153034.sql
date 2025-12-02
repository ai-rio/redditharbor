--
-- PostgreSQL database dump
--

\restrict m9fgftnviUpenSBynQGkY1KJfZ06UHw2uBkdpN5ZL2lBCSP1qwoCM8HboH73aDE

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

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: app_opportunities; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: app_opportunities app_opportunities__dlt_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.app_opportunities
    ADD CONSTRAINT app_opportunities__dlt_id_key UNIQUE (_dlt_id);


--
-- PostgreSQL database dump complete
--

\unrestrict m9fgftnviUpenSBynQGkY1KJfZ06UHw2uBkdpN5ZL2lBCSP1qwoCM8HboH73aDE

