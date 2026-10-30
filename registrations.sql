-- Adminer 5.4.0 PostgreSQL 17.6 dump

DROP TABLE IF EXISTS "registrations";
DROP SEQUENCE IF EXISTS registrations_sign_id_seq;
CREATE SEQUENCE registrations_sign_id_seq INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 CACHE 1;

CREATE TABLE "public"."registrations" (
    "event_id" integer NOT NULL,
    "name" character varying(30) NOT NULL,
    "phone_number" character varying(15) NOT NULL,
    "sign_id" integer DEFAULT nextval('registrations_sign_id_seq') NOT NULL,
    CONSTRAINT "registrations_pkey" PRIMARY KEY ("sign_id"),
    CONSTRAINT "registrations_phone_check" CHECK ("phone_number" ~ '^0[2-9][0-9]{7,8}$')
)
WITH (oids = false);

INSERT INTO "registrations" ("event_id", "name", "phone_number", "sign_id") VALUES
(1,	'洪想你',	'0966123456',	11111),
(5,	'王員瑛',	'0973382476',	11112),
(3,	'文阿棼',	'0966666666',	11113);

SELECT setval('registrations_sign_id_seq', (SELECT MAX(sign_id) FROM registrations));

-- 2026-10-30 07:19:13 UTC

ALTER TABLE "public"."registrations"
ADD CONSTRAINT "fk_registrations_event_id" 
FOREIGN KEY ("event_id") 
REFERENCES "public"."activities" ("event_id")
ON UPDATE CASCADE
ON DELETE CASCADE;
