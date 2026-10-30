-- Adminer 5.4.0 PostgreSQL 17.6 dump

DROP TABLE IF EXISTS "registrations";
DROP SEQUENCE IF EXISTS registrations_sign_id_seq;
CREATE SEQUENCE registrations_sign_id_seq INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 CACHE 1;

CREATE TABLE "public"."registrations" (
    "event_id" integer NOT NULL,
    "name" character varying(30) NOT NULL,
    "phone_number" character varying(15) NOT NULL,
    "sign_id" integer DEFAULT nextval('registrations_sign_id_seq') NOT NULL,
    CONSTRAINT "registrations_pkey" PRIMARY KEY ("sign_id")
)
WITH (oids = false);

INSERT INTO "registrations" ("event_id", "name", "phone_number", "sign_id") VALUES
(1,	'洪想你',	'0966123456',	11111);

-- 2026-10-30 07:19:13 UTC
