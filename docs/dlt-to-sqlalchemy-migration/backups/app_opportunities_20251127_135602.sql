--
-- PostgreSQL database dump
--

\restrict xVmpqELH042F4ob9RJSkOW29MfhnyEHQn6oXTlRzBFFOlYbwmCqwudDtDWqhZhu

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
-- Name: app_opportunities app_opportunities__dlt_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.app_opportunities
    ADD CONSTRAINT app_opportunities__dlt_id_key UNIQUE (_dlt_id);


--
-- Name: TABLE app_opportunities; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.app_opportunities TO anon;
GRANT ALL ON TABLE public.app_opportunities TO authenticated;
GRANT ALL ON TABLE public.app_opportunities TO service_role;


--
-- PostgreSQL database dump complete
--

\unrestrict xVmpqELH042F4ob9RJSkOW29MfhnyEHQn6oXTlRzBFFOlYbwmCqwudDtDWqhZhu

