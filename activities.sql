-- Adminer 5.4.0 PostgreSQL 17.6 dump

DROP TABLE IF EXISTS "activities";
DROP SEQUENCE IF EXISTS activities_event_id_seq;
CREATE SEQUENCE activities_event_id_seq INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 CACHE 1;

CREATE TABLE "public"."activities" (
    "event_id" integer DEFAULT nextval('activities_event_id_seq') NOT NULL,
    "title" character varying(100) NOT NULL,
    "date" date NOT NULL,
    CONSTRAINT "activities_pkey" PRIMARY KEY ("event_id")
)
WITH (oids = false);

INSERT INTO "activities" ("event_id", "title", "date") VALUES
(1,	'暨大馬拉松',	'2027-01-10');
(2,	'英文歌唱比賽',	'2027-02-22');
(3,	'排球新生盃',	'2026-09-28');
(4,	'籃球管院盃',	'2027-03-02');


-- 2026-10-30 07:16:08 UTC
